import numpy as np
import time

from numba import njit, jit
from pylang_annotations import native


# 原始 Python 实现
def simulate_diffusion_python(grid, steps, diffusion_rate):
    rows, cols = grid.shape
    for _ in range(steps):
        new_grid = grid.copy()
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                # 模拟扩散：更新每个点的值
                new_grid[i, j] = (
                        grid[i, j]
                        + diffusion_rate
                        * (
                                grid[i - 1, j]
                                + grid[i + 1, j]
                                + grid[i, j - 1]
                                + grid[i, j + 1]
                                - 4 * grid[i, j]
                        )
                )
        grid = new_grid
    return grid


# 使用 native 装饰器的实现
@native(True)
def simulate_diffusion_native(grid, steps, diffusion_rate):
    rows, cols = grid.shape
    for _ in range(steps):
        new_grid = grid.copy()
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                # 模拟扩散：更新每个点的值
                new_grid[i, j] = (
                        grid[i, j]
                        + diffusion_rate
                        * (
                                grid[i - 1, j]
                                + grid[i + 1, j]
                                + grid[i, j - 1]
                                + grid[i, j + 1]
                                - 4 * grid[i, j]
                        )
                )
        grid = new_grid
    return grid


# numba加速
@njit(parallel=True)
def simulate_diffusion_numba(grid, steps, diffusion_rate):
    rows, cols = grid.shape
    for _ in range(steps):
        new_grid = grid.copy()
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                # 模拟扩散：更新每个点的值
                new_grid[i, j] = (
                        grid[i, j]
                        + diffusion_rate
                        * (
                                grid[i - 1, j]
                                + grid[i + 1, j]
                                + grid[i, j - 1]
                                + grid[i, j + 1]
                                - 4 * grid[i, j]
                        )
                )
        grid = new_grid
    return grid


# 测试函数
def test_native_decorator():
    # 初始化参数
    size = 100  # 网格大小
    steps = 100  # 模拟步数
    diffusion_rate = 0.1  # 扩散速率
    initial_grid = np.random.rand(size, size).astype(np.float64)  # 随机生成初始网格

    # 使用 Python 实现
    print("Running Python version...")
    start_time = time.time()
    python_result = simulate_diffusion_python(initial_grid, steps, diffusion_rate)
    python_time = time.time() - start_time
    print(f"Python version completed in {python_time:.4f} seconds.")

    # 使用 native 装饰器实现
    print("Running Native version...")
    start_time = time.time()
    native_result = simulate_diffusion_native(initial_grid, steps, diffusion_rate)
    native_time = time.time() - start_time
    print(f"Native version completed in {native_time:.4f} seconds.")

    # 使用 NJit 装饰器实现
    print("Running NJit version...")
    start_time = time.time()
    nJit_result = simulate_diffusion_numba(initial_grid, steps, diffusion_rate)
    nJit_time = time.time() - start_time
    print(f"NJit version completed in {nJit_time:.4f} seconds.")

    # 验证结果是否一致
    if np.allclose(python_result, native_result, atol=0):
        print("Native Results are correct!")
    else:
        print("Native Results differ!")
    if np.allclose(python_result, nJit_result, atol=0):
        print("NJit Results are correct!")
    else:
        print("NJit Results differ!")

    # 比较性能
    print(f"Native version is {python_time / native_time:.2f}x faster than Python version.")
    print(f"NJit version is {native_time / nJit_time:.2f}x faster than Native version.")


# 运行测试
if __name__ == "__main__":
    test_native_decorator()
