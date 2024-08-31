import sys
from importlib import resources

import time
import fib

if __name__ == "__main__":
    print(sys.path)
    print(sys._stdlib_dir)  # pylint: disable=protected-access
    print(sys.argv)
    print(sys.meta_path)
    print(sys.path_hooks)
    print(sys.executable)
    print(resources.__spec__)
    print(resources.__spec__.origin)
    print(resources.__file__)
    print(fib)
    print(fib.fib)
    t1 = time.time()
    print(fib.fib(32))
    print("fib(32) cost: ", time.time() - t1)
