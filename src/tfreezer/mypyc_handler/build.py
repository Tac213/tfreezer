# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import sys
import os
import time

from mypy.build import BuildSource
from mypy.errors import CompileError
from mypy.options import Options
from mypy.fscache import FileSystemCache
from mypyc.namegen import exported_name
from mypyc.errors import Errors
from mypyc.codegen import emitmodule
from mypyc.options import CompilerOptions
from mypyc.ir.pprint import format_modules
from mypyc.build import get_mypy_config, construct_groups, emit_messages, write_file, get_header_deps

from tfreezer.mypyc_handler.codegen.emitmodule import compile_modules_to_c


def generate_c(
    sources: list[BuildSource],
    options: Options,
    groups: emitmodule.Groups,
    fscache: FileSystemCache,
    compiler_options: CompilerOptions,
) -> tuple[list[list[tuple[str, str]]], str]:
    """
    Our own implementation of `generate_c`.
    Drive the actual core compilation step.

    The groups argument describes how modules are assigned to C
    extension modules. See the comments on the Groups type in
    mypyc.emitmodule for details.

    Returns the C source code and (for debugging) the pretty printed IR.
    """
    t0 = time.time()

    try:
        result = emitmodule.parse_and_typecheck(sources, options, compiler_options, groups, fscache)
    except CompileError as e:
        emit_messages(options, e.messages, time.time() - t0, serious=not e.use_stdout)
        sys.exit(1)

    t1 = time.time()
    if result.errors:
        emit_messages(options, result.errors, t1 - t0)
        sys.exit(1)

    if compiler_options.verbose:
        print(f"Parsed and typechecked in {t1 - t0:.3f}s")

    errors = Errors(options)
    modules, ctext = compile_modules_to_c(result, compiler_options=compiler_options, errors=errors, groups=groups)
    t2 = time.time()
    emit_messages(options, errors.new_messages(), t2 - t1)
    if errors.num_errors:
        # No need to stop the build if only warnings were emitted.
        sys.exit(1)

    if compiler_options.verbose:
        print(f"Compiled to C in {t2 - t1:.3f}s")

    return ctext, "\n".join(format_modules(modules))


def mypyc_build(
    paths: list[str],
    compiler_options: CompilerOptions,
) -> tuple[emitmodule.Groups, list[tuple[list[str], list[str]]]]:
    """
    Our own implementation of `mypyc_build`.
    Do the front and middle end of mypyc building, producing and writing out C source.
    """
    fscache = FileSystemCache()
    mypyc_sources, all_sources, options = get_mypy_config(paths, None, compiler_options, fscache)

    groups = construct_groups(mypyc_sources, True, True)  # set both `separate` and `use_shared_lib` to `True`
    group_cfiles, ops_text = generate_c(all_sources, options, groups, fscache, compiler_options=compiler_options)
    for _, lib_name in groups:
        if not lib_name:
            continue
        write_file(os.path.join(compiler_options.target_dir, f"{exported_name(lib_name)}_ops.txt"), ops_text)

    # Write out the generated C and collect the files for each group
    # Should this be here??
    group_cfilenames: list[tuple[list[str], list[str]]] = []
    for cfiles in group_cfiles:
        cfilenames = []
        for cfile, ctext in cfiles:
            cfile = os.path.join(compiler_options.target_dir, cfile)
            write_file(cfile, ctext)
            if os.path.splitext(cfile)[1] == ".c":
                cfilenames.append(cfile)

        deps = [os.path.join(compiler_options.target_dir, dep) for dep in get_header_deps(cfiles)]
        group_cfilenames.append((cfilenames, deps))

    return groups, group_cfilenames
