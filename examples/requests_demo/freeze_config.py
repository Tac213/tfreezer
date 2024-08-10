import os

entry_module = os.path.normpath(os.path.join(__file__, "..", "requests_demo.py"))

hidden_imports = []

# The following extensions are needed
# _socket, _ssl, select, unicodedata
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
    "_testcapi",
    "_testinternalcapi",
    "_tkinter",
    "_wmi",
    "pyexpat",
]
