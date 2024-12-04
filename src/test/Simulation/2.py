import timeit

from pylang_annotations import native


def inline():
    res = 0
    for _ in range(100000):
        res = 1
    return res


def noinline():
    def f():
        return 1

    res = 0
    for _ in range(100000):
        res = f()
    return res


@native
def native_inline():
    res = 0
    for _ in range(100000):
        res = 1
    return res


@native
def native_noinline():
    def f():
        return 1

    res = 0
    for _ in range(100000):
        res = f()
    return res


if __name__ == '__main__':
    baseline = timeit.Timer(lambda: noinline()).timeit(100) / 100
    optimized = timeit.Timer(lambda: inline()).timeit(100) / 100
    native_baseline = timeit.Timer(lambda: native_noinline()).timeit(100) / 100
    native_optimized = timeit.Timer(lambda: native_inline()).timeit(100) / 100

    print("No-Inline:", baseline, f"{baseline / baseline * 100}%")
    print("Inline:", optimized, f"{baseline / optimized * 100}%")

    print("Native No-Inline:", native_baseline, f"{baseline / native_baseline * 100}%")
    print("Native Inline:", native_optimized, f"{baseline / native_optimized * 100}%")
