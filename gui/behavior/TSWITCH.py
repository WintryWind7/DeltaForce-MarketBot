# -*- coding: utf-8 -*-
"""
窗口切换性能测试行为模块 - TSWITCH (Test Window Switch)
用于测试主端和辅端窗口切换的性能
代码ID: TSWITCH
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from Behavior import Behavior, LogLevel
from base.decorators import protocol_handler

import time

# 行为信息定义
BEHAVIOR_INFO = {
    "code_id": "TSWITCH",
    "title": "窗口切换性能测试",
    "description": "测试主端和辅端窗口切换的性能，进行5次切换并记录耗时",
    "version": "1.0.0",
    "author": "DeltaForce Team",
    "tags": ["测试", "双端"],
    "custom_config": {
        "switch_count": {
            "type": "int",
            "label": "切换次数",
            "default": 5,
            "min": 1,
            "max": 20,
            "description": "测试的切换次数"
        },
        "debug_mode": {
            "type": "int",
            "label": "调试模式",
            "default": 2,
            "min": 0,
            "max": 2,
            "description": "0=关闭, 1=简化debug(隐藏底层函数), 2=详细debug(显示所有函数)"
        }
    }
}

class WindowSwitchTestBehavior(Behavior):
    """窗口切换性能测试行为类"""
    
    @classmethod
    def args(cls):
        """定义参数和UI配置"""
        return {
            'switch_count': {
                'type': 'int',
                'label': '切换次数',
                'default': 5,
                'min': 1,
                'max': 20,
                'description': '测试的切换次数'
            },
            'debug_mode': {
                'type': 'int',
                'label': '调试模式',
                'default': 2,
                'min': 0,
                'max': 2,
                'description': '0=关闭, 1=简化debug(隐藏底层函数), 2=详细debug(显示所有函数)'
            }
        }
    
    def __init__(self, window_handles, config=None):
        """初始化行为"""
        super().__init__(window_handles, config)
        
        # 获取配置参数
        self.switch_count = self.config.get('switch_count', 5)
        self.debug_mode = self.config.get('debug_mode', 2)
        
        # 行为要求双端
        self.require_main = True
        self.require_aux = True
        
        self.send_log(LogLevel.INFO, f"📊 窗口切换测试初始化完成")
        self.send_log(LogLevel.INFO, f"📊 切换次数: {self.switch_count}")
        self.send_log(LogLevel.INFO, f"📊 调试模式: {self.debug_mode}")
    
    @protocol_handler()
    def single_switch_test(self, protocol, switch_index):
        """单次切换测试"""
        # 获取主端和辅端实例
        main_delta = self.get_main_delta()
        aux_delta = self.get_aux_delta()
        
        self.send_log(LogLevel.INFO, f"")
        self.send_log(LogLevel.INFO, f"{'='*50}")
        self.send_log(LogLevel.INFO, f"🔄 第 {switch_index}/{self.switch_count} 次切换测试")
        self.send_log(LogLevel.INFO, f"{'='*50}")
        
        # 切换到主端（使用验证）
        self.send_log(LogLevel.INFO, "🔄 切换到主端（验证模式）...")
        try:
            main_result = main_delta.verify_window_focus(loop=False)  # 装饰器自动合并
            
            if not main_result.success:
                self.send_log(LogLevel.ERROR, f"❌ 切换到主端失败")
                if hasattr(main_result, 'error_message'):
                    self.send_log(LogLevel.ERROR, f"   错误: {main_result.error_message}")
                if hasattr(main_result, 'verify_result'):
                    self.send_log(LogLevel.ERROR, f"   验证结果: {main_result.verify_result}")
                return False
            
            verify_info = f"验证: {main_result.verify_result}" if hasattr(main_result, 'verify_result') else ""
            self.send_log(LogLevel.SUCCESS, f"✅ 切换到主端成功，耗时: {main_result.elapsed_time*1000:.3f}ms ({verify_info})")
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 切换到主端异常: {e}")
            import traceback
            self.send_log(LogLevel.ERROR, traceback.format_exc())
            return False
        
        time.sleep(0.2)  # 短暂延迟
        
        # 切换到辅端（使用验证）
        self.send_log(LogLevel.INFO, "🔄 切换到辅端（验证模式）...")
        try:
            aux_result = aux_delta.verify_window_focus(loop=False)  # 装饰器自动合并
            
            if not aux_result.success:
                self.send_log(LogLevel.ERROR, f"❌ 切换到辅端失败")
                if hasattr(aux_result, 'error_message'):
                    self.send_log(LogLevel.ERROR, f"   错误: {aux_result.error_message}")
                if hasattr(aux_result, 'verify_result'):
                    self.send_log(LogLevel.ERROR, f"   验证结果: {aux_result.verify_result}")
                return False
            
            verify_info = f"验证: {aux_result.verify_result}" if hasattr(aux_result, 'verify_result') else ""
            self.send_log(LogLevel.SUCCESS, f"✅ 切换到辅端成功，耗时: {aux_result.elapsed_time*1000:.3f}ms ({verify_info})")
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 切换到辅端异常: {e}")
            import traceback
            self.send_log(LogLevel.ERROR, traceback.format_exc())
            return False
        
        time.sleep(0.2)  # 短暂延迟
        
        # 不在这里打印（因为 single_switch_test 自己的记录还没添加）
        # 调用链会在 test_window_switch 中统一打印
        
        return True
    
    @protocol_handler()
    def test_window_switch(self, protocol):
        """测试窗口切换性能"""
        self.send_log(LogLevel.INFO, "🔄 开始窗口切换测试...")
        
        # 获取主端和辅端实例
        main_delta = self.get_main_delta()
        aux_delta = self.get_aux_delta()
        
        if not main_delta or not aux_delta:
            self.send_log(LogLevel.ERROR, "❌ 无法获取主端或辅端实例")
            return False
        
        self.send_log(LogLevel.INFO, f"✅ 主端窗口句柄: {main_delta.target_window_handle}")
        self.send_log(LogLevel.INFO, f"✅ 辅端窗口句柄: {aux_delta.target_window_handle}")
        
        # 执行多次切换测试
        for i in range(self.switch_count):
            switch_result = self.single_switch_test(switch_index=i+1)  # 装饰器自动合并
            
            if not switch_result.success:
                self.send_log(LogLevel.ERROR, f"❌ 第{i+1}次切换测试失败")
                return False
            
            # 打印本次切换的调用链（switch_result 已经包含完整记录）
            if self.debug_mode > 0:
                mode = "simple" if self.debug_mode == 1 else "detail"
                lines = self.formatter.format_timing_records(
                    switch_result,  # 使用 switch_result 而不是 protocol
                    title=f"第{i+1}次切换调用链",
                    mode=mode
                )
                for line in lines:
                    self.debug_log(LogLevel.INFO, line)
        
        self.send_log(LogLevel.INFO, f"")
        self.send_log(LogLevel.SUCCESS, f"✅ 窗口切换测试完成！共进行 {self.switch_count} 次双向切换")
        return True
    
    @protocol_handler()
    def main_logic(self, protocol):
        """主执行逻辑 - 由 Behavior 基类的线程架构调用"""
        self.send_log(LogLevel.INFO, "🚀 开始执行窗口切换测试")
        
        # 执行测试
        test_result = self.test_window_switch()  # 装饰器自动合并
        
        if not test_result.success:
            self.send_log(LogLevel.ERROR, "❌ 测试失败")
            return False
        
        # 打印整体汇总的调用链（如果启用了调试模式）
        if self.debug_mode >= 1:
            self.send_log(LogLevel.INFO, "")
            self.send_log(LogLevel.INFO, "📊 ===== 整体性能分析 =====")
            mode = "simple" if self.debug_mode == 1 else "detail"
            lines = self.formatter.format_timing_records(
                protocol,
                title=f"完整测试调用链汇总 (共{self.switch_count}次切换)",
                mode=mode
            )
            for line in lines:
                self.debug_log(LogLevel.INFO, line)
        
        self.send_log(LogLevel.SUCCESS, "✅ 窗口切换测试全部完成")
        return True

def get_behavior_class():
    """返回行为类（GUI加载器会调用此函数）"""
    return WindowSwitchTestBehavior

