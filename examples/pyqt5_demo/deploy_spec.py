import os
import sys

entry_module = os.path.join(os.path.dirname(__file__), "pyqt5_demo.py")

hidden_imports = [
    "encodings.cp437",
]

excludes = [
    "_asyncio",
    "_bz2",
    "_decimal",
    "_hashlib",
    "_lzma",
    "_multiprocessing",
    "_overlapped",
    "_queue",
    "_socket",
    "_ssl",
    "_testcapi",
    "_testinternalcapi",
    "_tkinter",
    "_wmi",
    "pyexpat",
    "select",
    "unicodedata",
    "test",
    "unittest",
]

if sys.platform.startswith("win"):
    excludes.append("multiprocessing.popen_fork")
    excludes.append("multiprocessing.popen_forkserver")
    excludes.append("multiprocessing.popen_spawn_posix")
else:
    excludes.append("multiprocessing.popen_spawn_win32")

qt_library_name = "PyQt5"
qt_modules = [
    "PyQt5.QtCore",
    "PyQt5.sip",
    "PyQt5.QtWidgets",
]
