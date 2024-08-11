# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os
import modulefinder


def hook(
    hidden_imports: list[str], excludes: list[str], path: list[str], replace_paths: list[tuple[str, str]]
) -> dict[str, modulefinder.Module]:
    extra_modules: dict[str, modulefinder.Module] = {}
    try:
        import win32com  # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError:
        return extra_modules
    if "pywin32_system32" not in excludes:
        excludes.append("pywin32_system32")
    modulefinder.AddPackagePath("win32com", os.path.normpath(os.path.join(win32com.__file__, "..", "..", "win32comext")))
    return extra_modules
