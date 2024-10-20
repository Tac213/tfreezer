# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os

try:
    from charset_normalizer import md__mypyc
except ImportError:
    md__mypyc = None

hiddenimports = []
if md__mypyc:
    _mdpyc_basename = os.path.basename(md__mypyc.__file__)
    binaries = [
        (os.path.join("charset_normalizer", _mdpyc_basename), md__mypyc.__file__, "BINARY"),
    ]
else:
    binaries = []
datas = []
