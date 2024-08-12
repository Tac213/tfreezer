import multiprocessing
from multiprocessing import spawn


def f():
    print("hello world!")


if __name__ == "__main__":
    print(spawn.get_preparation_data("test"))
    p = multiprocessing.Process(target=f)
    p.start()
    # join is necessary here
    # or the parent process will exit early and make the child process unable to get parent process handle
    p.join()
