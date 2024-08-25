# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os
from typing import Iterable

from mypy.build import BuildResult
from mypyc.errors import Errors
from mypyc.options import CompilerOptions
from mypyc.namegen import NameGenerator, exported_name
from mypyc.ir.rtypes import RType
from mypyc.ir.func_ir import FuncIR
from mypyc.ir.module_ir import ModuleIR, ModuleIRs
from mypyc.irbuild.mapper import Mapper
from mypyc.codegen.emit import Emitter, EmitterContext, HeaderDeclaration, c_array_initializer
from mypyc.codegen.emitclass import generate_class
from mypyc.codegen.emitfunc import generate_native_function
from mypyc.codegen.emitwrapper import (
    generate_legacy_wrapper_function,
    generate_wrapper_function,
)
from mypyc.codegen.emitmodule import (
    Groups,
    FileContents,
    MarkedDeclaration,
    compile_modules_to_ir,
    write_cache,
    collect_literals,
    is_fastcall_supported,
    group_dir,
    c_string_array_initializer,
)
from mypyc.common import (
    PREFIX,
    NATIVE_PREFIX,
    MODULE_PREFIX,
    STATIC_PREFIX,
    TYPE_PREFIX,
    TYPE_VAR_PREFIX,
    TOP_LEVEL_NAME,
    short_id_from_name,
)

from tfreezer.mypyc_handler.codegen.emitfunc import native_function_header
from tfreezer.mypyc_handler.codegen.emitclass import generate_class_type_decl
from tfreezer.mypyc_handler.codegen.emitwrapper import wrapper_function_header, legacy_wrapper_function_header


def compile_ir_to_c(
    groups: Groups,
    modules: ModuleIRs,
    result: BuildResult,
    mapper: Mapper,
    compiler_options: CompilerOptions,
) -> dict[str | None, list[tuple[str, str]]]:
    """
    Our own implementation of `compile_ir_to_c`.
    Compile a collection of ModuleIRs to C source text.

    Returns a dictionary mapping group names to a list of (file name,
    file text) pairs.
    """
    source_paths = {source.module: result.graph[source.module].xpath for sources, _ in groups for source in sources}

    names = NameGenerator([[source.module for source in sources] for sources, _ in groups])

    # Generate C code for each compilation group. Each group will be
    # compiled into a separate extension module.
    ctext: dict[str | None, list[tuple[str, str]]] = {}
    for group_sources, group_name in groups:
        assert group_name is not None
        group_modules = {source.module: modules[source.module] for source in group_sources if source.module in modules}
        if not group_modules:
            ctext[group_name] = []
            continue
        generator = GroupGenerator(group_modules, source_paths, group_name, mapper.group_map, names, compiler_options)
        ctext[group_name] = generator.generate_c_for_modules()

    return ctext


def compile_modules_to_c(
    result: BuildResult, compiler_options: CompilerOptions, errors: Errors, groups: Groups
) -> tuple[ModuleIRs, list[FileContents]]:
    """
    Our own implementation of `compile_modules_to_c`.
    Compile Python module(s) to the source of Python C extension modules.

    This generates the source code for the "shared library" module
    for each group. The shim modules are generated in mypyc.build.
    Each shared library module provides, for each module in its group,
    a PyCapsule containing an initialization function.
    Additionally, it provides a capsule containing an export table of
    pointers to all of the group's functions and static variables.

    Arguments:
        result: The BuildResult from the mypy front-end
        compiler_options: The compilation options
        errors: Where to report any errors encountered
        groups: The groups that we are compiling. See documentation of Groups type above.

    Returns the IR of the modules and a list containing the generated files for each group.
    """
    # Construct a map from modules to what group they belong to
    group_map = {source.module: lib_name for group, lib_name in groups for source in group}
    mapper = Mapper(group_map)

    # Sometimes when we call back into mypy, there might be errors.
    # We don't want to crash when that happens.
    result.manager.errors.set_file("<mypyc>", module=None, scope=None, options=result.manager.options)

    modules = compile_modules_to_ir(result, mapper, compiler_options, errors)
    if errors.num_errors > 0:
        return {}, []

    ctext = compile_ir_to_c(groups, modules, result, mapper, compiler_options)
    write_cache(modules, result, group_map, ctext)

    return modules, [ctext[name] for _, name in groups]


def generate_function_declaration(fn: FuncIR, emitter: Emitter, module_name: str) -> None:
    native_fn_name = f"{NATIVE_PREFIX}{fn.cname(emitter.names)}_{exported_name(module_name)}"
    emitter.context.declarations[native_fn_name] = HeaderDeclaration(
        f"{native_function_header(fn.decl, emitter, module_name)};", needs_export=True
    )
    if fn.name != TOP_LEVEL_NAME:
        py_fn_name = f"{PREFIX}{fn.cname(emitter.names)}_{exported_name(module_name)}"
        if is_fastcall_supported(fn, emitter.capi_version):
            emitter.context.declarations[py_fn_name] = HeaderDeclaration(f"{wrapper_function_header(fn, emitter.names, module_name)};")
        else:
            emitter.context.declarations[py_fn_name] = HeaderDeclaration(
                f"{legacy_wrapper_function_header(fn, emitter.names, module_name)};"
            )


class GroupGenerator:
    def __init__(
        self,
        modules: dict[str, ModuleIR],
        source_paths: dict[str, str],
        group_name: str,
        group_map: dict[str, str | None],
        names: NameGenerator,
        compiler_options: CompilerOptions,
    ) -> None:
        """
        Our own implementation of `GroupGenerator`.
        Generator for C source for a compilation group.

        The code for a compilation group contains an internal and an
        external .h file, and then one .c if not in multi_file mode or
        one .c file per module if in multi_file mode.)

        Arguments:
            modules: (name, ir) pairs for each module in the group
            source_paths: Map from module names to source file paths
            group_name: The name of the group (or None if this is single-module compilation)
            group_map: A map of modules to their group names
            names: The name generator for the compilation
            multi_file: Whether to put each module in its own source file regardless
                        of group structure.
        """
        self.modules = modules
        self.source_paths = source_paths
        self.context = EmitterContext(names, group_name, group_map)
        self.names = names
        # Initializations of globals to simple values that we can't
        # do statically because the windows loader is bad.
        self.simple_inits: list[tuple[str, str]] = []
        self.group_name = group_name
        self.compiler_options = compiler_options
        self.multi_file = compiler_options.multi_file

    @property
    def group_suffix(self) -> str:
        return "_" + exported_name(self.group_name)

    @property
    def module_name_no_dot(self) -> str:
        return exported_name(self.group_name)

    def type_name_map(self, module_name: str, module: ModuleIR, emitter: Emitter) -> dict[str, str]:
        name_map: dict[str, str] = {}
        for cl in module.classes:
            original_type_name = f"{TYPE_PREFIX}{cl.name}"
            type_name = f"{TYPE_PREFIX}{cl.name}_{module_name}"
            name_map[original_type_name] = type_name
        return name_map

    def function_name_map(self, module_name: str, module: ModuleIR, emitter: Emitter) -> dict[str, str]:
        name_map: dict[str, str] = {}
        for cl in module.classes:
            original_native_ctor_name = f"{NATIVE_PREFIX}{cl.ctor.cname(emitter.names)}("
            native_ctor_name = f"{NATIVE_PREFIX}{cl.ctor.cname(emitter.names)}_{exported_name(module_name)}("
            name_map[original_native_ctor_name] = native_ctor_name
        for fn in module.functions:
            original_native_fn_name = f"{NATIVE_PREFIX}{fn.cname(emitter.names)}"
            native_fn_name = f"{NATIVE_PREFIX}{fn.cname(emitter.names)}_{exported_name(module_name)}"
            name_map[original_native_fn_name] = native_fn_name
            original_py_fn_name = f"{PREFIX}{fn.cname(emitter.names)}"
            py_fn_name = f"{PREFIX}{fn.cname(emitter.names)}_{exported_name(module_name)}"
            name_map[original_py_fn_name] = py_fn_name
        return name_map

    def generate_c_for_modules(self) -> list[tuple[str, str]]:
        file_contents = []

        # Collect all literal refs in IR.
        for module in self.modules.values():
            for fn in module.functions:
                collect_literals(fn, self.context.literals)

        base_emitter = Emitter(self.context)
        base_emitter.emit_line(f'#include "{self.module_name_no_dot}.h"')
        base_emitter.emit_line(f'#include "{self.module_name_no_dot}_internal.h"')
        emitter = base_emitter

        self.generate_literal_tables()

        for module_name, module in self.modules.items():
            self.declare_module(module_name, emitter)
            self.declare_internal_globals(module_name, emitter)
            self.declare_imports(module.imports, emitter)

            # region tfreezer class mod
            current_line_index = len(emitter.fragments)
            for cl in module.classes:
                if cl.is_ext_class:
                    generate_class(cl, module_name, emitter)
            function_name_map = self.function_name_map(module_name, module, emitter)
            type_name_map = self.type_name_map(module_name, module, emitter)
            for i in range(current_line_index, len(emitter.fragments)):
                line = emitter.fragments[i]
                for original_name, new_name in function_name_map.items():
                    if original_name in line:
                        line = line.replace(original_name, new_name)
                        emitter.fragments[i] = line
                        break
                for original_name, new_name in type_name_map.items():
                    if original_name in line:
                        line = line.replace(original_name, new_name)
                        emitter.fragments[i] = line
                        break
            # endregion

            # Generate Python extension module definitions and module initialization functions.
            self.generate_module_def(emitter, module_name, module)

            for fn in module.functions:
                emitter.emit_line()
                # region tfreezer func mod
                current_line_index = len(emitter.fragments)
                generate_native_function(fn, emitter, self.source_paths[module_name], module_name)
                if fn.name != TOP_LEVEL_NAME:
                    emitter.emit_line()
                    if is_fastcall_supported(fn, emitter.capi_version):
                        generate_wrapper_function(fn, emitter, self.source_paths[module_name], module_name)
                    else:
                        generate_legacy_wrapper_function(fn, emitter, self.source_paths[module_name], module_name)
                for i in range(current_line_index, len(emitter.fragments)):
                    line = emitter.fragments[i]
                    global_var_name = f"{STATIC_PREFIX}globals"
                    py_fn_name = f"{PREFIX}{fn.cname(emitter.names)}"
                    native_fn_name = f"{NATIVE_PREFIX}{fn.cname(emitter.names)}"
                    if global_var_name in line:
                        line = line.replace(global_var_name, f"{STATIC_PREFIX}{exported_name(module_name)}_globals")
                        emitter.fragments[i] = line
                    elif "CPyStatics[" in line:
                        line = line.replace("CPyStatics[", f"CPyStatics{self.group_suffix}[")
                        emitter.fragments[i] = line
                    elif py_fn_name in line:
                        line = line.replace(py_fn_name, f"{PREFIX}{fn.cname(emitter.names)}_{exported_name(module_name)}")
                        emitter.fragments[i] = line
                    elif native_fn_name in line:
                        line = line.replace(native_fn_name, f"{NATIVE_PREFIX}{fn.cname(emitter.names)}_{exported_name(module_name)}")
                        emitter.fragments[i] = line
                    for original_name, new_name in type_name_map.items():
                        if original_name in line:
                            line = line.replace(original_name, new_name)
                            emitter.fragments[i] = line
                            break
                # endregion

        # The external header file contains type declarations while
        # the internal contains declarations of functions and objects
        # (which are shared between shared libraries via dynamic
        # exports tables and not accessed directly.)
        ext_declarations = Emitter(self.context)
        ext_declarations.emit_line(f"#ifndef MYPYC_NATIVE{self.group_suffix}_H")
        ext_declarations.emit_line(f"#define MYPYC_NATIVE{self.group_suffix}_H")
        ext_declarations.emit_line("#include <Python.h>")
        ext_declarations.emit_line("#include <CPy.h>")
        ext_declarations.emit_line("#ifdef __cplusplus")
        ext_declarations.emit_line('extern "C" {')
        ext_declarations.emit_line("#endif")
        ext_declarations.emit_line(f"PyMODINIT_FUNC PyInit_{self.module_name_no_dot}(void);")

        declarations = Emitter(self.context)
        declarations.emit_line(f"#ifndef MYPYC_NATIVE_INTERNAL{self.group_suffix}_H")
        declarations.emit_line(f"#define MYPYC_NATIVE_INTERNAL{self.group_suffix}_H")
        declarations.emit_line("#include <Python.h>")
        declarations.emit_line("#include <CPy.h>")
        declarations.emit_line(f'#include "{self.module_name_no_dot}.h"')
        declarations.emit_line()
        declarations.emit_line(f"int CPyGlobalsInit{self.group_suffix}(void);")
        declarations.emit_line()

        for module_name, module in self.modules.items():
            self.declare_finals(module_name, module.final_names, declarations)
            for cl in module.classes:
                generate_class_type_decl(cl, emitter, ext_declarations, declarations)
            self.declare_type_vars(module_name, module.type_var_names, declarations)
            for fn in module.functions:
                generate_function_declaration(fn, declarations, module_name)

        for lib in sorted(self.context.group_deps):
            elib = exported_name(lib)
            # short_lib = exported_name(lib.split(".")[-1])
            declarations.emit_lines(
                f"#include <{os.path.join(group_dir(lib), f'{elib}.h')}>",
                f"struct export_table_{elib} exports_{elib};",
            )

        sorted_decls = self.toposort_declarations()

        emitter = base_emitter
        self.generate_globals_init(emitter)

        emitter.emit_line()

        for declaration in sorted_decls:
            decls = ext_declarations if declaration.is_type else declarations
            if not declaration.is_type:
                decls.emit_lines(f"{declaration.decl[0]}", *declaration.decl[1:])
                # If there is a definition, emit it. Otherwise repeat the declaration
                # (without an extern).
                if declaration.defn:
                    emitter.emit_lines(*declaration.defn)
                else:
                    emitter.emit_lines(*declaration.decl)
            else:
                decls.emit_lines(*declaration.decl)

        ext_declarations.emit_line("#ifdef __cplusplus")
        ext_declarations.emit_line("}")
        ext_declarations.emit_line("#endif")
        ext_declarations.emit_line("#endif")
        declarations.emit_line("#endif")

        # output_dir = group_dir(self.group_name)
        return file_contents + [
            (
                f"{self.module_name_no_dot}.c",
                "".join(emitter.fragments),
            ),
            (
                f"{self.module_name_no_dot}_internal.h",
                "".join(declarations.fragments),
            ),
            (
                f"{self.module_name_no_dot}.h",
                "".join(ext_declarations.fragments),
            ),
        ]

    def generate_literal_tables(self) -> None:
        """
        Generate tables containing descriptions of Python literals to construct.

        We will store the constructed literals in a single array that contains
        literals of all types. This way we can refer to an arbitrary literal by
        its index.
        """
        literals = self.context.literals
        # During module initialization we store all the constructed objects here
        self.declare_global(f"PyObject *[{literals.num_literals()}]", f"CPyStatics{self.group_suffix}")
        # Descriptions of str literals
        init_str = c_string_array_initializer(literals.encoded_str_values())
        self.declare_global("const char * const []", f"CPyLit_Str{self.group_suffix}", initializer=init_str)
        # Descriptions of bytes literals
        init_bytes = c_string_array_initializer(literals.encoded_bytes_values())
        self.declare_global("const char * const []", f"CPyLit_Bytes{self.group_suffix}", initializer=init_bytes)
        # Descriptions of int literals
        init_int = c_string_array_initializer(literals.encoded_int_values())
        self.declare_global("const char * const []", f"CPyLit_Int{self.group_suffix}", initializer=init_int)
        # Descriptions of float literals
        init_floats = c_array_initializer(literals.encoded_float_values())
        self.declare_global("const double []", f"CPyLit_Float{self.group_suffix}", initializer=init_floats)
        # Descriptions of complex literals
        init_complex = c_array_initializer(literals.encoded_complex_values())
        self.declare_global("const double []", f"CPyLit_Complex{self.group_suffix}", initializer=init_complex)
        # Descriptions of tuple literals
        init_tuple = c_array_initializer(literals.encoded_tuple_values())
        self.declare_global("const int []", f"CPyLit_Tuple{self.group_suffix}", initializer=init_tuple)
        # Descriptions of frozenset literals
        init_frozenset = c_array_initializer(literals.encoded_frozenset_values())
        self.declare_global("const int []", f"CPyLit_FrozenSet{self.group_suffix}", initializer=init_frozenset)

    def generate_globals_init(self, emitter: Emitter) -> None:
        emitter.emit_lines(
            "",
            f"int CPyGlobalsInit{self.group_suffix}(void)",
            "{",
            "static int is_initialized = 0;",
            "if (is_initialized) return 0;",
            "",
        )

        emitter.emit_line("CPy_Init();")
        for symbol, fixup in self.simple_inits:
            emitter.emit_line(f"{symbol} = {fixup};")

        values = f"CPyLit_Str{self.group_suffix}, CPyLit_Bytes{self.group_suffix}, CPyLit_Int{self.group_suffix}, CPyLit_Float{self.group_suffix}, CPyLit_Complex{self.group_suffix}, CPyLit_Tuple{self.group_suffix}, CPyLit_FrozenSet{self.group_suffix}"  # pylint:disable=line-too-long
        emitter.emit_lines(f"if (CPyStatics_Initialize(CPyStatics{self.group_suffix}, {values}) < 0) {{", "return -1;", "}")

        emitter.emit_lines("is_initialized = 1;", "return 0;", "}")

    def generate_module_def(self, emitter: Emitter, module_name: str, module: ModuleIR) -> None:
        """Emit the PyModuleDef struct for a module and the module init function."""
        # Emit module methods
        module_prefix = emitter.names.private_name(module_name)
        emitter.emit_line(f"static PyMethodDef {module_prefix}module_methods[] = {{")
        for fn in module.functions:
            if fn.class_name is not None or fn.name == TOP_LEVEL_NAME:
                continue
            name = short_id_from_name(fn.name, fn.decl.shortname, fn.line)
            if is_fastcall_supported(fn, emitter.capi_version):
                flag = "METH_FASTCALL"
            else:
                flag = "METH_VARARGS"
            emitter.emit_line(
                ('{{"{name}", (PyCFunction){prefix}{cname}_{suffix}, {flag} | METH_KEYWORDS, ' "NULL /* docstring */}},").format(
                    name=name, cname=fn.cname(emitter.names), prefix=PREFIX, suffix=exported_name(module_name), flag=flag
                )
            )
        emitter.emit_line("{NULL, NULL, 0, NULL}")
        emitter.emit_line("};")
        emitter.emit_line()

        # Emit module definition struct
        emitter.emit_lines(
            f"static struct PyModuleDef {module_prefix}module = {{",
            "PyModuleDef_HEAD_INIT,",
            f'"{module_name}",',
            "NULL, /* docstring */",
            "-1,       /* size of per-interpreter state of the module,",
            "             or -1 if the module keeps state in global variables. */",
            f"{module_prefix}module_methods",
            "};",
        )
        emitter.emit_line()

        declaration = f"PyMODINIT_FUNC PyInit_{exported_name(module_name)}(void)"
        emitter.emit_lines(declaration, "{")
        emitter.emit_line("PyObject* modname = NULL;")
        # Store the module reference in a static and return it when necessary.
        # This is separate from the *global* reference to the module that will
        # be populated when it is imported by a compiled module. We want that
        # reference to only be populated when the module has been successfully
        # imported, whereas this we want to have to stop a circular import.
        module_static = self.module_internal_static_name(module_name, emitter)
        emitter.emit_lines(
            f"if ({module_static}) {{",
            f"Py_INCREF({module_static});",
            f"return {module_static};",
            "}",
        )

        emitter.emit_lines(
            f"{module_static} = PyModule_Create(&{module_prefix}module);",
            f"if (unlikely({module_static} == NULL))",
            "    goto fail;",
        )
        emitter.emit_line(f'modname = PyObject_GetAttrString((PyObject *){module_static}, "__name__");')

        module_globals = f"{STATIC_PREFIX}{exported_name(module_name)}_globals"
        emitter.emit_lines(
            f"{module_globals} = PyModule_GetDict({module_static});",
            f"if (unlikely({module_globals} == NULL))",
            "    goto fail;",
        )

        # HACK: Manually instantiate generated classes here
        type_structs: list[str] = []
        for cl in module.classes:
            type_struct = f"{TYPE_PREFIX}{cl.name}_{cl.module_name}"
            type_structs.append(type_struct)
            if cl.is_generated:
                emitter.emit_lines(
                    "{t} = (PyTypeObject *)CPyType_FromTemplate(" "(PyObject *){t}_template, NULL, modname);".format(t=type_struct)
                )
                emitter.emit_lines(f"if (unlikely(!{type_struct}))", "    goto fail;")

        emitter.emit_lines(f"if (CPyGlobalsInit_{exported_name(module_name)}() < 0)", "    goto fail;")

        self.generate_top_level_call(module_name, module, emitter)

        emitter.emit_lines("Py_DECREF(modname);")

        emitter.emit_line(f"return {module_static};")
        emitter.emit_lines("fail:", f"Py_CLEAR({module_static});", "Py_CLEAR(modname);")
        for name, typ in module.final_names:
            static_name = emitter.static_name(name, module_name)
            emitter.emit_dec_ref(static_name, typ, is_xdec=True)
            undef = emitter.c_undefined_value(typ)
            emitter.emit_line(f"{static_name} = {undef};")
        # the type objects returned from CPyType_FromTemplate are all new references
        # so we have to decref them
        for t in type_structs:
            emitter.emit_line(f"Py_CLEAR({t});")
        emitter.emit_line("return NULL;")
        emitter.emit_line("}")

    def generate_top_level_call(self, module_name: str, module: ModuleIR, emitter: Emitter) -> None:
        """Generate call to function representing module top level."""
        # Optimization: we tend to put the top level last, so reverse iterate
        for fn in reversed(module.functions):
            if fn.name == TOP_LEVEL_NAME:
                emitter.emit_lines(
                    f"char result = {emitter.native_function_name(fn.decl)}_{exported_name(module_name)}();",
                    "if (result == 2)",
                    "    goto fail;",
                )
                break

    def toposort_declarations(self) -> list[HeaderDeclaration]:
        """Topologically sort the declaration dict by dependencies.

        Declarations can require other declarations to come prior in C (such as declaring structs).
        In order to guarantee that the C output will compile the declarations will thus need to
        be properly ordered. This simple DFS guarantees that we have a proper ordering.

        This runs in O(V + E).
        """
        result = []
        marked_declarations: dict[str, MarkedDeclaration] = {}
        for k, v in self.context.declarations.items():
            marked_declarations[k] = MarkedDeclaration(v, False)

        def _toposort_visit(name: str) -> None:
            decl = marked_declarations[name]
            if decl.mark:
                return

            for child in decl.declaration.dependencies:
                _toposort_visit(child)

            result.append(decl.declaration)
            decl.mark = True

        for name in marked_declarations:
            _toposort_visit(name)

        return result

    def declare_global(self, type_spaced: str, name: str, *, initializer: str | None = None) -> None:
        if "[" not in type_spaced:
            base = f"{type_spaced}{name}"
        else:
            a, b = type_spaced.split("[", 1)
            base = f"{a}{name}[{b}"

        if not initializer:
            defn = None
        else:
            defn = [f"{base} = {initializer};"]
        if name not in self.context.declarations:
            self.context.declarations[name] = HeaderDeclaration(f"{base};", defn=defn)

    def declare_internal_globals(self, module_name: str, emitter: Emitter) -> None:
        static_name = f"{STATIC_PREFIX}{exported_name(module_name)}_globals"
        self.declare_global("PyObject *", static_name)

    def module_internal_static_name(self, module_name: str, emitter: Emitter) -> str:
        return emitter.static_name(module_name + "_internal", None, prefix=MODULE_PREFIX)

    def declare_module(self, module_name: str, emitter: Emitter) -> None:
        # We declare two globals for each compiled module:
        # one used internally in the implementation of module init to cache results
        # and prevent infinite recursion in import cycles, and one used
        # by other modules to refer to it.
        if module_name in self.modules:
            internal_static_name = self.module_internal_static_name(module_name, emitter)
            self.declare_global("CPyModule *", internal_static_name, initializer="NULL")
        static_name = emitter.static_name(module_name, None, prefix=MODULE_PREFIX)
        self.declare_global("CPyModule *", static_name)
        self.simple_inits.append((static_name, "Py_None"))

    def declare_imports(self, imps: Iterable[str], emitter: Emitter) -> None:
        for imp in imps:
            self.declare_module(imp, emitter)

    def declare_finals(self, module: str, final_names: Iterable[tuple[str, RType]], emitter: Emitter) -> None:
        for name, typ in final_names:
            static_name = emitter.static_name(name, module)
            emitter.context.declarations[static_name] = HeaderDeclaration(
                f"{emitter.ctype_spaced(typ)}{static_name};",
                [self.final_definition(module, name, typ, emitter)],
                needs_export=True,
            )

    def final_definition(self, module: str, name: str, typ: RType, emitter: Emitter) -> str:
        static_name = emitter.static_name(name, module)
        # Here we rely on the fact that undefined value and error value are always the same
        undefined = emitter.c_initializer_undefined_value(typ)
        return f"{emitter.ctype_spaced(typ)}{static_name} = {undefined};"

    def declare_static_pyobject(self, identifier: str, emitter: Emitter) -> None:
        symbol = emitter.static_name(identifier, None)
        self.declare_global("PyObject *", symbol)

    def declare_type_vars(self, module: str, type_var_names: list[str], emitter: Emitter) -> None:
        for name in type_var_names:
            static_name = emitter.static_name(name, module, prefix=TYPE_VAR_PREFIX)
            emitter.context.declarations[static_name] = HeaderDeclaration(
                f"PyObject *{static_name};",
                [f"PyObject *{static_name} = NULL;"],
                needs_export=False,
            )
