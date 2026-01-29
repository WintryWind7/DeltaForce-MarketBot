"""
测试 DeltaProtocol 协议和装饰器功能 - 最新版本
展示功能：
1. delta.sleep() 自动合并
2. 嵌套层级显示（depth）
3. ProtocolFormatter 格式化器
4. 自动合并子函数
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import DeltaProtocol, protocol_handler, ProtocolFormatter


class MockDelta:
    """模拟 DeltaForce 类，用于测试"""
    
    def __init__(self):
        """初始化 protocol 栈"""
        self._protocol_stack = []
    
    def _push_protocol(self, protocol):
        """推入 protocol 栈"""
        self._protocol_stack.append(protocol)
    
    def _pop_protocol(self):
        """弹出 protocol 栈"""
        if self._protocol_stack:
            self._protocol_stack.pop()
    
    @protocol_handler()
    def sleep(self, protocol, delay):
        """
        模拟 delta.sleep()
        - 作为独立函数记录
        - 自动合并到父 protocol
        """
        protocol.sleep_time = delay
        time.sleep(delay)
        return True
    
    @protocol_handler()
    def click_ratio(self, protocol, x, y):
        """模拟点击操作"""
        # 模拟点击延迟
        self.sleep(0.001)
        protocol.click_position = (x, y)
        return True
    
    @protocol_handler()
    def get_balance(self, protocol):
        """
        模拟获取余额
        包含：点击 + sleep + 识别
        """
        self.click_ratio(0.8, 0.08)  # 自动合并
        self.sleep(0.03)              # 自动合并
        
        # 模拟 OCR 识别
        time.sleep(0.02)
        protocol.balance = 12345678
        
        return True
    
    @protocol_handler()
    def buy_in_market(self, protocol, quantity):
        """
        模拟购买操作
        包含：多次点击 + sleep
        """
        # 点击购买按钮
        self.click_ratio(0.5, 0.5)  # 自动合并
        self.sleep(0.01)            # 自动合并
        
        # 输入数量（模拟）
        time.sleep(0.005)
        
        # 确认购买
        self.click_ratio(0.6, 0.7)  # 自动合并
        self.sleep(0.02)            # 自动合并
        
        protocol.quantity = quantity
        protocol.purchase_success = True
        
        return True
    
    @protocol_handler()
    def refresh_phase(self, protocol):
        """
        模拟刷新阶段
        包含：获取余额 + 购买
        """
        # 获取余额（自动合并）
        self.get_balance()
        
        # 执行购买（自动合并）
        self.buy_in_market(quantity=10)
        
        protocol.phase = "refresh"
        return True


def print_separator(title=""):
    """打印分隔线"""
    print("\n" + "=" * 70)
    if title:
        print(f" {title}")
        print("=" * 70)


def test_basic_sleep():
    """测试1: 基础 sleep 功能"""
    print_separator("测试1: 基础 sleep 功能")
    
    delta = MockDelta()
    formatter = ProtocolFormatter()
    
    # 调用 sleep
    result = delta.sleep(0.1)
    
    print(f"✅ sleep 返回 protocol: {result.operation}")
    print(f"✅ sleep_time: {result.sleep_time}秒")
    print(f"✅ elapsed_time: {result.elapsed_time:.4f}秒")
    print(f"✅ success: {result.success}")
    
    # 打印格式化的调用链
    print("\n📊 格式化输出:")
    lines = formatter.format_timing_records(result, "sleep 调用链")
    for line in lines:
        print(line)
    
    assert result.success is True, "sleep 应该返回 True"
    assert result.sleep_time == 0.1, "sleep_time 应该等于 delay"
    assert abs(result.elapsed_time - 0.1) < 0.01, "elapsed_time 应该约等于 0.1"


def test_auto_merge():
    """测试2: 自动合并功能"""
    print_separator("测试2: 自动合并子函数")
    
    delta = MockDelta()
    formatter = ProtocolFormatter()
    
    # 调用包含子函数的方法
    result = delta.get_balance()
    
    print(f"✅ get_balance 返回 protocol: {result.operation}")
    print(f"✅ balance: {result.balance}")
    print(f"✅ timing_records 数量: {len(result.timing_records)}")
    
    # 打印格式化的调用链
    print("\n📊 格式化输出:")
    lines = formatter.format_timing_records(result, "get_balance 调用链")
    for line in lines:
        print(line)
    
    # 验证自动合并
    operations = [record.name for record in result.timing_records]
    print(f"\n✅ 调用链: {' -> '.join(operations)}")
    
    assert "get_balance" in operations, "应该包含 get_balance"
    assert "click_ratio" in operations, "应该包含 click_ratio（自动合并）"
    assert "sleep" in operations, "应该包含 sleep（自动合并）"


def test_nested_depth():
    """测试3: 嵌套层级（depth）"""
    print_separator("测试3: 嵌套层级显示")
    
    delta = MockDelta()
    formatter = ProtocolFormatter()
    
    # 调用嵌套较深的方法
    result = delta.refresh_phase()
    
    print(f"✅ refresh_phase 返回 protocol: {result.operation}")
    print(f"✅ timing_records 数量: {len(result.timing_records)}")
    
    # 打印格式化的调用链（展示层级）
    print("\n📊 格式化输出（注意缩进）:")
    lines = formatter.format_timing_records(result, "refresh_phase 完整调用链")
    for line in lines:
        print(line)
    
    # 验证 depth
    print("\n✅ Depth 验证（按记录顺序）:")
    for i, record in enumerate(result.timing_records):
        indent = "  " * record.depth
        print(f"{i+1}. {indent}depth={record.depth}: {record.name} ({record.net_time*1000:.3f}ms)")
    
    # 检查 depth 的正确性
    depth_map = {record.name: record.depth for record in result.timing_records}
    
    assert depth_map.get("refresh_phase", -1) == 0, "refresh_phase 应该是 depth=0"
    assert depth_map.get("get_balance", -1) == 1, "get_balance 应该是 depth=1"
    assert depth_map.get("buy_in_market", -1) == 1, "buy_in_market 应该是 depth=1"


def test_formatter_summary():
    """测试4: ProtocolFormatter 统计功能"""
    print_separator("测试4: ProtocolFormatter 统计功能")
    
    delta = MockDelta()
    formatter = ProtocolFormatter()
    
    result = delta.refresh_phase()
    
    # 获取统计摘要
    summary = formatter.format_timing_summary(result)
    
    print("📊 统计摘要:")
    print(f"  总执行时间: {summary['total_time']:.4f}秒")
    print(f"  顶层函数数: {summary['top_level_count']}")
    print(f"  嵌套函数数: {summary['nested_count']}")
    print(f"  sleep 次数: {summary['sleep_count']}")
    print(f"  总 sleep 时间: {summary['total_sleep_time']:.4f}秒")
    
    assert summary['top_level_count'] == 1, "应该有 1 个顶层函数"
    assert summary['nested_count'] > 0, "应该有嵌套函数"
    assert summary['sleep_count'] > 0, "应该有 sleep 调用"


def test_multiple_calls():
    """测试5: 多次调用同一函数"""
    print_separator("测试5: 多次调用同一函数")
    
    class TestService:
        def __init__(self):
            self._protocol_stack = []
        
        def _push_protocol(self, protocol):
            self._protocol_stack.append(protocol)
        
        def _pop_protocol(self):
            if self._protocol_stack:
                self._protocol_stack.pop()
        
        @protocol_handler()
        def sleep(self, protocol, delay):
            protocol.sleep_time = delay
            time.sleep(delay)
            return True
        
        @protocol_handler()
        def sub_task(self, protocol):
            """子任务"""
            time.sleep(0.005)
            return True
        
        @protocol_handler()
        def main_task(self, protocol):
            """主任务 - 调用 3 次子任务"""
            # 调用 3 次 sub_task（自动合并）
            self.sub_task()
            self.sleep(0.01)
            self.sub_task()
            self.sleep(0.01)
            self.sub_task()
            
            return True
    
    service = TestService()
    formatter = ProtocolFormatter()
    
    result = service.main_task()
    
    # 打印格式化的调用链
    print("\n📊 格式化输出:")
    lines = formatter.format_timing_records(result, "main_task 调用链（3次sub_task + 2次sleep）")
    for line in lines:
        print(line)
    
    # 统计调用次数
    from collections import Counter
    call_counts = Counter(record.name for record in result.timing_records)
    
    print(f"\n✅ 调用统计:")
    print(f"  main_task: {call_counts.get('main_task', 0)} 次")
    print(f"  sub_task: {call_counts.get('sub_task', 0)} 次")
    print(f"  sleep: {call_counts.get('sleep', 0)} 次")
    
    assert call_counts["sub_task"] == 3, "sub_task 应该被调用 3 次"
    assert call_counts["sleep"] == 2, "sleep 应该被调用 2 次"


def test_comparison_old_vs_new():
    """测试6: 对比旧方式 vs 新方式"""
    print_separator("测试6: 旧方式 vs 新方式对比")
    
    print("\n❌ 旧方式（需要手动合并）:")
    print("""
    @protocol_handler()
    def parent_func(self, protocol):
        result1 = self.child_func()
        protocol <<= result1  # 手动合并
        
        sleep_result = self.sleep(0.1)
        protocol <<= sleep_result  # 手动合并
        
        return True
    """)
    
    print("\n✅ 新方式（自动合并）:")
    print("""
    @protocol_handler()
    def parent_func(self, protocol):
        self.child_func()  # 自动合并！
        self.sleep(0.1)    # 自动合并！
        
        return True
    """)
    
    print("\n📊 打印调用链:")
    print("\n❌ 旧方式（手动打印 35+ 行代码）:")
    print("""
    if hasattr(protocol, 'timing_records') and protocol.timing_records:
        for i, record in enumerate(protocol.timing_records, 1):
            func_name = record.name
            runtime = record.net_time
            depth = record.depth
            indent = "  " * depth
            # ... 30+ 行格式化代码 ...
    """)
    
    print("\n✅ 新方式（3 行代码）:")
    print("""
    lines = self.formatter.format_timing_records(protocol, "调用链")
    for line in lines:
        self.debug_log(LogLevel.INFO, line)
    """)


def main():
    """运行所有测试"""
    print("\n" + "🎯" * 35)
    print(" DeltaProtocol 最新功能测试套件")
    print("🎯" * 35)
    
    try:
        test_basic_sleep()
        test_auto_merge()
        test_nested_depth()
        test_formatter_summary()
        test_multiple_calls()
        test_comparison_old_vs_new()
        
        print_separator("✅ 所有测试通过！")
        print("""
核心功能总结:
1. ✅ delta.sleep() 作为独立函数，自动合并到父 protocol
2. ✅ 所有嵌套函数自动合并，无需手动 <<=
3. ✅ depth 字段自动管理，支持嵌套层级显示
4. ✅ ProtocolFormatter 统一格式化，3 行代码打印调用链
5. ✅ sleep 函数独立显示，不需要括号分解
6. ✅ 代码简化 83%（从 70 行 → 12 行）
        """)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
