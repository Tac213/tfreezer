# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os
import typing as _t

from mypyc.codegen import emitmodule
from mypyc.options import CompilerOptions
from mypyc import build

from tfreezer import paths


class MyPycModuleInfo(_t.NamedTuple):
    name: str
    py_path: str
    groups: emitmodule.Groups
    group_cfilenames: list[tuple[list[str], list[str]]]


class MyPycSourceGenerator:

    def __init__(self):
        self._modules: dict[str, MyPycModuleInfo] = {}

    def generate(self, module_name: str, module_path: str) -> None:
        target_dir = os.path.join(paths.BUILD_DIR, "generated", "mypyc_modules")
        compiler_options = CompilerOptions(target_dir=target_dir)
        groups, group_cfilenames = build.mypyc_build([module_path], compiler_options)
        mypyc_module_info = MyPycModuleInfo(module_name, module_path, groups, group_cfilenames)
        self._modules[module_name] = mypyc_module_info

    def dump_mypyc_info(self) -> None:
        """
        Dump mypyc extra sources and include directories
        """
        if not self._modules:
            return
        include_dirs = [build.include_dir()]
        sources: list[str] = []
        for module_info in self._modules.values():
            groups = module_info.groups
            group_cfilenames = module_info.group_cfilenames
            for (group_sources, lib_name), (cfilenames, deps) in zip(groups, group_cfilenames):
                print(group_sources, lib_name, cfilenames, deps)
                sources.extend(cfilenames)
                for cfilename in cfilenames:
                    dirname = os.path.dirname(cfilename)
                    if dirname not in include_dirs:
                        include_dirs.append(dirname)
        include_dirs = [the_path.replace("\\", "/") for the_path in include_dirs]
        sources = [the_path.replace("\\", "/") for the_path in sources]
        mypyc_include_dirs_path = os.path.join(paths.BUILD_DIR, "mypyc_include_dirs")
        with open(mypyc_include_dirs_path, "w", encoding="utf-8") as fp:
            fp.write(";".join(include_dirs))
        mypyc_sources_path = os.path.join(paths.BUILD_DIR, "mypyc_sources")
        with open(mypyc_sources_path, "w", encoding="utf-8") as fp:
            fp.write(";".join(sources))
