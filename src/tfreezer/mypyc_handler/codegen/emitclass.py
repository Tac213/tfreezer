# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

from mypyc.ir.class_ir import ClassIR
from mypyc.common import NATIVE_PREFIX, TYPE_PREFIX
from mypyc.namegen import exported_name
from mypyc.codegen.emitclass import generate_object_struct
from mypyc.codegen.emit import Emitter, HeaderDeclaration

from tfreezer.mypyc_handler.codegen.emitfunc import native_function_header


def generate_class_type_decl(cl: ClassIR, c_emitter: Emitter, external_emitter: Emitter, emitter: Emitter) -> None:
    context = c_emitter.context
    name = f"{TYPE_PREFIX}{cl.name}_{cl.module_name}"
    context.declarations[name] = HeaderDeclaration(f"PyTypeObject *{name};", needs_export=True)

    # If this is a non-extension class, all we want is the type object decl.
    if not cl.is_ext_class:
        return

    generate_object_struct(cl, external_emitter)
    generate_full = not cl.is_trait and not cl.builtin_base
    if generate_full:
        native_function_name = f"{NATIVE_PREFIX}{cl.ctor.cname(emitter.names)}_{exported_name(cl.module_name)}"
        context.declarations[native_function_name] = HeaderDeclaration(
            f"{native_function_header(cl.ctor, emitter, cl.module_name)};", needs_export=True
        )
