# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

from mypyc.ir.func_ir import FuncDecl
from mypyc.namegen import exported_name
from mypyc.codegen.emit import Emitter
from mypyc.common import REG_PREFIX, NATIVE_PREFIX


def native_function_header(fn: FuncDecl, emitter: Emitter, module_name: str) -> str:
    args = []
    for arg in fn.sig.args:
        args.append(f"{emitter.ctype_spaced(arg.type)}{REG_PREFIX}{arg.name}")

    native_fn_name = f"{NATIVE_PREFIX}{fn.cname(emitter.names)}_{exported_name(module_name)}"
    return "{ret_type}{name}({args})".format(
        ret_type=emitter.ctype_spaced(fn.sig.ret_type),
        name=native_fn_name,
        args=", ".join(args) or "void",
    )
