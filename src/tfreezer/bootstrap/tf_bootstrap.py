# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import sys

import tf_importer

# Install tf frozen importer
tf_importer.install()

# Let other python modules know that the code is running in frozen mode.
if not hasattr(sys, "frozen"):
    sys.frozen = True


import tf_multiprocessing

# Install tf multiprocessing hooks
tf_multiprocessing.install()

# Install the hooks for pywin32 (Windows only)
if sys.platform.startswith("win"):
    import tf_pywin32

    tf_pywin32.install()
