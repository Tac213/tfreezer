import time
import fib
import fib2
import subpackage
from subpackage import fib3

if __name__ == "__main__":
    print(subpackage)
    print(fib)
    print(fib.Fib)
    print(fib.Fib.fib)
    t1 = time.time()
    f0 = fib.Fib(7)
    print(f0.fib(32))
    t2 = time.time()
    print("fib.Fib(7).fib(32) cost: ", t2 - t1)
    f = fib2.Fib(11)
    print(f.fib(32))
    t3 = time.time()
    print("fib2.Fib(11).fib(32) cost: ", t3 - t2)
    f.n += 22
    print(f.n)
    print(fib3.fib(32))
    t4 = time.time()
    print("fib3.fib(32) cost: ", t4 - t3)
