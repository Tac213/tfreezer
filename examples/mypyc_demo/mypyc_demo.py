import time
import fib
import fib2
from subpackage import fib3

if __name__ == "__main__":
    print(fib)
    print(fib.fib)
    t1 = time.time()
    print(fib.fib(32))
    t2 = time.time()
    print("fib.fib(32) cost: ", t2 - t1)
    print(fib2.fib(32))
    t3 = time.time()
    print("fib2.fib(32) cost: ", t3 - t2)
    print(fib3.fib(32))
    t4 = time.time()
    print("fib3.fib(32) cost: ", t4 - t3)
