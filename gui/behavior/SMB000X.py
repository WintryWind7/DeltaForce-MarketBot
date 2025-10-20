# -*- coding: utf-8 -*-
"""
购买刷新单端自定义子弹行为模块 - SMB000X
通过购买机制检测低价子弹并批量购买
代码ID: SMB000X (Single Market Bot)
"""

# 行为信息定义
BEHAVIOR_INFO = {
    "code_id": "SMB000X",  # 内部代码ID
    "title": "购买刷新单端自定义子弹行为",
    "description": "通过实际购买1个子弹来检测价格，发现低价时批量购买。需要用户手动切换到期望购买的子弹类型。",
    "version": "1.0.0",
    "author": "DeltaForce Team",
    "tags": ["单端", "购买查价"],
    "custom_config": {
        "target_price": {
            "type": "int", 
            "label": "目标价格阈值",
            "default": 480,
            "description": "低于此价格即为有效，进入购买阶段"
        },
        "min_price_threshold": {
            "type": "int",
            "label": "最低价格阈值",
            "default": 200,
            "description": "低于此价格认为是识别错误"
        },
        "refresh_delay": {
            "type": "float",
            "label": "购买刷新延迟(秒)",
            "default": 3.0,
            "min": 0.5,
            "max": 10.0,
            "description": "刷新阶段每次检测之间的延迟时间"
        },
        "refresh_quantity": {
            "type": "int",
            "label": "购买刷新时的数量",
            "default": 1,
            "min": 1,
            "max": 10,
            "description": "刷新阶段购买的数量（通常为1）"
        },
        "purchase_quantity": {
            "type": "int",
            "label": "购买时一次购买的数量",
            "default": 2,
            "min": 1,
            "max": 999,
            "description": "购买阶段每次购买的数量"
        },
        "click_times": {
            "type": "int",
            "label": "点击次数",
            "default": 5,
            "min": 1,
            "max": 20,
            "description": "购买阶段连续点击的次数"
        },
        "max_quantity": {
            "type": "int",
            "label": "数量滑条最大值",
            "default": 200,
            "min": 50,
            "max": 999,
            "description": "游戏内数量选择滑条的最大值，影响数量选择精度"
        },
        "work_start_time": {
            "type": "str",
            "label": "工作开始时间",
            "default": "00:00",
            "description": "每日工作开始时间，格式为HH:MM（24小时制）"
        },
        "work_end_time": {
            "type": "str",
            "label": "工作结束时间",
            "default": "05:15",
            "description": "每日工作结束时间，格式为HH:MM（24小时制）"
        }
    }
}

import os
import sys
import time
import threading
from datetime import datetime
from PySide6.QtCore import QThread, Signal

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# DeltaForce导入 - 支持相对和绝对导入
try:
    from DeltaForce import DeltaForceClass
except ImportError:
    # 添加DeltaForce路径
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'DeltaForce'))
    from DeltaForceClass import DeltaForceClass

class PurchaseRefreshBehavior(QThread):
    """购买刷新单端行为类 - SMB000X"""
    
    # 信号定义
    log_message = Signal(str)
    status_update = Signal(str)
    status_changed = Signal(str)  # 添加缺少的信号
    finished_signal = Signal(bool)  # 完成信号
    
    def __init__(self, window_handles, config=None):
        super().__init__()
        
        # 窗口句柄（单端只需要一个）
        self.window_handles = window_handles
        self.delta = None
        
        # 配置参数
        self.config = config or {}
        self.target_price = self.config.get('target_price', 480)
        self.min_price_threshold = self.config.get('min_price_threshold', 200)
        self.refresh_delay = self.config.get('refresh_delay', 3.0)
        self.refresh_quantity = self.config.get('refresh_quantity', 1)
        self.purchase_quantity = self.config.get('purchase_quantity', 2)
        self.click_times = self.config.get('click_times', 5)
        self.max_quantity = self.config.get('max_quantity', 200)
        
        # 工作时间参数（从配置中读取并验证）
        self.work_start_time = self._validate_time_format(
            self.config.get('work_start_time', '00:00'), 'work_start_time'
        )
        self.work_end_time = self._validate_time_format(
            self.config.get('work_end_time', '05:15'), 'work_end_time'
        )
        
        # 控制变量
        self.should_stop = False
        self.is_running = False
        self.current_phase = "刷新阶段"  # "刷新阶段" 或 "购买阶段"
        
        # 统计变量
        self.refresh_count = 0
        self.purchase_count = 0
        self.low_price_found_count = 0
        
        # 余额跟踪变量
        self.initial_balance = None  # 初始余额
        self.current_balance = None  # 当前余额
        self.balance_initialized = False  # 余额是否已初始化
        
        # 花费跟踪变量
        self.refresh_cost_total = 0  # 购买刷新总花费
        self.purchase_cost_total = 0  # 低价购入总花费
        self.refresh_cost_records = []  # 每次刷新花费记录
        self.purchase_cost_records = []  # 每次购买花费记录
        
        # 任务统计数据
        self.task_start_time = datetime.now()
        self.task_data = {
            'start_time': self.task_start_time.isoformat(),
            'status': 'running',
            'statistics': {},
            'summary': ''
        }
        
        # 日志文件 - 保存到 log/pricedate 目录
        self.start_time = datetime.now()
        self.log_file = self._create_log_file_path()
    
    def _create_log_file_path(self):
        """创建日志文件路径"""
        # 创建 log/pricedate 目录
        log_dir = os.path.join(os.getcwd(), "log", "pricedate")
        os.makedirs(log_dir, exist_ok=True)
        
        # 使用脚本开始时间作为文件名
        time_str = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"SMB000X_{time_str}.csv"
        
        return os.path.join(log_dir, filename)
    
    def _validate_time_format(self, time_str, param_name):
        """
        验证时间格式是否正确
        
        Args:
            time_str (str): 时间字符串，格式为HH:MM
            param_name (str): 参数名称，用于错误提示
            
        Returns:
            tuple: (hour, minute) 如果格式正确
            
        Raises:
            ValueError: 如果时间格式不正确
        """
        try:
            # 检查基本格式
            if not isinstance(time_str, str) or ':' not in time_str:
                raise ValueError(f"时间格式错误")
            
            # 分割并转换
            parts = time_str.split(':')
            if len(parts) != 2:
                raise ValueError(f"时间格式错误，应为HH:MM格式")
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            # 验证范围
            if not (0 <= hour <= 23):
                raise ValueError(f"小时必须在0-23之间")
            if not (0 <= minute <= 59):
                raise ValueError(f"分钟必须在0-59之间")
            
            return (hour, minute)
            
        except (ValueError, TypeError) as e:
            error_msg = f"参数 {param_name} 的时间格式无效: '{time_str}' - {str(e)}"
            # 使用默认值并记录警告
            if param_name == 'work_start_time':
                default_time = (0, 0)  # 00:00
                self.log_message.emit(f"⚠️ {error_msg}，使用默认值 00:00")
            else:  # work_end_time
                default_time = (5, 15)  # 05:15
                self.log_message.emit(f"⚠️ {error_msg}，使用默认值 05:15")
            return default_time
        
    def initialize_delta(self):
        """初始化Delta实例"""
        try:
            if not self.window_handles:
                self.log_message.emit("❌ 未提供窗口句柄")
                return False
            
            # 创建Delta实例并绑定到窗口
            self.delta = DeltaForceClass()
            if not self.delta.bind_to_window(self.window_handles[0]):
                self.log_message.emit("❌ 窗口绑定失败")
                return False
            
            # 设置日志回调
            self.delta.set_log_callback(self.log_message.emit)
            
            self.log_message.emit(f"✅ 成功绑定到窗口: {self.window_handles[0]}")
            self.log_message.emit(f"📊 配置参数:")
            self.log_message.emit(f"   目标价格: {self.target_price}")
            self.log_message.emit(f"   最低价格阈值: {self.min_price_threshold}")
            self.log_message.emit(f"   刷新延迟: {self.refresh_delay}秒")
            self.log_message.emit(f"   刷新数量: {self.refresh_quantity}")
            self.log_message.emit(f"   购买数量: {self.purchase_quantity}")
            self.log_message.emit(f"   点击次数: {self.click_times}")
            
            # 显示工作时间配置
            start_time_str = f"{self.work_start_time[0]:02d}:{self.work_start_time[1]:02d}"
            end_time_str = f"{self.work_end_time[0]:02d}:{self.work_end_time[1]:02d}"
            self.log_message.emit(f"   工作时间: {start_time_str} - {end_time_str}")
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ Delta初始化失败: {e}")
            return False
    
    def is_balance_reasonable(self, price_diff):
        """
        判断余额差值是否合理
        考虑刷新数量：合理范围 = 刷新数量 × (最低阈值 ~ 2倍目标价格)
        """
        actual_refresh_quantity = max(1, self.refresh_quantity)
        
        # 计算预期的价格范围（考虑刷新数量）
        min_reasonable = self.min_price_threshold * actual_refresh_quantity
        max_reasonable = self.target_price * 2 * actual_refresh_quantity
        
        is_reasonable = min_reasonable <= price_diff <= max_reasonable
        self.log_message.emit(f"💡 价格合理性检查: {price_diff} (数量{actual_refresh_quantity}×合理范围: {min_reasonable}-{max_reasonable}) -> {'✅合理' if is_reasonable else '❌不合理'}")
        
        return is_reasonable
    
    def is_in_work_time(self):
        """
        检查当前是否在工作时间内
        使用配置的工作时间参数
        Returns:
            bool: True表示在工作时间内，False表示不在
        """
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_total_minutes = current_hour * 60 + current_minute
        
        # 从配置获取工作时间
        start_hour, start_minute = self.work_start_time
        end_hour, end_minute = self.work_end_time
        
        start_total_minutes = start_hour * 60 + start_minute
        end_total_minutes = end_hour * 60 + end_minute
        
        # 处理跨天的情况（如23:00到06:00）
        if start_total_minutes <= end_total_minutes:
            # 同一天内的时间段
            return start_total_minutes <= current_total_minutes <= end_total_minutes
        else:
            # 跨天的时间段
            return current_total_minutes >= start_total_minutes or current_total_minutes <= end_total_minutes
    
    def log_current_time_status(self):
        """记录当前时间状态"""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        if self.is_in_work_time():
            self.log_message.emit(f"⏰ 当前时间: {time_str} - ✅ 在工作时间内，继续执行")
        else:
            self.log_message.emit(f"⏰ 当前时间: {time_str} - ⏸️ 不在工作时间内，等待中...")
    
    def wait_for_work_time(self):
        """等待工作时间，每分钟检查一次"""
        while not self.should_stop and not self.is_in_work_time():
            self.log_current_time_status()
            
            # 分段等待60秒，提高Q键响应性
            wait_time = 0
            while wait_time < 60 and not self.should_stop:
                time.sleep(1)
                wait_time += 1
        
        # 如果进入工作时间，记录一下
        if not self.should_stop and self.is_in_work_time():
            self.log_current_time_status()
    
    def initialize_balance(self):
        """初始化余额跟踪"""
        try:
            balance = self.delta.get_balance(where="market", loop=True)
            if balance is not None:
                self.initial_balance = balance
                self.current_balance = balance
                self.balance_initialized = True
                self.log_message.emit(f"💰 [SMB000X] 初始余额记录: {balance}")
                return True
            else:
                self.log_message.emit("⚠️ [SMB000X] 初始余额获取失败")
                return False
        except Exception as e:
            self.log_message.emit(f"❌ [SMB000X] 初始余额获取异常: {e}")
            return False
    
    def update_current_balance(self):
        """更新当前余额"""
        try:
            balance = self.delta.get_balance(where="market", loop=True)
            if balance is not None:
                self.current_balance = balance
                return balance
            else:
                self.log_message.emit("⚠️ 当前余额获取失败")
                return None
        except Exception as e:
            self.log_message.emit(f"❌ 当前余额获取异常: {e}")
            return None
    
    def get_balance_safe(self):
        """安全获取余额（使用交易行位置）"""
        try:
            balance = self.delta.get_balance(where="market", loop=True)
            if balance is not None:
                # 更新当前余额跟踪
                if self.balance_initialized:
                    self.current_balance = balance
                self.log_message.emit(f"💰 当前余额: {balance}")
                return balance
            else:
                self.log_message.emit("⚠️ 余额获取失败")
                return None
        except Exception as e:
            self.log_message.emit(f"❌ 余额获取异常: {e}")
            return None
    
    def _format_work_time_range(self):
        """安全格式化工作时间范围"""
        try:
            if (self.work_start_time and len(self.work_start_time) >= 2 and 
                self.work_end_time and len(self.work_end_time) >= 2):
                return f"{self.work_start_time[0]:02d}:{self.work_start_time[1]:02d}-{self.work_end_time[0]:02d}:{self.work_end_time[1]:02d}"
            else:
                return "未设置"
        except (TypeError, ValueError, IndexError):
            return "格式错误"
    
    def _calculate_price_statistics(self, price_list, label="价格"):
        """
        计算价格统计数据：众数、平均数、最高价、最低价
        
        Args:
            price_list: 价格列表
            label: 数据标签
            
        Returns:
            dict: 统计结果
        """
        if not price_list:
            return None
        
        from collections import Counter
        
        # 转换为整数列表（四舍五入）
        rounded_prices = [round(price) for price in price_list]
        
        # 计算统计数据
        counter = Counter(rounded_prices)
        most_common = counter.most_common(1)[0]  # (价格, 出现次数)
        
        stats = {
            'count': len(price_list),
            'average': sum(price_list) / len(price_list),
            'mode': most_common[0],
            'mode_count': most_common[1],
            'max_price': max(price_list),
            'max_count': counter[round(max(price_list))],
            'min_price': min(price_list),
            'min_count': counter[round(min(price_list))]
        }
        
        return stats
    
    def print_balance_summary(self):
        """打印余额统计摘要"""
        if not self.balance_initialized or self.initial_balance is None:
            self.log_message.emit("⚠️ [SMB000X] 余额跟踪未初始化，无法生成统计")
            return
        
        # 确保有最新的当前余额
        final_balance = self.update_current_balance()
        if final_balance is None:
            final_balance = self.current_balance  # 使用最后一次成功获取的余额
        
        if final_balance is not None:
            total_cost = self.initial_balance - final_balance  # 总花费
            
            self.log_message.emit("=" * 70)
            self.log_message.emit("💰 [SMB000X] 详细花费统计摘要")
            self.log_message.emit("=" * 70)
            
            # 摘要部分（6行）
            self.log_message.emit(f"📊 初始余额: {self.initial_balance:,}")
            self.log_message.emit(f"📊 最终余额: {final_balance:,}")
            self.log_message.emit(f"💸 共花费: {total_cost:,}")
            self.log_message.emit(f"🔄 购买刷新时花费: {self.refresh_cost_total:,}")
            self.log_message.emit(f"💰 低价购入花费: {self.purchase_cost_total:,}")
            if self.refresh_count > 0:
                refresh_efficiency = (self.low_price_found_count / self.refresh_count) * 100
                self.log_message.emit(f"📈 发现低价效率: {refresh_efficiency:.1f}% ({self.low_price_found_count}/{self.refresh_count})")
            
            self.log_message.emit("=" * 70)
            
            # 详细分析 - 大板块1: 大数统计
            self.log_message.emit("📊 【大数统计】")
            
            # 刷新阶段大数统计
            if self.refresh_cost_records:
                refresh_costs = [record['cost'] for record in self.refresh_cost_records]
                refresh_stats = self._calculate_price_statistics(refresh_costs, "刷新花费")
                
                self.log_message.emit("🔄 刷新阶段:")
                self.log_message.emit(f"   众数: {refresh_stats['mode']:,} (出现{refresh_stats['mode_count']}次)")
                self.log_message.emit(f"   平均数: {refresh_stats['average']:,.1f}")
                self.log_message.emit(f"   最高价: {refresh_stats['max_price']:,.1f} (出现{refresh_stats['max_count']}次)")
                self.log_message.emit(f"   最低价: {refresh_stats['min_price']:,.1f} (出现{refresh_stats['min_count']}次)")
            
            # 低价购入阶段大数统计
            if self.purchase_cost_records:
                purchase_costs = [record['cost'] for record in self.purchase_cost_records]
                purchase_stats = self._calculate_price_statistics(purchase_costs, "购买花费")
                
                self.log_message.emit("💰 低价购入阶段:")
                self.log_message.emit(f"   众数: {purchase_stats['mode']:,} (出现{purchase_stats['mode_count']}次)")
                self.log_message.emit(f"   平均数: {purchase_stats['average']:,.1f}")
                self.log_message.emit(f"   最高价: {purchase_stats['max_price']:,.1f} (出现{purchase_stats['max_count']}次)")
                self.log_message.emit(f"   最低价: {purchase_stats['min_price']:,.1f} (出现{purchase_stats['min_count']}次)")
            
            self.log_message.emit("=" * 70)
            
            # 详细分析 - 大板块2: 单价统计
            self.log_message.emit("💱 【单价统计】")
            
            # 刷新阶段单价统计
            if self.refresh_cost_records:
                refresh_unit_prices = [record['unit_price'] for record in self.refresh_cost_records]
                refresh_unit_stats = self._calculate_price_statistics(refresh_unit_prices, "刷新单价")
                
                self.log_message.emit("🔄 刷新阶段:")
                self.log_message.emit(f"   众数: {refresh_unit_stats['mode']:.1f} (出现{refresh_unit_stats['mode_count']}次)")
                self.log_message.emit(f"   平均数: {refresh_unit_stats['average']:.1f}")
                self.log_message.emit(f"   最高价: {refresh_unit_stats['max_price']:.1f} (出现{refresh_unit_stats['max_count']}次)")
                self.log_message.emit(f"   最低价: {refresh_unit_stats['min_price']:.1f} (出现{refresh_unit_stats['min_count']}次)")
            
            # 低价购入阶段单价统计
            if self.purchase_cost_records:
                purchase_unit_prices = [record['actual_unit_price'] for record in self.purchase_cost_records]
                purchase_unit_stats = self._calculate_price_statistics(purchase_unit_prices, "购买单价")
                
                self.log_message.emit("💰 低价购入阶段:")
                self.log_message.emit(f"   众数: {purchase_unit_stats['mode']:.1f} (出现{purchase_unit_stats['mode_count']}次)")
                self.log_message.emit(f"   平均数: {purchase_unit_stats['average']:.1f}")
                self.log_message.emit(f"   最高价: {purchase_unit_stats['max_price']:.1f} (出现{purchase_unit_stats['max_count']}次)")
                self.log_message.emit(f"   最低价: {purchase_unit_stats['min_price']:.1f} (出现{purchase_unit_stats['min_count']}次)")
            
            self.log_message.emit("=" * 70)
        else:
            self.log_message.emit("❌ [SMB000X] 无法获取最终余额，统计不完整")
    
    def _collect_task_statistics(self):
        """收集任务统计数据"""
        try:
            # 计算运行时长
            end_time = datetime.now()
            duration = (end_time - self.task_start_time).total_seconds()
            
            # 收集统计数据
            statistics = {
                'refresh_count': self.refresh_count,
                'purchase_count': self.purchase_count,
                'low_price_found_count': self.low_price_found_count,
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'balance_change': None,
                'balance_change_percentage': None,
                'total_cost': None,
                'refresh_cost_total': self.refresh_cost_total,
                'purchase_cost_total': self.purchase_cost_total,
                'refresh_efficiency': None,
                'target_price': self.target_price,
                'min_price_threshold': self.min_price_threshold,
                'work_time_range': self._format_work_time_range()
            }
            
            # 添加详细价格统计数据
            if self.refresh_cost_records:
                refresh_costs = [record['cost'] for record in self.refresh_cost_records]
                refresh_unit_prices = [record['unit_price'] for record in self.refresh_cost_records]
                statistics['refresh_cost_stats'] = self._calculate_price_statistics(refresh_costs, "刷新花费")
                statistics['refresh_unit_stats'] = self._calculate_price_statistics(refresh_unit_prices, "刷新单价")
            
            if self.purchase_cost_records:
                purchase_costs = [record['cost'] for record in self.purchase_cost_records]
                purchase_unit_prices = [record['actual_unit_price'] for record in self.purchase_cost_records]
                statistics['purchase_cost_stats'] = self._calculate_price_statistics(purchase_costs, "购买花费")
                statistics['purchase_unit_stats'] = self._calculate_price_statistics(purchase_unit_prices, "购买单价")
            
            # 计算余额变化和花费
            if self.initial_balance is not None and self.current_balance is not None:
                balance_change = self.current_balance - self.initial_balance
                total_cost = self.initial_balance - self.current_balance
                statistics['balance_change'] = balance_change
                statistics['total_cost'] = total_cost
                if self.initial_balance > 0:
                    statistics['balance_change_percentage'] = (balance_change / self.initial_balance) * 100
            
            # 计算效率
            if self.refresh_count > 0:
                statistics['refresh_efficiency'] = (self.low_price_found_count / self.refresh_count) * 100
            
            # 生成摘要
            summary_parts = []
            summary_parts.append(f"运行时长: {duration:.1f}秒")
            summary_parts.append(f"刷新次数: {self.refresh_count}")
            summary_parts.append(f"购买次数: {self.purchase_count}")
            summary_parts.append(f"发现低价: {self.low_price_found_count}次")
            
            # 添加花费信息到摘要
            total_cost = statistics.get('total_cost')
            if total_cost is not None:
                summary_parts.append(f"总花费: {total_cost:,}")
                summary_parts.append(f"刷新花费: {self.refresh_cost_total:,}")
                summary_parts.append(f"购买花费: {self.purchase_cost_total:,}")
            
            refresh_efficiency = statistics.get('refresh_efficiency')
            if refresh_efficiency is not None:
                summary_parts.append(f"发现效率: {refresh_efficiency:.1f}%")
            
            # 更新任务数据
            self.task_data.update({
                'duration': duration,
                'status': 'completed' if not self.should_stop else 'interrupted',
                'statistics': statistics,
                'summary': ' | '.join(summary_parts)
            })
            
        except Exception as e:
            self.log_message.emit(f"⚠️ [SMB000X] 收集任务统计失败: {e}")
    
    def _save_task_record(self):
        """保存任务记录到任务日志"""
        try:
            # 导入任务日志管理器
            import sys
            import os
            gui_dir = os.path.join(os.path.dirname(__file__), '..')
            gui_dir = os.path.abspath(gui_dir)
            if gui_dir not in sys.path:
                sys.path.append(gui_dir)
            from task_logger import get_task_logger
            
            # 收集统计数据
            self._collect_task_statistics()
            
            # 保存任务记录
            task_logger = get_task_logger()
            success = task_logger.add_task_record('SMB000X', self.task_data)
            
            if success:
                self.log_message.emit("📝 [SMB000X] 任务记录已保存")
            else:
                self.log_message.emit("⚠️ [SMB000X] 任务记录保存失败")
                
        except Exception as e:
            self.log_message.emit(f"❌ [SMB000X] 保存任务记录异常: {e}")
    
    def refresh_phase_buy(self):
        """刷新阶段购买（点击最左侧最小值）"""
        try:
            # 确保刷新数量至少为1
            actual_refresh_quantity = max(1, self.refresh_quantity)
            
            success = self.delta.buy_in_market(
                buyin=actual_refresh_quantity,  # 使用配置的刷新数量
                maxin=self.max_quantity,  # 使用配置的最大值
                times=1,
                delay=0.1,
                buy=True,
                loop=True
            )
            
            if success:
                self.log_message.emit(f"🔄 刷新阶段购买完成 (数量: {actual_refresh_quantity})")
                return True
            else:
                self.log_message.emit("❌ 刷新阶段购买失败")
                return False
                
        except Exception as e:
            self.log_message.emit(f"❌ 刷新阶段购买异常: {e}")
            return False
    
    def purchase_phase_buy(self):
        """购买阶段批量购买（切换至最大值）"""
        try:
            # 计算实际点击次数：2n-1，其中n为配置的点击次数
            effective_clicks = self.click_times  # 有效点击次数（配置值）
            actual_clicks = 2 * effective_clicks - 1  # 实际执行的点击次数
            
            self.log_message.emit(f"💰 开始购买阶段: 数量={self.purchase_quantity}, 有效点击={effective_clicks}, 实际点击={actual_clicks}")
            
            success = self.delta.buy_in_market(
                buyin=self.purchase_quantity,
                maxin=self.max_quantity,  # 使用配置的最大值
                times=actual_clicks,  # 使用计算后的实际点击次数
                delay=0.1,
                buy=True,
                loop=True
            )
            
            if success:
                self.log_message.emit(f"✅ 购买阶段完成: {self.purchase_quantity}x{effective_clicks} (实际点击{actual_clicks}次)")
                self.purchase_count += effective_clicks  # 记录有效点击次数
                return True
            else:
                self.log_message.emit("❌ 购买阶段失败")
                return False
                
        except Exception as e:
            self.log_message.emit(f"❌ 购买阶段异常: {e}")
            return False
    
    def reset_to_minimum(self):
        """重置购买数量为最小值（为下次刷新阶段准备）"""
        try:
            # 确保刷新数量至少为1
            actual_refresh_quantity = max(1, self.refresh_quantity)
            
            # 使用测试模式只设置数量，不实际购买
            success = self.delta.buy_in_market(
                buyin=actual_refresh_quantity,
                maxin=self.max_quantity,  # 使用配置的最大值
                times=1,
                delay=0.1,
                buy=False,  # 只设置数量，不购买
                loop=True
            )
            
            if success:
                self.log_message.emit(f"🔄 已重置购买数量为刷新数量: {actual_refresh_quantity}")
                return True
            else:
                self.log_message.emit("⚠️ 重置购买数量失败")
                return False
                
        except Exception as e:
            self.log_message.emit(f"❌ 重置数量异常: {e}")
            return False
    
    def write_log(self, check_num, balance_before, balance_after, unit_price, action):
        """写入日志文件"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                if check_num == 1:
                    # 写入表头
                    f.write("检测次数,购买前余额,购买后余额,单价,动作,时间\n")
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{check_num},{balance_before},{balance_after},{unit_price:.1f},{action},{timestamp}\n")
                
        except Exception as e:
            self.log_message.emit(f"⚠️ 日志写入失败: {e}")
    
    def run(self):
        """主运行逻辑 - 两阶段流程"""
        try:
            self.is_running = True
            self.status_update.emit("运行中")
            self.status_changed.emit("running")  # 发送状态变更信号
            
            # 初始化
            if not self.initialize_delta():
                return
            
            # 初始化余额跟踪
            if not self.initialize_balance():
                self.log_message.emit("⚠️ [SMB000X] 余额初始化失败，但程序将继续运行")
            
            self.log_message.emit("🚀 [SMB000X] 购买刷新行为开始运行")
            self.log_message.emit("⚠️ 请确保已手动切换到期望购买的子弹类型")
            self.log_message.emit("📋 流程说明: 刷新阶段 → 价格检测 → 购买阶段（如满足条件）→ 循环")
            # 显示配置的工作时间
            start_time_str = f"{self.work_start_time[0]:02d}:{self.work_start_time[1]:02d}"
            end_time_str = f"{self.work_end_time[0]:02d}:{self.work_end_time[1]:02d}"
            self.log_message.emit(f"⏰ 工作时间: 每天 {start_time_str} - {end_time_str}")
            
            # 首次检查工作时间
            self.log_current_time_status()
            
            # 如果不在工作时间，先等待
            if not self.is_in_work_time():
                self.log_message.emit("⏸️ 当前不在工作时间，进入等待模式...")
                self.wait_for_work_time()
            
            # 检查是否被停止
            if self.should_stop:
                return
            
            # 主循环
            while not self.should_stop:
                try:
                    # 检查停止标志（提高Q键响应性）
                    if self.should_stop:
                        break
                    
                    # 在每次循环开始时检查工作时间（一阶段开始前）
                    if not self.is_in_work_time():
                        self.log_message.emit("⏸️ 已超出工作时间，进入等待模式...")
                        self.wait_for_work_time()
                        
                        # 等待后检查是否被停止
                        if self.should_stop:
                            break
                        
                        self.log_message.emit("✅ 重新进入工作时间，继续执行任务")
                        
                    # ============ 第一阶段：刷新阶段 ============
                    self.current_phase = "刷新阶段"
                    self.refresh_count += 1
                    self.log_message.emit(f"\n🔄 第 {self.refresh_count} 次刷新阶段")
                    
                    # (st) 获取初始余额
                    balance_before = self.get_balance_safe()
                    if balance_before is None:
                        self.log_message.emit("❌ 无法获取初始余额，跳过本次检测")
                        time.sleep(self.refresh_delay)
                        continue
                    time.sleep(0.1)  # 延迟0.1s
                    
                    # 检查停止标志
                    if self.should_stop:
                        break
                    
                    while True:  # 内部循环，直到获得合理的余额差
                        # 检查停止标志（内部循环中也要检查）
                        if self.should_stop:
                            break
                            
                        # 步骤1: 刷新阶段购买
                        if not self.refresh_phase_buy():
                            self.log_message.emit("❌ 刷新阶段购买失败，跳过本次检测")
                            time.sleep(self.refresh_delay)
                            break
                        
                        time.sleep(0.1)  # 延迟0.1s
                        
                        # 检查停止标志
                        if self.should_stop:
                            break
                        
                        # 步骤2: 获取购买后余额
                        balance_after = self.get_balance_safe()
                        if balance_after is None:
                            self.log_message.emit("❌ 无法获取购买后余额，跳过本次检测")
                            time.sleep(self.refresh_delay)
                            break
                        
                        # 步骤3: 计算价格差和单价
                        price_diff = balance_before - balance_after
                        actual_refresh_quantity = max(1, self.refresh_quantity)
                        unit_price = price_diff / actual_refresh_quantity  # 计算单价
                        self.log_message.emit(f"💸 检测到总价: {price_diff}, 单价: {unit_price:.1f} (数量: {actual_refresh_quantity}, 余额: {balance_before} → {balance_after})")
                        
                        # 步骤4: 价格合理性检查
                        if self.is_balance_reasonable(price_diff):
                            # 只有合理的价格才记录到统计中
                            self.refresh_cost_total += price_diff
                            self.refresh_cost_records.append({
                                'cycle': self.refresh_count,
                                'cost': price_diff,
                                'unit_price': unit_price,
                                'quantity': actual_refresh_quantity,
                                'balance_before': balance_before,
                                'balance_after': balance_after
                            })
                            
                            # 合理的价格差，继续判断是否满足购买条件（使用单价比较）
                            if unit_price < self.target_price:
                                # ============ 第二阶段：购买阶段 ============
                                self.current_phase = "购买阶段"
                                self.log_message.emit(f"🎉 发现低价子弹! 单价: {unit_price:.1f} < 目标: {self.target_price}")
                                self.log_message.emit("💰 进入购买阶段...")
                                self.low_price_found_count += 1
                                
                                # 记录购买前余额
                                purchase_balance_before = balance_after  # 刷新后的余额作为购买前余额
                                
                                # 执行批量购买
                                if self.purchase_phase_buy():
                                    # 获取购买后余额，计算购买花费
                                    purchase_balance_after = self.get_balance_safe()
                                    if purchase_balance_after is not None:
                                        purchase_cost = purchase_balance_before - purchase_balance_after
                                        self.purchase_cost_total += purchase_cost
                                        
                                        # 修改后的逻辑：有效点击次数为配置值，实际购买数量为 有效点击次数 * 购买数量
                                        effective_clicks = self.click_times  # 有效点击次数
                                        actual_total_quantity = effective_clicks * self.purchase_quantity
                                        actual_unit_price = purchase_cost / actual_total_quantity if actual_total_quantity > 0 else 0
                                        
                                        self.purchase_cost_records.append({
                                            'cycle': self.refresh_count,
                                            'low_price_found': self.low_price_found_count,
                                            'cost': purchase_cost,
                                            'expected_unit_price': unit_price,  # 刷新时发现的单价
                                            'actual_unit_price': actual_unit_price,  # 实际购买单价
                                            'quantity_per_click': self.purchase_quantity,
                                            'effective_clicks': effective_clicks,
                                            'total_quantity': actual_total_quantity,
                                            'balance_before': purchase_balance_before,
                                            'balance_after': purchase_balance_after
                                        })
                                        self.log_message.emit(f"💰 购买阶段花费: {purchase_cost:,} | 数量: {actual_total_quantity} | 实际单价: {actual_unit_price:.1f} (购买前: {purchase_balance_before:,} → 购买后: {purchase_balance_after:,})")
                                    self.write_log(self.refresh_count, balance_before, balance_after, unit_price, f"购买成功({self.purchase_quantity}x{self.click_times})")
                                    self.log_message.emit("✅ 购买阶段完成，准备下次刷新")
                                else:
                                    self.write_log(self.refresh_count, balance_before, balance_after, unit_price, "购买失败")
                                    self.log_message.emit("❌ 购买阶段失败")
                                
                                # 重置为最小值，准备下次刷新阶段
                                self.reset_to_minimum()
                            else:
                                self.log_message.emit(f"📊 价格过高: 单价 {unit_price:.1f} >= 目标: {self.target_price}，继续刷新")
                                self.write_log(self.refresh_count, balance_before, balance_after, unit_price, "价格过高")
                                
                                # 重置为最小值（为下次刷新阶段准备）
                                self.reset_to_minimum()
                            
                            # 使用当前余额作为下次的基准
                            balance_before = balance_after
                            break  # 跳出内部循环
                        else:
                            # 不合理的价格差，重新获取余额 (st)
                            self.log_message.emit("🔄 价格差不合理，重新获取余额...")
                            balance_before = self.get_balance_safe()
                            if balance_before is None:
                                self.log_message.emit("❌ 重新获取余额失败，跳过本次检测")
                                time.sleep(self.refresh_delay)
                                break
                            time.sleep(0.1)  # 延迟0.1s
                            # 继续内部循环
                    
                    # 检查停止标志
                    if self.should_stop:
                        break
                    
                    # 更新统计信息
                    self.log_message.emit(f"📈 统计: 刷新{self.refresh_count}次, 购买{self.purchase_count}次, 发现低价{self.low_price_found_count}次")
                    
                    # 等待下次刷新（分段检查停止标志）
                    if not self.should_stop:
                        self.log_message.emit(f"⏳ 等待 {self.refresh_delay} 秒后进行下次刷新...")
                        # 分段等待，提高响应性
                        wait_time = 0
                        while wait_time < self.refresh_delay and not self.should_stop:
                            time.sleep(0.1)
                            wait_time += 0.1
                   
                except Exception as e:
                    self.log_message.emit(f"❌ 循环异常: {e}")
                    time.sleep(self.refresh_delay)
            
        except Exception as e:
            self.log_message.emit(f"❌ 运行异常: {e}")
        
        finally:
            # 输出余额统计摘要
            self.print_balance_summary()
            
            # 保存任务记录
            self._save_task_record()
            
            self.is_running = False
            self.status_update.emit("已停止")
            self.status_changed.emit("stopped")  # 发送状态变更信号
            self.finished_signal.emit(not self.should_stop)  # True表示正常完成，False表示被中断
            self.log_message.emit("🏁 [SMB000X] 购买刷新行为已停止")
    
    def stop(self):
        """停止行为"""
        self.should_stop = True
        self.log_message.emit("🛑 正在停止购买刷新行为...")
        
        # 等待线程结束
        if self.isRunning():
            self.wait(5000)  # 等待5秒
        
        self.log_message.emit("✅ 购买刷新行为已完全停止")
