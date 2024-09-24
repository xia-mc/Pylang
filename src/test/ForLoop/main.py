import timeit


def benchmark():
    counter = 0
    for i in range(10000):
        counter += 1


if __name__ == '__main__':
    timeCost = timeit.Timer(lambda: benchmark()).timeit(100) / 100
    print(timeCost)
