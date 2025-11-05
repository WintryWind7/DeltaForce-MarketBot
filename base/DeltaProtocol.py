"""
DeltaProtocol - 简单的通信协议类

用于项目内部组件之间的数据传递，采用混合设计：
- 核心字段：每个协议实例都有的基本字段
- 动态字段：根据具体使用场景动态添加的字段
"""

import time
from typing import Any, NamedTuple


class TimingRecord(NamedTuple):
    """时间记录（使用 NamedTuple 获得元组性能和字典便利性）"""
    name: str           # 函数名
    net_time: float     # 净运行时间（秒）- 不包括子函数
    sleep_time: float   # sleep延迟时间（秒）
    is_base: bool       # 是否为底层函数
    depth: int = 0      # 调用层级深度（预留，默认0）
    elapsed_time: float = 0.0  # 总执行时间（秒）- 包括子函数
    call_order: int = 0 # 调用序号（用于按调用顺序排序）


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
    
    def add_timing(self, call_order: int = 0):
        """添加执行时间记录"""
        # 计算净执行时间 = 总时间 - 嵌套调用时间（逻辑不变）
        elapsed = getattr(self, 'elapsed_time', 0.0)
        nested = getattr(self, 'nested_time', 0.0)
        net_time = elapsed - nested
        
        # 计算自己的sleep延迟（仅用于显示）
        # 由于只有最内层Timer记录sleep，所以sleep_time就是当前函数自己的sleep
        # 不需要减去嵌套sleep，因为嵌套函数的sleep被各自的Timer单独记录了
        own_sleep = getattr(self, 'sleep_time', 0.0)
        
        # 创建 TimingRecord 实例
        record = TimingRecord(
            name=self.operation,
            net_time=net_time,
            sleep_time=own_sleep,
            is_base=self.is_base_function,
            depth=0,  # 预留字段，暂时为0
            elapsed_time=elapsed,  # 总执行时间
            call_order=call_order  # 调用序号
        )
        self.timing_records.append(record)
        return self
    
    def __lshift__(self, other_protocol):
        """重载 << 运算符，添加协议数据"""
        if not isinstance(other_protocol, DeltaProtocol):
            raise TypeError(f"只能合并 DeltaProtocol 实例，实际类型: {type(other_protocol)}")
        
        # 🎯 自动短路：如果子协议失败，标记父协议需要短路
        if hasattr(other_protocol, 'success') and other_protocol.success == False:
            self._child_failed = True
            # 传播 error_message
            if hasattr(other_protocol, 'error_message') and not hasattr(self, 'error_message'):
                self.error_message = other_protocol.error_message
        
        other_dict = other_protocol.to_dict()
        for key, value in other_dict.items():
            # 跳过核心字段，只继承业务数据
            if key not in ['success', 'operation', 'elapsed_time', 'timing_records', 'is_base_function', 'nested_time', '_child_failed']:
                setattr(self, key, value)
        
        # 🎯 继承时间记录（并增加深度）
        if hasattr(other_protocol, 'timing_records'):
            for record in other_protocol.timing_records:
                # 创建新的 TimingRecord，深度 +1
                nested_record = TimingRecord(
                    name=record.name,
                    net_time=record.net_time,
                    sleep_time=record.sleep_time,
                    is_base=record.is_base,
                    depth=record.depth + 1,  # 嵌套深度 +1
                    elapsed_time=record.elapsed_time,  # 保留总执行时间
                    call_order=record.call_order  # 🎯 保留调用序号
                )
                self.timing_records.append(nested_record)
        
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


class ProtocolFormatter:
    """
    DeltaProtocol 格式化器
    
    提供统一的协议格式化和打印功能，支持：
    - 嵌套调用链格式化
    - 时间统计（仅统计顶层函数）
    - 自动缩进显示
    - sleep 函数特殊处理
    
    使用示例:
        formatter = ProtocolFormatter()
        lines = formatter.format_timing_records(protocol)
        for line in lines:
            self.debug_log(LogLevel.INFO, line)
    """
    
    def __init__(self):
        """初始化格式化器"""
        pass
    
    def format_timing_records(self, protocol, title: str = "调用链", show_total: bool = True, mode: str = "detail") -> list:
        """
        格式化 timing_records 为可打印的字符串列表（调用顺序）
        
        Args:
            protocol: DeltaProtocol 实例
            title: 标题文本
            show_total: 是否显示总执行时间
            mode: 打印模式
                - "detail" (详细模式): 显示所有函数，包括 is_base=True 的底层函数
                - "simple" (简化模式): 隐藏 is_base=True 的函数，时间合并到父函数
        
        Returns:
            list: 格式化后的字符串列表（每行一个字符串）
        
        Example:
            # 详细模式
            formatter = ProtocolFormatter()
            lines = formatter.format_timing_records(protocol, "调用链", mode="detail")
            # 返回:
            # [
            #     "📊 调用链:",
            #     "  1. A: 1.000ms",
            #     "    - B: 1.000ms",
            #     "      - C: 1.000ms",
            #     "  总执行时间: 1.000ms"
            # ]
            
            # 简化模式（C 为 is_base=True）
            lines = formatter.format_timing_records(protocol, "调用链", mode="simple")
            # 返回:
            # [
            #     "📊 调用链:",
            #     "  1. A: 1.000ms",
            #     "    - B: 2.000ms",  # C 的时间合并到 B
            #     "  总执行时间: 1.000ms"
            # ]
        """
        lines = []
        
        # 检查是否有 timing_records
        if not hasattr(protocol, 'timing_records') or not protocol.timing_records:
            return lines
        
        # 添加标题
        lines.append(f"📊 {title}:")
        
        # 重新组织 timing_records 为树状结构（按调用顺序）
        tree_lines = self._build_tree_structure(protocol.timing_records, mode=mode)
        lines.extend(tree_lines)
        
        # 添加总执行时间（只统计顶层函数的 elapsed_time）
        if show_total:
            total_time = sum(r.elapsed_time for r in protocol.timing_records if r.depth == 0)
            total_time_ms = total_time * 1000
            lines.append(f"  总执行时间: {total_time_ms:.3f}ms")
        
        return lines
    
    def _build_tree_structure(self, timing_records: list, mode: str = "detail") -> list:
        """
        将 timing_records 构建为树状结构（调用顺序）
        
        现在 timing_records 已经包含 call_order 字段，按照调用序号排序即可
        
        Args:
            timing_records: TimingRecord 列表
            mode: 打印模式
                - "detail": 显示所有函数，包括底层函数
                - "simple": 隐藏 is_base=True 的底层函数
        
        Returns:
            list: 格式化后的字符串列表
        """
        lines = []
        
        # 🎯 按 call_order 排序，确保调用顺序
        sorted_records = sorted(timing_records, key=lambda r: r.call_order)
        
        # 找到所有顶层函数（depth=0）
        top_level_records = [r for r in sorted_records if r.depth == 0]
        
        # 为每个顶层函数构建树
        for idx, top_record in enumerate(top_level_records, 1):
            # 找到这个顶层函数的所有子记录（按调用顺序）
            # 策略：所有 depth > 0 且 call_order 在顶层函数范围内的记录
            top_call_order = top_record.call_order
            
            # 找到下一个顶层函数的 call_order（如果有）
            next_top_idx = top_level_records.index(top_record) + 1
            if next_top_idx < len(top_level_records):
                next_top_call_order = top_level_records[next_top_idx].call_order
            else:
                next_top_call_order = float('inf')
            
            # 筛选出属于这个顶层函数的子记录
            children_records = [
                r for r in sorted_records 
                if r.depth > 0 and top_call_order < r.call_order < next_top_call_order
            ]
            
            # 构建树（传递 mode 参数）
            result = self._format_tree(top_record, children_records, idx, mode, parent_is_base=False)
            lines.extend(result)
        
        return lines
    
    def _format_tree(self, record, all_children: list, top_index: int = None, mode: str = "detail", parent_is_base: bool = False) -> list:
        """
        递归格式化节点树（按调用顺序）
        
        Args:
            record: 当前 TimingRecord
            all_children: 所有可能的子记录（已按 call_order 排序）
            top_index: 顶层序号（仅 depth=0 使用）
            mode: 打印模式 ("detail" 或 "simple")
            parent_is_base: 父函数是否为底层函数（用于传播 is_base 标记）
        
        Returns:
            list: 格式化后的字符串列表
        """
        lines = []
        
        # 🎯 判断当前节点是否为底层函数
        # 规则：如果父函数是底层，或自己标记为底层，则为底层
        current_is_base = parent_is_base or record.is_base
        
        # 🎯 简化模式：如果当前节点是底层函数，则不显示（时间合并到父节点）
        if mode == "simple" and current_is_base and record.depth > 0:
            # 底层函数不显示，直接返回
            return lines
        
        # 生成缩进
        indent = "  " + "  " * record.depth
        
        # 顶层用序号，子层用 -
        if record.depth == 0:
            prefix = f"{top_index}."
        else:
            prefix = "-"
        
        # 找到当前节点的直接子节点（depth = current_depth + 1）
        # 策略：按 call_order 顺序查找
        direct_children = []
        children_total_elapsed = 0.0
        base_children_total_elapsed = 0.0  # 底层子函数的总时间
        
        # all_children 已经按 call_order 排序，直接遍历
        for child in all_children:
            if child.depth == record.depth + 1:
                # 这是直接子节点
                direct_children.append(child)
                
                # 🎯 判断子节点是否为底层
                child_is_base = current_is_base or child.is_base
                
                # 🎯 简化模式：底层子函数的时间不计入 children_total_elapsed
                if mode == "simple" and child_is_base:
                    base_children_total_elapsed += child.elapsed_time
                else:
                    children_total_elapsed += child.elapsed_time
        
        # 🎯 计算并显示父函数的净时间（自身耗时，不包括子函数）
        # 详细模式：总时间 - 所有子函数时间
        # 简化模式：总时间 - 非底层子函数时间（底层函数时间合并到父函数）
        if mode == "simple":
            self_time = record.elapsed_time - children_total_elapsed
        else:
            self_time = record.elapsed_time - children_total_elapsed - base_children_total_elapsed
        
        self_time_ms = self_time * 1000
        
        # 显示格式：函数名: 自身耗时
        lines.append(f"{indent}{prefix} {record.name}: {self_time_ms:.3f}ms")
        
        # 递归格式化子节点（按调用顺序）
        for child in direct_children:
            # 找到这个子节点的所有子孙节点（call_order 在子节点之后的）
            child_call_order = child.call_order
            
            # 找到下一个同级兄弟节点的 call_order（如果有）
            child_idx = direct_children.index(child)
            if child_idx + 1 < len(direct_children):
                next_sibling_call_order = direct_children[child_idx + 1].call_order
            else:
                next_sibling_call_order = float('inf')
            
            # 筛选出属于这个子节点的子孙记录
            child_descendants = [
                r for r in all_children
                if r.depth > child.depth and child_call_order < r.call_order < next_sibling_call_order
            ]
            
            # 🎯 递归格式化子节点（传递 current_is_base）
            child_lines = self._format_tree(child, child_descendants, None, mode, current_is_base)
            lines.extend(child_lines)
        
        return lines
    
    def format_timing_summary(self, protocol) -> dict:
        """
        生成时间统计摘要
        
        Args:
            protocol: DeltaProtocol 实例
        
        Returns:
            dict: 统计信息
                {
                    'total_time': 总时间（秒）,
                    'top_level_count': 顶层函数数量,
                    'nested_count': 嵌套函数数量,
                    'sleep_count': sleep 调用次数,
                    'total_sleep_time': 总 sleep 时间（秒）
                }
        """
        if not hasattr(protocol, 'timing_records') or not protocol.timing_records:
            return {
                'total_time': 0.0,
                'top_level_count': 0,
                'nested_count': 0,
                'sleep_count': 0,
                'total_sleep_time': 0.0
            }
        
        total_time = 0.0
        top_level_count = 0
        nested_count = 0
        sleep_count = 0
        total_sleep_time = 0.0
        
        for record in protocol.timing_records:
            if record.depth == 0:
                total_time += record.net_time
                top_level_count += 1
            else:
                nested_count += 1
            
            if record.name == 'sleep':
                sleep_count += 1
                total_sleep_time += record.sleep_time
        
        return {
            'total_time': total_time,
            'top_level_count': top_level_count,
            'nested_count': nested_count,
            'sleep_count': sleep_count,
            'total_sleep_time': total_sleep_time
        }
    
    def print_timing_tree(self, protocol, title: str = "调用链") -> str:
        """
        生成树状结构的调用链（单个字符串，包含换行符）
        
        Args:
            protocol: DeltaProtocol 实例
            title: 标题文本
        
        Returns:
            str: 树状结构的字符串
        
        Example:
            formatter = ProtocolFormatter()
            tree = formatter.print_timing_tree(protocol)
            print(tree)
            # 输出:
            # 📊 调用链:
            # ├─ get_balance: 100.123ms
            # │  ├─ click_ratio: 10.456ms
            # │  └─ sleep: 30.000ms
            # └─ purchase_phase: 200.456ms
            #    ├─ click_ratio: 10.456ms
            #    └─ sleep: 50.000ms
        """
        lines = self.format_timing_records(protocol, title, show_total=False)
        return '\n'.join(lines)


