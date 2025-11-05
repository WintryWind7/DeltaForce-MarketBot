# -*- coding: utf-8 -*-
"""
双端自定义子弹滚仓行为模块 - DPB000X
辅端刷新查价，主端批量购买和配装
代码ID: DPB000X (Dual Purchase Bot)
"""
import pyautogui
import time
import csv
import os
import sys
import numpy as np
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(__file__))

from Behavior import Behavior, LogLevel
from base.decorators import protocol_handler

# 行为信息定义
BEHAVIOR_INFO = {
    "code_id": "DPB000X",  # 内部代码ID
    "title": "双端自定义子弹滚仓行为",
    "description": "辅端刷新查价，主端批量购买和配装。适用于双端协同操作场景。",
    "version": "1.0.0",
    "author": "DeltaForce Team",
    "tags": ["双端", "购买查价", "配装"],
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

class DualPurchaseBehavior(Behavior):
    """双端自定义子弹滚仓行为类 - DPB000X"""
    
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
        
        # 解析工作开始时间（HH:MM 格式）
        try:
            start_parts = self.work_start_time.split(':')
            self.work_start_hour = int(start_parts[0])
            self.work_start_minute = int(start_parts[1])
        except (ValueError, IndexError, AttributeError):
            self.send_log(LogLevel.WARNING, f"⚠️ 工作开始时间格式错误: {self.work_start_time}，使用默认值 00:00")
            self.work_start_hour = 0
            self.work_start_minute = 0
            self.work_start_time = "00:00"
        
        # 解析工作结束时间（HH:MM 格式）
        try:
            end_parts = self.work_end_time.split(':')
            self.work_end_hour = int(end_parts[0])
            self.work_end_minute = int(end_parts[1])
        except (ValueError, IndexError, AttributeError):
            self.send_log(LogLevel.WARNING, f"⚠️ 工作结束时间格式错误: {self.work_end_time}，使用默认值 05:15")
            self.work_end_hour = 5
            self.work_end_minute = 15
            self.work_end_time = "05:15"
        
        # 处理24小时的特殊情况
        if self.work_start_hour == 24:
            self.work_start_hour = 23
            self.work_start_minute = 59
            self.work_start_time = "23:59"
        if self.work_end_hour == 24:
            self.work_end_hour = 23
            self.work_end_minute = 59
            self.work_end_time = "23:59"
        
        # 固定参数
        self.refresh_quantity = 31  # 刷新时固定购买31发
        self.max_quantity = 200  # 最大购买数量固定为200
        
        # 发送配置信息
        self.send_log(LogLevel.INFO, f"📋 配置: 目标价格≤{self.target_price}, 刷新{self.refresh_quantity}发, 工作时间{self.work_start_time}-{self.work_end_time}")
        
        # 调试模式信息
        if self.debug_mode == 0:
            self.send_log(LogLevel.INFO, "📝 普通模式，显示所有日志")
        elif self.debug_mode == 1:
            self.debug_log(LogLevel.INFO, f"🔍 简化调试模式已开启（隐藏底层函数）")
            self.debug_log(LogLevel.INFO, f"🔧 配置参数: target_price={self.target_price}, refresh_quantity={self.refresh_quantity}")
        elif self.debug_mode == 2:
            self.debug_log(LogLevel.INFO, f"🔍 详细调试模式已开启（显示所有函数）")
            self.debug_log(LogLevel.INFO, f"🔧 配置参数: target_price={self.target_price}, refresh_quantity={self.refresh_quantity}")
    
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
        
        # 余额跟踪（辅端）
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
        
        self.system_log(LogLevel.SUCCESS, "🎯 DPB000X行为初始化完成")
        
        # 检查双端状态
        if not self.is_dual_mode():
            self.system_log(LogLevel.ERROR, "❌ DPB000X需要双端模式，当前不是双端模式")
            return
        
        # 显示Delta状态
        delta_info = self.get_delta_info()
        self.system_log(LogLevel.INFO, f"🔧 {delta_info}")
        
        if not self.is_delta_ready():
            self.system_log(LogLevel.ERROR, "❌ Delta实例未就绪，无法执行游戏操作")
    
    def main_logic(self):
        """主业务逻辑"""
        print("=" * 80)
        print("🔍 [DEBUG] main_logic 函数已被调用！")
        print("=" * 80)
        
        try:
            self.send_log(LogLevel.INFO, "🔍 [DEBUG] main_logic 函数开始执行")
        except Exception as e:
            print(f"❌ [DEBUG] send_log 异常: {e}")
        
        # ========== 临时测试模式：仅测试仓库配装流程（已注释） ==========
        # if not self.is_delta_ready():
        #     self.send_log(LogLevel.ERROR, "❌ Delta实例未就绪，程序退出")
        #     return False
        # 
        # self.system_log(LogLevel.SUCCESS, "🚀 DPB000X开始执行 - 仓库配装测试")
        # 
        # # 获取主端Delta实例
        # main_delta = self.get_main_delta()
        # if not main_delta:
        #     self.send_log(LogLevel.ERROR, "❌ 无法获取主端Delta实例")
        #     return False
        # 
        # # 切换到主端窗口
        # self.send_log(LogLevel.INFO, "🔄 切换到主端窗口...")
        # if not main_delta.focus_window():
        #     self.send_log(LogLevel.WARNING, "⚠️ 切换主端窗口失败")
        # 
        # # 创建一个临时protocol用于记录
        # from base.DeltaProtocol import DeltaProtocol
        # temp_protocol = DeltaProtocol()
        # 
        # # 直接执行仓库配装流程
        # warehouse_result = self.warehouse_equip_flow(main_delta, temp_protocol)
        # 
        # if warehouse_result:
        #     self.send_log(LogLevel.SUCCESS, "✅ 仓库配装流程完成")
        #     self.handle_program_completion("测试完成")
        #     return True
        # else:
        #     self.send_log(LogLevel.ERROR, "❌ 仓库配装流程失败")
        #     return False
        # ========== 临时测试模式结束 ==========
        
        # ========== 完整逻辑 ==========
        # 检查双端模式
        print("🔍 [DEBUG] 开始检查双端模式...")
        try:
            self.send_log(LogLevel.INFO, f"🔍 [DEBUG] 准备检查双端模式")
            is_dual = self.is_dual_mode()
            print(f"🔍 [DEBUG] is_dual_mode() 返回: {is_dual}")
            self.send_log(LogLevel.INFO, f"🔍 检查双端模式: {is_dual}")
            if not is_dual:
                print("❌ [DEBUG] 不是双端模式，准备退出")
                self.send_log(LogLevel.ERROR, "❌ DPB000X需要双端模式")
                return self.exit_behavior("DPB000X需要双端模式", success=False)
            
            print("✅ [DEBUG] 是双端模式，继续执行")
            self.system_log(LogLevel.SUCCESS, "🚀 DPB000X开始执行（双端模式）")
            print("🔍 [DEBUG] system_log 第1条执行完成")
            self.system_log(LogLevel.INFO, "📋 执行流程: 初始化 → 辅端刷新阶段 → 主端购买阶段")
            print("🔍 [DEBUG] system_log 第2条执行完成")
            # 暂时注释掉 send_log 测试
            # self.send_log(LogLevel.INFO, "🔍 [DEBUG] system_log 执行完成")
            print("🔍 [DEBUG] 检查双端模式完成")
        except Exception as e:
            print(f"❌ [DEBUG] 异常: {e}")
            self.send_log(LogLevel.ERROR, f"❌ [DEBUG] 异常: {e}")
            import traceback
            traceback.print_exc()
        
        print("🔍 [DEBUG] 准备初始化余额...")
        # 初始化余额（辅端）
        self.send_log(LogLevel.INFO, "💰 开始初始化余额...")
        print("🔍 [DEBUG] send_log 执行完成")
        init_result = self.initialize_balance()
        self.send_log(LogLevel.INFO, f"💰 初始化余额结果: {init_result}")
        if not init_result:
            self.send_log(LogLevel.ERROR, "❌ 余额初始化失败")
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
            
            # 切换到辅端（在进入刷新循环前）
            aux_delta = self.get_aux_delta()
            if aux_delta:
                self.debug_log(LogLevel.INFO, "🔄 切换到辅端窗口...")
                focus_result = aux_delta.focus_window()  # 装饰器自动追踪
                if not focus_result.success:
                    self.send_log(LogLevel.WARNING, "⚠️ 切换辅端窗口失败")
                time.sleep(0.1)
            
            # 执行一轮刷新购买流程
            cycle_result = self.execute_refresh_purchase_cycle()
            success = cycle_result.success if cycle_result else False
            found_low_price = getattr(cycle_result, 'found_low_price', False)
            
            if success:
                self.increment_success()
                if found_low_price:
                    self.send_log(LogLevel.SUCCESS, "✅ 已发现低价并完成配装，等待5秒后继续循环")
                    time.sleep(5.0)
                else:
                    self.send_log(LogLevel.SUCCESS, "✅ 一轮刷新完成")
            else:
                self.increment_error()
                # 刷新失败（不打印日志）
            
            # 检查余额变化 - 连续20次余额不变则退出
            if not self.monitor_balance_change():
                return self.exit_behavior("余额未变化", success=True)
            
            # 等待下次循环
            self.segmented_sleep(self.refresh_delay)
        
        # 正常结束循环后的处理（用户手动停止或正常完成）
        reason = "用户退出" if self.is_stopped() else "正常完成"
        return self.exit_behavior(reason, success=True)
    
    @protocol_handler()
    def execute_refresh_purchase_cycle(self, protocol):
        """执行一轮刷新购买循环"""
        try:
            self.increment_cycle()
            
            # 刷新阶段（辅端）
            self.current_phase = "刷新阶段"
            refresh_result = self.refresh_phase()
            
            # 从protocol中获取unit_price
            unit_price = getattr(refresh_result, 'unit_price', None)
            
            # 判断是否进入购买阶段
            if unit_price <= self.target_price and unit_price >= self.min_price_threshold:
                # 价格合理，进入购买阶段（主端）
                self.current_phase = "购买阶段"
                purchase_result = self.purchase_phase(unit_price)
                # 自动合并（self 的方法会自动合并到 protocol）
                purchase_success = purchase_result.success if purchase_result else False
                
                # 标记发现低价
                protocol.found_low_price = True
                
                # 打印完整的调用链（从刷新到购买完成）- 根据 debug_mode 选择模式
                if self.debug_mode > 0:  # debug_mode=1 或 2
                    mode = "simple" if self.debug_mode == 1 else "detail"
                    lines = self.formatter.format_timing_records(
                        protocol, 
                        title=f"第{self.refresh_count}次完整流程调用链 (刷新→切换主端，单价: {unit_price:.1f})",
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
                
                # 价格不合理，继续刷新（不打印日志）
                
                return False
                
        except Exception as e:
            self.send_log(LogLevel.ERROR, f"❌ 刷新购买循环异常: {e}")
            return False
    
    def initialize_balance(self):
        """初始化余额跟踪（辅端）"""
        # 获取辅端Delta实例
        aux_delta = self.get_aux_delta()
        if not aux_delta:
            self.send_log(LogLevel.ERROR, "❌ 无法获取辅端Delta实例")
            return False
        
        # 切换到辅端窗口
        self.send_log(LogLevel.INFO, "🔄 切换到辅端窗口...")
        focus_result = aux_delta.focus_window()  # 装饰器自动追踪
        if not focus_result.success:
            self.send_log(LogLevel.WARNING, "⚠️ 切换辅端窗口失败")
        
        self.send_log(LogLevel.INFO, "💰 正在获取辅端初始余额...")
        
        balance_result = aux_delta.get_balance(where="market", retry=50)
        if not balance_result.success:
            self.send_log(LogLevel.ERROR, "❌ 无法获取辅端初始余额")
            return False
        
        balance = balance_result.balance
        self.initial_balance = balance
        self.current_balance = balance
        self.last_balance = balance
        
        self.log_with_stats(LogLevel.SUCCESS, f"💰 辅端初始余额: {balance:,}", 
                           initial_balance=balance)
        self.debug_log(LogLevel.INFO, f"🔍 初始化余额设置: {balance:,}")
        return True
    
    @protocol_handler()
    def refresh_phase(self, protocol):
        """刷新阶段 - 辅端购买少量子弹检测价格"""
        # 获取辅端Delta实例
        aux_delta = self.get_aux_delta()
        
        self.refresh_count += 1
        
        # 获取刷新前余额
        self.debug_log(LogLevel.INFO, f"🔍 开始第{self.refresh_count}次刷新操作（辅端）")
        balance_before_result = aux_delta.get_balance(where="market")
        
        balance_before = balance_before_result.balance
        
        # 执行刷新购买（不打印日志）
        buy_result = aux_delta.buy_in_market(
            buyin=self.refresh_quantity,
            maxin=self.max_quantity,
            times=1,
            buy=True,
            loop=False
        )
        
        # 获取刷新后余额（使用变化检测模式）
        self.debug_log(LogLevel.INFO, f"🔍 获取刷新后余额（变化检测模式，基准: {balance_before}）...")
        balance_after_result = aux_delta.get_balance(where="market", retry=10, change=balance_before)
        
        # 检查余额是否变化（get_balance_success已包含：识别到数字 且 与change不同）
        if not balance_after_result.get_balance_success:
            self.send_log(LogLevel.WARNING, f"⚠️ 余额未变化（重试{balance_after_result.get_balance_retry_attempt}次后仍为 {balance_after_result.balance}）")
            return False
        
        balance_after = balance_after_result.balance
        
        # 计算价格
        price_diff = balance_before - balance_after
        unit_price = price_diff / self.refresh_quantity
        
        # 将unit_price存入protocol
        protocol.unit_price = unit_price
        
        # 保存OCR截图（已注释，调试完成）
        # if hasattr(balance_before_result, 'screenshot') and balance_before_result.screenshot:
        #     screenshot_dir = os.path.join(os.getcwd(), "log", "screenshots")
        #     os.makedirs(screenshot_dir, exist_ok=True)
        #     filename = f"{balance_before}.png"
        #     filepath = os.path.join(screenshot_dir, filename)
        #     balance_before_result.screenshot.save(filepath)
        #     self.debug_log(LogLevel.INFO, f"💾 已保存刷新前余额截图: {filename}")
        # 
        # if hasattr(balance_after_result, 'screenshot') and balance_after_result.screenshot:
        #     screenshot_dir = os.path.join(os.getcwd(), "log", "screenshots")
        #     os.makedirs(screenshot_dir, exist_ok=True)
        #     filename = f"{balance_after}.png"
        #     filepath = os.path.join(screenshot_dir, filename)
        #     balance_after_result.screenshot.save(filepath)
        #     self.debug_log(LogLevel.INFO, f"💾 已保存刷新后余额截图: {filename}")
        
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
        
        # 判断价格状态并生成输出
        if unit_price <= self.target_price and unit_price >= self.min_price_threshold:
            action = "发现低价"
            price_comparison = f"单价: {unit_price:.1f} <={self.target_price}"
        elif unit_price < self.min_price_threshold:
            action = "价格过低"
            price_comparison = f"单价: {unit_price:.1f} <{self.min_price_threshold}"
        else:
            action = "价格过高"
            price_comparison = f"单价: {unit_price:.1f} >{self.target_price}"
        
        # 普通模式：简洁输出
        self.send_log(LogLevel.INFO, f"[第{self.refresh_count}轮] {price_comparison}，余额变化 {balance_before:,} → {balance_after:,}")
        
        # Debug模式：详细输出
        self.debug_log(LogLevel.INFO, f"🔄 刷新详情: 单价 {unit_price:.1f}, 数量 {self.refresh_quantity}发, 花费 {price_diff:,.0f}, 余额 {balance_after:,}")
        
        self.record_price_data(balance_before, balance_after, unit_price, action)
        
        return True
            
    
    @protocol_handler()
    def purchase_phase(self, protocol, unit_price):
        """购买阶段 - 切换到主端窗口并执行点击"""
        # 获取主端Delta实例
        main_delta = self.get_main_delta()
        
        # 切换到主端窗口
        self.send_log(LogLevel.SUCCESS, f"💰 发现低价 {unit_price:.1f} ≤ {self.target_price}，切换到主端")
        self.debug_log(LogLevel.INFO, "🔄 切换到主端窗口...")
        
        focus_result = main_delta.focus_window()  # 装饰器自动追踪
        if not focus_result.success:
            self.send_log(LogLevel.WARNING, "⚠️ 切换主端窗口失败")
        
        self.purchase_count += 1
        self.send_log(LogLevel.INFO, "🖱️ 执行连续点击操作...")
        
        for i in range(1):
            click_result = main_delta.click_ratio(0.8758, 0.7973)
            
            if not click_result.success:
                self.send_log(LogLevel.WARNING, f"⚠️ 第{i+1}次点击失败")
            else:
                self.debug_log(LogLevel.INFO, f"🖱️ 第{i+1}次点击完成")
            
            if i < 4:
                time.sleep(0.001)
        
        self.send_log(LogLevel.INFO, "✅ 已完成5次点击")
        
        # 延迟3秒
        time.sleep(3.0)
        
        # 第一次检查购买结果
        self.send_log(LogLevel.INFO, "🔍 检查购买结果...")
        error_check_result = main_delta.check_purchase_error((0.4679, 0.6938), (0.5532, 0.7170))
        
        if not error_check_result.has_purchase_error:
            # 没有数字 → 购买成功
            self.send_log(LogLevel.SUCCESS, "✅ 购买成功，进入仓库配装流程")
            
            # 执行仓库配装流程
            warehouse_result = self.warehouse_equip_flow(main_delta, protocol)
            if not warehouse_result:
                self.send_log(LogLevel.ERROR, "❌ 仓库配装流程失败")
                return False
            
            self.send_log(LogLevel.SUCCESS, "✅ 仓库配装流程完成")
            
            # 执行最终步骤
            final_result = self.execute_final_steps(main_delta)
            if not final_result:
                self.send_log(LogLevel.ERROR, "❌ 最终步骤执行失败")
                return False
            
            self.send_log(LogLevel.SUCCESS, "✅ 购买阶段完成")
            return True
        else:
            # 有数字 → 购买失败，进入重试循环
            self.send_log(LogLevel.WARNING, f"⚠️ 检测到购买失败提示（数字: {error_check_result.error_text}），进入重试流程...")
            
            max_retry = 10
            for attempt in range(max_retry):
                self.debug_log(LogLevel.INFO, f"🔍 第{attempt + 1}次重试检测...")
                
                error_check_result = main_delta.check_purchase_error((0.4679, 0.6938), (0.5532, 0.7170))
                
                if error_check_result.has_purchase_error:
                    # 还有数字，按ESC
                    self.debug_log(LogLevel.WARNING, f"⚠️ 仍有错误数字（{error_check_result.error_text}），按ESC...")
                    pyautogui.press('esc')
                    time.sleep(0.5)
                else:
                    # 数字消失了，按L键 + 点击位置，返回主循环
                    self.send_log(LogLevel.INFO, "✅ 错误数字消失，按L键并点击位置，进入下个循环")
                    pyautogui.press('l')
                    time.sleep(0.5)
                    main_delta.click_ratio(0.1000, 0.4300)
                    return False
            
            # 10次都有数字，放弃，按L键 + 点击位置
            self.send_log(LogLevel.WARNING, "⚠️ 重试10次仍有错误数字，放弃本次购买，进入下个循环")
            pyautogui.press('l')
            time.sleep(0.5)
            main_delta.click_ratio(0.1000, 0.4300)
            return False
    
    def execute_final_steps(self, main_delta):
        """执行购买成功后的最终步骤：跳转开始游戏 + 按L键 + 点击"""
        # 跳转到开始游戏
        self.send_log(LogLevel.INFO, "🎮 跳转到开始游戏...")
        goto_result = main_delta.goto("开始游戏")
        self.send_log(LogLevel.INFO, f"🎮 跳转结果: {goto_result.success if goto_result else False}")
        time.sleep(1)
        
        # 按L键
        self.send_log(LogLevel.INFO, "⌨️ 按L键...")
        press_result = pyautogui.press('l')
        self.send_log(LogLevel.INFO, f"⌨️ 按键结果: {press_result.success if press_result else False}")
        time.sleep(0.5)
        
        # 点击 (0.1000, 0.4300)
        self.send_log(LogLevel.INFO, "🖱️ 点击位置 (0.1000, 0.4300)...")
        for i in range(5):
            time.sleep(0.2)
            click_result = main_delta.click_ratio(0.1000, 0.4300)
            self.send_log(LogLevel.INFO, f"🖱️ 第{i+1}次点击结果: {click_result.success if click_result else False}")
        
        self.send_log(LogLevel.SUCCESS, "✅ 最终步骤全部完成")
        return True
    
    def warehouse_equip_flow(self, main_delta, parent_protocol):
        """仓库配装流程 - 循环直到价格 > 500"""
        while True:
            # 第一步：跳转到仓库
            self.send_log(LogLevel.INFO, "📦 跳转到仓库...")
            main_delta.goto("仓库")
            
            # 第二步：延迟2秒后，点击位置 (0.1576, 0.9609) 三次，每次延迟0.5秒
            time.sleep(2.0)
            self.send_log(LogLevel.INFO, "🖱️ 开始点击位置 (0.1576, 0.9609) (3次)...")
            for i in range(3):
                main_delta.click_ratio(0.1576, 0.9609)
                self.send_log(LogLevel.INFO, f"🖱️ 第{i+1}次点击")
                time.sleep(0.5)
            
            # 第三步：跳转到出售
            self.send_log(LogLevel.INFO, "💰 跳转到出售...")
            main_delta.goto("出售")
            time.sleep(1.0)
            
            # 第四步：搜索前9格并出售
            self.send_log(LogLevel.INFO, "🔍 开始搜索前9格并出售...")
            main_delta.search_and_sell_first_9_items(price_difference=10)
            self.send_log(LogLevel.SUCCESS, "✅ 前9格出售完成")
            
            # 仓库配装流程完成，退出循环
            return True
    
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
            
            self.send_log(LogLevel.SUCCESS, "📊 ===== DPB000X执行报告 =====")
            self.send_log(LogLevel.INFO, f"💰 辅端余额变化: {self.initial_balance:,} → {self.current_balance:,} (花费: {total_cost:,})")
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
            
            # 生成CSV文件名：DPB000X_YYYYMMDD_HHMMSS.csv
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DPB000X_{timestamp}.csv"
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
            
            # 价格记录（不打印日志）
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 价格记录写入失败: {e}")
    
    def save_balance_screenshots(self, balance_before_result, balance_after_result, unit_price):
        """保存余额OCR截图"""
        try:
            # 创建log/screenshots目录
            screenshot_dir = os.path.join(os.getcwd(), "log", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # 生成文件名：DPB000X_第X次_单价_时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存刷新前截图
            if hasattr(balance_before_result, 'screenshot') and balance_before_result.screenshot:
                before_filename = f"DPB000X_第{self.refresh_count}次_刷新前_{timestamp}.png"
                before_path = os.path.join(screenshot_dir, before_filename)
                balance_before_result.screenshot.save(before_path)
                self.debug_log(LogLevel.INFO, f"📸 已保存刷新前截图: {before_filename}")
            
            # 保存刷新后截图
            if hasattr(balance_after_result, 'screenshot') and balance_after_result.screenshot:
                after_filename = f"DPB000X_第{self.refresh_count}次_刷新后_单价{unit_price:.1f}_{timestamp}.png"
                after_path = os.path.join(screenshot_dir, after_filename)
                balance_after_result.screenshot.save(after_path)
                self.debug_log(LogLevel.INFO, f"📸 已保存刷新后截图: {after_filename}")
            
        except Exception as e:
            self.send_log(LogLevel.WARNING, f"⚠️ 保存截图失败: {e}")


def get_behavior_class():
    return DualPurchaseBehavior

