import timeit

from pylang_annotations import native
from numba import jit

_: int


def benchmark_for_original():
    global _
    counter = 0
    for i in range(10001):
        counter += 1
    _ = counter


def benchmark_for():
    global _
    counter = 0
    for i in range(10000):
        counter += 1
    _ = counter


def benchmark_listComp():
    global _
    _ = sum(i for i in range(10000))


@native
def benchmark_native_for():
    global _
    counter = 0
    for i in range(10000):
        counter += 1
    _ = counter


if __name__ == '__main__':
    @jit(nopython=True)
    def benchmark_n_jit_for():
        counter = 0
        for i in range(10001):
            counter += 1
        _ = counter

    print("For(Original):", timeit.Timer(lambda: benchmark_for_original()).timeit(100) / 100)
    print("For:", timeit.Timer(lambda: benchmark_for()).timeit(100) / 100)
    print("ListComp:", timeit.Timer(lambda: benchmark_listComp()).timeit(100) / 100)
    print("Native For:", timeit.Timer(lambda: benchmark_native_for()).timeit(100) / 100)
    print('NJit For:', timeit.Timer(lambda: benchmark_n_jit_for()).timeit(100) / 100)
    print('NJit(prepared) For:', timeit.Timer(lambda: benchmark_n_jit_for()).timeit(100) / 100)
