import os

entry_module = os.path.normpath(os.path.join(__file__, "..", "pywin32_demo.py"))

hidden_imports = []

# The following extensions are needed
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
