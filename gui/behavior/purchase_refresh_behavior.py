# -*- coding: utf-8 -*-
"""
购买刷新单端自定义子弹行为模块
通过购买机制检测低价子弹并批量购买
"""

# 行为信息定义
BEHAVIOR_INFO = {
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
    """购买刷新单端行为类"""
    
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
        
        # 控制变量
        self.should_stop = False
        self.is_running = False
        self.current_phase = "刷新阶段"  # "刷新阶段" 或 "购买阶段"
        
        # 统计变量
        self.refresh_count = 0
        self.purchase_count = 0
        self.low_price_found_count = 0
        
        # 日志文件
        self.log_file = f"purchase_refresh_{int(time.time())}.csv"
        
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
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ Delta初始化失败: {e}")
            return False
    
    def is_balance_reasonable(self, price_diff):
        """
        判断余额差值是否合理
        合理范围：最低阈值 <= price_diff <= 2倍目标价格
        """
        min_reasonable = self.min_price_threshold
        max_reasonable = self.target_price * 2
        
        is_reasonable = min_reasonable <= price_diff <= max_reasonable
        self.log_message.emit(f"💡 价格合理性检查: {price_diff} (合理范围: {min_reasonable}-{max_reasonable}) -> {'✅合理' if is_reasonable else '❌不合理'}")
        
        return is_reasonable
    
    def is_in_work_time(self):
        """
        检查当前是否在工作时间内
        工作时间：每天00:00到05:15
        Returns:
            bool: True表示在工作时间内，False表示不在
        """
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # 工作时间：00:00 到 05:15
        if current_hour < 5 or (current_hour == 5 and current_minute <= 15):
            return True
        else:
            return False
    
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
    
    def get_balance_safe(self):
        """安全获取余额（使用交易行位置）"""
        try:
            balance = self.delta.get_balance(where="market", loop=True)
            if balance is not None:
                self.log_message.emit(f"💰 当前余额: {balance}")
                return balance
            else:
                self.log_message.emit("⚠️ 余额获取失败")
                return None
        except Exception as e:
            self.log_message.emit(f"❌ 余额获取异常: {e}")
            return None
    
    def refresh_phase_buy(self):
        """刷新阶段购买（点击最左侧最小值）"""
        try:
            # 确保刷新数量至少为1
            actual_refresh_quantity = max(1, self.refresh_quantity)
            
            success = self.delta.buy_in_market(
                buyin=actual_refresh_quantity,  # 使用配置的刷新数量
                maxin=999,
                times=1,
                delay=0.07,
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
            self.log_message.emit(f"💰 开始购买阶段: 数量={self.purchase_quantity}, 点击次数={self.click_times}")
            
            success = self.delta.buy_in_market(
                buyin=self.purchase_quantity,
                maxin=999,
                times=self.click_times,
                delay=0.07,
                buy=True,
                loop=True
            )
            
            if success:
                self.log_message.emit(f"✅ 购买阶段完成: {self.purchase_quantity}x{self.click_times}")
                self.purchase_count += self.click_times
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
                maxin=999,
                times=1,
                delay=0.07,
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
    
    def write_log(self, check_num, balance_before, balance_after, price_diff, action):
        """写入日志文件"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                if check_num == 1:
                    # 写入表头
                    f.write("检测次数,购买前余额,购买后余额,价格差,动作,时间\n")
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{check_num},{balance_before},{balance_after},{price_diff},{action},{timestamp}\n")
                
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
            
            self.log_message.emit("🚀 购买刷新行为开始运行")
            self.log_message.emit("⚠️ 请确保已手动切换到期望购买的子弹类型")
            self.log_message.emit("📋 流程说明: 刷新阶段 → 价格检测 → 购买阶段（如满足条件）→ 循环")
            self.log_message.emit("⏰ 工作时间: 每天 00:00 - 05:15")
            
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
                        
                        # 步骤3: 计算价格差
                        price_diff = balance_before - balance_after
                        self.log_message.emit(f"💸 检测到价格: {price_diff} (余额: {balance_before} → {balance_after})")
                        
                        # 步骤4: 价格合理性检查
                        if self.is_balance_reasonable(price_diff):
                            # 合理的价格差，继续判断是否满足购买条件
                            if price_diff < self.target_price:
                                # ============ 第二阶段：购买阶段 ============
                                self.current_phase = "购买阶段"
                                self.log_message.emit(f"🎉 发现低价子弹! 价格: {price_diff} < 目标: {self.target_price}")
                                self.log_message.emit("💰 进入购买阶段...")
                                self.low_price_found_count += 1
                                
                                # 执行批量购买
                                if self.purchase_phase_buy():
                                    self.write_log(self.refresh_count, balance_before, balance_after, price_diff, f"购买成功({self.purchase_quantity}x{self.click_times})")
                                    self.log_message.emit("✅ 购买阶段完成，准备下次刷新")
                                else:
                                    self.write_log(self.refresh_count, balance_before, balance_after, price_diff, "购买失败")
                                    self.log_message.emit("❌ 购买阶段失败")
                                
                                # 重置为最小值，准备下次刷新阶段
                                self.reset_to_minimum()
                            else:
                                self.log_message.emit(f"📊 价格过高: {price_diff} >= 目标: {self.target_price}，继续刷新")
                                self.write_log(self.refresh_count, balance_before, balance_after, price_diff, "价格过高")
                                
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
            self.is_running = False
            self.status_update.emit("已停止")
            self.status_changed.emit("stopped")  # 发送状态变更信号
            self.finished_signal.emit(not self.should_stop)  # True表示正常完成，False表示被中断
            self.log_message.emit("🏁 购买刷新行为已停止")
    
    def stop(self):
        """停止行为"""
        self.should_stop = True
        self.log_message.emit("🛑 正在停止购买刷新行为...")
        
        # 等待线程结束
        if self.isRunning():
            self.wait(5000)  # 等待5秒
        
        self.log_message.emit("✅ 购买刷新行为已完全停止")
