import timeit


def main():
    for i in range(1000):
        if 4 ** 10000 // 10000 == 1:
            print(1)


def func1():
    if False:
        pass


if __name__ == '__main__':
    main.__code__ = compile("print(1)", "<string>", "exec")  # unsupported
    timeCost = timeit.Timer(lambda: main()).timeit(100) / 100
    print(timeCost)
