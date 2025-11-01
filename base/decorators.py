"""
Decorators - 装饰器模块

提供项目中使用的各种装饰器
"""

import functools
from typing import Callable, Optional
import os
import sys

# 添加当前目录到路径并优先使用
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from timer import Timer
from DeltaProtocol import DeltaProtocol


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
            
            # 创建协议实例
            protocol = DeltaProtocol(operation=op_name)  # success默认为None，只能通过函数返回值设置
            
            with Timer() as timer:
                # 将protocol作为第二个参数注入到原函数中
                result = func(self, protocol, *args, **kwargs)
                
                # 检查返回值必须是True或False
                if result not in (True, False):
                    raise ValueError(f"函数 {op_name} 必须返回 True 或 False，实际返回: {result}")
                
                # 根据函数返回值设置协议success状态
                protocol.success = result
                if not hasattr(protocol, 'message'):
                    if result:
                        protocol.message = f"{op_name} 执行成功"
                    else:
                        protocol.message = f"{op_name} 执行失败"
            
            # 将执行时间添加到协议中
            protocol.elapsed_time = timer.elapsed_time
            # 记录sleep时间（仅用于显示）
            protocol.sleep_time = timer.sleep_time
            
            # 添加到时间记录列表（逻辑不变）
            protocol.add_timing()
            
            # 返回协议实例，而不是原函数的返回值
            return protocol
        
        return wrapper
    return decorator
