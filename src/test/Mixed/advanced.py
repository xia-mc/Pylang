import time
from pylang_annotations import native


# 原始 Python 实现
def complex_python(data):
    nested_list = [list(range(i)) for i in range(1, 6)]
    nested_dict = {i: {j: i * j for j in range(1, 4)} for i in range(1, 4)}
    unique_values = set(data)

    processed_strings = [f"Value-{x}" for x in data if x % 2 == 0]
    concatenated = " | ".join(processed_strings)
    replaced = concatenated.replace("Value", "Num")

    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)

    fact_result = factorial(10)

    def apply_function(func, value):
        return func(value)

    squared = apply_function(lambda x: x ** 2, 10)

    # 确定性逻辑替代随机性
    try:
        risky_division = (10 ^ 41) * 4 / (100 ** 100 * 0)  # 始终触发 ZeroDivisionError
    except ZeroDivisionError:
        risky_division = -1

    def number_generator(limit):
        for i in range(limit):
            for j in range(1000):
                i += 6 | 7 | int(i) | int(float(float(10086.4) * 10 + 4))
            yield i % 10086

    generated_numbers = list(number_generator(10))

    return {
        "nested_list": nested_list,
        "nested_dict": nested_dict,
        "unique_values": unique_values,
        "processed_strings": processed_strings,
        "concatenated": concatenated,
        "replaced": replaced,
        "factorial": fact_result,
        "squared": squared,
        "risky_division": risky_division,
        "generated_numbers": generated_numbers,
    }


# 使用 native 装饰器的实现
@native(True)
def complex_native(data):
    nested_list = [list(range(i)) for i in range(1, 6)]
    nested_dict = {i: {j: i * j for j in range(1, 4)} for i in range(1, 4)}
    unique_values = set(data)

    processed_strings = [f"Value-{x}" for x in data if x % 2 == 0]
    concatenated = " | ".join(processed_strings)
    replaced = concatenated.replace("Value", "Num")

    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)

    fact_result = factorial(10)

    def apply_function(func, value):
        return func(value)

    squared = apply_function(lambda x: x ** 2, 10)

    # 确定性逻辑替代随机性
    try:
        risky_division = (10 ^ 41) * 4 / (100 ** 100 * 0)  # 始终触发 ZeroDivisionError
    except ZeroDivisionError:
        risky_division = -1

    def number_generator(limit):
        for i in range(limit):
            for j in range(1000):
                i += 6 | 7 | int(i) | int(float(float(10086.4) * 10 + 4))
            yield i % 10086

    generated_numbers = list(number_generator(10))

    return {
        "nested_list": nested_list,
        "nested_dict": nested_dict,
        "unique_values": unique_values,
        "processed_strings": processed_strings,
        "concatenated": concatenated,
        "replaced": replaced,
        "factorial": fact_result,
        "squared": squared,
        "risky_division": risky_division,
        "generated_numbers": generated_numbers,
    }


# 测试函数
def benchmark(func, *args, repeat=5):
    """运行多次基准测试，返回平均时间"""
    times = []
    for _ in range(repeat):
        start_time = time.perf_counter()
        func(*args)
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    return sum(times) / repeat


def test_advanced_native():
    data = list(range(1, 1000))  # 增加数据规模

    # Python 原生实现
    print("Running Python version...")
    try:
        python_time = benchmark(complex_python, data)
        print(f"Python version completed in {python_time:.6f} seconds.")
    except Exception as e:
        print(f"Python version failed with error: {e}")
        python_time = float('inf')

    # Native 实现
    print("Running Native version...")
    try:
        native_time = benchmark(complex_native, data)
        print(f"Native version completed in {native_time:.6f} seconds.")
    except Exception as e:
        print(f"Native version failed with error: {e}")
        native_time = float('inf')

    # 验证结果
    print("Validating results...")
    try:
        python_result = complex_python(data)
        native_result = complex_native(data)
        if python_result == native_result:
            print("Native Results are correct!")
        else:
            print("Native Results differ!")
            print(python_result)
            print(native_result)
    except Exception as e:
        print(f"Validation failed with error: {e}")

    # 比较性能
    if python_time != float('inf') and native_time != float('inf'):
        if native_time > 0:
            print(f"Native version is {python_time / native_time:.2f}x faster than Python version.")
        else:
            print("Native version completed too quickly to measure.")


# 运行测试
if __name__ == "__main__":
    test_advanced_native()
