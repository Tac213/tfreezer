import sys
import multiprocessing
from multiprocessing import spawn


def f(x):
    print("hello world!")
    print(sys.argv)
    return x * x


if __name__ == "__main__":
    print(dir(sys.modules["__main__"]))
    print(f.__module__)
    print(spawn.is_forking.__module__)
    # multiprocessing.freeze_support()
    print(spawn.get_preparation_data("test"))
    with multiprocessing.Pool(5) as p:
        print(p.map(f, [1, 2, 3]))
