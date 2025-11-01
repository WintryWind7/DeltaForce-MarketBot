"""
Timer - 简单计时器模块
支持追踪time.sleep延迟（仅用于显示，不影响净时间计算）
"""

import time
import threading

# 全局栈，用于跟踪当前最内层的Timer（每个线程独立）
_timer_stack = threading.local()

def _get_timer_stack():
    """获取当前线程的Timer栈"""
    if not hasattr(_timer_stack, 'stack'):
        _timer_stack.stack = []
    return _timer_stack.stack


class Timer:
    """
    上下文管理器形式的计时器
    支持追踪time.sleep延迟（仅用于显示）
    
    使用示例:
        with Timer() as timer:
            # 执行一些操作
            time.sleep(1)
            result = some_function()
        
        print(f"执行时间: {timer.elapsed_time:.4f}秒")
        print(f"sleep延迟: {timer.sleep_time:.4f}秒")
        # 输出: 执行时间: 1.0012秒
        #      sleep延迟: 1.0000秒
    
    时间单位: 秒 (浮点数)
    精度: 微秒级 (使用 time.perf_counter())
    
    常见时间范围:
    - 微秒级操作: 0.000001秒 (1微秒)
    - 毫秒级操作: 0.001秒 (1毫秒)
    - 秒级操作: 1.0秒
    
    单位转换:
        milliseconds = timer.elapsed_time * 1000    # 转换为毫秒
        microseconds = timer.elapsed_time * 1000000 # 转换为微秒
    
    注意: sleep_time仅用于显示，不影响净时间计算逻辑
    """
    
    def __init__(self):
        self.elapsed_time = 0.0
        self.sleep_time = 0.0  # 仅用于显示，不影响净时间计算
        self._start_time = None
        self._previous_sleep = None  # 保存上一层的sleep函数
        self._original_sleep = time.sleep  # 保存原始sleep函数
    
    def _sleep_wrapper(self, delay):
        """包装time.sleep，只有最内层（栈顶）Timer记录sleep"""
        stack = _get_timer_stack()
        # 只有当前Timer是最内层（栈顶）时，才记录sleep
        # 这样可以确保每个sleep只被一个Timer记录，避免重复计算
        if len(stack) > 0 and stack[-1] is self:
            self.sleep_time += delay
        # 调用上一层的sleep函数
        return self._previous_sleep(delay)
    
    def __enter__(self):
        self._start_time = time.perf_counter()
        
        # 临时替换time.sleep为包装版本
        self._previous_sleep = time.sleep
        stack = _get_timer_stack()
        stack.append(self)
        time.sleep = self._sleep_wrapper
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复上一层的sleep函数
        stack = _get_timer_stack()
        if len(stack) > 0 and stack[-1] is self:
            stack.pop()
        if self._previous_sleep is not None:
            time.sleep = self._previous_sleep
            self._previous_sleep = None
        
        # 计算总执行时间（包含所有sleep，逻辑不变）
        self.elapsed_time = time.perf_counter() - self._start_time


# 输出类似: 执行时间: 0.001234秒