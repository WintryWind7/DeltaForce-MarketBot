"""
DeltaProtocol - 简单的通信协议类

用于项目内部组件之间的数据传递，采用混合设计：
- 核心字段：每个协议实例都有的基本字段
- 动态字段：根据具体使用场景动态添加的字段
"""

import time
from typing import Any


class DeltaProtocol:
    """DeltaForce通信协议 - 简单混合设计"""
    
    def __init__(self, operation: str = None, **kwargs):
        # 核心字段 - 每个协议都有
        self.success = None             # 必须字段：操作是否成功，默认None，只能通过装饰器设置
        self.operation = operation      # 操作类型
        # self.timestamp = time.time()    # 自动生成时间戳 (暂时注释)
        self.timing_records = []        # 执行时间记录：[(函数名, 运行时长, sleep延迟, 是否为底层), ...]
        self.is_base_function = False   # 是否为底层函数，默认False
        self.nested_time = 0.0          # 嵌套调用时间累积，用于计算净执行时间
        self.nested_sleep_time = 0.0    # 嵌套调用的sleep延迟累积（仅用于显示）
        
        # 动态字段 - 根据需要添加
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.__dict__.copy()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DeltaProtocol':
        """从字典创建协议实例"""
        success = data.pop('success')
        operation = data.pop('operation', None)
        # data.pop('timestamp', None)  # 移除时间戳，让构造函数重新生成 (暂时注释)
        return cls(success, operation, **data)
    
    def __bool__(self):
        """布尔值判断 - 返回操作是否成功"""
        return self.success
    
    def __str__(self):
        """字符串表示 - 返回success的布尔值"""
        return str(self.success)
    
    def add_timing(self):
        """添加执行时间记录"""
        # 计算净执行时间 = 总时间 - 嵌套调用时间（逻辑不变）
        elapsed = getattr(self, 'elapsed_time', 0.0)
        nested = getattr(self, 'nested_time', 0.0)
        net_time = elapsed - nested
        
        # 计算自己的sleep延迟（仅用于显示）
        # 由于只有最内层Timer记录sleep，所以sleep_time就是当前函数自己的sleep
        # 不需要减去嵌套sleep，因为嵌套函数的sleep被各自的Timer单独记录了
        own_sleep = getattr(self, 'sleep_time', 0.0)
        
        # 记录格式：(函数名, 净运行时长, sleep延迟, 是否为底层)
        self.timing_records.append((self.operation, net_time, own_sleep, self.is_base_function))
        return self
    
    def __lshift__(self, other_protocol):
        """重载 << 运算符，添加协议数据"""
        if not isinstance(other_protocol, DeltaProtocol):
            raise TypeError(f"只能合并 DeltaProtocol 实例，实际类型: {type(other_protocol)}")
        
        other_dict = other_protocol.to_dict()
        for key, value in other_dict.items():
            # 跳过核心字段，只继承业务数据
            if key not in ['success', 'operation', 'elapsed_time', 'timing_records', 'is_base_function', 'nested_time']:
                setattr(self, key, value)
        
        # 继承时间记录
        if hasattr(other_protocol, 'timing_records'):
            self.timing_records.extend(other_protocol.timing_records)
        
        # 累积嵌套调用时间（逻辑不变）
        if hasattr(other_protocol, 'elapsed_time'):
            self.nested_time += other_protocol.elapsed_time
        
        # 累积嵌套调用的sleep延迟（仅用于显示）
        if hasattr(other_protocol, 'sleep_time'):
            self.nested_sleep_time += other_protocol.sleep_time
        
        return self
    
    def __ilshift__(self, other_protocol):
        """重载 <<= 运算符，添加协议数据"""
        return self.__lshift__(other_protocol)


