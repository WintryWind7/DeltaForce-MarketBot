# -*- coding: utf-8 -*-
"""
双端满仓自定义子弹行为模块 - DMB000X
通过双窗口操作，辅端31发刷新检测价格，主端200发批量购买
代码ID: DMB000X (Dual Market Bot)
"""

# 行为信息定义
BEHAVIOR_INFO = {
    "code_id": "DMB000X",  # 内部代码ID
    "title": "双端满仓自定义子弹行为",
    "description": "双窗口操作：辅端31发刷新检测价格，主端200发批量购买。需要用户手动切换到期望购买的子弹类型。",
    "version": "1.0.0",
    "author": "DeltaForce Team",
    "tags": ["双端", "满仓", "购买查价"],
    "custom_config": {
        "target_price": {
            "type": "int", 
            "label": "目标价格阈值",
            "default": 540,
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
            "default": 0.8,
            "min": 0.5,
            "max": 10.0,
            "description": "刷新阶段每次检测之间的延迟时间"
        },
        "auxiliary_refresh_quantity": {
            "type": "int",
            "label": "辅端刷新数量",
            "default": 31,
            "min": 1,
            "max": 50,
            "description": "辅端刷新阶段购买的数量（用于价格检测）"
        },
        "main_purchase_quantity": {
            "type": "int",
            "label": "主端购买数量",
            "default": 200,
            "min": 50,
            "max": 999,
            "description": "主端购买阶段每次购买的数量"
        },
        "click_times": {
            "type": "int",
            "label": "点击次数",
            "default": 6,
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
        },
        "auto_shutdown": {
            "type": "bool",
            "label": "自动关机",
            "default": True,
            "description": "到达工作结束时间时自动关闭电脑"
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

from DeltaForce.DeltaForceClass import DeltaForceClass
from DeltaForce.DeltaForceManager import DeltaForceManager
from gui.task_logger import TaskLogger

class DualMarketBotBehavior(QThread):
    """双端满仓自定义子弹行为类"""
    
    # 信号定义
    log_message = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self, window_handles, config=None):
        """
        初始化双端满仓行为
        
        Args:
            window_handles: 窗口句柄列表，需要至少2个窗口
            config: 配置参数字典
        """
        super().__init__()
        
        # 检查窗口数量
        if len(window_handles) < 2:
            raise ValueError("DMB000X需要至少2个窗口句柄")
        
        # 窗口句柄
        self.window_handles = window_handles
        
        # 使用DeltaForceManager管理双端窗口
        self.manager = DeltaForceManager(window_handles)
        
        if not self.manager.is_initialized:
            raise RuntimeError("DeltaForceManager初始化失败")
        
        # 获取主辅实例
        self.main_delta = self.manager.get_main()      # 主端（200发购买）
        self.auxiliary_delta = self.manager.get_aux()  # 辅端（31发刷新）
        
        if not self.main_delta or not self.auxiliary_delta:
            raise RuntimeError("主辅窗口实例获取失败")
        
        # 配置参数
        self.config = config or {}
        self.target_price = self.config.get('target_price', 540)
        self.min_price_threshold = self.config.get('min_price_threshold', 200)
        self.refresh_delay = self.config.get('refresh_delay', 0.8)
        self.auxiliary_refresh_quantity = self.config.get('auxiliary_refresh_quantity', 31)
        self.main_purchase_quantity = self.config.get('main_purchase_quantity', 200)
        self.click_times = self.config.get('click_times', 6)
        self.max_quantity = self.config.get('max_quantity', 200)
        self.work_start_time = self.config.get('work_start_time', '00:00')
        self.work_end_time = self.config.get('work_end_time', '05:15')
        self.auto_shutdown = self.config.get('auto_shutdown', True)
        
        # 运行状态
        self.should_stop = False
        self.current_phase = "未开始"
        
        # 统计数据
        self.refresh_count = 0
        self.purchase_count = 0
        self.low_price_found_count = 0
        self.zero_price_diff_count = 0
        
        # 余额跟踪
        self.main_initial_balance = None
        self.main_current_balance = None
        self.auxiliary_initial_balance = None
        self.auxiliary_current_balance = None
        self.balance_initialized = False
        
        # 辅端余额监控
        self.auxiliary_balance_unchanged_count = 0  # 辅端余额连续不变次数
        self.auxiliary_last_balance = None  # 辅端上次余额
        self.main_only_mode = False  # 是否切换为纯主端模式
        
        # 主端余额监控
        self.main_balance_unchanged_count = 0  # 主端余额连续不变次数
        self.main_last_balance = None  # 主端上次余额
        
        # 花费跟踪变量
        self.refresh_cost_total = 0  # 购买刷新总花费
        self.purchase_cost_total = 0  # 低价购入总花费
        self.refresh_cost_records = []  # 每次刷新花费记录
        self.purchase_cost_records = []  # 每次购买花费记录
        
        # 任务日志记录器
        try:
            from gui.task_logger import TaskLogger
            self.task_logger = TaskLogger()
        except ImportError:
            # 如果导入失败，创建一个简单的替代品
            class DummyTaskLogger:
                def add_task_record(self, *args, **kwargs):
                    pass
            self.task_logger = DummyTaskLogger()
    
    def stop(self):
        """停止行为执行"""
        self.should_stop = True
        self.log_message.emit("🛑 [DMB000X] 收到停止信号")
    
    def is_in_work_time(self):
        """检查当前是否在工作时间内"""
        try:
            current_time = datetime.now().time()
            
            # 解析工作时间
            start_parts = self.work_start_time.split(':')
            end_parts = self.work_end_time.split(':')
            
            if len(start_parts) != 2 or len(end_parts) != 2:
                self.log_message.emit("⚠️ 工作时间格式错误，默认为工作时间")
                return True
            
            start_time = datetime.strptime(f"{start_parts[0]:0>2}:{start_parts[1]:0>2}", "%H:%M").time()
            end_time = datetime.strptime(f"{end_parts[0]:0>2}:{end_parts[1]:0>2}", "%H:%M").time()
            
            # 处理跨天的情况
            if start_time <= end_time:
                # 同一天内
                return start_time <= current_time <= end_time
            else:
                # 跨天
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            self.log_message.emit(f"⚠️ 工作时间检查异常: {e}，默认为工作时间")
            return True
    
    def is_in_shutdown_window(self):
        """检查当前是否在关机时间窗口内（工作结束时间到工作结束时间+5分钟）"""
        try:
            current_time = datetime.now().time()
            
            # 解析结束时间
            end_parts = self.work_end_time.split(':')
            if len(end_parts) != 2:
                return False
            
            end_hour = int(end_parts[0])
            end_minute = int(end_parts[1])
            
            # 计算结束时间和结束时间+5分钟
            end_time = datetime.strptime(f"{end_hour:02d}:{end_minute:02d}", "%H:%M").time()
            
            # 计算结束时间+5分钟
            end_minute_plus_5 = end_minute + 5
            end_hour_plus_5 = end_hour
            if end_minute_plus_5 >= 60:
                end_minute_plus_5 -= 60
                end_hour_plus_5 += 1
                if end_hour_plus_5 >= 24:
                    end_hour_plus_5 -= 24
            
            end_time_plus_5 = datetime.strptime(f"{end_hour_plus_5:02d}:{end_minute_plus_5:02d}", "%H:%M").time()
            
            # 检查是否在关机窗口内
            if end_time <= end_time_plus_5:
                # 同一天内
                return end_time <= current_time <= end_time_plus_5
            else:
                # 跨天
                return current_time >= end_time or current_time <= end_time_plus_5
                
        except Exception as e:
            self.log_message.emit(f"⚠️ 关机时间检查异常: {e}")
            return False
    
    def shutdown_computer(self):
        """关闭计算机"""
        try:
            self.log_message.emit("🔌 [DMB000X] 执行自动关机...")
            import subprocess
            subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
            self.log_message.emit("✅ [DMB000X] 关机命令已发送，10秒后关机")
            return True
        except Exception as e:
            self.log_message.emit(f"❌ [DMB000X] 关机失败: {e}")
            return False
    
    def initialize_dual_windows(self):
        """初始化双端窗口：检查余额"""
        try:
            self.log_message.emit("🔄 [DMB000X] 开始双端初始化...")
            
            # 1. 检查主端余额
            self.log_message.emit("💰 检查主端账户余额...")
            self.manager.focus_main()
            time.sleep(0.5)  # 窗口切换后等待
            main_balance = self.main_delta.get_balance(where="market", loop=True)
            if main_balance is not None:
                self.main_initial_balance = main_balance
                self.main_current_balance = main_balance
                self.log_message.emit(f"💰 主端初始余额: {main_balance:,}")
            else:
                self.log_message.emit("❌ 主端余额获取失败")
                return False
            
            # 2. 检查辅端余额
            self.log_message.emit("💰 检查辅端账户余额...")
            self.manager.focus_aux()
            time.sleep(0.5)  # 窗口切换后等待
            auxiliary_balance = self.auxiliary_delta.get_balance(where="market", loop=True)
            if auxiliary_balance is not None:
                self.auxiliary_initial_balance = auxiliary_balance
                self.auxiliary_current_balance = auxiliary_balance
                self.log_message.emit(f"💰 辅端初始余额: {auxiliary_balance:,}")
            else:
                self.log_message.emit("❌ 辅端余额获取失败")
                return False
            
            self.balance_initialized = True
            self.log_message.emit("✅ [DMB000X] 双端初始化完成")
            self.log_message.emit(f"📊 配置参数:")
            self.log_message.emit(f"   目标价格: {self.target_price}")
            self.log_message.emit(f"   辅端刷新数量: {self.auxiliary_refresh_quantity}")
            self.log_message.emit(f"   主端购买数量: {self.main_purchase_quantity}")
            self.log_message.emit(f"   点击次数: {self.click_times}")
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ [DMB000X] 双端初始化异常: {e}")
            return False
    
    def get_auxiliary_balance_safe(self, debug=True):
        """安全获取辅端余额"""
        try:
            if debug:
                # 调试模式：使用return_json=True获取详细信息
                debug_info = self.auxiliary_delta.get_balance(where="market", loop=True, return_json=True)
                
                if debug_info and debug_info.get("success"):
                    balance = debug_info["balance"]
                    # 只保存图片，不保存JSON
                    self._save_auxiliary_balance_debug_image(debug_info)
                    
                    if self.balance_initialized:
                        self.auxiliary_current_balance = balance
                        # 监控辅端余额变动
                        self._monitor_auxiliary_balance_change(balance)
                    return balance
                else:
                    self.log_message.emit("⚠️ 辅端余额获取失败")
                    # 即使失败也保存调试图片
                    if debug_info:
                        self._save_auxiliary_balance_debug_image(debug_info)
                    return None
            else:
                # 非调试模式：使用普通方式
                balance = self.auxiliary_delta.get_balance(where="market", loop=True)
                
                if balance is not None:
                    if self.balance_initialized:
                        self.auxiliary_current_balance = balance
                        # 监控辅端余额变动
                        self._monitor_auxiliary_balance_change(balance)
                    return balance
                else:
                    self.log_message.emit("⚠️ 辅端余额获取失败")
                    return None
                    
        except Exception as e:
            self.log_message.emit(f"❌ 辅端余额获取异常: {e}")
            return None
    
    def get_main_balance_safe(self):
        """安全获取主端余额"""
        try:
            balance = self.main_delta.get_balance(where="market", loop=True)
            if balance is not None:
                if self.balance_initialized:
                    self.main_current_balance = balance
                    # 监控主端余额变动
                    self._monitor_main_balance_change(balance)
                return balance
            else:
                self.log_message.emit("⚠️ 主端余额获取失败")
                return None
        except Exception as e:
            self.log_message.emit(f"❌ 主端余额获取异常: {e}")
            return None
    
    def is_balance_reasonable(self, price_diff):
        """检查价格差是否合理"""
        min_reasonable = self.auxiliary_refresh_quantity * self.min_price_threshold
        max_reasonable = self.auxiliary_refresh_quantity * 900  # 假设最高单价900
        return min_reasonable <= price_diff <= max_reasonable
    
    def auxiliary_refresh_phase(self):
        """辅端刷新阶段：31发购买检测价格"""
        try:
            # 聚焦到辅端窗口
            self.log_message.emit("🔄 切换到辅端窗口进行刷新...")
            if not self.manager.focus_aux():
                self.log_message.emit("⚠️ 辅端窗口聚焦失败，但继续尝试操作")
            
            # 窗口切换后缓冲延迟
            time.sleep(0.1)
            
            # 获取刷新前余额
            balance_before = self.get_auxiliary_balance_safe()
            if balance_before is None:
                self.log_message.emit("❌ 无法获取辅端刷新前余额")
                return None, None
            
            # 执行31发购买（刷新）
            success = self.auxiliary_delta.buy_in_market(
                buyin=self.auxiliary_refresh_quantity,
                maxin=self.max_quantity,
                times=1,
                buy=True,
                loop=True
            )
            
            if not success:
                self.log_message.emit("❌ 辅端刷新购买失败")
                return None, None
            
            # 添加31发点击延迟
            time.sleep(0.3)
            
            # 获取刷新后余额
            balance_after = self.get_auxiliary_balance_safe()
            if balance_after is None:
                self.log_message.emit("❌ 无法获取辅端刷新后余额")
                return None, None
            
            # 计算价格差和单价
            price_diff = balance_before - balance_after
            unit_price = price_diff / self.auxiliary_refresh_quantity
            
            return unit_price, price_diff
            
        except Exception as e:
            self.log_message.emit(f"❌ 辅端刷新阶段异常: {e}")
            return None, None
    
    def main_purchase_phase(self):
        """主端购买阶段：200发批量购买"""
        try:
            # 聚焦到主端窗口
            self.log_message.emit("💰 切换到主端窗口进行购买...")
            if not self.manager.focus_main():
                self.log_message.emit("⚠️ 主端窗口聚焦失败，但继续尝试操作")
            
            # 窗口切换后缓冲延迟
            time.sleep(0.1)
            
            # 获取购买前余额
            balance_before = self.get_main_balance_safe()
            if balance_before is None:
                self.log_message.emit("❌ 无法获取主端购买前余额")
                return False
            
            # 执行200发批量购买
            success = self.main_delta.buy_in_market(
                buyin=self.main_purchase_quantity,
                maxin=self.max_quantity,
                times=self.click_times,
                buy=True,
                loop=True
            )
            
            if success:
                # 获取购买后余额
                balance_after = self.get_main_balance_safe()
                if balance_after is not None:
                    purchase_cost = balance_before - balance_after
                    actual_unit_price = purchase_cost / (self.main_purchase_quantity * self.click_times)
                    
                    # 记录购买数据
                    self.purchase_cost_total += purchase_cost
                    self.purchase_cost_records.append({
                        'cycle': self.refresh_count,
                        'cost': purchase_cost,
                        'expected_unit_price': 0,  # 这里没有预期单价
                        'actual_unit_price': actual_unit_price,
                        'quantity_per_click': self.main_purchase_quantity,
                        'effective_clicks': self.click_times,
                        'total_quantity': self.main_purchase_quantity * self.click_times,
                        'balance_before': balance_before,
                        'balance_after': balance_after
                    })
                    
                    self.log_message.emit(f"💰 第{self.refresh_count}次主端购买 | 单价: {actual_unit_price:.1f} | 购买次数: {self.purchase_count}")
                
                self.purchase_count += self.click_times
                return True
            else:
                self.log_message.emit("❌ 主端购买失败")
                return False
                
        except Exception as e:
            self.log_message.emit(f"❌ 主端购买阶段异常: {e}")
            return False
    
    def write_log(self, cycle, balance_before, balance_after, unit_price, status):
        """写入日志记录"""
        try:
            # 这里可以实现具体的日志写入逻辑
            pass
        except Exception as e:
            self.log_message.emit(f"⚠️ 日志写入失败: {e}")
    
    def _monitor_auxiliary_balance_change(self, current_balance):
        """监控辅端余额变动，连续10次不变时切换为纯主端模式"""
        if self.auxiliary_last_balance is None:
            # 首次记录余额
            self.auxiliary_last_balance = current_balance
            self.auxiliary_balance_unchanged_count = 0
            return
        
        if current_balance == self.auxiliary_last_balance:
            # 余额未变动
            self.auxiliary_balance_unchanged_count += 1
            
            if self.auxiliary_balance_unchanged_count >= 10 and not self.main_only_mode:
                # 连续10次余额不变，切换为纯主端模式
                self.main_only_mode = True
                self.log_message.emit("🔄 [DMB000X] 辅端余额连续10次未变动，切换为纯主端模式")
                self.log_message.emit("📋 [DMB000X] 现在将使用主端进行刷新和购买操作")
        else:
            # 余额有变动，重置计数器
            if self.auxiliary_balance_unchanged_count > 0:
                self.log_message.emit(f"✅ [DMB000X] 辅端余额恢复变动，重置监控计数器")
            self.auxiliary_balance_unchanged_count = 0
            self.auxiliary_last_balance = current_balance
    
    def _monitor_main_balance_change(self, current_balance):
        """监控主端余额变动，连续10次不变时结束程序"""
        if self.main_last_balance is None:
            # 首次记录余额
            self.main_last_balance = current_balance
            self.main_balance_unchanged_count = 0
            return
        
        if current_balance == self.main_last_balance:
            # 余额未变动
            self.main_balance_unchanged_count += 1
            
            if self.main_balance_unchanged_count >= 10:
                # 连续10次余额不变，结束程序
                self.log_message.emit("🏪 [DMB000X] 主端余额连续10次未变动，可能仓库已满")
                self.log_message.emit("🔚 [DMB000X] 程序执行结束")
                
                # 检查是否需要自动关机
                if self.auto_shutdown:
                    self.log_message.emit("🔌 [DMB000X] 启用自动关机，准备关闭电脑...")
                    if self.shutdown_computer():
                        self.log_message.emit("✅ [DMB000X] 自动关机命令已执行")
                    else:
                        self.log_message.emit("❌ [DMB000X] 自动关机失败")
                
                # 停止程序
                self.should_stop = True
                return
        else:
            # 余额有变动，重置计数器
            if self.main_balance_unchanged_count > 0:
                self.log_message.emit(f"✅ [DMB000X] 主端余额恢复变动，重置监控计数器")
            self.main_balance_unchanged_count = 0
            self.main_last_balance = current_balance
    
    def _save_auxiliary_balance_debug_image(self, debug_info):
        """保存辅端余额OCR识别调试图片"""
        try:
            import os
            import base64
            from datetime import datetime
            
            # 创建调试目录
            debug_dir = os.path.join("log", "images", "auxiliary_balance")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 获取当前时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            
            # 准备文件名
            balance = debug_info.get("balance", "unknown")
            success_status = "success" if debug_info.get("success") else "failed"
            
            # 保存截图
            if debug_info.get("screenshot_base64"):
                image_filename = f"auxiliary_balance_{balance}_{success_status}_{timestamp}.png"
                image_filepath = os.path.join(debug_dir, image_filename)
                
                # 解码并保存图片
                image_data = base64.b64decode(debug_info["screenshot_base64"])
                with open(image_filepath, "wb") as f:
                    f.write(image_data)
                
                # 静默保存，不输出提示信息
            else:
                # 没有截图数据时也不输出错误信息
                pass
                
        except Exception as e:
            # 静默处理保存失败，不输出提示
            pass
    
    def _collect_task_statistics(self):
        """收集任务统计数据"""
        return {
            'refresh_count': self.refresh_count,
            'purchase_count': self.purchase_count,
            'low_price_found_count': self.low_price_found_count,
            'zero_price_diff_count': self.zero_price_diff_count,
            'refresh_cost_total': self.refresh_cost_total,
            'purchase_cost_total': self.purchase_cost_total,
            'main_initial_balance': self.main_initial_balance,
            'main_current_balance': self.main_current_balance,
            'auxiliary_initial_balance': self.auxiliary_initial_balance,
            'auxiliary_current_balance': self.auxiliary_current_balance,
            'main_balance_change': (self.main_initial_balance - self.main_current_balance) if self.main_initial_balance and self.main_current_balance else 0,
            'auxiliary_balance_change': (self.auxiliary_initial_balance - self.auxiliary_current_balance) if self.auxiliary_initial_balance and self.auxiliary_current_balance else 0
        }
    
    def run(self):
        """主运行逻辑"""
        try:
            self.log_message.emit("🚀 [DMB000X] 双端满仓自定义子弹行为开始运行")
            self.log_message.emit(f"📋 配置信息: 目标价格≤{self.target_price}, 辅端{self.auxiliary_refresh_quantity}发刷新, 主端{self.main_purchase_quantity}发×{self.click_times}次购买")
            self.status_changed.emit("running")
            
            # 双端初始化
            if not self.initialize_dual_windows():
                self.log_message.emit("❌ [DMB000X] 双端初始化失败，程序退出")
                return
            
            # 主循环
            while not self.should_stop:
                try:
                    # 检查工作时间
                    if not self.is_in_work_time():
                        self.log_message.emit("⏰ [DMB000X] 当前不在工作时间内，等待...")
                        time.sleep(60)  # 等待1分钟后重新检查
                        continue
                    
                    # 检查关机时间窗口
                    if self.is_in_shutdown_window() and self.auto_shutdown:
                        self.log_message.emit("🔌 [DMB000X] 检测到关机时间窗口")
                        if self.shutdown_computer():
                            return
                        else:
                            self.log_message.emit("⚠️ [DMB000X] 自动关机失败，程序继续运行")
                    
                    # 刷新计数
                    self.refresh_count += 1
                    
                    # 辅端刷新阶段：31发检测价格
                    self.current_phase = "辅端刷新阶段"
                    unit_price, price_diff = self.auxiliary_refresh_phase()
                    
                    # 检查是否因余额监控而停止
                    if self.should_stop:
                        break
                    
                    if unit_price is None or price_diff is None:
                        self.log_message.emit(f"❌ 第{self.refresh_count}次辅端刷新失败")
                        time.sleep(self.refresh_delay)
                        continue
                    
                    # 检查价格差为0的连续情况（可能是仓库满了）
                    if price_diff == 0:
                        self.zero_price_diff_count += 1
                        self.log_message.emit(f"⚠️ 检测到价格差为0，连续次数: {self.zero_price_diff_count}/10")
                        
                        if self.zero_price_diff_count >= 10:
                            self.log_message.emit("🏪 连续10次价格差为0，可能仓库已满，退出循环")
                            self.should_stop = True
                            break
                    else:
                        # 价格差不为0，重置计数器
                        if self.zero_price_diff_count > 0:
                            self.log_message.emit(f"✅ 价格差恢复正常，重置连续0次计数器")
                            self.zero_price_diff_count = 0
                    
                    # 检查价格合理性
                    if not self.is_balance_reasonable(price_diff):
                        self.log_message.emit(f"🔄 第{self.refresh_count}次刷新 | 价格不合理: {unit_price:.1f} (余额变动: {price_diff})")
                        time.sleep(self.refresh_delay)
                        continue
                    
                    # 记录刷新数据
                    self.refresh_cost_total += price_diff
                    self.refresh_cost_records.append({
                        'cycle': self.refresh_count,
                        'cost': price_diff,
                        'unit_price': unit_price,
                        'quantity': self.auxiliary_refresh_quantity,
                        'balance_before': self.auxiliary_current_balance + price_diff,
                        'balance_after': self.auxiliary_current_balance
                    })
                    
                    # 判断是否进入购买阶段
                    if unit_price <= self.target_price and unit_price >= self.min_price_threshold:
                        # 价格合理，进入主端购买阶段
                        self.current_phase = "主端购买阶段"
                        self.low_price_found_count += 1
                        
                        if self.main_purchase_phase():
                            self.write_log(self.refresh_count, 0, 0, unit_price, f"购买成功({self.main_purchase_quantity}x{self.click_times})")
                        else:
                            self.write_log(self.refresh_count, 0, 0, unit_price, "购买失败")
                        
                        # 检查是否因余额监控而停止
                        if self.should_stop:
                            break
                    else:
                        # 价格过高，继续刷新
                        self.log_message.emit(f"🔄 第{self.refresh_count}次刷新 | 单价 {unit_price:.1f} >= 目标: {self.target_price} (数量: {self.auxiliary_refresh_quantity}, 余额变动: {price_diff})")
                        self.write_log(self.refresh_count, 0, 0, unit_price, "价格过高")
                    
                    # 检查停止标志
                    if self.should_stop:
                        break
                    
                    # 等待下次刷新（分段检查停止标志）
                    if not self.should_stop:
                        self.log_message.emit(f"⏳ 等待 {self.refresh_delay} 秒后进行下次刷新...")
                        # 分段等待，提高响应性
                        wait_segments = max(1, int(self.refresh_delay * 10))  # 分成10段
                        segment_time = self.refresh_delay / wait_segments
                        
                        for _ in range(wait_segments):
                            if self.should_stop:
                                break
                            time.sleep(segment_time)
                
                except Exception as e:
                    self.log_message.emit(f"❌ [DMB000X] 主循环异常: {e}")
                    time.sleep(5)  # 异常后等待5秒
            
        except Exception as e:
            self.log_message.emit(f"❌ [DMB000X] 运行异常: {e}")
        
        finally:
            # 结束处理
            self.current_phase = "已结束"
            self.status_changed.emit("stopped")
            
            # 收集统计数据
            statistics = self._collect_task_statistics()
            
            # 记录任务完成
            if self.task_logger:
                self.task_logger.add_task_record(
                    script_id="DMB000X",
                    task_data=statistics
                )
            
            # 输出统计信息
            self.log_message.emit("📊 [DMB000X] 任务统计:")
            self.log_message.emit(f"   刷新次数: {statistics['refresh_count']}")
            self.log_message.emit(f"   购买次数: {statistics['purchase_count']}")
            self.log_message.emit(f"   发现低价: {statistics['low_price_found_count']}")
            self.log_message.emit(f"   主端余额变化: {statistics['main_balance_change']:,}")
            self.log_message.emit(f"   辅端余额变化: {statistics['auxiliary_balance_change']:,}")
            self.log_message.emit("🏁 [DMB000X] 双端满仓自定义子弹行为结束")

def get_behavior_class():
    """返回行为类"""
    return DualMarketBotBehavior
