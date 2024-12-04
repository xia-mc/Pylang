import timeit

from pylang_annotations import native
from numba import jit

_: int


def benchmark_for_original():
    global _
    counter = 0
    for i in range(1001):
        counter += 1
    _ = counter


def benchmark_for():
    global _
    counter = 0
    for i in range(1000):
        counter += 1
    _ = counter


def benchmark_listComp():
    global _
    counter = sum(i for i in range(1000))
    _ = counter


@native
def benchmark_native_for():
    global _
    counter = 0
    for i in range(1000):
        counter += 1
    _ = counter


if __name__ == '__main__':
    @jit(nopython=True)
    def benchmark_n_jit_for():
        counter = 0
        for i in range(1000):
            counter += 1
        _ = counter
        return _

    baseline = timeit.Timer(lambda: benchmark_for_original()).timeit(100) / 100
    optimized = timeit.Timer(lambda: benchmark_for()).timeit(100) / 100
    listComp = timeit.Timer(lambda: benchmark_listComp()).timeit(100) / 100
    native = timeit.Timer(lambda: benchmark_native_for()).timeit(100) / 100
    nJit = timeit.Timer(lambda: benchmark_n_jit_for()).timeit(1) / 1
    nJitPrepared = timeit.Timer(lambda: benchmark_n_jit_for()).timeit(100) / 100

    print("For(Original):", baseline, f"{baseline / baseline * 100}%")
    print("For:", optimized, f"{baseline / optimized * 100}%")
    print("ListComp:", listComp, f"{baseline / listComp * 100}%")
    print("Native For:", native, f"{baseline / native * 100}%")
    print('NJit For:', nJit, f"{baseline / nJit * 100}%")
    print('NJit(prepared) For:', nJitPrepared, f"{baseline / nJitPrepared * 100}%")
