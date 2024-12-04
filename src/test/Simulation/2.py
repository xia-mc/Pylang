import timeit

from numba import jit
from pylang_annotations import native


def inline():
    res = 0
    for _ in range(1000000):
        res += 1
    return res


def noinline():
    def f():
        return 1

    res = 0
    for _ in range(1000000):
        res += f()
    return res


@native(True)
def native_inline():
    res = 0
    for _ in range(1000000):
        res += 1
    return res


@native(True)
def native_noinline():
    def f():
        return 1

    res = 0
    for _ in range(1000000):
        res += f()
    return res


@jit
def jit_inline():
    res = 0
    for _ in range(1000000):
        res += 1
    return res


@jit
def jit_noinline():
    def f():
        return 1

    res = 0
    for _ in range(1000000):
        res += f()
    return res


def main():
    baseline = timeit.Timer(lambda: noinline()).timeit(100) / 100
    optimized = timeit.Timer(lambda: inline()).timeit(100) / 100
    native_baseline = timeit.Timer(lambda: native_noinline()).timeit(100) / 100
    native_optimized = timeit.Timer(lambda: native_inline()).timeit(100) / 100
    jit_first_baseline = timeit.Timer(lambda: jit_noinline()).timeit(1)
    jit_first_optimized = timeit.Timer(lambda: jit_inline()).timeit(1)
    jit_baseline = timeit.Timer(lambda: jit_noinline()).timeit(100) / 100
    jit_optimized = timeit.Timer(lambda: jit_inline()).timeit(100) / 100

    print("No-Inline:", baseline, f"{baseline / baseline * 100}%")
    print("Inline:", optimized, f"{baseline / optimized * 100}%")

    print("Native No-Inline:", native_baseline, f"{baseline / native_baseline * 100}%")
    print("Native Inline:", native_optimized, f"{baseline / native_optimized * 100}%")

    print("Jit First No-Inline:", jit_first_baseline, f"{baseline / jit_first_baseline * 100}%")
    print("Jit First Inline:", jit_first_optimized, f"{baseline / jit_first_optimized * 100}%")

    print("Jit No-Inline:", jit_baseline, f"{baseline / jit_baseline * 100}%")
    print("Jit Inline:", jit_optimized, f"{baseline / jit_optimized * 100}%")


if __name__ == '__main__':
    main()
