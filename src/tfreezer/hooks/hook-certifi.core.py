# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import os
import certifi

hiddenimports = []
binaries = []
_cacert_path = os.path.normpath(os.path.join(certifi.__file__, "..", "cacert.pem"))
datas = [
    (os.path.join("certifi", "cacert.pem"), _cacert_path, "DATA"),
]
