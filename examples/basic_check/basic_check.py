import sys
from importlib import resources

if __name__ == "__main__":
    print(sys.path)
    print(sys._stdlib_dir)
    print(sys.argv)
    print(sys.meta_path)
    print(sys.path_hooks)
    print(sys.executable)
    print(resources.__spec__)
    print(resources.__spec__.origin)
    print(resources.__file__)
