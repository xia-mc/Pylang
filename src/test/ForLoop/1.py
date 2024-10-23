import timeit

from pylang_annotations import native

_: int


@native
def benchmark_for():
    global _
    counter = 0
    for i in range(1000):
        counter += 1
    _ = counter


def benchmark_listComp():
    global _
    _ = sum([1 for i in range(1000)])
    _ = sum([i for i in range(1000)])


def wrongCode():
    for i in range(0, 100, 0):  # ValueError
        pass


if __name__ == '__main__':
    print("For:", timeit.Timer(lambda: benchmark_for()).timeit(100) / 100)
    print("ListComp:", timeit.Timer(lambda: benchmark_listComp()).timeit(100) / 100)
