import os
import sys

entry_module = os.path.join(os.path.dirname(__file__), "pyqt5_demo.py")

hidden_imports = [
    "encodings.cp437",
]

excludes = ["debugpy"]

if sys.platform.startswith("win"):
    excludes.append("multiprocessing.popen_fork")
    excludes.append("multiprocessing.popen_forkserver")
    excludes.append("multiprocessing.popen_spawn_posix")
else:
    excludes.append("multiprocessing.popen_spawn_win32")

qt_library_name = "PyQt5"
qt_modules = [
    "PyQt5.QtCore",
    "PyQt5.QtWidgets",
]
