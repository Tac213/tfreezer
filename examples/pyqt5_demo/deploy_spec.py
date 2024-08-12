import os

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

qt_library_name = "PyQt5"
qt_modules = [
    "PyQt5.QtCore",
    "PyQt5.sip",
    "PyQt5.QtWidgets",
]
