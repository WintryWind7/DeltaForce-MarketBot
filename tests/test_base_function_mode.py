"""
测试 is_base_function 的两种打印模式
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from base import DeltaProtocol, ProtocolFormatter, protocol_handler, Timer
import time


class MockDelta:
    """模拟 Delta 类"""
    def __init__(self):
        self._protocol_stack = []
    
    def _push_protocol(self, protocol):
        self._protocol_stack.append(protocol)
    
    def _pop_protocol(self):
        if self._protocol_stack:
            self._protocol_stack.pop()
    
    @protocol_handler()
    def sleep(self, protocol, delay):
        """sleep 函数（is_base=True）"""
        protocol.sleep_time = delay
        protocol.is_base_function = True  # 标记为底层函数
        time.sleep(delay)
        return True
    
    @protocol_handler()
    def click_ratio(self, protocol, x, y):
        """点击函数（is_base=True）"""
        protocol.is_base_function = True  # 标记为底层函数
        self.sleep(0.01)
        return True
    
    @protocol_handler()
    def get_balance(self, protocol):
        """获取余额（非底层函数）"""
        self.click_ratio(0.5, 0.5)
        self.sleep(0.03)
        protocol.balance = 12345678
        return True
    
    @protocol_handler()
    def buy_in_market(self, protocol, quantity):
        """购买函数（非底层函数）"""
        self.click_ratio(0.7, 0.7)  # 点击数量条
        self.sleep(0.005)
        self.click_ratio(0.8, 0.8)  # 点击购买按钮
        protocol.quantity = quantity
        return True


def test_modes():
    """测试两种打印模式"""
    print("\n" + "="*70)
    print(" 测试 is_base_function 的两种打印模式")
    print("="*70)
    
    delta = MockDelta()
    formatter = ProtocolFormatter()
    
    # 执行一个包含多层调用的函数
    result = delta.buy_in_market(31)
    
    print("\n" + "="*70)
    print(" 模式1: 详细模式 (mode='detail')")
    print(" 显示所有函数，包括底层函数")
    print("="*70)
    lines = formatter.format_timing_records(result, "buy_in_market 调用链", mode="detail")
    for line in lines:
        print(line)
    
    print("\n" + "="*70)
    print(" 模式2: 简化模式 (mode='simple')")
    print(" 隐藏底层函数 (is_base=True)，时间合并到父函数")
    print("="*70)
    lines = formatter.format_timing_records(result, "buy_in_market 调用链", mode="simple")
    for line in lines:
        print(line)
    
    print("\n" + "="*70)
    print(" 说明")
    print("="*70)
    print("详细模式: 可以看到所有 click_ratio 和 sleep 调用")
    print("简化模式: click_ratio 和 sleep 被隐藏，时间合并到 buy_in_market")
    print("         buy_in_market 的时间 = 自己的时间 + 所有底层函数的时间")


if __name__ == "__main__":
    test_modes()

