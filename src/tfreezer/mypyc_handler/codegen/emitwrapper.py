# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

from mypyc.namegen import NameGenerator, exported_name
from mypyc.ir.func_ir import FuncIR
from mypyc.common import PREFIX


def wrapper_function_header(fn: FuncIR, names: NameGenerator, module_name: str) -> str:
    """Return header of a vectorcall wrapper function.

    See comment above for a summary of the arguments.
    """
    return ("PyObject *{prefix}{name}(" "PyObject *self, PyObject *const *args, size_t nargs, PyObject *kwnames)").format(
        prefix=PREFIX, name=f"{fn.cname(names)}_{exported_name(module_name)}"
    )


def legacy_wrapper_function_header(fn: FuncIR, names: NameGenerator, module_name: str) -> str:
    return "PyObject *{prefix}{name}(PyObject *self, PyObject *args, PyObject *kw)".format(
        prefix=PREFIX, name=f"{fn.cname(names)}_{exported_name(module_name)}"
    )
