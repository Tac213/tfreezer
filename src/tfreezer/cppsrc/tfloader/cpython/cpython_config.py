# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

"""
Script for cmake to link python
"""

from __future__ import print_function, absolute_import, division

import sys
import sysconfig
import re
import os
import functools
from collections import namedtuple

try:
    from importlib import machinery
except ImportError:
    machinery = None
try:
    import imp  # type: ignore  # pylint: disable=deprecated-module
except ImportError:
    imp = None


PythonLinkData = namedtuple("PythonLinkData", ["libdir", "lib"])


def is_debug():
    # type: () -> bool
    """
    Check whether cpython is debug build
    Returns:
        bool
    """
    debug_suffix = "_d.pyd" if sys.platform == "win32" else "_d.so"
    if machinery:
        return any(s.endswith(debug_suffix) for s in machinery.EXTENSION_SUFFIXES)
    if imp:
        return any(s[0].endswith(debug_suffix) for s in imp.get_suffixes())
    raise RuntimeError("Neither 'importlib.machinery' nor 'imp' could be imported.")


def python_version():
    # type: () -> str
    """
    Get python version
    Returns:
        str
    """
    return "{}{}".format(sys.version_info.major, sys.version_info.minor)


def get_python_include_path():
    # type: () -> str
    """
    Get python include path
    Returns:
        str
    """
    return sysconfig.get_path("include")


def python3_link_flags_cmake():
    # type: () -> str
    """
    Get cmake libpython3 link flags
    Returns:
        str
    """
    data = python_link_data(True)
    libdir = data.libdir
    lib = re.sub(r".dll$", ".lib", data.lib)
    return "{};{}".format(libdir, lib)


def python_link_flags_cmake():
    # type: () -> str
    """
    Get cmake libpython link flags
    Returns:
        str
    """
    data = python_link_data(False)
    libdir = data.libdir
    lib = re.sub(r".dll$", ".lib", data.lib)
    return "{};{}".format(libdir, lib)


def python_link_data(is_libpython3):
    # type: (bool) -> PythonLinkData
    """
    Get python link data
    Args:
        is_libpython3: whether to get libpython3
    Returns:
        PythonLinkData
    """
    libdir = sysconfig.get_config_var("LIBDIR")
    if libdir is None:
        libdir = os.path.abspath(os.path.join(sysconfig.get_config_var("LIBDEST"), "..", "libs"))
    if is_libpython3:
        version = "3"
        version_no_dots = "3"
    else:
        version = python_version()
        version_no_dots = version.replace(".", "")

    lib = ""
    suffix = sysconfig.get_config_var("abi_thread") or ""
    if sys.platform == "win32":
        suffix = "{}_d".format(suffix) if is_debug() else suffix
        lib = "python{}{}".format(version_no_dots, suffix)

    elif sys.platform == "darwin":
        lib = "python{}{}".format(version, suffix)

    # Linux and anything else
    else:
        lib = "python{}{}".format(version, sys.abiflags)  # pylint: disable=no-member

    return PythonLinkData(libdir, lib)


def python_dll_path(is_libpython3):
    # type: (bool) -> str
    """
    Get python dll path
    Args:
        is_libpython3: whether to get libpython3
    Returns:
        str
    """
    if not sys.platform.startswith("win"):
        return ""
    if is_libpython3:
        version_no_dots = "3"
    else:
        version = python_version()
        version_no_dots = version.replace(".", "")
    suffix = sysconfig.get_config_var("abi_thread") or ""
    suffix = "{}_d".format(suffix) if is_debug() else suffix
    file_name = "python{}{}.dll".format(version_no_dots, suffix)
    file_path = os.path.join(sys.base_exec_prefix, file_name)
    if os.path.isfile(file_path):
        return file_path
    return ""


def get_extension_suffix():
    # type: () -> str
    if machinery:
        if not machinery.EXTENSION_SUFFIXES:
            return ".pyd" if sys.platform.startswith("win") else ".so"
        return machinery.EXTENSION_SUFFIXES[0]
    if imp:
        for suffix, _, flag in imp.get_suffixes():
            if flag == imp.C_EXTENSION:
                return suffix
        return ".pyd" if sys.platform.startswith("win") else ".so"
    raise EnvironmentError("Can't get extension suffixes.")


def main():
    # type: () -> None
    """
    Entry point
    Returns:
        None
    """
    options = []

    # option, function, error, description
    options.append(
        (
            "--python-include-path",
            get_python_include_path,
            "Unable to locate the Python include headers directory.",
            "Print Python include path",
        )
    )
    options.append(
        (
            "--python-link-flags-cmake",
            python_link_flags_cmake,
            "Unable to locate the Python library for linking.",
            "Print python link flags for cmake",
        )
    )
    options.append(
        (
            "--python3-link-flags-cmake",
            python3_link_flags_cmake,
            "Unable to locate the Python library for linking.",
            "Print python link flags for cmake",
        )
    )
    options.append(
        (
            "--python-dll-path",
            functools.partial(python_dll_path, False),
            "Unable to locate the Python library for linking.",
            "Print python link flags for cmake",
        )
    )
    options.append(
        (
            "--python3-dll-path",
            functools.partial(python_dll_path, True),
            "Unable to locate the Python library for linking.",
            "Print python link flags for cmake",
        )
    )
    options.append(
        (
            "--extension-suffix",
            lambda: print(get_extension_suffix()),
            "Unable to get extension suffix.",
            "Print extension suffix for cmake",
        )
    )

    option = sys.argv[1]
    for argument, handler, error, _ in options:
        if option != argument:
            continue
        handler_result = handler()
        if handler_result is None:
            sys.exit(error)

        line = handler_result
        print(line)


if __name__ == "__main__":
    main()
