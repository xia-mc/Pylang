import timeit


def benchmark():
    counter = 0
    for index in range(10):
        counter += 1
    # print(counter)


if __name__ == '__main__':
    timeCost = timeit.Timer(lambda: benchmark()).timeit(100) / 100
    print(timeCost)
