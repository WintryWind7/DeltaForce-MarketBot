"""
Timer - 简单计时器模块
精确测量代码执行时间（sleep 时间由 delta.sleep() 直接追踪）
"""

import time


class Timer:
    """
    上下文管理器形式的计时器
    
    使用示例:
        with Timer() as timer:
            # 执行一些操作
            delta.sleep(1)  # sleep 时间由 delta.sleep() 自动记录到 protocol
            result = some_function()
        
        print(f"执行时间: {timer.elapsed_time:.4f}秒")
        # 输出: 执行时间: 1.0012秒
    
    时间单位: 秒 (浮点数)
    精度: 微秒级 (使用 time.perf_counter())
    
    常见时间范围:
    - 微秒级操作: 0.000001秒 (1微秒)
    - 毫秒级操作: 0.001秒 (1毫秒)
    - 秒级操作: 1.0秒
    
    单位转换:
        milliseconds = timer.elapsed_time * 1000    # 转换为毫秒
        microseconds = timer.elapsed_time * 1000000 # 转换为微秒
    """
    
    def __init__(self):
        self.elapsed_time = 0.0
        self._start_time = None
    
    def __enter__(self):
        self._start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 计算总执行时间（包含所有操作，包括 sleep）
        self.elapsed_time = time.perf_counter() - self._start_time


# 输出类似: 执行时间: 0.001234秒