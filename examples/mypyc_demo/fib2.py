class Fib:

    def __init__(self, n: int) -> None:
        self._x = n

    def fib(self, n: int) -> int:
        if n <= 1:
            return n + self._x
        return self.fib(n - 2) + self.fib(n - 1)

    @property
    def n(self) -> int:
        return self._x

    @n.setter
    def n(self, n: int) -> None:
        self._x = n
