import os
import sys

sys.path.append(os.path.normpath(os.path.dirname(__file__)))

entry_module = os.path.normpath(os.path.join(__file__, "..", "multimodule_multiprocessing.py"))

hidden_imports = []

excludes = [
    "_asyncio",
    "_bz2",
    "_ctypes",
    "_decimal",
    "_hashlib",
    "_lzma",
    # "_multiprocessing",
    "_overlapped",
    "_queue",
    # "_socket",
    "_ssl",
    "_testcapi",
    "_testinternalcapi",
    "_tkinter",
    "_wmi",
    "pyexpat",
    # "select",
    "unicodedata",
]
