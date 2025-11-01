"""
Base模块 - DeltaForce项目基础组件

提供项目核心的基础类和协议定义，包括：
- DeltaProtocol: 标准化通信协议类
- Timer: 计时器功能
- 相关枚举类型和便捷函数

使用示例:
    from base import DeltaProtocol, success_protocol, error_protocol
    from base import Timer, timing_decorator, timer_context
    
    # 创建成功协议
    msg = DeltaProtocol(True, "get_balance", balance=64498254)
    
    # 使用计时器
    @timing_decorator()
    def my_function():
        pass
"""

from .DeltaProtocol import (
    # 主要协议类
    DeltaProtocol,
)

from .timer import (
    # 计时器类
    Timer,
)

from .decorators import (
    # 装饰器
    protocol_handler,
)

__version__ = "1.0.0"
__author__ = "DeltaForce Team"

# 导出的公共接口
__all__ = [
    # 主要类
    "DeltaProtocol",
    "Timer",
    
    # 装饰器
    "protocol_handler",
]
