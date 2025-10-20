"""
标准行为脚本模板 - DeltaForce MarketBot
作者：AI Assistant
创建时间：2024-10-18

这是一个标准的行为脚本模板，包含了所有必需的组件和最佳实践。
使用此模板创建新的行为脚本可以避免常见错误。

支持单端和双端两种模式，通过注释区分实现方式。
"""

import sys
import os
import time
import random
from datetime import datetime
from PySide6.QtCore import QThread, Signal

# 添加路径以导入 TaskLogger
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from task_logger import get_task_logger
except ImportError:
    # 如果导入失败，创建一个空的 logger
    def get_task_logger():
        class DummyLogger:
            def add_task_record(self, *args, **kwargs):
                pass
        return DummyLogger()

# ================================
# BEHAVIOR_INFO 配置
# ================================
BEHAVIOR_INFO = {
    "title": "模板行为",  # 必需：行为标题
    "description": "这是一个标准的行为脚本模板，展示了正确的实现方式",  # 必需：行为描述
    "code_id": "TPL000X",  # 必需：行为代码ID，格式：XXX000X
    "tags": ["模板", "示例"],  # 必需：标签列表
    "custom_config": {  # 必需：自定义配置参数
        # 示例：整数参数
        "loop_count": {
            "type": "int",
            "default": 10,
            "label": "循环次数",
            "step": 1,
            # 注意：不要设置 min/max 限制（除非特殊需要）
        },
        # 示例：浮点数参数
        "delay_time": {
            "type": "float", 
            "default": 1.0,
            "label": "延迟时间(秒)",
            "step": 0.1,
            # 注意：GUI 会自动设置 setDecimals(3) 提供足够精度
        },
        # 示例：字符串参数
        "work_start_time": {
            "type": "str",
            "default": "00:00",
            "label": "开始时间(HH:MM)",
        },
        "work_end_time": {
            "type": "str", 
            "default": "23:59",
            "label": "结束时间(HH:MM)",
        }
    }
}

class TemplateBehavior(QThread):
    """
    标准行为脚本模板类
    
    继承要求：
    - 必须继承 QThread（不是 QObject）
    - 必须定义所有必需的信号
    """
    
    # ================================
    # 必需信号定义
    # ================================
    log_message = Signal(str)       # 必需：日志消息信号
    status_update = Signal(str)     # 必需：状态更新信号
    status_changed = Signal(str)    # 必需：状态变化信号
    finished_signal = Signal(bool)  # 必需：完成信号
    
    def __init__(self, window_handles, config=None):
        """
        构造函数
        
        参数要求：
        - 必须使用标准签名：(self, window_handles, config=None)
        - 不要使用其他签名如 (self, delta_instance, config) 等
        
        Args:
            window_handles: 窗口句柄列表或单个句柄
            config: 配置字典，包含用户设置的参数
        """
        super().__init__()
        
        # ================================
        # 基础属性初始化
        # ================================
        self.window_handles = window_handles if isinstance(window_handles, list) else []
        self.config = config or {}
        
        # ================================
        # 运行状态管理（必需的完整状态）
        # ================================
        self.running = False      # 运行状态
        self.paused = False       # 暂停状态  
        self.should_stop = False  # 必需！用于 Q 键退出，BehaviorManager 会设置此属性
        
        # ================================
        # DeltaForce 实例
        # ================================
        self.delta = None  # 单端模式：单个 DeltaForce 实例
        # self.delta_list = []  # 双端模式：DeltaForce 实例列表
        
        # ================================
        # 配置参数解析
        # ================================
        self.loop_count = self.config.get('loop_count', 10)
        self.delay_time = self.config.get('delay_time', 1.0)
        self.work_start_time = self.config.get('work_start_time', "00:00")
        self.work_end_time = self.config.get('work_end_time', "23:59")
        
        # ================================
        # 统计数据
        # ================================
        self.start_time = None
        self.end_time = None
        self.total_cycles = 0
        self.success_count = 0
        self.error_count = 0
        
        # ================================
        # 任务记录器
        # ================================
        self.task_logger = get_task_logger()
    
    def initialize_delta(self):
        """
        初始化 DeltaForce 实例
        
        返回:
            bool: 初始化是否成功
        """
        try:
            # ================================
            # 单端模式实现
            # ================================
            if not self.window_handles:
                self.log_message.emit("❌ [TPL000X] 没有可用的窗口句柄")
                return False
            
            # 导入 DeltaForce 类
            from DeltaForce.DeltaForceClass import DeltaForceClass
            
            # 创建单个实例
            window_handle = self.window_handles[0]
            self.delta = DeltaForceClass(window_handle)
            
            if not self.delta:
                self.log_message.emit("❌ [TPL000X] DeltaForce 实例创建失败")
                return False
            
            self.log_message.emit(f"✅ [TPL000X] 成功绑定到窗口 {window_handle}")
            return True
            
            # ================================
            # 双端模式实现（注释掉的示例）
            # ================================
            # if len(self.window_handles) < 2:
            #     self.log_message.emit("❌ [TPL000X] 双端模式需要至少2个窗口句柄")
            #     return False
            # 
            # # 导入 DeltaForce 类
            # from DeltaForce.DeltaForceClass import DeltaForceClass
            # 
            # # 创建多个实例
            # self.delta_list = []
            # for i, window_handle in enumerate(self.window_handles):
            #     delta_instance = DeltaForceClass(window_handle)
            #     if delta_instance:
            #         self.delta_list.append(delta_instance)
            #         self.log_message.emit(f"✅ [TPL000X] 成功绑定到窗口 {window_handle} (实例 {i+1})")
            #     else:
            #         self.log_message.emit(f"❌ [TPL000X] 窗口 {window_handle} 绑定失败")
            # 
            # if not self.delta_list:
            #     self.log_message.emit("❌ [TPL000X] 没有成功绑定的窗口")
            #     return False
            # 
            # self.log_message.emit(f"✅ [TPL000X] 双端模式初始化完成，共 {len(self.delta_list)} 个实例")
            # return True
            
        except Exception as e:
            self.log_message.emit(f"❌ [TPL000X] 初始化失败: {e}")
            return False
    
    def _validate_time_format(self, time_str):
        """
        验证时间格式
        
        Args:
            time_str: 时间字符串，格式 HH:MM
            
        Returns:
            bool: 格式是否正确
        """
        try:
            time.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def is_in_work_time(self):
        """
        检查当前是否在工作时间内
        
        Returns:
            bool: 是否在工作时间
        """
        try:
            # 验证时间格式
            if not self._validate_time_format(self.work_start_time):
                self.log_message.emit(f"❌ [TPL000X] 开始时间格式错误: {self.work_start_time}")
                return False
                
            if not self._validate_time_format(self.work_end_time):
                self.log_message.emit(f"❌ [TPL000X] 结束时间格式错误: {self.work_end_time}")
                return False
            
            # 获取当前时间
            current_time = datetime.now().strftime("%H:%M")
            
            # 比较时间
            return self.work_start_time <= current_time <= self.work_end_time
            
        except Exception as e:
            self.log_message.emit(f"❌ [TPL000X] 时间检查失败: {e}")
            return False
    
    def _execute_single_cycle(self):
        """
        执行单次循环（单端模式）
        
        Returns:
            bool: 执行是否成功
        """
        try:
            # ================================
            # 单端模式：使用 self.delta
            # ================================
            
            # ================================
            # 在这里实现具体的业务逻辑
            # ================================
            
            # 示例：点击操作（已注释，仅供参考）
            # success = self.delta.click_ratio(0.5, 0.5)  # 点击屏幕中心
            # if success:
            #     self.log_message.emit("✅ [TPL000X] 点击操作成功")
            #     self.success_count += 1
            #     return True
            # else:
            #     self.log_message.emit("❌ [TPL000X] 点击操作失败")
            #     self.error_count += 1
            #     return False
            
            # 模板行为：不执行实际操作，仅用于参考
            self.log_message.emit("📋 [TPL000X] 模板行为 - 仅供参考，无实际操作")
            self.success_count += 1
            return True
                
        except Exception as e:
            self.log_message.emit(f"❌ [TPL000X] 循环执行异常: {e}")
            self.error_count += 1
            return False
    
    def _execute_dual_cycle(self):
        """
        执行单次循环（双端模式）
        
        Returns:
            bool: 执行是否成功
        """
        # ================================
        # 双端模式：使用 self.delta_list
        # ================================
        try:
            # ================================
            # 在这里实现双端模式的具体业务逻辑
            # ================================
            
            # 示例：双端点击操作（已注释，仅供参考）
            # success_count = 0
            # for i, delta_instance in enumerate(self.delta_list):
            #     try:
            #         success = delta_instance.click_ratio(0.5, 0.5)
            #         if success:
            #             self.log_message.emit(f"✅ [TPL000X] 窗口 {i+1} 点击成功")
            #             success_count += 1
            #         else:
            #             self.log_message.emit(f"❌ [TPL000X] 窗口 {i+1} 点击失败")
            #     except Exception as e:
            #         self.log_message.emit(f"❌ [TPL000X] 窗口 {i+1} 操作异常: {e}")
            
            # 模板行为：不执行实际操作，仅用于参考
            self.log_message.emit("📋 [TPL000X] 双端模板行为 - 仅供参考，无实际操作")
            self.success_count += 1
            return True
                
        except Exception as e:
            self.log_message.emit(f"❌ [TPL000X] 双端循环执行异常: {e}")
            self.error_count += 1
            return False
    
    def run(self):
        """
        主运行方法
        
        注意事项：
        - 必须在 finally 块中发送所有必需信号
        - 必须检查所有停止条件：running 和 should_stop
        - 必须处理暂停逻辑
        """
        try:
            # ================================
            # 初始化阶段
            # ================================
            self.running = True
            self.start_time = datetime.now()
            self.status_update.emit("运行中")
            self.status_changed.emit("running")
            
            # 初始化 DeltaForce
            if not self.initialize_delta():
                return
            
            # 检查工作时间
            if not self.is_in_work_time():
                self.log_message.emit(f"⏰ [TPL000X] 当前不在工作时间内 ({self.work_start_time}-{self.work_end_time})")
                return
            
            self.log_message.emit("=" * 60)
            self.log_message.emit("🚀 [TPL000X] 模板行为开始运行")
            self.log_message.emit(f"📊 配置参数: 循环次数={self.loop_count}, 延迟={self.delay_time}秒")
            self.log_message.emit(f"⏰ 工作时间: {self.work_start_time}-{self.work_end_time}")
            self.log_message.emit("=" * 60)
            
            # ================================
            # 主循环（必需的完整条件检查）
            # ================================
            while self.running and not self.should_stop and self.total_cycles < self.loop_count:
                try:
                    # 检查暂停状态（必需的完整条件）
                    while self.paused and self.running and not self.should_stop:
                        time.sleep(0.1)
                    
                    # 检查停止条件（必需）
                    if not self.running or self.should_stop:
                        break
                    
                    # 检查工作时间
                    if not self.is_in_work_time():
                        self.log_message.emit("⏰ [TPL000X] 超出工作时间，停止运行")
                        break
                    
                    # ================================
                    # 执行业务逻辑
                    # ================================
                    self.log_message.emit(f"🔄 [TPL000X] 执行第 {self.total_cycles + 1} 次循环")
                    
                    # 选择执行模式
                    success = self._execute_single_cycle()  # 单端模式
                    # success = self._execute_dual_cycle()  # 双端模式
                    
                    self.total_cycles += 1
                    
                    # 延迟
                    if self.delay_time > 0:
                        time.sleep(self.delay_time)
                    
                    # 检查停止条件（循环内再次检查）
                    if not self.running or self.should_stop:
                        break
                        
                except Exception as e:
                    self.log_message.emit(f"❌ [TPL000X] 循环异常: {e}")
                    self.error_count += 1
                    time.sleep(1)  # 异常后短暂延迟
            
            # ================================
            # 完成阶段
            # ================================
            self.log_message.emit("🏁 [TPL000X] 主循环结束")
            
        except Exception as e:
            self.log_message.emit(f"❌ [TPL000X] 运行异常: {e}")
            
        finally:
            # ================================
            # 清理阶段（必需的完整清理）
            # ================================
            self.running = False
            self.end_time = datetime.now()
            
            # 发送必需信号
            self.status_update.emit("已停止")
            self.status_changed.emit("stopped")
            
            # 打印运行摘要
            self.print_run_summary()
            
            # 保存任务记录
            self._save_task_record()
            
            # 发送完成信号
            self.finished_signal.emit(True)
            
            # 最终日志
            self.log_message.emit("🏁 [TPL000X] 模板行为已停止")
    
    def print_run_summary(self):
        """
        打印运行摘要
        """
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            duration_seconds = duration.total_seconds()
            
            self.log_message.emit("=" * 60)
            self.log_message.emit("📊 [TPL000X] 运行摘要")
            self.log_message.emit("=" * 60)
            self.log_message.emit(f"⏱️ 运行时长: {duration_seconds:.1f} 秒")
            self.log_message.emit(f"🔄 总循环次数: {self.total_cycles}")
            self.log_message.emit(f"✅ 成功次数: {self.success_count}")
            self.log_message.emit(f"❌ 失败次数: {self.error_count}")
            
            if self.total_cycles > 0:
                success_rate = (self.success_count / self.total_cycles) * 100
                self.log_message.emit(f"📈 成功率: {success_rate:.1f}%")
            
            if duration_seconds > 0:
                cycles_per_minute = (self.total_cycles / duration_seconds) * 60
                self.log_message.emit(f"⚡ 每分钟循环: {cycles_per_minute:.1f}次")
            
            self.log_message.emit("=" * 60)
    
    def _save_task_record(self):
        """
        保存任务记录到 TaskLogger
        """
        try:
            if self.start_time and self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
                
                # 创建任务记录
                task_record = {
                    "behavior_id": "TPL000X",
                    "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": duration,
                    "total_cycles": self.total_cycles,
                    "success_count": self.success_count,
                    "error_count": self.error_count,
                    "success_rate": (self.success_count / max(self.total_cycles, 1)) * 100,
                    "config": self.config
                }
                
                # 保存记录
                self.task_logger.add_task_record(task_record)
                self.log_message.emit("💾 [TPL000X] 任务记录已保存")
                
        except Exception as e:
            self.log_message.emit(f"❌ [TPL000X] 保存任务记录失败: {e}")
    
    def stop(self):
        """
        停止行为脚本
        
        注意：必须设置所有停止标志
        """
        self.log_message.emit("🛑 [TPL000X] 正在停止...")
        self.running = False
        self.should_stop = True  # 必需！用于 Q 键退出
    
    def pause(self):
        """
        暂停行为脚本
        """
        self.paused = True
        self.log_message.emit("⏸️ [TPL000X] 已暂停")
    
    def resume(self):
        """
        恢复行为脚本
        """
        self.paused = False
        self.log_message.emit("▶️ [TPL000X] 已恢复")

# ================================
# 模块导出
# ================================
# 确保 BehaviorManager 能够找到并实例化这个类
__all__ = ['TemplateBehavior', 'BEHAVIOR_INFO']
