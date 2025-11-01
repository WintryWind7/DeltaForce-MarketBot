# -*- coding: utf-8 -*-
"""
统一Behavior基类 - 分层线程管理架构

线程层级 (优先级从高到低):
1. 监听线程 (Q键监听) - 最高优先级，立即响应
2. 日志线程 (消息处理) - 第二优先级，处理所有日志和状态
3. 主逻辑线程 (业务执行) - 第三优先级，执行具体业务

消息传递机制:
- 主逻辑 → 日志线程 (通过log_queue)
- 监听线程 → 所有线程 (通过master_stop_event)
- 线程间命令 (通过command_queue)

作者: DeltaForce Team
"""

import threading
import time
import keyboard
import queue
from PySide6.QtCore import QThread, Signal
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable
from functools import wraps

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

class ThreadCommand(Enum):
    """线程命令"""
    STOP = "STOP"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    STATUS = "STATUS"

class LogManager:
    """
    日志管理器 - 统一处理日志显示、统计记录和任务历史
    
    职责:
    1. 接收并格式化日志消息
    2. 发送日志到UI显示
    3. 实时统计数据收集
    4. 任务历史记录管理
    5. 线程安全的数据处理
    
    设计原则:
    - 单一职责: 所有日志相关功能集中管理
    - 线程安全: 在日志线程中运行，避免竞态条件
    - 数据一致性: 统计和记录同步进行
    """
    
    def __init__(self, behavior_instance):
        """
        初始化日志管理器
        
        Args:
            behavior_instance: Behavior实例的引用，用于访问信号和属性
        """
        self.behavior = behavior_instance
        self.behavior_name = getattr(behavior_instance, 'behavior_name', 'Unknown')
        
        # 任务信息
        self.task_id = None
        self.start_time = None
        self.end_time = None
        
        # 统计计数器
        self.message_count = 0
        self.debug_count = 0
        self.info_count = 0
        self.warning_count = 0
        self.error_count = 0
        self.success_count = 0
        
        # 业务统计 (由具体behavior更新)
        self.business_stats = {}
        
        # 详细日志记录 (用于UI显示)
        self.detailed_logs = []
        
        # TaskLogger实例 (延迟初始化)
        self._task_logger = None
        
    def _get_task_logger(self):
        """延迟初始化TaskLogger"""
        if self._task_logger is None:
            try:
                from gui.task_logger import get_task_logger
                self._task_logger = get_task_logger()
            except ImportError:
                print("⚠️ 无法导入TaskLogger，任务历史功能将不可用")
                self._task_logger = None
        return self._task_logger
    
    def start_task(self, script_id: str):
        """开始任务记录"""
        try:
            self.start_time = datetime.now()
            
            # 生成task_id
            timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
            self.task_id = f"{script_id}_{timestamp}"
            
            # TaskLogger会在end_task时统一记录，这里只记录开始
            self._emit_log(f"📝 任务开始: {self.task_id}")
            return self.task_id
            
        except Exception as e:
            self._emit_log(f"❌ 任务开始记录失败: {e}")
            return None
    
    def end_task(self, status: str = "completed"):
        """结束任务记录"""
        try:
            self.end_time = datetime.now()
            
            if self.start_time and self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
            else:
                duration = 0
            
            # 准备统计数据
            statistics = {
                # 日志统计
                'message_count': self.message_count,
                'debug_count': self.debug_count,
                'info_count': self.info_count,
                'warning_count': self.warning_count,
                'error_count': self.error_count,
                'success_count': self.success_count,
                
                # 基础统计 (从behavior实例获取)
                'cycle_count': getattr(self.behavior, 'cycle_count', 0),
                'success_count_behavior': getattr(self.behavior, 'success_count', 0),
                'error_count_behavior': getattr(self.behavior, 'error_count', 0),
            }
            
            # 合并业务统计
            statistics.update(self.business_stats)
            
            # 记录到TaskLogger
            task_logger = self._get_task_logger()
            if task_logger and self.task_id:
                # 准备TaskLogger需要的数据格式
                task_data = {
                    'task_id': self.task_id,
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'end_time': self.end_time.isoformat() if self.end_time else None,
                    'duration': duration,
                    'status': status,
                    'statistics': statistics,
                    'summary': self._generate_summary(statistics),
                    'detailed_logs': self.detailed_logs  # 包含详细日志
                }
                
                # 从task_id中提取script_id
                script_id = self.task_id.split('_')[0] if '_' in self.task_id else 'Unknown'
                task_logger.add_task_record(script_id, task_data)
            
            # 生成最终报告
            self._generate_final_report(duration, statistics)
            
        except Exception as e:
            self._emit_log(f"❌ 任务结束记录失败: {e}")
    
    def process_message(self, level: LogLevel, message: str, **kwargs):
        """
        处理日志消息 - 核心方法
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的统计数据
        """
        try:
            # 更新计数器
            self.message_count += 1
            
            if level == LogLevel.DEBUG:
                self.debug_count += 1
            elif level == LogLevel.INFO:
                self.info_count += 1
            elif level == LogLevel.WARNING:
                self.warning_count += 1
            elif level == LogLevel.ERROR:
                self.error_count += 1
            elif level == LogLevel.SUCCESS:
                self.success_count += 1
            
            # 更新业务统计 (如果提供)
            if kwargs:
                self.business_stats.update(kwargs)
            
            # 记录详细日志 (用于UI显示)
            log_entry = {
                'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                'level': level.value,
                'message': message,
                'kwargs': kwargs
            }
            self.detailed_logs.append(log_entry)
            
            # 格式化并发送消息
            formatted_msg = self._format_message(level, message)
            self._emit_log(formatted_msg)
            
        except Exception as e:
            # 避免日志系统本身出错导致死循环
            print(f"LogManager处理消息异常: {e}")
    
    def _format_message(self, level: LogLevel, message: str) -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 级别图标
        level_icons = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️",
            LogLevel.WARNING: "⚠️", 
            LogLevel.ERROR: "❌",
            LogLevel.SUCCESS: "✅"
        }
        
        icon = level_icons.get(level, "📝")
        return f"[{timestamp}] {icon} {message}"
    
    def _emit_log(self, message: str):
        """发送日志到UI"""
        try:
            if hasattr(self.behavior, 'log_message'):
                self.behavior.log_message.emit(message)
        except Exception:
            # 如果UI信号发送失败，至少打印到控制台
            print(message)
    
    def _generate_final_report(self, duration: float, statistics: dict):
        """生成最终执行报告"""
        try:
            self._emit_log("📊 ===== 执行报告 =====")
            self._emit_log(f"⏱️ 执行时长: {duration:.1f}秒")
            self._emit_log(f"📝 日志统计: 总计{self.message_count}条 (成功{self.success_count}, 警告{self.warning_count}, 错误{self.error_count})")
            
            # 业务统计报告 (如果有)
            if self.business_stats:
                self._emit_log("📈 业务统计:")
                for key, value in self.business_stats.items():
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            self._emit_log(f"   {key}: {value:,.1f}")
                        else:
                            self._emit_log(f"   {key}: {value:,}")
                    else:
                        self._emit_log(f"   {key}: {value}")
            
            self._emit_log("📊 ==================")
            
        except Exception as e:
            self._emit_log(f"❌ 生成报告异常: {e}")
    
    def update_business_stat(self, key: str, value: Any):
        """更新业务统计数据"""
        self.business_stats[key] = value
    
    def increment_business_stat(self, key: str, increment: int = 1):
        """递增业务统计计数"""
        if key in self.business_stats:
            self.business_stats[key] += increment
        else:
            self.business_stats[key] = increment
    
    def _generate_summary(self, statistics: dict) -> str:
        """生成任务摘要"""
        try:
            summary_parts = []
            
            # 基本信息
            duration = statistics.get('duration', 0)
            if duration > 3600:
                duration_str = f"{duration/3600:.1f}小时"
            elif duration > 60:
                duration_str = f"{duration/60:.1f}分钟"
            else:
                duration_str = f"{duration:.1f}秒"
            
            summary_parts.append(f"运行时长: {duration_str}")
            
            # 日志统计
            message_count = statistics.get('message_count', 0)
            if message_count > 0:
                summary_parts.append(f"日志: {message_count}条")
            
            # 业务统计
            refresh_count = statistics.get('refresh_count', 0)
            if refresh_count > 0:
                summary_parts.append(f"刷新次数: {refresh_count}")
            
            purchase_count = statistics.get('purchase_count', 0)
            if purchase_count > 0:
                summary_parts.append(f"购买次数: {purchase_count}")
            
            # 余额变化
            initial_balance = statistics.get('initial_balance')
            current_balance = statistics.get('current_balance')
            if initial_balance and current_balance:
                balance_change = current_balance - initial_balance
                summary_parts.append(f"余额变化: {balance_change:+,}")
            
            return " | ".join(summary_parts) if summary_parts else "无统计数据"
            
        except Exception as e:
            return f"摘要生成失败: {e}"

# ================================
# DeltaManager集成
# ================================
# 移除了所有require_*_delta装饰器
# 现在Behavior直接从DeltaManager获取Delta实例

class Behavior(QThread):
    """
    统一Behavior基类 - 分层线程管理架构
    
    线程层级 (优先级从高到低):
    1. 监听线程 (Q键监听) - 最高优先级，立即响应
    2. 日志线程 (消息处理) - 第二优先级，处理所有日志和状态
    3. 主逻辑线程 (业务执行) - 第三优先级，执行具体业务
    
    消息传递机制:
    - 主逻辑 → 日志线程 (通过log_queue)
    - 监听线程 → 所有线程 (通过master_stop_event)
    - 线程间命令 (通过command_queue)
    """
    
    # ================================
    # Qt信号定义 (与UI通信)
    # ================================
    log_message = Signal(str)           # 日志消息
    status_changed = Signal(str)        # 状态变化
    finished_signal = Signal(bool)      # 完成信号
    progress_update = Signal(int)       # 进度更新
    
    def __init__(self, window_handles, config=None):
        """
        统一初始化
        
        Args:
            window_handles: 窗口句柄列表
            config: 配置参数字典
        """
        super().__init__()
        
        # ================================
        # 基础属性
        # ================================
        self.window_handles = window_handles if isinstance(window_handles, list) else [window_handles]
        self.config = config or {}
        self.behavior_name = self.__class__.__name__
        
        # ================================
        # 线程管理核心
        # ================================
        self.master_stop_event = threading.Event()     # 主停止事件
        self.threads_lock = threading.Lock()           # 线程锁
        self.child_threads = []                        # 子线程列表
        
        # ================================
        # 线程间通信队列
        # ================================
        self.log_queue = queue.Queue(maxsize=1000)     # 日志消息队列
        self.command_queue = queue.Queue(maxsize=100)  # 命令队列
        self.status_queue = queue.Queue(maxsize=50)    # 状态队列
        
        # ================================
        # 运行状态管理
        # ================================
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.end_time = None
        
        # ================================
        # 统计数据
        # ================================
        self.cycle_count = 0
        self.success_count = 0
        self.error_count = 0
        self.warning_count = 0
        
        # ================================
        # 日志管理器 (在日志线程中初始化)
        # ================================
        self.log_manager = None  # 将在日志线程中创建
        
        # ================================
        # 监听线程配置
        # ================================
        self.monitor_startup_delay = 3.0  # 监听启动延迟
        self.monitor_check_interval = 0.05  # 监听检查间隔(50ms)
        
        # ================================
        # 自动关机配置
        # ================================
        self.auto_shutdown = self.config.get('auto_shutdown', False)
        self.work_start_time = self.config.get('work_start_time', '00:00')
        self.work_end_time = self.config.get('work_end_time', '23:59')
        
        # ================================
        # DeltaManager集成
        # ================================
        from DeltaForce.DeltaManager import get_delta_manager
        self.delta_manager = get_delta_manager()  # 全局DeltaManager实例
        
        # ================================
        # 调用子类初始化
        # ================================
        self.init_config()
        self.init_behavior()
        
        # ================================
        # 绑定窗口句柄到DeltaManager
        # ================================
        if self.window_handles:
            success = self.delta_manager.bind_handles(self.window_handles)
            if success:
                self.system_log(LogLevel.SUCCESS, f"✅ 成功绑定{len(self.window_handles)}个窗口到DeltaManager")
            else:
                self.system_log(LogLevel.ERROR, "❌ DeltaManager窗口绑定失败")
        else:
            self.system_log(LogLevel.WARNING, "⚠️ 未提供窗口句柄，跳过DeltaManager绑定")
    
    @classmethod
    def args(cls):
        """
        参数定义函数 - 子类重写 (类方法)
        返回参数定义字典，用于UI生成和参数解析
        
        Returns:
            dict: 参数定义字典
            {
                'param_name': {
                    'type': 'int|float|str|bool',
                    'label': 'UI显示名称',
                    'default': 默认值,
                    'description': '参数说明',
                    'min': 最小值(可选),
                    'max': 最大值(可选)
                }
            }
        """
        return {}
    
    @classmethod
    def get_ui_config(cls):
        """
        获取UI配置信息 - 供UI系统调用
        
        Returns:
            dict: 兼容现有UI系统的配置格式
        """
        # 直接调用类方法获取args配置
        args_config = cls.args()
        
        # 转换为UI系统期望的格式
        ui_config = {}
        for param_name, param_config in args_config.items():
            ui_config[param_name] = {
                'type': param_config.get('type', 'str'),
                'label': param_config.get('label', param_name),
                'default': param_config.get('default'),
                'description': param_config.get('description', ''),
                'min': param_config.get('min'),
                'max': param_config.get('max')
            }
        
        return ui_config
    
    def init_config(self):
        """
        配置参数初始化 - 自动执行args()并解析参数
        子类通常不需要重写此方法，而是重写args()
        """
        # 获取参数定义 (调用类方法)
        args_config = self.__class__.args()
        
        # 自动解析参数并设置为实例属性
        for param_name, param_config in args_config.items():
            default_value = param_config.get('default')
            config_value = self.config.get(param_name, default_value)
            
            # 类型转换和验证
            param_type = param_config.get('type', 'str')
            try:
                if param_type == 'int':
                    config_value = int(config_value) if config_value is not None else default_value
                elif param_type == 'float':
                    config_value = float(config_value) if config_value is not None else default_value
                elif param_type == 'bool':
                    config_value = bool(config_value) if config_value is not None else default_value
                elif param_type == 'str':
                    config_value = str(config_value) if config_value is not None else default_value
                
                # 范围验证
                if param_type in ['int', 'float']:
                    min_val = param_config.get('min')
                    max_val = param_config.get('max')
                    if min_val is not None and config_value < min_val:
                        self.send_log(LogLevel.WARNING, f"⚠️ 参数{param_name}值{config_value}小于最小值{min_val}，使用最小值")
                        config_value = min_val
                    if max_val is not None and config_value > max_val:
                        self.send_log(LogLevel.WARNING, f"⚠️ 参数{param_name}值{config_value}大于最大值{max_val}，使用最大值")
                        config_value = max_val
                
                # 设置为实例属性
                setattr(self, param_name, config_value)
                
            except (ValueError, TypeError) as e:
                self.send_log(LogLevel.WARNING, f"⚠️ 参数{param_name}类型转换失败: {e}，使用默认值{default_value}")
                setattr(self, param_name, default_value)
    
    def init_behavior(self):
        """
        行为特定初始化 - 子类重写
        在这里进行behavior特定的初始化逻辑
        """
        pass
    
    def main_logic(self):
        """
        主业务逻辑 - 子类必须实现
        这个方法在第三优先级线程中执行
        
        Returns:
            bool: 执行是否成功
        """
        raise NotImplementedError("子类必须实现main_logic方法")
    
    
    def run(self):
        """
        主线程入口 - 启动分层线程架构
        """
        try:
            self.is_running = True
            self.start_time = datetime.now()
            
            # 清空所有事件和队列
            self.master_stop_event.clear()
            self._clear_all_queues()
            
            # 按优先级启动线程
            self._start_monitor_thread()    # 第一优先级: 监听线程
            self._start_log_thread()        # 第二优先级: 日志线程 (内部会延迟启动主逻辑线程)
            
            # 发送启动状态
            self._send_status("running")
            self._send_log(LogLevel.SUCCESS, f"🚀 [{self.behavior_name}] 分层线程架构启动完成")
            
            # 主线程等待完成
            self._wait_for_completion()
            
        except Exception as e:
            self._send_log(LogLevel.ERROR, f"❌ [{self.behavior_name}] 主线程异常: {e}")
        finally:
            self._cleanup_all_threads()
    
    # ================================
    # 第一优先级: 监听线程
    # ================================
    def _start_monitor_thread(self):
        """启动监听线程 - 最高优先级"""
        def monitor_worker():
            thread_name = "MonitorThread"
            try:
                self.system_log(LogLevel.INFO, f"🛑 [{thread_name}] 启动 (第一优先级)")
                
                self.system_log(LogLevel.SUCCESS, f"👁️ [{thread_name}] Q键监听激活 - 按Q键立即退出")
                
                # 注册Q键监听
                def on_q_pressed(event):
                    if not self.master_stop_event.is_set():
                        self.system_log(LogLevel.WARNING, f"🛑 [{thread_name}] 检测到Q键 - 立即停止所有线程")
                        self._emergency_stop()
                
                keyboard.on_press_key('q', on_q_pressed)
                
                # 高频监听循环
                while not self.master_stop_event.is_set():
                    try:
                        # 处理命令队列
                        self._process_commands()
                        
                        # 高频检查，确保响应速度
                        time.sleep(self.monitor_check_interval)
                        
                    except Exception as e:
                        self.system_log(LogLevel.ERROR, f"❌ [{thread_name}] 监听异常: {e}")
                        break
                
                # 清理键盘监听
                keyboard.unhook_all()
                self.system_log(LogLevel.INFO, f"🛑 [{thread_name}] 已停止")
                
            except Exception as e:
                self.system_log(LogLevel.ERROR, f"❌ [{thread_name}] 线程异常: {e}")
            finally:
                try:
                    keyboard.unhook_all()
                except:
                    pass
        
        thread = threading.Thread(target=monitor_worker, name="MonitorThread", daemon=True)
        thread.start()
        self._register_thread(thread)
    
    # ================================
    # 第二优先级: 日志线程
    # ================================
    def _start_log_thread(self):
        """启动日志处理线程 - 第二优先级，负责延迟启动主逻辑线程"""
        def log_worker():
            thread_name = "LogThread"
            try:
                # 在日志线程中初始化LogManager
                self.log_manager = LogManager(self)
                
                self.system_log(LogLevel.INFO, f"📝 [{thread_name}] 启动 (第二优先级)")
                self.system_log(LogLevel.INFO, f"🎯 LogManager已初始化")
                
                # 开始任务记录
                script_id = getattr(self, 'behavior_name', 'Unknown')
                task_id = self.log_manager.start_task(script_id)
                
                # 延迟启动主逻辑线程 - 3秒倒计时
                self.system_log(LogLevel.INFO, "⏰ 准备启动主逻辑线程...")
                for i in range(3, 0, -1):
                    if self.master_stop_event.is_set():
                        self.system_log(LogLevel.WARNING, f"🛑 [{thread_name}] 倒计时期间收到停止信号")
                        return
                    
                    self.system_log(LogLevel.INFO, f"⏳ {i}秒后开始行为...")
                    time.sleep(1)
                
                if not self.master_stop_event.is_set():
                    self.system_log(LogLevel.SUCCESS, f"🎮 启动主逻辑线程...")
                    self._start_logic_thread()  # 在日志线程内启动主逻辑线程
                
                # 继续处理日志消息
                while not self.master_stop_event.is_set():
                    try:
                        # 处理日志队列 - 使用LogManager
                        self._process_log_queue_with_manager()
                        
                        # 处理状态队列
                        self._process_status_queue()
                        
                        # 适中的检查间隔
                        time.sleep(0.1)
                        
                    except Exception as e:
                        if self.log_manager:
                            self.log_manager.process_message(LogLevel.ERROR, f"❌ [{thread_name}] 处理异常: {e}")
                        else:
                            self._direct_log(f"❌ [{thread_name}] 处理异常: {e}")
                
                # 结束任务记录
                if self.log_manager:
                    status = "interrupted" if self.master_stop_event.is_set() else "completed"
                    self.log_manager.end_task(status)
                
                # 处理剩余消息
                self._flush_all_queues()
                self.system_log(LogLevel.INFO, f"📝 [{thread_name}] 已停止")
                
            except Exception as e:
                self.system_log(LogLevel.ERROR, f"❌ [{thread_name}] 线程异常: {e}")
        
        thread = threading.Thread(target=log_worker, name="LogThread", daemon=True)
        thread.start()
        self._register_thread(thread)
    
    # ================================
    # 第三优先级: 主逻辑线程
    # ================================
    def _start_logic_thread(self):
        """启动主逻辑线程 - 第三优先级"""
        def logic_worker():
            thread_name = "LogicThread"
            success = False
            
            try:
                self.system_log(LogLevel.INFO, f"🎮 [{thread_name}] 启动 (第三优先级)")
                
                # 执行子类的主业务逻辑
                success = self.main_logic()
                
                if not self.master_stop_event.is_set():
                    if success:
                        self._send_log(LogLevel.SUCCESS, f"✅ [{self.behavior_name}] 主逻辑执行完成")
                    else:
                        self._send_log(LogLevel.WARNING, f"⚠️ [{self.behavior_name}] 主逻辑执行中断")
                
            except Exception as e:
                self.system_log(LogLevel.ERROR, f"❌ [{thread_name}] 主逻辑异常: {e}")
                success = False
            finally:
                # 发送完成信号
                if not self.master_stop_event.is_set():
                    self.finished_signal.emit(success)
                
                # 设置停止事件，通知其他线程
                self.master_stop_event.set()
        
        thread = threading.Thread(target=logic_worker, name="LogicThread", daemon=True)
        thread.start()
        self._register_thread(thread)
    
    # ================================
    # 消息传递接口 (供子类使用)
    # ================================
    def send_log(self, level: LogLevel, message: str, **kwargs):
        """
        发送日志消息 - 线程安全
        
        Args:
            level: 日志级别
            message: 日志内容
            **kwargs: 额外的统计数据 (如 refresh_count=5, balance=1000000)
        """
        # 如果开启debug模式，只输出debug_log的消息，过滤普通日志
        if getattr(self, 'debug_mode', False):
            return  # debug模式下不输出普通日志
        
        self._send_log(level, message, **kwargs)
    
    def debug_log(self, level: LogLevel, message: str, **kwargs):
        """
        发送调试日志消息 - 仅在debug模式下显示
        
        Args:
            level: 日志级别
            message: 日志内容
            **kwargs: 额外的统计数据
        """
        # 只在debug模式下输出
        if getattr(self, 'debug_mode', False):
            # 添加DEBUG标识
            debug_message = f"[DEBUG] {message}"
            self._send_log(level, debug_message, **kwargs)
    
    def system_log(self, level: LogLevel, message: str, **kwargs):
        """
        发送系统日志消息 - 在两种模式下都会输出
        用于系统级别的信息，如监测Q键、启动前等待等
        
        Args:
            level: 日志级别
            message: 日志内容
            **kwargs: 额外的统计数据
        """
        # 添加SYSTEM标识
        system_message = f"[SYSTEM] {message}"
        self._send_log(level, system_message, **kwargs)
    
    def send_status(self, status: str):
        """
        发送状态更新 - 线程安全
        
        Args:
            status: 状态字符串
        """
        self._send_status(status)
    
    def update_business_stat(self, key: str, value):
        """
        更新业务统计数据 - 通过日志系统传递
        
        Args:
            key: 统计项名称
            value: 统计值
        """
        # 通过日志系统传递统计数据到LogManager
        self.send_log(LogLevel.DEBUG, f"统计更新: {key} = {value}", **{key: value})
    
    def log_with_stats(self, level: LogLevel, message: str, **stats):
        """
        发送日志并同时更新统计数据
        
        Args:
            level: 日志级别
            message: 日志消息
            **stats: 统计数据
        """
        self.send_log(level, message, **stats)
    
    def send_progress(self, progress: int):
        """
        发送进度更新 - 线程安全
        
        Args:
            progress: 进度百分比 (0-100)
        """
        try:
            self.progress_update.emit(progress)
        except Exception:
            pass
    
    def is_stopped(self) -> bool:
        """检查是否已停止"""
        return self.master_stop_event.is_set()
    
    def segmented_sleep(self, duration: float):
        """
        分段等待，支持中途停止
        
        Args:
            duration: 等待时间(秒)
        """
        if duration <= 0:
            return
        
        segments = max(1, int(duration * 20))  # 分成更多段，提高响应速度
        segment_time = duration / segments
        
        for _ in range(segments):
            if self.is_stopped():
                break
            time.sleep(segment_time)
    
    def increment_cycle(self):
        """增加循环计数"""
        self.cycle_count += 1
    
    def increment_success(self):
        """增加成功计数"""
        self.success_count += 1
    
    def increment_error(self):
        """增加错误计数"""
        self.error_count += 1
    
    def increment_warning(self):
        """增加警告计数"""
        self.warning_count += 1
    
    def get_delta_info(self) -> str:
        """
        获取Delta实例信息 - 用于调试
        
        Returns:
            str: Delta实例状态信息
        """
        status = self.delta_manager.get_status_summary()
        mode = status.get('mode', 'none')
        bound_count = status.get('bound_count', 0)
        
        if mode == 'dual':
            main_info = status.get('main_window', {})
            aux_info = status.get('aux_window', {})
            return f"双端模式 - 主端: {main_info.get('hwnd', 'None')}, 辅端: {aux_info.get('hwnd', 'None')}"
        elif mode == 'single':
            main_info = status.get('main_window', {})
            return f"单端模式 - 主端: {main_info.get('hwnd', 'None')}"
        else:
            return f"未绑定模式 - 已绑定窗口: {bound_count}"
    
    def is_delta_ready(self) -> bool:
        """
        检查Delta实例是否就绪
        
        Returns:
            bool: Delta实例是否可用
        """
        return self.delta_manager.get_bound_count() > 0
    
    # ================================
    # DeltaManager集成方法
    # ================================
    def get_main_delta(self):
        """
        获取主端Delta实例（单端使用）
        
        Returns:
            DeltaForceClass or None: 主端Delta实例
        """
        return self.delta_manager.get_main()
    
    def get_aux_delta(self):
        """
        获取辅端Delta实例
        
        Returns:
            DeltaForceClass or None: 辅端Delta实例
        """
        return self.delta_manager.get_aux()
    
    def get_both_deltas(self):
        """
        同时获取主辅端Delta实例（双端使用）
        
        Returns:
            Tuple[DeltaForceClass, DeltaForceClass]: (主端实例, 辅端实例)
        """
        return self.delta_manager.get_both()
    
    def get_any_delta(self):
        """
        获取任意可用的Delta实例
        优先级: 主端 > 辅端
        
        Returns:
            DeltaForceClass or None: 可用的Delta实例
        """
        main = self.delta_manager.get_main()
        if main:
            return main
        return self.delta_manager.get_aux()
    
    def is_single_mode(self):
        """检查是否为单端模式"""
        return self.delta_manager.is_single_mode()
    
    def is_dual_mode(self):
        """检查是否为双端模式"""
        return self.delta_manager.is_dual_mode()
    
    def get_delta_status(self):
        """获取Delta状态摘要"""
        return self.delta_manager.get_status_summary()
    
    # ================================
    # 内部消息传递实现
    # ================================
    def _send_log(self, level: LogLevel, message: str, **kwargs):
        """内部日志发送"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 精确到毫秒
            log_entry = {
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'thread': threading.current_thread().name,
                'kwargs': kwargs  # 额外的统计数据
            }
            self.log_queue.put(log_entry, timeout=0.5)
        except queue.Full:
            # 队列满时直接发送
            self._direct_log(f"[LOG_QUEUE_FULL] {message}")
        except Exception as e:
            # 异常时直接发送
            self._direct_log(f"[LOG_ERROR] {message} (Error: {e})")
    
    def _send_status(self, status: str):
        """内部状态发送"""
        try:
            self.status_queue.put(status, timeout=0.5)
        except queue.Full:
            # 队列满时直接发送
            self.status_changed.emit(status)
        except Exception:
            pass
    
    def _direct_log(self, message: str):
        """直接发送日志 (绕过队列)"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            formatted_msg = f"[{timestamp}] {message}"
            self.log_message.emit(formatted_msg)
        except Exception:
            pass
    
    # ================================
    # 队列处理
    # ================================
    def _process_log_queue(self):
        """处理日志队列"""
        try:
            while not self.log_queue.empty():
                log_entry = self.log_queue.get_nowait()
                
                # 格式化日志消息
                level_icon = {
                    LogLevel.DEBUG: "🔍",
                    LogLevel.INFO: "ℹ️",
                    LogLevel.WARNING: "⚠️",
                    LogLevel.ERROR: "❌",
                    LogLevel.SUCCESS: "✅"
                }.get(log_entry['level'], "📝")
                
                formatted_msg = f"[{log_entry['timestamp']}] {level_icon} {log_entry['message']}"
                
                # 发送到UI
                self.log_message.emit(formatted_msg)
                
                # 标记任务完成
                self.log_queue.task_done()
                
        except queue.Empty:
            pass
        except Exception as e:
            self._direct_log(f"日志队列处理异常: {e}")
    
    def _process_log_queue_with_manager(self):
        """使用LogManager处理日志队列"""
        try:
            while not self.log_queue.empty():
                log_entry = self.log_queue.get_nowait()
                
                # 使用LogManager处理消息
                if self.log_manager:
                    # 提取额外的统计数据
                    kwargs = log_entry.get('kwargs', {})
                    self.log_manager.process_message(
                        log_entry['level'], 
                        log_entry['message'],
                        **kwargs
                    )
                else:
                    # 降级到原始处理方式
                    level_icon = {
                        LogLevel.DEBUG: "🔍",
                        LogLevel.INFO: "ℹ️",
                        LogLevel.WARNING: "⚠️",
                        LogLevel.ERROR: "❌",
                        LogLevel.SUCCESS: "✅"
                    }.get(log_entry['level'], "📝")
                    
                    formatted_msg = f"[{log_entry['timestamp']}] {level_icon} {log_entry['message']}"
                    self.log_message.emit(formatted_msg)
                
                # 标记任务完成
                self.log_queue.task_done()
                
        except queue.Empty:
            pass
        except Exception as e:
            self._direct_log(f"LogManager队列处理异常: {e}")
    
    def _process_status_queue(self):
        """处理状态队列"""
        try:
            while not self.status_queue.empty():
                status = self.status_queue.get_nowait()
                self.status_changed.emit(status)
                self.status_queue.task_done()
        except queue.Empty:
            pass
        except Exception:
            pass
    
    def _process_commands(self):
        """处理命令队列"""
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                self._handle_command(command)
                self.command_queue.task_done()
        except queue.Empty:
            pass
        except Exception:
            pass
    
    def _handle_command(self, command):
        """处理线程命令"""
        if command == ThreadCommand.STOP:
            self.master_stop_event.set()
        elif command == ThreadCommand.PAUSE:
            self.is_paused = True
        elif command == ThreadCommand.RESUME:
            self.is_paused = False
    
    # ================================
    # 线程管理
    # ================================
    def _register_thread(self, thread):
        """注册子线程"""
        with self.threads_lock:
            self.child_threads.append(thread)
    
    def _emergency_stop(self):
        """紧急停止 - Q键触发"""
        self.master_stop_event.set()
        
        # 发送停止命令
        try:
            self.command_queue.put(ThreadCommand.STOP, timeout=0.1)
        except:
            pass
    
    def _wait_for_completion(self):
        """主线程等待完成"""
        try:
            # 等待停止事件
            self.master_stop_event.wait()
            
            # 发送统计信息
            self.end_time = datetime.now()
            if self.start_time:
                duration = self.end_time - self.start_time
                stats_msg = (f"📊 执行统计: 耗时{duration.total_seconds():.1f}秒, "
                           f"循环{self.cycle_count}次, 成功{self.success_count}次, "
                           f"错误{self.error_count}次, 警告{self.warning_count}次")
                self._send_log(LogLevel.INFO, stats_msg)
            
        except Exception as e:
            self._send_log(LogLevel.ERROR, f"❌ 主线程等待异常: {e}")
    
    def _cleanup_all_threads(self):
        """清理所有线程"""
        try:
            self.is_running = False
            
            # 设置停止事件
            self.master_stop_event.set()
            
            # 等待所有子线程结束
            with self.threads_lock:
                for thread in self.child_threads:
                    if thread.is_alive():
                        thread.join(timeout=2.0)  # 最多等待2秒
                        if thread.is_alive():
                            self._direct_log(f"⚠️ 线程 {thread.name} 未能正常结束")
            
            # 清理键盘监听
            try:
                keyboard.unhook_all()
            except:
                pass
            
            # 清理Delta实例
            self._cleanup_delta_instances()
            
            # 最终状态更新
            self._send_status("stopped")
            self._direct_log(f"🧹 [{self.behavior_name}] 所有线程已清理完成")
            
        except Exception as e:
            self._direct_log(f"❌ 线程清理异常: {e}")
    
    def _clear_all_queues(self):
        """清空所有队列"""
        queues = [self.log_queue, self.command_queue, self.status_queue]
        for q in queues:
            try:
                while not q.empty():
                    q.get_nowait()
                    q.task_done()
            except:
                pass
    
    def _flush_all_queues(self):
        """刷新所有队列 (处理剩余消息)"""
        # 处理剩余日志
        try:
            while not self.log_queue.empty():
                log_entry = self.log_queue.get_nowait()
                formatted_msg = f"[{log_entry['timestamp']}] {log_entry['message']}"
                self.log_message.emit(formatted_msg)
                self.log_queue.task_done()
        except:
            pass
        
        # 处理剩余状态
        try:
            while not self.status_queue.empty():
                status = self.status_queue.get_nowait()
                self.status_changed.emit(status)
                self.status_queue.task_done()
        except:
            pass
    
    # ================================
    # 自动关机功能
    # ================================
    def handle_program_completion(self, reason):
        """统一的程序结束处理，包括关机检查"""
        try:
            self.send_log(LogLevel.INFO, f"📋 程序结束原因: {reason}")
            
            # 检查是否需要关机
            if self.auto_shutdown:
                self.send_log(LogLevel.INFO, "🔌 检查关机条件...")
                
                # 如果在关机时间窗口内，或者是因为任务完成而结束，都应该关机
                # 但用户手动Q键退出不应该关机
                should_shutdown = (self.is_in_shutdown_window() or 
                                 reason in ["余额未变化", "正常完成", "任务完成", "到达关机时间"])
                
                # 排除用户手动退出的情况
                if reason in ["用户退出", "手动停止", "Q键退出"]:
                    should_shutdown = False
                
                if should_shutdown:
                    if self.shutdown_computer():
                        self.send_log(LogLevel.SUCCESS, f"✅ 程序{reason}，已启动关机")
                    else:
                        self.send_log(LogLevel.WARNING, "⚠️ 关机失败，程序正常退出")
                else:
                    if reason in ["用户退出", "手动停止", "Q键退出"]:
                        self.send_log(LogLevel.INFO, f"🔌 用户手动退出，不执行关机")
                    else:
                        self.send_log(LogLevel.INFO, f"🔌 不在关机时间窗口内，程序正常退出")
            else:
                self.send_log(LogLevel.INFO, f"🔌 自动关机已禁用，程序正常退出")
                
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 结束处理异常: {e}")
    
    def is_in_work_time(self):
        """检查是否在工作时间内"""
        try:
            from datetime import datetime
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            # 处理跨日情况
            if self.work_start_time <= self.work_end_time:
                # 同一天内
                return self.work_start_time <= current_time <= self.work_end_time
            else:
                # 跨日情况
                return current_time >= self.work_start_time or current_time <= self.work_end_time
                
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 工作时间检查异常: {e}，默认为工作时间")
            return True
    
    def is_in_shutdown_window(self):
        """检查是否在关机时间窗口内"""
        try:
            from datetime import datetime, timedelta
            now = datetime.now()
            current_time = now.time()
            
            # 关机窗口：工作结束时间前后5分钟
            end_time = datetime.strptime(self.work_end_time, "%H:%M").time()
            
            # 计算时间窗口（处理跨日情况）
            end_datetime = datetime.combine(now.date(), end_time)
            start_datetime = end_datetime - timedelta(minutes=5)
            end_datetime = end_datetime + timedelta(minutes=5)
            
            # 检查是否在时间窗口内
            current_datetime = datetime.combine(now.date(), current_time)
            
            # 处理跨日情况
            if start_datetime.date() != end_datetime.date():
                # 跨日情况：检查是否在前一天的结束时间或当天的开始时间
                return (current_datetime >= start_datetime or 
                        current_datetime <= end_datetime)
            else:
                # 同日情况：正常检查
                return start_datetime <= current_datetime <= end_datetime
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 关机时间检查异常: {e}")
            return False
    
    def shutdown_computer(self):
        """执行自动关机"""
        try:
            self.send_log(LogLevel.INFO, "🔌 执行自动关机...")
            import subprocess
            subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
            self.send_log(LogLevel.SUCCESS, "✅ 关机命令已发送，10秒后关机")
            return True
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 关机失败: {e}")
            return False
    
    def _validate_time_format(self, time_str, param_name):
        """验证时间格式"""
        try:
            from datetime import datetime
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            self.send_log(LogLevel.WARNING, f"⚠️ {param_name}格式错误: {time_str}, 使用默认值")
            return "00:00" if param_name == 'work_start_time' else "23:59"
    
    # ================================
    # 外部控制接口
    # ================================
    def stop_behavior(self):
        """外部停止接口"""
        self._send_log(LogLevel.WARNING, f"🛑 [{self.behavior_name}] 收到外部停止信号")
        self.master_stop_event.set()
    
    def pause_behavior(self):
        """暂停行为"""
        try:
            self.command_queue.put(ThreadCommand.PAUSE, timeout=0.5)
            self._send_log(LogLevel.INFO, f"⏸️ [{self.behavior_name}] 暂停")
        except:
            pass
    
    def resume_behavior(self):
        """恢复行为"""
        try:
            self.command_queue.put(ThreadCommand.RESUME, timeout=0.5)
            self._send_log(LogLevel.INFO, f"▶️ [{self.behavior_name}] 恢复")
        except:
            pass
