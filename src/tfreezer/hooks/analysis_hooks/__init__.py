# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import modulefinder

from tfreezer.hooks.analysis_hooks import pywin32


def hook(
    hidden_imports: list[str], excludes: list[str], path: list[str], replace_paths: list[tuple[str, str]]
) -> dict[str, modulefinder.Module]:
    extra_modules: dict[str, modulefinder.Module] = {}
    extra_modules.update(pywin32.hook(hidden_imports, excludes, path, replace_paths))
    return extra_modules
