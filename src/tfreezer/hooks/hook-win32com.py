# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os
import modulefinder
from importlib import machinery

import pythoncom
import pywintypes
import win32com

hiddenimports = []
_pythoncom_basename = os.path.basename(pythoncom.__file__)
_pywintypes_basename = os.path.basename(pywintypes.__file__)
binaries = [
    (os.path.join("pywin32_system32", _pythoncom_basename), pythoncom.__file__, "BINARY"),
    (os.path.join("pywin32_system32", _pywintypes_basename), pywintypes.__file__, "BINARY"),
]
datas = []


def hook(modules: dict[str, modulefinder.Module], pyi_binaries: list[tuple[str, str, str]], pyi_datas: list[tuple[str, str, str]]) -> None:
    win32comext_dir = os.path.normpath(os.path.join(win32com.__file__, "..", "..", "win32comext"))
    win32comext_parent_dir = os.path.dirname(win32comext_dir)
    comext_to_com: dict[tuple[str, str, str], tuple[str, str, str]] = {}
    for root, _, files in os.walk(win32comext_dir):
        for file_name in files:
            if not file_name.endswith(tuple(machinery.EXTENSION_SUFFIXES)):
                continue
            full_path = os.path.join(root, file_name)
            relpath = os.path.relpath(full_path, win32comext_parent_dir)
            comext = (relpath, full_path, "BINARY")
            relpath = relpath.replace("win32comext", "win32com")
            com = (relpath, full_path, "BINARY")
            comext_to_com[comext] = com
    for index, pyi_binary in enumerate(pyi_binaries):
        if pyi_binary in comext_to_com:
            pyi_binaries[index] = comext_to_com[pyi_binary]
