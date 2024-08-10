# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os
from charset_normalizer import md__mypyc

hiddenimports = []
_mdpyc_basename = os.path.basename(md__mypyc.__file__)
binaries = [
    (os.path.join("charset_normalizer", _mdpyc_basename), md__mypyc.__file__, "BINARY"),
]
datas = []
