# -*- coding: utf-8 -*-
"""
购买刷新单端自定义子弹行为模块 - SMB000X (重构版)
通过购买机制检测低价子弹并批量购买
代码ID: SMB000X (Single Market Bot)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from Behavior import Behavior, LogLevel
from base.decorators import protocol_handler

import time
import csv
import os
from datetime import datetime, timedelta

# 行为信息定义
BEHAVIOR_INFO = {
    "code_id": "SMB000X",  # 内部代码ID
    "title": "购买刷新单端自定义子弹行为",
    "description": "通过实际购买1个子弹来检测价格，发现低价时批量购买。需要用户手动切换到期望购买的子弹类型。",
    "version": "2.0.0",  # 重构版本
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
            "default": 1,
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
            "description": "批量购买时每次购买的数量"
        },
        "click_times": {
            "type": "int",
            "label": "购买时点击次数",
            "default": 5,
            "min": 1,
            "max": 20,
            "description": "批量购买时的点击次数"
        },
        "max_quantity": {
            "type": "int",
            "label": "最大购买数量",
            "default": 200,
            "min": 10,
            "max": 999,
            "description": "单次批量购买的最大数量限制"
        },
        "work_start_hour": {
            "type": "int",
            "label": "工作开始时间-时",
            "default": 0,
            "min": 0,
            "max": 24,
            "description": "工作开始时间的小时部分 (0-24，24会自动转为23:59)"
        },
        "work_start_minute": {
            "type": "int",
            "label": "工作开始时间-分",
            "default": 0,
            "min": 0,
            "max": 59,
            "description": "工作开始时间的分钟部分 (0-59)"
        },
        "work_end_hour": {
            "type": "int",
            "label": "工作结束时间-时",
            "default": 5,
            "min": 0,
            "max": 24,
            "description": "工作结束时间的小时部分 (0-24，24会自动转为23:59)"
        },
        "work_end_minute": {
            "type": "int",
            "label": "工作结束时间-分",
            "default": 15,
            "min": 0,
            "max": 59,
            "description": "工作结束时间的分钟部分 (0-59)"
        },
        "auto_shutdown": {
            "type": "bool",
            "label": "自动关机",
            "default": False,
            "description": "工作完成后是否自动关机"
        },
        "debug_mode": {
            "type": "int",
            "label": "调试模式",
            "default": 0,
            "min": 0,
            "max": 2,
            "description": "0=关闭, 1=简化debug(隐藏底层函数), 2=详细debug(显示所有函数)"
        }
    }
}

class PurchaseRefreshBehavior(Behavior):
    """购买刷新单端行为类 - SMB000X (重构版)"""
    
    @classmethod
    def args(cls):
        """定义参数和UI配置"""
        return {
            'target_price': {
                'type': 'int',
                'label': '目标价格阈值',
                'default': 480,
                'description': '低于此价格即为有效，进入购买阶段'
            },
            'min_price_threshold': {
                'type': 'int',
                'label': '最低价格阈值',
                'default': 1,
                'description': '低于此价格认为是识别错误'
            },
            'refresh_delay': {
                'type': 'float',
                'label': '购买刷新延迟(秒)',
                'default': 3.0,
                'description': '刷新阶段每次检测之间的延迟时间'
            },
            'refresh_quantity': {
                'type': 'int',
                'label': '购买刷新时的数量',
                'default': 1,
                'description': '刷新阶段购买的数量（通常为1）'
            },
            'purchase_quantity': {
                'type': 'int',
                'label': '购买时一次购买的数量',
                'default': 2,
                'description': '批量购买时每次购买的数量'
            },
            'click_times': {
                'type': 'int',
                'label': '购买时点击次数',
                'default': 5,
                'description': '批量购买时的点击次数'
            },
            'max_quantity': {
                'type': 'int',
                'label': '最大购买数量',
                'default': 200,
                'description': '单次批量购买的最大数量限制'
            },
            'work_start_hour': {
                'type': 'int',
                'label': '工作开始时间-时',
                'default': 0,
                'min': 0,
                'max': 24,
                'description': '工作开始时间的小时部分 (0-24，24会自动转为23:59)'
            },
            'work_start_minute': {
                'type': 'int',
                'label': '工作开始时间-分',
                'default': 0,
                'min': 0,
                'max': 59,
                'description': '工作开始时间的分钟部分 (0-59)'
            },
            'work_end_hour': {
                'type': 'int',
                'label': '工作结束时间-时',
                'default': 5,
                'min': 0,
                'max': 24,
                'description': '工作结束时间的小时部分 (0-24，24会自动转为23:59)'
            },
            'work_end_minute': {
                'type': 'int',
                'label': '工作结束时间-分',
                'default': 15,
                'min': 0,
                'max': 59,
                'description': '工作结束时间的分钟部分 (0-59)'
            },
            'auto_shutdown': {
                'type': 'bool',
                'label': '自动关机',
                'default': False,
                'description': '工作完成后是否自动关机'
            },
            'debug_mode': {
                'type': 'int',
                'label': '调试模式',
                'default': 0,
                'min': 0,
                'max': 2,
                'description': '0=关闭, 1=简化debug(隐藏底层函数), 2=详细debug(显示所有函数)'
            }
        }
    
    def init_config(self):
        """调用基类自动参数解析"""
        # 基类会自动调用args()并设置所有参数为实例属性
        super().init_config()
        
        # 处理24小时的特殊情况
        if self.work_start_hour == 24:
            self.work_start_hour = 23
            self.work_start_minute = 59
        if self.work_end_hour == 24:
            self.work_end_hour = 23
            self.work_end_minute = 59
        
        # 构建工作时间字符串（用于显示和内部使用）
        self.work_start_time = f"{self.work_start_hour:02d}:{self.work_start_minute:02d}"
        self.work_end_time = f"{self.work_end_hour:02d}:{self.work_end_minute:02d}"
        
        # 发送配置信息
        self.send_log(LogLevel.INFO, f"📋 配置: 目标价格≤{self.target_price}, 刷新{self.refresh_quantity}发, 购买{self.purchase_quantity}发×{self.click_times}次, 工作时间{self.work_start_time}-{self.work_end_time}")
        
        # 调试模式信息
        if self.debug_mode == 0:
            self.send_log(LogLevel.INFO, "📝 普通模式，显示所有日志")
        elif self.debug_mode == 1:
            self.debug_log(LogLevel.INFO, f"🔍 简化调试模式已开启（隐藏底层函数）")
            self.debug_log(LogLevel.INFO, f"🔧 配置参数: target_price={self.target_price}, refresh_quantity={self.refresh_quantity}, purchase_quantity={self.purchase_quantity}")
        elif self.debug_mode == 2:
            self.debug_log(LogLevel.INFO, f"🔍 详细调试模式已开启（显示所有函数）")
            self.debug_log(LogLevel.INFO, f"🔧 配置参数: target_price={self.target_price}, refresh_quantity={self.refresh_quantity}, purchase_quantity={self.purchase_quantity}")
    
    def init_behavior(self):
        """初始化行为特定逻辑"""
        # 状态变量
        self.current_phase = "初始化"  # "刷新阶段" 或 "购买阶段"
        
        # 统计变量
        self.refresh_count = 0
        self.purchase_count = 0
        self.total_purchased = 0
        self.refresh_cost_total = 0
        self.purchase_cost_total = 0
        
        # 余额跟踪
        self.initial_balance = None
        self.current_balance = None
        self.balance_unchanged_count = 0
        self.last_balance = None
        
        # 记录列表
        self.refresh_cost_records = []
        self.purchase_cost_records = []
        
        # 价格记录相关
        self.detection_count = 0  # 检测次数计数器
        self.csv_file_path = None
        self.init_price_logging()
        
        self.system_log(LogLevel.SUCCESS, "🎯 SMB000X行为初始化完成")
        
        # 显示Delta状态
        delta_info = self.get_delta_info()
        self.system_log(LogLevel.INFO, f"🔧 {delta_info}")
        
        if not self.is_delta_ready():
            self.system_log(LogLevel.ERROR, "❌ Delta实例未就绪，无法执行游戏操作")
    
    def main_logic(self):
        """主业务逻辑"""
        try:
            self.system_log(LogLevel.SUCCESS, "🚀 SMB000X开始执行")
            self.system_log(LogLevel.INFO, "📋 执行流程: 初始化 → 刷新阶段 → 购买阶段")
            
            # 初始化余额
            if not self.initialize_balance():
                return self.exit_behavior("余额初始化失败", success=False)
            
            # 主循环
            while not self.is_stopped():
                # 检查工作时间
                if not self.is_in_work_time():
                    self.send_log(LogLevel.INFO, "⏰ 当前不在工作时间内，等待...")
                    self.segmented_sleep(60)  # 等待1分钟后重新检查
                    continue
                
                # 检查关机时间窗口
                if self.is_in_shutdown_window() and self.auto_shutdown:
                    return self.exit_behavior("到达关机时间", success=True)
                
                # 执行一轮刷新购买流程
                cycle_result = self.execute_refresh_purchase_cycle()
                success = cycle_result.success if cycle_result else False
                
                if success:
                    self.increment_success()
                    self.send_log(LogLevel.SUCCESS, "✅ 一轮刷新购买完成")
                else:
                    self.increment_error()
                    self.send_log(LogLevel.WARNING, "⚠️ 一轮刷新购买失败")
                
                # 检查余额变化 - 连续20次余额不变则退出
                if not self.monitor_balance_change():
                    return self.exit_behavior("余额未变化", success=True)
                
                # 等待下次循环
                self.segmented_sleep(self.refresh_delay)
            
            # 正常结束循环后的处理（用户手动停止或正常完成）
            reason = "用户退出" if self.is_stopped() else "正常完成"
            return self.exit_behavior(reason, success=True)
            
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 主逻辑执行异常: {e}")
            return self.exit_behavior(f"异常: {e}", success=False)
    
    @protocol_handler()
    def execute_refresh_purchase_cycle(self, protocol):
        """执行一轮刷新购买循环"""
        try:
            self.increment_cycle()
            
            # 刷新阶段
            self.current_phase = "刷新阶段"
            refresh_result = self.refresh_phase()
            # 自动合并（self 的方法会自动合并到 protocol）
            
            # 检查刷新是否成功
            if not refresh_result or not refresh_result.success:
                return False
            
            # 从protocol中获取unit_price
            unit_price = getattr(refresh_result, 'unit_price', None)
            
            if unit_price is None:
                return False
            
            # 判断是否进入购买阶段
            if unit_price <= self.target_price and unit_price >= self.min_price_threshold:
                # 价格合理，进入购买阶段
                self.current_phase = "购买阶段"
                purchase_result = self.purchase_phase(unit_price)
                # 自动合并（self 的方法会自动合并到 protocol）
                purchase_success = purchase_result.success if purchase_result else False
                
                # 打印完整的调用链（从刷新到购买完成）- 根据 debug_mode 选择模式
                if self.debug_mode > 0:  # debug_mode=1 或 2
                    mode = "simple" if self.debug_mode == 1 else "detail"
                    lines = self.formatter.format_timing_records(
                        refresh_result,  # 使用 refresh_result 包含刷新和购买的完整调用链
                        title=f"第{self.refresh_count}次完整流程调用链 (刷新→购买，单价: {unit_price:.1f})",
                        mode=mode
                    )
                    for line in lines:
                        self.debug_log(LogLevel.INFO, line)
                
                return purchase_success
            else:
                # 价格不合理，只执行了刷新阶段，打印刷新阶段的调用链
                # 根据 debug_mode 选择模式
                if self.debug_mode > 0:  # debug_mode=1 或 2
                    mode = "simple" if self.debug_mode == 1 else "detail"
                    lines = self.formatter.format_timing_records(
                        refresh_result,  # 使用 refresh_result 只看刷新阶段
                        title=f"第{self.refresh_count}次刷新阶段调用链 (单价: {unit_price:.1f})",
                        mode=mode
                    )
                    for line in lines:
                        self.debug_log(LogLevel.INFO, line)
                
                # 价格不合理，继续刷新
                if unit_price < self.min_price_threshold:
                    self.send_log(LogLevel.WARNING, f"⚠️ 价格过低: {unit_price:.1f} < {self.min_price_threshold} (可能识别错误)")
                else:
                    self.send_log(LogLevel.DEBUG, f"🔄 价格过高: {unit_price:.1f} > {self.target_price}")
                
                return False
                
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 刷新购买循环异常: {e}")
            return False
    
    def initialize_balance(self):
        """初始化余额跟踪"""
        try:
            # 获取Delta实例
            delta = self.get_any_delta()
            if not delta:
                self.send_log(LogLevel.ERROR, "❌ 无法获取Delta实例")
                return False
            
            self.send_log(LogLevel.INFO, "💰 正在获取初始余额...")
            
            balance_result = delta.get_balance(where="market", loop=True)
            if not balance_result.success:
                self.send_log(LogLevel.ERROR, "❌ 无法获取初始余额")
                return False
            
            # 初始化阶段不打印调用链
            
            balance = balance_result.balance
            self.initial_balance = balance
            self.current_balance = balance
            self.last_balance = balance
            
            self.log_with_stats(LogLevel.SUCCESS, f"💰 初始余额: {balance:,}", 
                               initial_balance=balance)
            self.debug_log(LogLevel.INFO, f"🔍 初始化余额设置: {balance:,}")
            return True
            
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 余额初始化异常: {e}")
            return False
    
    @protocol_handler()
    def refresh_phase(self, protocol):
        """刷新阶段 - 购买少量子弹检测价格"""
        try:
            # 获取Delta实例
            delta = self.get_any_delta()
            if not delta:
                self.send_log(LogLevel.ERROR, "❌ 无法获取Delta实例")
                return False
            
            self.refresh_count += 1
            
            # 获取刷新前余额
            self.debug_log(LogLevel.INFO, f"🔍 开始第{self.refresh_count}次刷新操作")
            balance_before_result = delta.get_balance(where="market", loop=True)
            if not balance_before_result.success:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取刷新前余额")
                self.debug_log(LogLevel.ERROR, "🔍 获取刷新前余额失败")
                return False
            
            # 自动合并（全局协议栈自动处理）
            balance_before = balance_before_result.balance
            
            # 执行刷新购买
            self.log_with_stats(LogLevel.INFO, f"🔄 第{self.refresh_count}次刷新: 购买{self.refresh_quantity}发检测价格 (参数: buyin={self.refresh_quantity}, maxin={self.max_quantity})",
                              refresh_count=self.refresh_count, refresh_quantity=self.refresh_quantity)
            
            buy_result = delta.buy_in_market(
                buyin=self.refresh_quantity,
                maxin=self.max_quantity,
                times=1,
                buy=True,
                loop=False
            )
            # 自动合并（全局协议栈自动处理）
            
            if not buy_result.success:
                self.send_log(LogLevel.WARNING, f"⚠️ 第{self.refresh_count}次刷新购买失败")
                self.debug_log(LogLevel.ERROR, f"🔍 刷新购买失败: {self.refresh_quantity}发")
                return False
            
            # 获取刷新后余额（带重试机制，处理余额延迟更新）
            balance_after = None
            max_retries = 6
            self.sleep(0.15)
            for attempt in range(max_retries):
                self.debug_log(LogLevel.INFO, f"🔍 第{attempt + 1}次获取刷新后余额...")
                
                balance_after_result = delta.get_balance(where="market", loop=True)
                # 自动合并（全局协议栈自动处理）
                
                if not balance_after_result.success:
                    self.send_log(LogLevel.WARNING, f"⚠️ 第{attempt + 1}次刷新后余额获取失败")
                    continue
                
                current_balance = balance_after_result.balance
                balance_change = balance_before - current_balance
                
                # 如果余额有变化（差价不为0），说明购买生效了
                if balance_change != 0:
                    self.debug_log(LogLevel.SUCCESS, f"🔍 第{attempt + 1}次检测成功：余额变化 {balance_change}")
                    balance_after = current_balance
                    break
                else:
                    self.debug_log(LogLevel.WARNING, f"🔍 第{attempt + 1}次余额未变化: {balance_before} == {current_balance}")
                    balance_after = current_balance  # 保存最后一次的结果
            
            if balance_after is None:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取刷新后余额")
                return False
            
            # 计算价格
            price_diff = balance_before - balance_after
            unit_price = price_diff / self.refresh_quantity
            
            # 将unit_price存入protocol
            protocol.unit_price = unit_price
            
            # 更新统计
            self.refresh_cost_total += price_diff
            self.current_balance = balance_after
            
            # 记录刷新数据
            self.refresh_cost_records.append({
                'cycle': self.refresh_count,
                'cost': price_diff,
                'unit_price': unit_price,
                'quantity': self.refresh_quantity,
                'balance_before': balance_before,
                'balance_after': balance_after
            })
            
            self.log_with_stats(LogLevel.INFO, f"🔄 第{self.refresh_count}次刷新完成: 单价 {unit_price:.1f}, 数量 {self.refresh_quantity}发, 花费 {price_diff:,.0f}, 余额 {balance_after:,}",
                              refresh_count=self.refresh_count, 
                              unit_price=unit_price,
                              refresh_cost=price_diff,
                              current_balance=balance_after)
            
            # 记录价格数据到CSV
            if unit_price <= self.target_price and unit_price >= self.min_price_threshold:
                action = "发现低价"
            elif unit_price < self.min_price_threshold:
                action = "价格过低"
            else:
                action = "价格过高"
            
            self.record_price_data(balance_before, balance_after, unit_price, action)
            
            return True
                
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 刷新阶段异常: {e}")
            return False
    
    @protocol_handler()
    def purchase_phase(self, protocol, unit_price):
        """购买阶段 - 批量购买"""
        try:
            # 获取Delta实例
            delta = self.get_any_delta()
            if not delta:
                self.send_log(LogLevel.ERROR, "❌ 无法获取Delta实例")
                return False
            
            self.purchase_count += 1
            
            self.send_log(LogLevel.SUCCESS, f"💰 发现低价 {unit_price:.1f} ≤ {self.target_price}, 开始批量购买: {self.purchase_quantity}发×{self.click_times}次 (参数: buyin={self.purchase_quantity}, maxin={self.max_quantity})")
            
            # 获取购买前余额
            balance_before_result = delta.get_balance(where="market", loop=True)
            if not balance_before_result.success:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取购买前余额")
                return False
            
            # 自动合并（全局协议栈自动处理）
            balance_before = balance_before_result.balance
            
            # 执行批量购买
            buy_result = delta.buy_in_market(
                buyin=self.purchase_quantity,
                maxin=self.max_quantity,
                times=self.click_times,
                buy=True,
                loop=False
            )
            # 自动合并（全局协议栈自动处理）
            
            if not buy_result.success:
                self.send_log(LogLevel.ERROR, f"❌ 第{self.purchase_count}次批量购买失败")
                self.debug_log(LogLevel.ERROR, f"🔍 批量购买失败: {self.purchase_quantity}发 x {self.click_times}次")
                return False
                
            # 获取购买后余额（简单一次检测）
            balance_after_result = delta.get_balance(where="market", loop=True)
            if not balance_after_result.success:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取购买后余额")
                return False
            
            protocol <<= balance_after_result
            balance_after = balance_after_result.balance
    
            # 计算购买统计
            purchase_cost = balance_before - balance_after
            purchased_quantity = purchase_cost / unit_price
            
            # 更新统计
            self.purchase_cost_total += purchase_cost
            self.total_purchased += purchased_quantity
            self.current_balance = balance_after
            
            # 记录购买数据
            self.purchase_cost_records.append({
                'cycle': self.purchase_count,
                'cost': purchase_cost,
                'unit_price': unit_price,
                'quantity': purchased_quantity,
                'balance_before': balance_before,
                'balance_after': balance_after
            })
            
            self.log_with_stats(LogLevel.SUCCESS, f"✅ 第{self.purchase_count}次购买完成: 单价 {unit_price:.1f}, 数量 {purchased_quantity:.0f}发, 花费 {purchase_cost:,.0f}, 余额 {balance_after:,}",
                              purchase_count=self.purchase_count,
                              unit_price=unit_price,
                              purchased_quantity=purchased_quantity,
                              purchase_cost=purchase_cost,
                              current_balance=balance_after)
            
            # 记录购买价格数据到CSV
            self.record_price_data(balance_before, balance_after, unit_price, "批量购买")
            
            return True
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 购买阶段异常: {e}")
            return False
    
    def monitor_balance_change(self):
        """监控余额变化 - 连续20次余额不变则认为仓库已满"""
        try:
            # 如果是第一次检查，初始化last_balance
            if self.last_balance is None:
                self.last_balance = self.current_balance
                return True
            
            if self.current_balance == self.last_balance:
                self.balance_unchanged_count += 1
                self.send_log(LogLevel.DEBUG, f"🔍 余额未变化 ({self.balance_unchanged_count}/20): {self.current_balance}")
                
                if self.balance_unchanged_count >= 20:
                    self.send_log(LogLevel.WARNING, f"⚠️ 余额连续{self.balance_unchanged_count}次未变化，可能仓库已满")
                    return False
            else:
                if self.balance_unchanged_count > 0:
                    self.send_log(LogLevel.INFO, f"✅ 余额恢复变化，重置监控计数器 ({self.last_balance} → {self.current_balance})")
                self.balance_unchanged_count = 0
            
            # 每次都更新last_balance为当前余额
            self.last_balance = self.current_balance
            return True
                
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 余额监控异常: {e}")
            return True  # 异常时继续执行
    
    def generate_final_report(self):
        """生成最终执行报告"""
        try:
            if self.initial_balance is None or self.current_balance is None:
                return
            
            total_cost = self.initial_balance - self.current_balance
            
            self.send_log(LogLevel.SUCCESS, "📊 ===== SMB000X执行报告 =====")
            self.send_log(LogLevel.INFO, f"💰 余额变化: {self.initial_balance:,} → {self.current_balance:,} (花费: {total_cost:,})")
            self.send_log(LogLevel.INFO, f"🔄 刷新统计: {self.refresh_count}次, 花费: {self.refresh_cost_total:,.0f}")
            self.send_log(LogLevel.INFO, f"🛒 购买统计: {self.purchase_count}次, 花费: {self.purchase_cost_total:,.0f}")
            self.send_log(LogLevel.INFO, f"📦 总购买量: {self.total_purchased:.0f}发")
            
            if self.total_purchased > 0:
                avg_price = self.purchase_cost_total / self.total_purchased
                self.send_log(LogLevel.INFO, f"💱 平均单价: {avg_price:.1f}")
            
            self.send_log(LogLevel.SUCCESS, "📊 ========================")
            
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 生成报告异常: {e}")
    
    def init_price_logging(self):
        """初始化价格记录功能"""
        try:
            # 创建log/pricedate目录
            log_dir = os.path.join(os.getcwd(), "log", "pricedate")
            os.makedirs(log_dir, exist_ok=True)
            
            # 生成CSV文件名：SMB000X_YYYYMMDD_HHMMSS.csv
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SMB000X_{timestamp}.csv"
            self.csv_file_path = os.path.join(log_dir, filename)
            
            # 创建CSV文件并写入表头
            with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['检测次数', '购买前余额', '购买后余额', '单价', '动作', '时间'])
            
            self.send_log(LogLevel.INFO, f"📊 价格记录文件已创建: {filename}")
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 价格记录初始化失败: {e}")
            self.csv_file_path = None
    
    def record_price_data(self, balance_before, balance_after, unit_price, action):
        """记录价格数据到CSV文件"""
        if not self.csv_file_path:
            return
        
        try:
            self.detection_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 写入CSV文件
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    self.detection_count,
                    balance_before,
                    balance_after,
                    unit_price,
                    action,
                    current_time
                ])
            
            self.send_log(LogLevel.DEBUG, f"📊 价格记录: 检测{self.detection_count}次, 单价{unit_price:.1f}, 动作{action}")
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 价格记录写入失败: {e}")
    

def get_behavior_class():
    return PurchaseRefreshBehavior