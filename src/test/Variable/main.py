import timeit


def main():
    if 0:
        print(1)
    if 4 ** 10000 // 10000 != 1:
        ...


if __name__ == '__main__':
    timeCost = timeit.Timer(lambda: main()).timeit(10000) / 10000
    print(timeCost)
