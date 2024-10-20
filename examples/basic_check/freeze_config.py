import os

entry_module = os.path.normpath(os.path.join(__file__, "..", "basic_check.py"))

hidden_imports = []

excludes = [
    "_asyncio",
    "_bz2",
    "_ctypes",
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
]
