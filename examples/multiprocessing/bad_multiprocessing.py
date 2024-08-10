import multiprocessing
from multiprocessing import spawn


def f():
    print("hello world!")


if __name__ == "__main__":
    print(spawn.get_preparation_data("test"))
    multiprocessing.Process(target=f).start()
