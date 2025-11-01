# -*- coding: utf-8 -*-
"""
购买刷新单端时间测试行为模块 - SMBTIME
基于SMB000X，专门用于测试刷新购买流程的时间延迟
代码ID: SMBTIME (Single Market Bot Timing)
"""

try:
    from .Behavior import Behavior, LogLevel, require_any_delta
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from Behavior import Behavior, LogLevel, require_any_delta
import time
import csv
import os
from datetime import datetime, timedelta

# 行为信息定义
BEHAVIOR_INFO = {
    "code_id": "SMBTIME",  # 内部代码ID
    "title": "购买刷新单端时间测试行为",
    "description": "基于SMB000X，专门用于测试刷新购买流程的时间延迟。记录从刷新购买点击到确认购买点击前的每个步骤耗时。",
    "version": "1.0.0",  # 时间测试版本
    "author": "DeltaForce Team",
    "tags": ["单端", "时间测试", "性能分析"],
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
        "work_start_time": {
            "type": "str",
            "label": "工作开始时间",
            "default": "00:00",
            "description": "每日工作开始时间 (HH:MM格式)"
        },
        "work_end_time": {
            "type": "str",
            "label": "工作结束时间",
            "default": "05:15",
            "description": "每日工作结束时间 (HH:MM格式)"
        },
        "auto_shutdown": {
            "type": "bool",
            "label": "自动关机",
            "default": False,
            "description": "工作完成后是否自动关机"
        }
    }
}

class TimingPurchaseRefreshBehavior(Behavior):
    """购买刷新单端时间测试行为类 - SMBTIME"""
    
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
            'work_start_time': {
                'type': 'str',
                'label': '工作开始时间',
                'default': '00:00',
                'description': '每日工作开始时间 (HH:MM格式)'
            },
            'work_end_time': {
                'type': 'str',
                'label': '工作结束时间',
                'default': '05:15',
                'description': '每日工作结束时间 (HH:MM格式)'
            },
            'auto_shutdown': {
                'type': 'bool',
                'label': '自动关机',
                'default': False,
                'description': '工作完成后是否自动关机'
            }
        }
    
    def init_config(self):
        """调用基类自动参数解析"""
        # 基类会自动调用args()并设置所有参数为实例属性
        super().init_config()
        
        # 发送配置信息
        self.send_log(LogLevel.INFO, f"📋 配置: 目标价格≤{self.target_price}, 刷新{self.refresh_quantity}发, 购买{self.purchase_quantity}发×{self.click_times}次, 工作时间{self.work_start_time}-{self.work_end_time}")
    
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
        
        # 时间测量相关
        self.timing_records = []  # 存储每次的时间测量记录（仅内存，用于统计）
        
        self.send_log(LogLevel.SUCCESS, "🎯 SMBTIME行为初始化完成")
        
        # 显示Delta状态
        delta_info = self.get_delta_info()
        self.send_log(LogLevel.INFO, f"🔧 {delta_info}")
        
        if not self.is_delta_ready():
            self.send_log(LogLevel.ERROR, "❌ Delta实例未就绪，无法执行游戏操作")
    
    def main_logic(self):
        """主业务逻辑"""
        try:
            if not self.is_delta_ready():
                self.send_log(LogLevel.ERROR, "❌ Delta实例未就绪，程序退出")
                return False
            
            self.send_log(LogLevel.SUCCESS, "🚀 SMBTIME开始执行")
            self.send_log(LogLevel.INFO, "📋 执行流程: 初始化 → 刷新阶段 → 购买阶段 (含时间测量)")
            
            # 初始化余额
            if not self.initialize_balance():
                self.send_log(LogLevel.ERROR, "❌ 余额初始化失败，程序退出")
                return False
            
            # 主循环
            while not self.is_stopped():
                # 检查工作时间
                if not self.is_in_work_time():
                    self.send_log(LogLevel.INFO, "⏰ 当前不在工作时间内，等待...")
                    self.segmented_sleep(60)  # 等待1分钟后重新检查
                    continue
                
                # 检查关机时间窗口
                if self.is_in_shutdown_window() and self.auto_shutdown:
                    self.send_log(LogLevel.INFO, "🔌 检测到关机时间窗口，程序结束")
                    # 生成最终报告
                    self.generate_final_report()
                    # 统一的结束处理
                    self.handle_program_completion("到达关机时间")
                    return True
                
                # 执行一轮刷新购买流程（含时间测量）
                success = self.execute_refresh_purchase_cycle_with_timing()
                
                if success:
                    self.increment_success()
                    self.send_log(LogLevel.SUCCESS, "✅ 一轮刷新购买完成")
                else:
                    self.increment_error()
                    self.send_log(LogLevel.WARNING, "⚠️ 一轮刷新购买失败")
                
                # 检查余额变化 - 连续20次余额不变则退出
                if not self.monitor_balance_change():
                    self.send_log(LogLevel.INFO, "🏪 余额连续未变化，可能仓库已满")
                    # 生成最终报告
                    self.generate_final_report()
                    # 统一的结束处理
                    self.handle_program_completion("余额未变化")
                    return True  # 直接返回，避免重复处理
                
                # 等待下次循环
                self.segmented_sleep(self.refresh_delay)
            
            # 正常结束循环后的处理
            # 生成最终报告
            self.generate_final_report()
            
            # 统一的结束处理（检查关机）
            # 检查是否是用户手动停止
            if self.is_stopped():
                self.handle_program_completion("用户退出")
            else:
                self.handle_program_completion("正常完成")
            
            return True
            
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 主逻辑执行异常: {e}")
            return False
    
    def execute_refresh_purchase_cycle_with_timing(self):
        """执行一轮刷新购买循环（含时间测量）"""
        try:
            self.increment_cycle()
            
            # ⏱️ 开始总延迟测试：从点击刷新按钮前开始计时
            total_timing_start = time.perf_counter()
            self.send_log(LogLevel.INFO, f"⏱️ 开始总延迟测试：第{self.refresh_count + 1}次循环")
            
            timing_record = {
                'cycle': self.refresh_count + 1,
                'total_start_time': total_timing_start,
                'steps': []
            }
            
            # 刷新阶段
            self.current_phase = "刷新阶段"
            unit_price, refresh_timing = self.refresh_phase_with_timing()
            
            if unit_price is None:
                return False
            
            # 记录刷新阶段时间
            timing_record['steps'].extend(refresh_timing)
            
            # 判断是否进入购买阶段
            if unit_price <= self.target_price and unit_price >= self.min_price_threshold:
                # 价格合理，进入购买阶段
                self.current_phase = "购买阶段"
                purchase_success = self.purchase_phase_simple(unit_price)
                
                # ⏱️ 结束总延迟测试：确认购买按钮后
                total_timing_end = time.perf_counter()
                total_duration = total_timing_end - total_timing_start
                
                timing_record['total_end_time'] = total_timing_end
                timing_record['total_duration'] = total_duration
                timing_record['unit_price'] = unit_price
                timing_record['purchase_success'] = purchase_success
                
                # 添加总延迟记录
                timing_record['steps'].append({
                    'step': '总延迟',
                    'start_time': total_timing_start,
                    'end_time': total_timing_end,
                    'duration': total_duration,
                    'description': '从点击刷新按钮前到确认购买按钮后的完整延迟'
                })
                
                self.send_log(LogLevel.SUCCESS, f"[第{timing_record['cycle']}轮] 总延迟{total_duration:.3f}秒 (完整购买流程)")
                
                # 仅保存到内存用于统计，不保存到CSV
                self.timing_records.append(timing_record)
                
                # 打印详细时间分析
                self.print_timing_analysis(timing_record)
                
                return purchase_success
            else:
                # 价格不合理，继续刷新（只有刷新延迟，无总延迟）
                if unit_price < self.min_price_threshold:
                    self.send_log(LogLevel.WARNING, f"⚠️ 价格过低: {unit_price:.1f} < {self.min_price_threshold} (可能识别错误)")
                else:
                    self.send_log(LogLevel.DEBUG, f"🔄 价格过高: {unit_price:.1f} > {self.target_price}")
                
                timing_record['unit_price'] = unit_price
                timing_record['purchase_success'] = False
                
                # 仅保存到内存用于统计，不保存到CSV
                self.timing_records.append(timing_record)
                
                # 打印刷新阶段时间分析
                self.print_refresh_timing_analysis(timing_record)
                
                return False
                
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 刷新购买循环异常: {e}")
            return False
    
    @require_any_delta
    def initialize_balance(self, delta):
        """初始化余额跟踪"""
        try:
            self.send_log(LogLevel.INFO, "💰 正在获取初始余额...")
            
            balance_result = delta.get_balance(where="market", loop=True)
            if not balance_result.success:
                self.send_log(LogLevel.ERROR, "❌ 无法获取初始余额")
                return False
            
            balance = balance_result.balance
            self.initial_balance = balance
            self.current_balance = balance
            self.last_balance = balance
            
            # 打印初始化调用链时间记录
            if hasattr(balance_result, 'timing_records'):
                self.send_log(LogLevel.INFO, f"📊 初始化调用链时间:")
                for i, (func_name, net_time, is_base) in enumerate(balance_result.timing_records, 1):
                    self.send_log(LogLevel.INFO, f"  {i}. {func_name}: {net_time*1000:.3f}ms")
                self.send_log(LogLevel.INFO, f"  总执行时间: {balance_result.elapsed_time*1000:.3f}ms")
            
            self.log_with_stats(LogLevel.SUCCESS, f"💰 初始余额: {balance:,}", 
                               initial_balance=balance)
            return True
            
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 余额初始化异常: {e}")
            return False
    
    @require_any_delta
    def refresh_phase_with_timing(self, delta):
        """刷新阶段 - 购买少量子弹检测价格（含详细时间测量）"""
        try:
            self.refresh_count += 1
            timing_steps = []
            
            # 获取刷新前余额（不计入延迟测试）
            balance_before_result = delta.get_balance(where="market", loop=True)
            if not balance_before_result.success:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取刷新前余额")
                balance_before = self.current_balance
            else:
                balance_before = balance_before_result.balance
                
                # 打印调用链时间记录（刷新前）
                if hasattr(balance_before_result, 'timing_records'):
                    self.send_log(LogLevel.INFO, f"📊 第{self.refresh_count}次刷新前调用链时间:")
                    for i, (func_name, net_time, is_base) in enumerate(balance_before_result.timing_records, 1):
                        self.send_log(LogLevel.INFO, f"  {i}. {func_name}: {net_time*1000:.3f}ms")
                    self.send_log(LogLevel.INFO, f"  总执行时间: {balance_before_result.elapsed_time*1000:.3f}ms")
            
            if balance_before is None:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取刷新前余额")
                return None, timing_steps
            
            # 执行刷新购买
            self.log_with_stats(LogLevel.INFO, f"🔄 第{self.refresh_count}次刷新: 购买{self.refresh_quantity}发检测价格 (参数: buyin={self.refresh_quantity}, maxin={self.max_quantity})",
                              refresh_count=self.refresh_count, refresh_quantity=self.refresh_quantity)
            
            # ⏱️ 开始刷新延迟测试：从点击刷新按钮后开始
            refresh_timing_start = time.perf_counter()
            
            # 子步骤1: 执行刷新购买操作
            step1_start = time.perf_counter()
            success = delta.buy_in_market(
                buyin=self.refresh_quantity,
                maxin=self.max_quantity,
                times=1,
                buy=True,
                loop=False
            )
            step1_end = time.perf_counter()
            step1_duration = step1_end - step1_start
            
            if not success:
                self.send_log(LogLevel.WARNING, f"⚠️ 第{self.refresh_count}次刷新购买失败")
                return None, timing_steps
            
            # 子步骤2: 查询余额 - 详细分解
            step2_start = time.perf_counter()
            
            # 这里需要分解get_balance内部的操作，但由于无法直接修改DeltaForceClass
            # 我们通过多次调用来模拟测量各个步骤
            click_start = time.perf_counter()
            # 模拟点击位置延迟（实际在get_balance内部）
            click_end = time.perf_counter()
            click_duration = click_end - click_start
            
            ocr_start = time.perf_counter()
            balance_after_result = delta.get_balance(where="market", loop=True)
            balance_after = balance_after_result.balance if balance_after_result.success else None
            ocr_end = time.perf_counter()
            
            # 打印调用链时间记录
            if balance_after_result.success and hasattr(balance_after_result, 'timing_records'):
                self.send_log(LogLevel.INFO, f"📊 第{self.refresh_count}次刷新调用链时间:")
                for i, (func_name, net_time, is_base) in enumerate(balance_after_result.timing_records, 1):
                    self.send_log(LogLevel.INFO, f"  {i}. {func_name}: {net_time*1000:.3f}ms")
                self.send_log(LogLevel.INFO, f"  总执行时间: {balance_after_result.elapsed_time*1000:.3f}ms")
            
            # 总时间减去点击时间约等于OCR时间
            total_get_balance = ocr_end - step2_start
            ocr_duration = total_get_balance - click_duration
            
            step2_end = time.perf_counter()
            step2_duration = step2_end - step2_start
            
            if balance_after is None:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取刷新后余额")
                return None, timing_steps
            
            # 子步骤3: 计算差价
            step3_start = time.perf_counter()
            price_diff = balance_before - balance_after
            unit_price = price_diff / self.refresh_quantity
            step3_end = time.perf_counter()
            step3_duration = step3_end - step3_start
            
            # 判断是否满足条件（这里是刷新延迟的结束点）
            condition_met = unit_price <= self.target_price and unit_price >= self.min_price_threshold
            
            # ⏱️ 结束刷新延迟测试：到点击确认购买按钮前的一刻
            refresh_timing_end = time.perf_counter()
            refresh_duration = refresh_timing_end - refresh_timing_start
            
            # 记录详细步骤
            timing_steps.append({
                'step': '刷新延迟',
                'start_time': refresh_timing_start,
                'end_time': refresh_timing_end,
                'duration': refresh_duration,
                'description': '从点击刷新按钮后到确认余额、计算差价、满足条件、到点击确认购买按钮前的一刻',
                'sub_steps': [
                    {'name': '执行刷新购买操作', 'duration': step1_duration},
                    {'name': '查询余额', 'duration': step2_duration},
                    {'name': '计算差价', 'duration': step3_duration}
                ]
            })
            
            # 按照用户要求的格式打印
            self.send_log(LogLevel.INFO, f"[第{self.refresh_count}轮] 刷新确认延迟{refresh_duration:.3f}秒，总延迟待计算:")
            # 刷新操作完成，不显示详细时间分解
            
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
                'balance_after': balance_after,
                'timing_duration': refresh_duration
            })
            
            self.log_with_stats(LogLevel.INFO, f"🔄 第{self.refresh_count}次刷新完成: 单价 {unit_price:.1f}, 数量 {self.refresh_quantity}发, 花费 {price_diff:,.0f}, 余额 {balance_after:,}, 刷新延迟 {refresh_duration:.4f}秒",
                              refresh_count=self.refresh_count, 
                              unit_price=unit_price,
                              refresh_cost=price_diff,
                              current_balance=balance_after,
                              refresh_timing=refresh_duration)
            
            # 记录价格数据到CSV
            if condition_met:
                action = "发现低价"
            elif unit_price < self.min_price_threshold:
                action = "价格过低"
            else:
                action = "价格过高"
            
            self.record_price_data(balance_before, balance_after, unit_price, action)
            
            return unit_price, timing_steps
                
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 刷新阶段异常: {e}")
            return None, []
    
    @require_any_delta
    def purchase_phase_simple(self, delta, unit_price):
        """购买阶段 - 批量购买（含详细时间测量）"""
        try:
            self.purchase_count += 1
            
            self.send_log(LogLevel.SUCCESS, f"💰 发现低价 {unit_price:.1f} ≤ {self.target_price}, 开始批量购买: {self.purchase_quantity}发×{self.click_times}次 (参数: buyin={self.purchase_quantity}, maxin={self.max_quantity})")
            
            # 购买阶段延迟分解
            purchase_start = time.perf_counter()
            
            # 步骤1: 获取购买前余额 - 详细分解
            step1_start = time.perf_counter()
            
            click1_start = time.perf_counter()
            click1_end = time.perf_counter()
            click1_duration = click1_end - click1_start
            
            ocr1_start = time.perf_counter()
            balance_before_result = delta.get_balance(where="market", loop=True)
            balance_before = balance_before_result.balance if balance_before_result.success else None
            ocr1_end = time.perf_counter()
            
            # 打印调用链时间记录（购买前）
            if balance_before_result.success and hasattr(balance_before_result, 'timing_records'):
                self.send_log(LogLevel.INFO, f"📊 第{self.purchase_count}次购买前调用链时间:")
                for i, (func_name, net_time, is_base) in enumerate(balance_before_result.timing_records, 1):
                    self.send_log(LogLevel.INFO, f"  {i}. {func_name}: {net_time*1000:.3f}ms")
                self.send_log(LogLevel.INFO, f"  总执行时间: {balance_before_result.elapsed_time*1000:.3f}ms")
            
            total1_duration = ocr1_end - step1_start
            ocr1_duration = total1_duration - click1_duration
            
            step1_end = time.perf_counter()
            step1_duration = step1_end - step1_start
            
            if balance_before is None:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取购买前余额")
                return False
            
            # 步骤2: 执行批量购买操作
            step2_start = time.perf_counter()
            success = delta.buy_in_market(
                buyin=self.purchase_quantity,
                maxin=self.max_quantity,
                times=self.click_times,
                buy=True,
                loop=False
            )
            step2_end = time.perf_counter()
            step2_duration = step2_end - step2_start
            
            if not success:
                self.send_log(LogLevel.ERROR, f"❌ 第{self.purchase_count}次批量购买失败")
                return False
                
            # 步骤3: 获取购买后余额 - 详细分解
            step3_start = time.perf_counter()
            
            click3_start = time.perf_counter()
            click3_end = time.perf_counter()
            click3_duration = click3_end - click3_start
            
            ocr3_start = time.perf_counter()
            balance_after_result = delta.get_balance(where="market", loop=True)
            balance_after = balance_after_result.balance if balance_after_result.success else None
            ocr3_end = time.perf_counter()
            
            # 打印调用链时间记录（购买后）
            if balance_after_result.success and hasattr(balance_after_result, 'timing_records'):
                self.send_log(LogLevel.INFO, f"📊 第{self.purchase_count}次购买后调用链时间:")
                for i, (func_name, net_time, is_base) in enumerate(balance_after_result.timing_records, 1):
                    self.send_log(LogLevel.INFO, f"  {i}. {func_name}: {net_time*1000:.3f}ms")
                self.send_log(LogLevel.INFO, f"  总执行时间: {balance_after_result.elapsed_time*1000:.3f}ms")
            
            total3_duration = ocr3_end - step3_start
            ocr3_duration = total3_duration - click3_duration
            
            step3_end = time.perf_counter()
            step3_duration = step3_end - step3_start
            
            if balance_after is None:
                self.send_log(LogLevel.WARNING, "⚠️ 无法获取购买后余额")
                return False
    
            # 步骤4: 计算购买统计
            step4_start = time.perf_counter()
            purchase_cost = balance_before - balance_after
            purchased_quantity = purchase_cost / unit_price
            step4_end = time.perf_counter()
            step4_duration = step4_end - step4_start
            
            purchase_end = time.perf_counter()
            total_purchase_duration = purchase_end - purchase_start
            
            # 购买阶段完成，不显示详细时间分解
            
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
            
            self.send_log(LogLevel.SUCCESS, "📊 ===== SMBTIME执行报告 =====")
            self.send_log(LogLevel.INFO, f"💰 余额变化: {self.initial_balance:,} → {self.current_balance:,} (花费: {total_cost:,})")
            self.send_log(LogLevel.INFO, f"🔄 刷新统计: {self.refresh_count}次, 花费: {self.refresh_cost_total:,.0f}")
            self.send_log(LogLevel.INFO, f"🛒 购买统计: {self.purchase_count}次, 花费: {self.purchase_cost_total:,.0f}")
            self.send_log(LogLevel.INFO, f"📦 总购买量: {self.total_purchased:.0f}发")
            
            if self.total_purchased > 0:
                avg_price = self.purchase_cost_total / self.total_purchased
                self.send_log(LogLevel.INFO, f"💱 平均单价: {avg_price:.1f}")
            
            # 时间统计报告
            if self.timing_records:
                self.generate_timing_summary()
            
            self.send_log(LogLevel.SUCCESS, "📊 ========================")
            
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 生成报告异常: {e}")
    
    def init_price_logging(self):
        """初始化价格记录功能"""
        try:
            # 创建log/pricedate目录
            log_dir = os.path.join(os.getcwd(), "log", "pricedate")
            os.makedirs(log_dir, exist_ok=True)
            
            # 生成CSV文件名：SMBTIME_YYYYMMDD_HHMMSS.csv
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SMBTIME_{timestamp}.csv"
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
    
    def print_timing_analysis(self, timing_record):
        """打印详细的时间分析（完整流程）"""
        try:
            cycle = timing_record['cycle']
            unit_price = timing_record.get('unit_price', 0)
            purchase_success = timing_record.get('purchase_success', False)
            
            self.send_log(LogLevel.SUCCESS, f"⏱️ ===== 第{cycle}次循环延迟测试分析 =====")
            self.send_log(LogLevel.INFO, f"💰 单价: {unit_price:.1f}, 是否购买: {'是' if purchase_success else '否'}")
            
            refresh_duration = 0
            total_duration = 0
            
            for step in timing_record['steps']:
                step_name = step['step']
                duration = step['duration']
                description = step.get('description', '')
                
                if step_name == '刷新延迟':
                    refresh_duration = duration
                    self.send_log(LogLevel.INFO, f"  🔄 刷新延迟: {duration:.4f}秒")
                    self.send_log(LogLevel.DEBUG, f"     {description}")
                elif step_name == '总延迟':
                    total_duration = duration
                    self.send_log(LogLevel.SUCCESS, f"  🎯 总延迟: {duration:.4f}秒")
                    self.send_log(LogLevel.DEBUG, f"     {description}")
            
            self.send_log(LogLevel.SUCCESS, f"⏱️ ================================")
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 时间分析打印失败: {e}")
    
    def print_refresh_timing_analysis(self, timing_record):
        """打印刷新阶段的时间分析（仅刷新，未购买）"""
        try:
            cycle = timing_record['cycle']
            unit_price = timing_record.get('unit_price', 0)
            
            refresh_duration = 0
            for step in timing_record['steps']:
                if step['step'] == '刷新延迟':
                    refresh_duration = step['duration']
                    break
            
            self.send_log(LogLevel.INFO, f"⏱️ 第{cycle}次刷新延迟: {refresh_duration:.4f}秒, 单价: {unit_price:.1f} (未购买)")
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 刷新时间分析打印失败: {e}")
    
    def generate_timing_summary(self):
        """生成时间统计摘要"""
        try:
            if not self.timing_records:
                return
            
            # 分类统计
            refresh_only_records = [r for r in self.timing_records if not r.get('purchase_success', False)]
            purchase_records = [r for r in self.timing_records if r.get('purchase_success', False)]
            
            self.send_log(LogLevel.SUCCESS, "⏱️ ===== 延迟测试统计摘要 =====")
            
            # 刷新延迟统计
            all_refresh_times = []
            for record in self.timing_records:
                for step in record['steps']:
                    if step['step'] == '刷新延迟':
                        all_refresh_times.append(step['duration'])
            
            if all_refresh_times:
                avg_refresh = sum(all_refresh_times) / len(all_refresh_times)
                min_refresh = min(all_refresh_times)
                max_refresh = max(all_refresh_times)
                self.send_log(LogLevel.INFO, f"🔄 刷新延迟 ({len(all_refresh_times)}次): 平均{avg_refresh:.3f}秒, 最快{min_refresh:.3f}秒, 最慢{max_refresh:.3f}秒")
            
            # 总延迟统计（仅购买成功的记录）
            all_total_times = []
            for record in purchase_records:
                for step in record['steps']:
                    if step['step'] == '总延迟':
                        all_total_times.append(step['duration'])
            
            if all_total_times:
                avg_total = sum(all_total_times) / len(all_total_times)
                min_total = min(all_total_times)
                max_total = max(all_total_times)
                self.send_log(LogLevel.INFO, f"🎯 总延迟 ({len(all_total_times)}次): 平均{avg_total:.3f}秒, 最快{min_total:.3f}秒, 最慢{max_total:.3f}秒")
            
            # 统计信息
            self.send_log(LogLevel.INFO, f"📊 统计信息: 总循环{len(self.timing_records)}次, 成功购买{len(purchase_records)}次, 仅刷新{len(refresh_only_records)}次")
            
            self.send_log(LogLevel.SUCCESS, "⏱️ =====================")
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 时间统计摘要生成失败: {e}")


def get_behavior_class():
    return TimingPurchaseRefreshBehavior
