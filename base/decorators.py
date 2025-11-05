"""
Decorators - 装饰器模块

提供项目中使用的各种装饰器
"""

import functools
from typing import Callable, Optional
import os
import sys
import threading

# 添加当前目录到路径并优先使用
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from timer import Timer
from DeltaProtocol import DeltaProtocol

# 全局协议栈（使用线程本地存储，支持多线程）
_thread_local = threading.local()

# 全局调用序号计数器（使用线程本地存储）
def _get_next_call_order():
    """获取下一个调用序号"""
    if not hasattr(_thread_local, 'call_order_counter'):
        _thread_local.call_order_counter = 0
    _thread_local.call_order_counter += 1
    return _thread_local.call_order_counter


def protocol_handler(operation: Optional[str] = None):
    """
    DeltaProtocol装饰器 - 自动注入协议实例到实例方法
    
    该装饰器专门用于实例方法，会自动创建DeltaProtocol实例并作为第二个参数注入。
    实例方法的签名应该是: def method_name(self, protocol, ...)
    
    Args:
        operation: 操作名称，默认使用函数名
    
    使用示例:
        class MyService:
            @protocol_handler()
            def get_balance(self, protocol):
                # protocol 参数自动注入
                balance = 64498254
                protocol.balance = balance
                return balance
            
            @protocol_handler(operation="custom_buy")
            def buy_item(self, protocol, quantity, price):
                # protocol 参数自动注入
                total = quantity * price
                protocol.quantity = quantity
                protocol.price = price
                protocol.total = total
                return total
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 确定操作名称
            op_name = operation if operation is not None else func.__name__
            
            # 🎯 分配调用序号（在函数执行前就分配，确保按调用顺序）
            call_order = _get_next_call_order()
            
            # 创建协议实例
            protocol = DeltaProtocol(operation=op_name)  # success默认为None，只能通过函数返回值设置
            protocol.call_order = call_order  # 保存调用序号
            
            # 🎯 使用全局协议栈（线程安全）
            if not hasattr(_thread_local, 'protocol_stack'):
                _thread_local.protocol_stack = []
            
            # 推入全局协议栈
            _thread_local.protocol_stack.append(protocol)
            
            # 同时推入实例的协议栈（用于兼容性，如 delta.sleep()）
            if hasattr(self, '_push_protocol'):
                self._push_protocol(protocol)
            
            with Timer() as timer:
                # 将protocol作为第二个参数注入到原函数中
                result = func(self, protocol, *args, **kwargs)
                
                # 🎯 自动短路：如果子函数失败，直接让当前函数失败
                if hasattr(protocol, '_child_failed') and protocol._child_failed:
                    result = False
                
                # 检查返回值必须是True或False
                if result not in (True, False):
                    raise ValueError(f"函数 {op_name} 必须返回 True 或 False，实际返回: {result}")
                
                # 根据函数返回值设置协议success状态
                protocol.success = result
                
                # 设置消息并打印失败信息
                if not hasattr(protocol, 'message'):
                    if result:
                        protocol.message = f"{op_name} 执行成功"
                    else:
                        protocol.message = f"{op_name} 执行失败"
                
                # 如果失败，打印 error_message（如果有）
                if not result and hasattr(protocol, 'error_message') and protocol.error_message:
                    print(f"❌ [{op_name}] {protocol.error_message}")
            
            # 🎯 从全局协议栈获取父 protocol
            parent_protocol = None
            if len(_thread_local.protocol_stack) > 1:
                parent_protocol = _thread_local.protocol_stack[-2]  # 获取父 protocol
            
            # 弹出全局协议栈
            _thread_local.protocol_stack.pop()
            
            # 同时弹出实例的协议栈（用于兼容性）
            if hasattr(self, '_pop_protocol'):
                self._pop_protocol()
            
            # 将执行时间添加到协议中
            protocol.elapsed_time = timer.elapsed_time
            # sleep_time 已由 delta.sleep() 直接记录到 protocol 中
            # 不需要从 timer 获取（timer 不再追踪 sleep）
            
            # 添加到时间记录列表（传入调用序号）
            protocol.add_timing(call_order=call_order)
            
            # 🎯 自动合并到父 protocol（如果存在）
            # 无论是 self.xxx() 还是 other_obj.xxx()，只要有父 protocol 就自动合并
            if parent_protocol is not None:
                parent_protocol <<= protocol
            
            # 返回协议实例，而不是原函数的返回值
            return protocol
        
        return wrapper
    return decorator
