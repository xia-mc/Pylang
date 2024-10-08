import timeit


def main():
    if 0:
        print(1)
    if 4 ** 10000 // 10000 != 1:
        pass
    pass
    pass
    pass

def func1():
    if False:
        pass

if __name__ == '__main__':
    timeCost = timeit.Timer(lambda: main()).timeit(10000) / 10000
    print(timeCost)
