# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os
import pathlib
import typing as _t

from mypyc.codegen import emitmodule
from mypyc import options, common, namegen
from mypyc.build import include_dir

from tfreezer import paths
from tfreezer.mypyc_handler import build


class MyPycModuleInfo(_t.NamedTuple):
    name: str
    py_path: str
    groups: emitmodule.Groups
    group_cfilenames: list[tuple[list[str], list[str]]]


class MyPycSourceGenerator:

    _public_header_name = "__native.h"
    _private_header_name = "__native_internal.h"

    def __init__(self):
        self._modules: dict[str, MyPycModuleInfo] = {}
        self._target_dir = os.path.join(paths.BUILD_DIR, "generated", "mypyc_modules")

    def generate(self, module_name: str, module_path: str) -> None:
        target_dir = self._target_dir
        compiler_options = options.CompilerOptions(multi_file=True, target_dir=target_dir)
        groups, group_cfilenames = build.mypyc_build([module_path], compiler_options)
        mypyc_module_info = MyPycModuleInfo(module_name, module_path, groups, group_cfilenames)
        self._modules[module_name] = mypyc_module_info

    def dump_mypyc_info(self) -> None:
        """
        Dump mypyc extra sources and include directories
        """
        if not self._modules:
            return
        mypyc_modules_lines: list[str] = []
        initialize_macro_lines = ["#define INITIALIZE_MYPYC_MODULES"]
        mypyc_lib_rt_dir = include_dir()
        include_dirs = [mypyc_lib_rt_dir]
        sources = [os.path.join(mypyc_lib_rt_dir, runtime_c).replace("\\", "/") for runtime_c in common.RUNTIME_C_FILES]
        for module_name, module_info in self._modules.items():
            exported_name = namegen.exported_name(module_name)
            mypyc_modules_lines.append(f'#include "{exported_name}.h"')
            initialize_macro_lines[-1] += " \\"
            initialize_macro_lines.append(f'    PyImport_AppendInittab("{module_name}", &PyInit_{exported_name});')
            groups = module_info.groups
            group_cfilenames = module_info.group_cfilenames
            for (group_sources, lib_name), (cfilenames, deps) in zip(groups, group_cfilenames):  # pylint:disable=unused-variable
                # print(group_sources, lib_name, cfilenames, deps)
                sources.extend(cfilenames)
                sources.extend(deps)
        include_dirs = [the_path.replace("\\", "/") for the_path in include_dirs]
        sources = [the_path.replace("\\", "/") for the_path in sources]
        mypyc_include_dirs_path = os.path.join(paths.BUILD_DIR, "mypyc_include_dirs")
        with open(mypyc_include_dirs_path, "w", encoding="utf-8") as fp:
            fp.write(";".join(include_dirs))
        mypyc_sources_path = os.path.join(paths.BUILD_DIR, "mypyc_sources")
        with open(mypyc_sources_path, "w", encoding="utf-8") as fp:
            fp.write(";".join(sources))
        mypyc_modules_lines.append("")
        mypyc_modules_lines.extend(initialize_macro_lines)
        mypyc_modules_path = os.path.join(self._target_dir, "tfreezer_mypyc_modules.h")
        with open(mypyc_modules_path, "w", encoding="utf-8") as fp:
            fp.write("\n".join(mypyc_modules_lines))

    @classmethod
    def _process_module_headers(cls, module_name: str, public_header: str, private_header: str) -> tuple[str, str]:
        # Read public header generated by mypyc
        with open(public_header, "r", encoding="utf-8") as fp:
            public_header_lines = fp.readlines()
        assert public_header_lines[0].startswith("#ifndef MYPYC_NATIVE")
        assert public_header_lines[1].startswith("#define MYPYC_NATIVE")
        endif_macro_index = -1 if public_header_lines[-1] else -2
        assert public_header_lines[endif_macro_index].startswith("#endif")

        # Rename macro
        module_macro_name = module_name.upper().replace(".", "_")
        public_header_lines[0] = f"#ifndef MYPYC_{module_macro_name}_H\n"
        public_header_lines[1] = f"#define MYPYC_{module_macro_name}_H\n"

        # Insert: extern "C" { }
        public_header_lines.insert(2, "#endif\n")
        public_header_lines.insert(2, 'extern "C" {\n')
        public_header_lines.insert(2, "#ifdef __cplusplus\n")
        public_header_lines.insert(endif_macro_index, "#endif\n")
        public_header_lines.insert(endif_macro_index - 1, "}\n")
        public_header_lines.insert(endif_macro_index - 2, "#ifdef __cplusplus\n")

        # Insert: PyMODINIT_FUNC PyInit_{module_name}(void);
        last_include_index = 5
        for index, line in enumerate(public_header_lines):
            if index < last_include_index:
                continue
            if line.startswith("#include"):
                last_include_index = index
            else:
                break
        public_header_lines.insert(last_include_index + 1, f"PyMODINIT_FUNC PyInit_{module_name}(void);\n")

        # Write public header
        public_header_name = f"{module_name}.h"
        public_header_path = os.path.join(os.path.dirname(public_header), public_header_name)
        with open(public_header_path, "w", encoding="utf-8") as fp:
            fp.write("".join(public_header_lines))

        # Read private header generated by mypyc
        with open(private_header, "r", encoding="utf-8") as fp:
            private_header_lines = fp.readlines()

        # Rename macro and replace original header names with new header names
        new_private_header_lines = []
        for line in private_header_lines:
            if line.startswith("#ifndef MYPYC_NATIVE_INTERNAL"):
                new_private_header_lines.append(f"#ifndef MYPYC_{module_macro_name}_INTERNAL_H\n")
            elif line.startswith("#define MYPYC_NATIVE_INTERNAL"):
                new_private_header_lines.append(f"#define MYPYC_{module_macro_name}_INTERNAL_H\n")
            elif line.startswith("#include") and cls._public_header_name in line:
                new_private_header_lines.append(f'#include "{public_header_name}"\n')
            else:
                new_private_header_lines.append(line)

        # Write private header
        private_header_name = f"{module_name}_internal.h"
        private_header_path = os.path.join(os.path.dirname(public_header), private_header_name)
        with open(private_header_path, "w", encoding="utf-8") as fp:
            fp.write("".join(new_private_header_lines))

        # Remove the original headers generated by mypyc
        old_path = pathlib.Path(public_header)
        old_path.unlink()
        old_path = pathlib.Path(private_header)
        old_path.unlink()

        return public_header_path, private_header_path

    @classmethod
    def _process_module_source(cls, module_name: str, source_path: str, public_header_name: str, private_header_name: str) -> str:
        # Read source code generated by mypyc
        with open(source_path, "r", encoding="utf-8") as fp:
            source_lines = fp.readlines()

        # Replace original header names with new header names
        new_source_lines = []
        for line in source_lines:
            if line.startswith("#include") and cls._public_header_name in line:
                new_source_lines.append(f'#include "{public_header_name}"\n')
            elif line.startswith("#include") and cls._private_header_name in line:
                new_source_lines.append(f'#include "{private_header_name}"\n')
            else:
                new_source_lines.append(line)

        # Write source code
        new_source_name = f"{module_name}.c"
        new_source_path = os.path.join(os.path.dirname(source_path), new_source_name)
        with open(new_source_path, "w", encoding="utf-8") as fp:
            fp.write("".join(new_source_lines))

        # Remove the original source code generated by mypyc
        old_path = pathlib.Path(source_path)
        old_path.unlink()

        return new_source_path
