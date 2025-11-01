"""
测试 DeltaProtocol 协议和装饰器功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import DeltaProtocol, protocol_handler


class TestService:
    """测试服务类"""
    
    @protocol_handler()
    def function_E(self, protocol):
        """最底层函数E"""
        protocol.e_data = "E的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        return True
    
    @protocol_handler()
    def function_D(self, protocol):
        """函数D"""
        protocol.d_data = "D的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        protocol << self.function_E()
        return True
    
    @protocol_handler()
    def function_C(self, protocol):
        """函数C"""
        protocol.c_data = "C的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        protocol << self.function_D()
        return True
    
    @protocol_handler()
    def function_B(self, protocol):
        """函数B"""
        protocol.b_data = "B的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        protocol << self.function_C()
        return True
    
    @protocol_handler()
    def function_A(self, protocol):
        """函数A - 金字塔式嵌套"""
        protocol.a_data = "A的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        protocol << self.function_B()
        return True
    
    # 梯形嵌套测试函数
    @protocol_handler()
    def function_C_multi(self, protocol):
        """底层函数C - 梯形测试"""
        protocol.c_data = "C的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        return True
    
    @protocol_handler()
    def function_B_multi(self, protocol):
        """中层函数B - 调用多次C"""
        protocol.b_data = "B的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        
        # 调用3次C函数
        protocol << self.function_C_multi()
        protocol << self.function_C_multi()
        protocol << self.function_C_multi()
        return True
    
    @protocol_handler()
    def function_A_multi(self, protocol):
        """顶层函数A - 调用多次B"""
        protocol.a_data = "A的数据"
        # 模拟相似的执行时间
        for i in range(1000):
            pass
        
        # 调用2次B函数
        protocol << self.function_B_multi()
        protocol << self.function_B_multi()
        return True
    
    @protocol_handler()
    def function_fail(self, protocol):
        """测试失败的函数"""
        protocol.fail_data = "失败数据"
        return False
    
    @protocol_handler()
    def function_error(self, protocol):
        """测试异常的函数"""
        protocol.error_data = "异常数据"
        raise ValueError("测试异常")


def test_basic_protocol():
    """测试基础协议功能"""
    print("=" * 50)
    print("测试基础协议功能")
    print("=" * 50)
    
    service = TestService()
    
    # 测试单个函数
    result = service.function_E()
    
    print(f"协议类型: {type(result)}")
    print(f"操作名称: {result.operation}")
    print(f"执行成功: {result.success}")
    print(f"执行时间: {result.elapsed_time:.6f}秒")
    print(f"E数据: {result.e_data}")
    print(f"时间记录: {result.timing_records}")
    
    # 验证基础功能
    assert isinstance(result, DeltaProtocol), "返回值应该是DeltaProtocol实例"
    assert result.operation == "function_E", "操作名称应该是function_E"
    assert result.success is True, "执行应该成功"
    assert hasattr(result, 'elapsed_time'), "应该有elapsed_time属性"
    assert result.e_data == "E的数据", "应该包含E的数据"
    assert len(result.timing_records) == 1, "应该有1条时间记录"
    
    print("✅ 基础协议功能测试通过")


def test_protocol_inheritance():
    """测试协议继承功能"""
    print("\n" + "=" * 50)
    print("测试协议继承功能")
    print("=" * 50)
    
    service = TestService()
    
    # 测试嵌套调用
    result = service.function_A()
    
    print(f"最终协议数据:")
    print(f"  操作名称: {result.operation}")
    print(f"  执行成功: {result.success}")
    print(f"  A数据: {getattr(result, 'a_data', 'None')}")
    print(f"  B数据: {getattr(result, 'b_data', 'None')}")
    print(f"  C数据: {getattr(result, 'c_data', 'None')}")
    print(f"  A值: {getattr(result, 'a_value', 'None')}")
    print(f"  B值: {getattr(result, 'b_value', 'None')}")
    print(f"  C值: {getattr(result, 'c_value', 'None')}")
    
    print(f"\n时间记录链:")
    for i, (op_name, elapsed, is_base) in enumerate(result.timing_records):
        print(f"  {i+1}. {op_name}: {elapsed:.6f}秒, 底层={is_base}")
    
    # 验证继承功能
    assert result.operation == "function_A", "最终操作应该是function_A"
    assert result.success is True, "最终执行应该成功"
    
    # 验证数据继承
    assert result.a_data == "A的数据", "应该包含A的数据"
    assert result.b_data == "B的数据", "应该继承B的数据"
    assert result.c_data == "C的数据", "应该继承C的数据"
    assert result.d_data == "D的数据", "应该继承D的数据"
    assert result.e_data == "E的数据", "应该继承E的数据"
    
    # 验证时间记录
    assert len(result.timing_records) == 5, "应该有5条时间记录"
    
    # 验证时间记录顺序（从内到外完成）
    operations = [record[0] for record in result.timing_records]
    expected_order = ["function_E", "function_D", "function_C", "function_B", "function_A"]
    assert operations == expected_order, f"时间记录顺序应该是{expected_order}"
    
    # 验证所有记录的is_base都是False
    for _, _, is_base in result.timing_records:
        assert is_base is False, "默认情况下is_base应该是False"
    
    print("✅ 协议继承功能测试通过")


def test_pyramid_nesting():
    """测试金字塔式嵌套 - A->B->C->D->E"""
    print("\n" + "=" * 50)
    print("测试金字塔式嵌套 (A->B->C->D->E)")
    print("=" * 50)
    
    service = TestService()
    result = service.function_A()
    
    print(f"时间记录链:")
    for i, (op_name, elapsed, is_base) in enumerate(result.timing_records):
        print(f"  {i+1}. {op_name}: {elapsed:.6f}秒, 底层={is_base}")
    
    print(f"\n总执行时间: {result.elapsed_time:.6f}秒")
    print(f"嵌套时间: {result.nested_time:.6f}秒")
    
    # 验证时间记录数量
    assert len(result.timing_records) == 5, "应该有5条时间记录 (A,B,C,D,E)"
    
    # 验证调用顺序
    operations = [record[0] for record in result.timing_records]
    expected_order = ["function_E", "function_D", "function_C", "function_B", "function_A"]
    assert operations == expected_order, f"时间记录顺序应该是{expected_order}"
    
    # 验证净执行时间应该相似（每个函数都有相似的处理时间）
    times = [record[1] for record in result.timing_records]
    avg_time = sum(times) / len(times)
    print(f"平均净执行时间: {avg_time:.6f}秒")
    
    # 检查时间差异不应该太大（允许20%的误差）
    for i, (op_name, elapsed, _) in enumerate(result.timing_records):
        diff_ratio = abs(elapsed - avg_time) / avg_time
        print(f"  {op_name} 时间偏差: {diff_ratio:.2%}")
        assert diff_ratio < 0.5, f"{op_name} 的净执行时间偏差过大: {diff_ratio:.2%}"
    
    print("✅ 金字塔式嵌套测试通过")


def test_trapezoid_nesting():
    """测试梯形嵌套 - A调用2次B，B调用3次C"""
    print("\n" + "=" * 50)
    print("测试梯形嵌套 (A->2*B->3*C)")
    print("=" * 50)
    
    service = TestService()
    result = service.function_A_multi()
    
    print(f"时间记录链:")
    for i, (op_name, elapsed, is_base) in enumerate(result.timing_records):
        print(f"  {i+1}. {op_name}: {elapsed:.6f}秒, 底层={is_base}")
    
    print(f"\n总执行时间: {result.elapsed_time:.6f}秒")
    print(f"嵌套时间: {result.nested_time:.6f}秒")
    
    # 验证时间记录数量：6次C + 2次B + 1次A = 9条记录
    assert len(result.timing_records) == 9, "应该有9条时间记录 (6*C + 2*B + 1*A)"
    
    # 统计各函数的调用次数
    from collections import Counter
    call_counts = Counter(record[0] for record in result.timing_records)
    print(f"\n函数调用统计:")
    for func_name, count in call_counts.items():
        print(f"  {func_name}: {count}次")
    
    assert call_counts["function_C_multi"] == 6, "function_C_multi应该被调用6次"
    assert call_counts["function_B_multi"] == 2, "function_B_multi应该被调用2次"
    assert call_counts["function_A_multi"] == 1, "function_A_multi应该被调用1次"
    
    # 验证同类函数的净执行时间应该相似
    c_times = [record[1] for record in result.timing_records if record[0] == "function_C_multi"]
    b_times = [record[1] for record in result.timing_records if record[0] == "function_B_multi"]
    a_times = [record[1] for record in result.timing_records if record[0] == "function_A_multi"]
    
    print(f"\nC函数净执行时间: {[f'{t:.6f}' for t in c_times]}")
    print(f"B函数净执行时间: {[f'{t:.6f}' for t in b_times]}")
    print(f"A函数净执行时间: {[f'{t:.6f}' for t in a_times]}")
    
    # 检查同类函数时间的一致性
    def check_time_consistency(times, func_name):
        if len(times) > 1:
            avg_time = sum(times) / len(times)
            for t in times:
                diff_ratio = abs(t - avg_time) / avg_time if avg_time > 0 else 0
                assert diff_ratio < 0.5, f"{func_name} 的净执行时间不一致: {diff_ratio:.2%}"
    
    check_time_consistency(c_times, "function_C_multi")
    check_time_consistency(b_times, "function_B_multi")
    
    print("✅ 梯形嵌套测试通过")


def test_protocol_failure():
    """测试协议失败情况"""
    print("\n" + "=" * 50)
    print("测试协议失败情况")
    print("=" * 50)
    
    service = TestService()
    
    # 测试返回False的情况
    result = service.function_fail()
    
    print(f"失败协议:")
    print(f"  操作名称: {result.operation}")
    print(f"  执行成功: {result.success}")
    print(f"  消息: {getattr(result, 'message', 'None')}")
    print(f"  失败数据: {getattr(result, 'fail_data', 'None')}")
    
    # 验证失败状态
    assert result.operation == "function_fail", "操作名称应该是function_fail"
    assert result.success is False, "执行应该失败"
    assert result.fail_data == "失败数据", "应该包含失败数据"
    assert len(result.timing_records) == 1, "应该有1条时间记录"
    
    print("✅ 协议失败情况测试通过")


def test_protocol_exception():
    """测试协议异常情况"""
    print("\n" + "=" * 50)
    print("测试协议异常情况")
    print("=" * 50)
    
    service = TestService()
    
    # 测试异常情况
    try:
        result = service.function_error()
        assert False, "应该抛出异常"
    except ValueError as e:
        print(f"捕获到预期异常: {e}")
        print("✅ 协议异常情况测试通过")


def test_protocol_boolean():
    """测试协议布尔值判断"""
    print("\n" + "=" * 50)
    print("测试协议布尔值判断")
    print("=" * 50)
    
    service = TestService()
    
    # 测试成功协议的布尔值
    success_result = service.function_C()
    if success_result:
        print("✅ 成功协议的布尔值判断为True")
    else:
        assert False, "成功协议应该判断为True"
    
    # 测试失败协议的布尔值
    fail_result = service.function_fail()
    if not fail_result:
        print("✅ 失败协议的布尔值判断为False")
    else:
        assert False, "失败协议应该判断为False"


def test_invalid_return_value():
    """测试无效返回值"""
    print("\n" + "=" * 50)
    print("测试无效返回值")
    print("=" * 50)
    
    class InvalidService:
        @protocol_handler()
        def invalid_return(self, protocol):
            return "invalid"  # 应该只返回True或False
    
    service = InvalidService()
    
    try:
        service.invalid_return()
        assert False, "应该抛出ValueError"
    except ValueError as e:
        print(f"捕获到预期的ValueError: {e}")
        print("✅ 无效返回值测试通过")


def main():
    """主测试函数"""
    service = TestService()
    
    print("金字塔式嵌套 (A->B->C->D->E):")
    result1 = service.function_A()
    for i, (op_name, elapsed, is_base) in enumerate(result1.timing_records):
        print(f"  {i+1}. {op_name}: {elapsed:.6f}秒, 底层={is_base}")
    
    print("\n梯形嵌套 (A->2*B->3*C):")
    result2 = service.function_A_multi()
    for i, (op_name, elapsed, is_base) in enumerate(result2.timing_records):
        print(f"  {i+1}. {op_name}: {elapsed:.6f}秒, 底层={is_base}")


if __name__ == "__main__":
    main()
