import os

entry_module = os.path.join(os.path.dirname(__file__), "pyside6_demo.py")

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
    "_testlimitedcapi",
    "_tkinter",
    "_wmi",
    "pyexpat",
    "select",
    "unicodedata",
    "test",
    "unittest",
]

qt_library_name = "PySide6"
qt_modules = [
    "PySide6.QtCore",
    "PySide6.QtWidgets",
]
