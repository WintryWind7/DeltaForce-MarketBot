# -*- coding: utf-8 -*-
"""
测试Behavior基类的退出函数

测试内容:
1. exit_behavior() 成功退出
2. exit_behavior() 失败退出
3. 验证 master_stop_event 是否被正确设置
4. 验证 generate_final_report 是否被调用
5. 验证 handle_program_completion 是否被调用
6. 验证线程清理逻辑
"""

import sys
import os
import time
import threading
import queue
from unittest.mock import Mock, patch, MagicMock, call

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui.behavior.Behavior import Behavior, LogLevel
from PySide6.QtCore import QObject


class TestBehaviorExit:
    """测试Behavior退出功能的测试类"""
    
    def setup_method(self):
        """每个测试方法前的初始化"""
        # 创建一个简单的测试Behavior子类
        class SimpleBehavior(Behavior):
            def __init__(self):
                super().__init__(
                    behavior_name="TestBehavior",
                    log_signal=Mock(),
                    finished_signal=Mock(),
                    behavior_manager=Mock()
                )
                # 模拟必要的属性
                self.delta = None
                self.main_delta = None
                self.aux_delta = None
                self.config = {}
                
            def main_logic(self):
                """简单的主逻辑，直接返回True"""
                return True
            
            def init_config(self):
                """空配置初始化"""
                pass
        
        self.behavior = SimpleBehavior()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 确保停止事件被设置，避免线程泄漏
        if hasattr(self.behavior, 'master_stop_event'):
            self.behavior.master_stop_event.set()
        time.sleep(0.1)  # 等待线程结束
    
    def test_exit_behavior_success(self):
        """测试成功退出"""
        print("\n[TEST] 测试 exit_behavior 成功退出")
        
        # 模拟 generate_final_report 方法
        self.behavior.generate_final_report = Mock()
        
        # 调用 exit_behavior
        result = self.behavior.exit_behavior("测试成功退出", success=True)
        
        # 验证返回值
        assert result == True, "exit_behavior应该返回True"
        
        # 验证 master_stop_event 被设置
        assert self.behavior.master_stop_event.is_set(), "master_stop_event应该被设置"
        
        # 验证 generate_final_report 被调用
        self.behavior.generate_final_report.assert_called_once()
        
        print("✅ 成功退出测试通过")
    
    def test_exit_behavior_failure(self):
        """测试失败退出"""
        print("\n[TEST] 测试 exit_behavior 失败退出")
        
        # 模拟 generate_final_report 方法
        self.behavior.generate_final_report = Mock()
        
        # 调用 exit_behavior
        result = self.behavior.exit_behavior("测试失败退出", success=False)
        
        # 验证返回值
        assert result == False, "exit_behavior应该返回False"
        
        # 验证 master_stop_event 被设置
        assert self.behavior.master_stop_event.is_set(), "master_stop_event应该被设置"
        
        # 验证 generate_final_report 被调用
        self.behavior.generate_final_report.assert_called_once()
        
        print("✅ 失败退出测试通过")
    
    def test_exit_behavior_without_report(self):
        """测试没有 generate_final_report 方法的退出"""
        print("\n[TEST] 测试无 generate_final_report 的退出")
        
        # 确保没有 generate_final_report 方法
        if hasattr(self.behavior, 'generate_final_report'):
            delattr(self.behavior, 'generate_final_report')
        
        # 调用 exit_behavior 不应该抛出异常
        result = self.behavior.exit_behavior("无报告退出", success=True)
        
        # 验证返回值
        assert result == True, "exit_behavior应该返回True"
        
        # 验证 master_stop_event 被设置
        assert self.behavior.master_stop_event.is_set(), "master_stop_event应该被设置"
        
        print("✅ 无报告退出测试通过")
    
    def test_exit_behavior_report_exception(self):
        """测试 generate_final_report 抛出异常的情况"""
        print("\n[TEST] 测试 generate_final_report 抛出异常")
        
        # 模拟 generate_final_report 抛出异常
        def raise_exception():
            raise ValueError("报告生成失败")
        
        self.behavior.generate_final_report = raise_exception
        
        # 调用 exit_behavior 不应该抛出异常
        result = self.behavior.exit_behavior("报告异常退出", success=True)
        
        # 验证返回值（异常应该被捕获，仍然返回True）
        assert result == True, "exit_behavior应该返回True"
        
        # 验证 master_stop_event 被设置
        assert self.behavior.master_stop_event.is_set(), "master_stop_event应该被设置"
        
        print("✅ 报告异常测试通过")
    
    def test_exit_behavior_stop_event(self):
        """测试 master_stop_event 的状态变化"""
        print("\n[TEST] 测试 master_stop_event 状态变化")
        
        # 模拟 generate_final_report 方法
        self.behavior.generate_final_report = Mock()
        
        # 初始状态应该是未设置
        assert not self.behavior.master_stop_event.is_set(), "初始状态应该未设置"
        
        # 调用 exit_behavior
        self.behavior.exit_behavior("测试stop_event", success=True)
        
        # 验证 master_stop_event 被设置
        assert self.behavior.master_stop_event.is_set(), "master_stop_event应该被设置"
        
        print("✅ stop_event 测试通过")
    
    def test_exit_behavior_handle_completion_called(self):
        """测试 handle_program_completion 是否被调用"""
        print("\n[TEST] 测试 handle_program_completion 被调用")
        
        # 模拟 generate_final_report 和 handle_program_completion
        self.behavior.generate_final_report = Mock()
        original_handle = self.behavior.handle_program_completion
        self.behavior.handle_program_completion = Mock(side_effect=original_handle)
        
        # 调用 exit_behavior
        self.behavior.exit_behavior("测试完成处理", success=True)
        
        # 验证 handle_program_completion 被调用
        self.behavior.handle_program_completion.assert_called_once_with("测试完成处理")
        
        print("✅ handle_program_completion 测试通过")
    
    def test_exit_behavior_cleanup_threads(self):
        """测试线程清理逻辑"""
        print("\n[TEST] 测试线程清理逻辑")
        
        # 模拟 generate_final_report 方法
        self.behavior.generate_final_report = Mock()
        
        # 模拟 _cleanup_all_threads 方法
        original_cleanup = self.behavior._cleanup_all_threads
        self.behavior._cleanup_all_threads = Mock(side_effect=original_cleanup)
        
        # 调用 exit_behavior
        self.behavior.exit_behavior("测试线程清理", success=True)
        
        # 等待异步清理完成
        time.sleep(0.2)
        
        # 验证 _cleanup_all_threads 被调用
        self.behavior._cleanup_all_threads.assert_called_once()
        
        print("✅ 线程清理测试通过")
    
    def test_exit_behavior_exception_handling(self):
        """测试 exit_behavior 自身的异常处理"""
        print("\n[TEST] 测试 exit_behavior 自身异常处理")
        
        # 模拟 handle_program_completion 抛出异常
        def raise_exception(reason):
            raise RuntimeError("处理完成失败")
        
        self.behavior.handle_program_completion = raise_exception
        
        # 调用 exit_behavior 不应该抛出未捕获的异常
        result = self.behavior.exit_behavior("异常处理测试", success=True)
        
        # 即使发生异常，也应该返回False（因为异常处理中会返回False）
        assert result == False, "exit_behavior在异常时应该返回False"
        
        # 验证 master_stop_event 被设置
        assert self.behavior.master_stop_event.is_set(), "master_stop_event应该被设置"
        
        print("✅ 异常处理测试通过")
    
    def test_multiple_exit_calls(self):
        """测试多次调用 exit_behavior"""
        print("\n[TEST] 测试多次调用 exit_behavior")
        
        # 模拟 generate_final_report 方法
        self.behavior.generate_final_report = Mock()
        
        # 第一次调用
        result1 = self.behavior.exit_behavior("第一次退出", success=True)
        assert result1 == True
        
        # 第二次调用（应该仍然正常工作，不会崩溃）
        result2 = self.behavior.exit_behavior("第二次退出", success=False)
        assert result2 == False
        
        # 验证 master_stop_event 仍然被设置
        assert self.behavior.master_stop_event.is_set(), "master_stop_event应该被设置"
        
        print("✅ 多次调用测试通过")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试 Behavior.exit_behavior() 功能")
    print("="*60)
    
    test_instance = TestBehaviorExit()
    
    tests = [
        ("成功退出", test_instance.test_exit_behavior_success),
        ("失败退出", test_instance.test_exit_behavior_failure),
        ("无报告退出", test_instance.test_exit_behavior_without_report),
        ("报告异常", test_instance.test_exit_behavior_report_exception),
        ("stop_event", test_instance.test_exit_behavior_stop_event),
        ("handle_completion调用", test_instance.test_exit_behavior_handle_completion_called),
        ("线程清理", test_instance.test_exit_behavior_cleanup_threads),
        ("异常处理", test_instance.test_exit_behavior_exception_handling),
        ("多次调用", test_instance.test_multiple_exit_calls),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_instance.setup_method()
            test_func()
            test_instance.teardown_method()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {name}")
            print(f"   错误: {e}")
            failed += 1
            test_instance.teardown_method()
        except Exception as e:
            print(f"❌ 测试异常: {name}")
            print(f"   异常: {e}")
            failed += 1
            test_instance.teardown_method()
    
    print("\n" + "="*60)
    print(f"测试完成: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    # 运行测试
    success = run_tests()
    
    # 返回退出码
    sys.exit(0 if success else 1)

