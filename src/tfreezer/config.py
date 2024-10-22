# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import typing as _t
import dataclasses
import sys
import os

from tfreezer import paths, utils


UNSUPPORTED_MODULES = (
    "debugpy",
    "setuptools",
)


@dataclasses.dataclass
class FreezeConfig:
    entry_module: str
    hidden_imports: str
    excludes: str
    mypyc_modules: str
    datas: list[str]
    # qt related configs
    qt_library_name: str
    qt_modules: list[str]


def dump_freeze_config(
    *,
    entry_module: _t.Optional[str],
    hidden_imports: _t.Optional[list[str]],
    excludes: _t.Optional[list[str]],
    mypyc_modules: _t.Optional[list[str]],
    config_file: _t.Optional[str],
) -> FreezeConfig:
    freeze_config = _parse_config(entry_module, hidden_imports, excludes, mypyc_modules, config_file)
    if not os.path.isdir(paths.BUILD_DIR):
        os.makedirs(paths.BUILD_DIR)

    # entry_module
    entry_module_file = os.path.join(paths.BUILD_DIR, "entry_module")
    with open(entry_module_file, "w", encoding="utf-8") as fp:
        fp.write(freeze_config.entry_module)

    # hidden_imports
    hidden_imports_file = os.path.join(paths.BUILD_DIR, "hidden_imports")
    with open(hidden_imports_file, "w", encoding="utf-8") as fp:
        fp.write(freeze_config.hidden_imports)

    # excludes
    excludes_file = os.path.join(paths.BUILD_DIR, "excludes")
    with open(excludes_file, "w", encoding="utf-8") as fp:
        fp.write(freeze_config.excludes)

    # mypyc_modules
    mypyc_modules_file = os.path.join(paths.BUILD_DIR, "mypyc_modules")
    with open(mypyc_modules_file, "w", encoding="utf-8") as fp:
        fp.write(freeze_config.mypyc_modules)

    # datas
    datas_file = os.path.join(paths.BUILD_DIR, "datas")
    with open(datas_file, "w", encoding="utf-8") as fp:
        fp.write(",".join(freeze_config.datas))

    # qt_config
    qt_config_file = os.path.join(paths.BUILD_DIR, "qt_config")
    qt_config_contents = [f'qt_library_name = "{freeze_config.qt_library_name}"', "qt_modules = ["]
    for qt_module in freeze_config.qt_modules:
        qt_config_contents.append(f'    "{qt_module}",')
    qt_config_contents.append("]")
    qt_config_contents.append("")  # Extra empty line to make it prettier
    with open(qt_config_file, "w", encoding="utf-8") as fp:
        fp.write("\n".join(qt_config_contents))

    return freeze_config


def dump_python_path() -> None:
    if not os.path.isdir(paths.BUILD_DIR):
        os.makedirs(paths.BUILD_DIR)
    sys_path = os.path.join(paths.BUILD_DIR, "python_path")
    contents = ["python_path = ["]
    for path in sys.path:
        contents.append(f'    r"{path}",')
    contents.append("]")
    contents.append("")  # Extra empty line to make it prettier
    with open(sys_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(contents))


def load_sys_path() -> None:
    sys_path = os.path.join(paths.BUILD_DIR, "python_path")
    if not os.path.isfile(sys_path):
        return
    module = utils.load_signle_module("tfreezer.python_path", sys_path)
    for path in module.python_path:
        if path not in sys.path:
            sys.path.append(path)


def _parse_config(
    entry_module: _t.Optional[str],
    hidden_imports: _t.Optional[list[str]],
    excludes: _t.Optional[list[str]],
    mypyc_modules: _t.Optional[list[str]],
    config_file: _t.Optional[str],
) -> FreezeConfig:
    if config_file:
        fullname = "tfreezer.user_config"
        module = utils.load_signle_module(fullname, config_file)
        assert hasattr(module, "entry_module") and isinstance(module.entry_module, str)
        assert hasattr(module, "hidden_imports") and isinstance(module.hidden_imports, list)
        assert hasattr(module, "excludes") and isinstance(module.excludes, list)
        for unsupported_module in UNSUPPORTED_MODULES:
            module.excludes.append(unsupported_module)
        mypyc_modules = []
        if hasattr(module, "mypyc_modules") and isinstance(module.mypyc_modules, list):
            mypyc_modules = module.mypyc_modules
        freeze_config = FreezeConfig(
            module.entry_module, ",".join(module.hidden_imports), ",".join(module.excludes), ",".join(mypyc_modules), [], "", []
        )
        if hasattr(module, "datas") and isinstance(module.datas, list):
            freeze_config.datas = module.datas
        if hasattr(module, "qt_library_name") and isinstance(module.qt_library_name, str):
            freeze_config.qt_library_name = module.qt_library_name
        if hasattr(module, "qt_modules") and isinstance(module.qt_modules, list):
            freeze_config.qt_modules = module.qt_modules
        return freeze_config
    if not entry_module:
        raise ValueError("--entry-module should be specified")
    hidden_imports = hidden_imports or []
    excludes = excludes or []
    mypyc_modules = mypyc_modules or []
    for unsupported_module in UNSUPPORTED_MODULES:
        excludes.append(unsupported_module)
    return FreezeConfig(
        entry_module,
        ",".join(hidden_imports),
        ",".join(excludes),
        ",".join(mypyc_modules),
        [],
        "",
        [],
    )
