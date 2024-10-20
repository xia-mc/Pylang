import timeit

val = 123
result: str


def benchmark_str():
    global result
    for _ in range(10000):
        result = str(val)


def benchmark_fstring():
    global result
    for _ in range(10000):
        result = f"{val}"


if __name__ == '__main__':
    print("Str:", timeit.Timer(lambda: benchmark_str()).timeit(100) / 100)
    print("F-String:", timeit.Timer(lambda: benchmark_fstring()).timeit(100) / 100)
