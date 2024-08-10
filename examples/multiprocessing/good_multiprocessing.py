import multiprocessing
from multiprocessing import spawn


def f(x):
    print("hello world!")
    return x * x


if __name__ == "__main__":
    multiprocessing.freeze_support()
    print(spawn.get_preparation_data("test"))
    with multiprocessing.Pool(5) as p:
        print(p.map(f, [1, 2, 3]))
