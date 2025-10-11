# -*- coding: utf-8 -*-
"""
Test 300 交易行为模块 - GUI版本
移植自 DeltaForce/test_300.py，适配GUI多线程环境
"""

# 行为信息定义
BEHAVIOR_INFO = {
    "title": "Test 300 交易",
    "description": "自动化交易脚本，监控价格区间1680-900，自动购买符合条件的物品并出售。支持价格历史分析、智能出售价格计算、调和函数等高级功能。",
    "version": "1.0.0",
    "author": "DeltaForce Team"
}

import os
import sys
import time
import numpy as np
import pyautogui
from collections import Counter
from PySide6.QtCore import QThread, Signal
import datetime
import csv

# 添加DeltaForce路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'DeltaForce'))

# 导入新的管理器
from DeltaForceManager import DeltaForceManager

class Test300Behavior(QThread):
    """Test 300 交易行为线程"""
    
    # 信号定义
    log_message = Signal(str)  # 日志消息
    status_changed = Signal(str)  # 状态变化
    progress_updated = Signal(int)  # 进度更新
    finished_signal = Signal(bool)  # 完成信号
    
    def __init__(self, delta_instance, config=None):
        super().__init__()
        # 注意：delta_instance现在应该是窗口句柄列表，而不是单个Delta实例
        self.window_handles = delta_instance if isinstance(delta_instance, list) else []
        self.config = config or {}
        self.is_running = False
        self.should_stop = False
        
        # 新架构：使用DeltaForceManager管理主辅窗口
        self.manager = None
        self.main_delta = None
        self.aux_delta = None
        
        # 配置参数
        self.max_buy_number = self.config.get('max_buy_number', 25*60)
        self.low_price = self.config.get('low_price', 1680)
        self.min_price = self.config.get('min_price', 900)
        self.price_difference = self.config.get('price_difference', 35)
        
        # 价格历史记录
        self.price_history = []
        
        # 创建image文件夹
        self.image_folder = "DeltaForce/image"
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        
        # 初始化OCR
        try:
            import easyocr
            self.chinese_reader = easyocr.Reader(['ch_sim'])
            self.log_message.emit("✅ EasyOCR 初始化完成")
        except Exception as e:
            self.log_message.emit(f"❌ EasyOCR 初始化失败: {e}")
            self.chinese_reader = None
    
    def stop_behavior(self):
        """停止行为"""
        self.should_stop = True
        self.log_message.emit("🛑 正在停止 Test 300 交易...")
    
    def generate_grid_coords(self):
        """生成9x9网格的中心坐标"""
        left_x = 0.6600
        top_y = 0.2302
        right_x = 0.9234
        bottom_y = 0.6779
        
        grid_width = (right_x - left_x) / 8
        grid_height = (bottom_y - top_y) / 8
        
        grid_coords = []
        for row in range(9):
            for col in range(9):
                x = left_x + col * grid_width
                y = top_y + row * grid_height
                grid_coords.append((x, y))
        
        return grid_coords
    
    def get_price_mode(self, prices):
        """计算价格列表的众数"""
        if not prices:
            return None
        
        counter = Counter(prices)
        most_common = counter.most_common(1)
        return most_common[0][0] if most_common else None
    
    def update_price_history(self, price):
        """更新价格历史记录，保持最近10次记录"""
        self.price_history.append(price)
        if len(self.price_history) > 10:
            self.price_history.pop(0)
    
    def write_purchase_log(self, total_price, unit_price, action):
        """写入购买日志到本地文件"""
        log_file = "DeltaForce/purchase_log.csv"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        file_exists = os.path.exists(log_file)
        
        try:
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow(['时间戳', '总价', '单价', '行为'])
                
                writer.writerow([timestamp, total_price, unit_price, action])
                
        except Exception as e:
            self.log_message.emit(f"❌ 日志写入失败: {e}")
    
    def harmony_function(self):
        """调和函数 - 执行特定的点击和延迟操作序列"""
        try:
            self.log_message.emit("🔄 开始执行调和操作...")
            
            pyautogui.press('esc')
            time.sleep(0.5)
            pyautogui.press('esc')
            time.sleep(0.5)
            pyautogui.press('esc')
            
            # 点击序列
            for i in range(5):
                if self.should_stop:
                    return False
                pyautogui.press('esc')
                time.sleep(0.3)
                self.main_delta.click_ratio(0.1400, 0.2800)
            
            time.sleep(2)
            for i in range(3):
                if self.should_stop:
                    return False
                time.sleep(0.3) 
                self.main_delta.click_ratio(0.8628, 0.8860)

            time.sleep(3)
            self.main_delta.click_ratio(0.4333, 0.2239)
            time.sleep(1)
            self.main_delta.click_ratio(0.8585, 0.6030)
            time.sleep(1)
            
            self.log_message.emit("✅ 调和操作完成，现在处于'开始游戏'界面")
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ 调和操作失败: {e}")
            return False
    
    def check_waiting_status(self):
        """检查指定区域是否显示长度为4的文本"""
        if not self.chinese_reader:
            return False
            
        try:
            top_left_ratio = (0.2497, 0.2524)
            bottom_right_ratio = (0.2917, 0.2724)
            
            screen_left, screen_top = self.main_delta.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
            screen_right, screen_bottom = self.main_delta.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
            
            screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
            screenshot_array = np.array(screenshot)
            
            results = self.chinese_reader.readtext(screenshot_array)
            
            for (bbox, text, confidence) in results:
                if len(text) == 4:
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def main_process(self):
        """主要处理流程"""
        try:
            # 按下L键
            pyautogui.press('l')
            m1 = (0.1000, 0.4900)
            m1_screen = self.main_delta.ratio_to_screen_coords(m1[0], m1[1])
            pyautogui.click(m1_screen[0], m1_screen[1])
            time.sleep(0.02)
            
            # 识别价格区域
            screen_left, screen_top = self.main_delta.ratio_to_screen_coords(0.8225, 0.7962)
            screen_right, screen_bottom = self.main_delta.ratio_to_screen_coords(0.9300, 0.8200)
            
            # 获取预处理后的图像
            processed_image = self.main_delta.ocr._preprocess_image(
                self.main_delta.ocr._screenshot((screen_left, screen_top), (screen_right, screen_bottom)), 
                "peizhuang"
            )
            
            # 使用EasyOCR识别
            raw_results = self.main_delta.ocr.reader.readtext(
                processed_image, 
                allowlist='1234567890', 
                width_ths=0.7, 
                height_ths=0.7, 
                decoder='beamsearch', 
                text_threshold=0.5
            )
            
            # 合并文本
            combined_text = "".join(text for _, text, _ in raw_results)
            
            if combined_text:  # 识别成功
                current_full_price = int(combined_text)
                current_price = int(current_full_price / self.max_buy_number)
                
                # 判断是否满足条件
                if self.min_price <= current_price <= self.low_price:
                    self.log_message.emit(f"✅ 条件满足！总价={current_full_price}, 单价={current_price}")
                    
                    # 二次确认
                    confirm_processed_image = self.main_delta.ocr._preprocess_image(
                        self.main_delta.ocr._screenshot((screen_left, screen_top), (screen_right, screen_bottom)), 
                        "peizhuang"
                    )
                    
                    confirm_raw_results = self.main_delta.ocr.reader.readtext(
                        confirm_processed_image, 
                        allowlist='1234567890', 
                        width_ths=0.7, 
                        height_ths=0.7, 
                        decoder='beamsearch', 
                        text_threshold=0.5
                    )
                    
                    confirm_combined_text = "".join(text for _, text, _ in confirm_raw_results)
                    
                    if confirm_combined_text:
                        confirm_full_price = int(confirm_combined_text)
                        confirm_price = int(confirm_full_price / self.max_buy_number)
                        
                        if self.min_price <= confirm_price <= self.low_price:
                            self.log_message.emit(f"✅ 二次确认通过！总价={confirm_full_price}, 单价={confirm_price}")
                            
                            # 执行购买操作
                            m2 = (0.8727, 0.7888)
                            m2_screen = self.main_delta.ratio_to_screen_coords(m2[0], m2[1])
                            pyautogui.moveTo(m2_screen[0], m2_screen[1])
                            for i in range(5):
                                if self.should_stop:
                                    return False
                                pyautogui.click(m2_screen[0], m2_screen[1])
                                time.sleep(0.2)
                            
                            time.sleep(3)
                            for i in range(2):
                                if self.should_stop:
                                    return False
                                self.main_delta.goto("仓库")
                                time.sleep(1)
                                pyautogui.press('esc')
                                time.sleep(1)
                            
                            # 写入购买成功日志
                            self.write_purchase_log(confirm_full_price, confirm_price, "符合预期")
                            return "purchase_success"
                        else:
                            if confirm_price < self.min_price:
                                self.log_message.emit(f"❌ 二次确认失败：单价={confirm_price} < 最低价格: {self.min_price}")
                            else:
                                self.log_message.emit(f"❌ 二次确认失败：单价={confirm_price} > 目标价格: {self.low_price}")
                            pyautogui.press('esc')
                            time.sleep(0.05)
                            return False
                    else:
                        pyautogui.press('esc')
                        time.sleep(0.05)
                        return False
                else:
                    if current_price < self.min_price:
                        self.log_message.emit(f"❌ 价格异常：单价={current_price} < 最低价格: {self.min_price}")
                        self.write_purchase_log(current_full_price, current_price, "价格过低(异常)")
                    else:
                        self.log_message.emit(f"❌ 条件不满足：单价={current_price} > 目标价格: {self.low_price}")
                        self.update_price_history(current_price)
                        self.write_purchase_log(current_full_price, current_price, "价格过高")
                    
                    pyautogui.press('esc')
                    time.sleep(0.05)
                    return False
            else:
                # 识别失败
                pyautogui.press('esc')
                time.sleep(0.05)
                return "recognition_failed"
                
        except Exception as e:
            self.log_message.emit(f"❌ 处理异常: {e}")
            pyautogui.press('esc')
            time.sleep(0.05)
            return False
    
    def execute_selling_process(self):
        """执行出售流程"""
        try:
            self.log_message.emit("🔄 开始执行出售流程...")
            
            # 点击仓库
            if self.main_delta.goto("仓库"):
                self.log_message.emit("✅ 成功点击仓库")
                time.sleep(2)
                
                # 按下搜索快捷键
                self.main_delta.click_ratio(0.1576, 0.9609)
                time.sleep(1)
                
                # 执行出售操作
                if self.main_delta.goto("出售"):
                    grid_coords = self.generate_grid_coords()
                    success_count = 0
                    target_count = 1
                    
                    # 搜索前三行
                    for i in range(min(27, len(grid_coords))):
                        if self.should_stop:
                            break
                            
                        x_ratio, y_ratio = grid_coords[i]
                        
                        if self.main_delta.click_ratio(x_ratio, y_ratio, do_wait=0.2):
                            bar_price = self.main_delta.get_bar_price()
                            
                            if bar_price is not None:
                                success_count += 1
                                
                                # 执行确认操作
                                self.main_delta.click_ratio(0.7546, 0.5343)
                                time.sleep(0.3)
                                self.main_delta.click_ratio(0.6891, 0.6051)
                                time.sleep(0.2)
                                pyautogui.hotkey('ctrl', 'a')
                                time.sleep(0.2)
                                
                                price_value = int(bar_price)
                                
                                # 计算最低出售价格
                                min_sell_price = None
                                if self.price_history:
                                    mode_price = self.get_price_mode(self.price_history)
                                    if mode_price is not None:
                                        min_sell_price = mode_price - (3 * self.price_difference)
                                        self.log_message.emit(f"📊 价格历史众数: {mode_price}, 最低出售价: {min_sell_price}")
                                
                                input_price = price_value - self.price_difference
                                
                                # 价格刷新循环
                                max_refresh_attempts = 20
                                refresh_count = 0
                                
                                while (min_sell_price is not None and price_value < min_sell_price and 
                                       refresh_count < max_refresh_attempts and not self.should_stop):
                                    refresh_count += 1
                                    self.log_message.emit(f"🔄 价格 {price_value} 低于标准 {min_sell_price}，第{refresh_count}次刷新...")
                                    
                                    pyautogui.press('esc')
                                    time.sleep(1)
                                    
                                    if self.main_delta.click_ratio(x_ratio, y_ratio, do_wait=0.2):
                                        new_bar_price = self.main_delta.get_bar_price()
                                        if new_bar_price is not None:
                                            price_value = int(new_bar_price)
                                            input_price = price_value - self.price_difference
                                            self.log_message.emit(f"📈 刷新后价格: {price_value}")
                                            
                                            if min_sell_price is None or price_value >= min_sell_price:
                                                self.log_message.emit("✅ 价格合适，执行确认操作")
                                                self.main_delta.click_ratio(0.7546, 0.5343)
                                                time.sleep(0.3)
                                                self.main_delta.click_ratio(0.6891, 0.6051)
                                                time.sleep(0.2)
                                                pyautogui.hotkey('ctrl', 'a')
                                                time.sleep(0.2)
                                                break
                                        else:
                                            self.log_message.emit("❌ 刷新后无法获取价格")
                                            break
                                    else:
                                        self.log_message.emit("❌ 重新点击失败")
                                        break
                                
                                # 强制出售逻辑
                                if (min_sell_price is not None and price_value < min_sell_price and 
                                    refresh_count >= max_refresh_attempts):
                                    self.log_message.emit(f"⚠️ 经过{max_refresh_attempts}次刷新仍不合适，强制出售")
                                    input_price = price_value - self.price_difference
                                    self.main_delta.click_ratio(0.7546, 0.5343)
                                    time.sleep(0.3)
                                    self.main_delta.click_ratio(0.6891, 0.6051)
                                    time.sleep(0.2)
                                    pyautogui.hotkey('ctrl', 'a')
                                    time.sleep(0.2)
                                
                                # 输入价格并确认
                                pyautogui.typewrite(str(input_price))
                                time.sleep(0.2)
                                self.main_delta.click_ratio(0.6823, 0.6990)
                                time.sleep(2)
                                
                                # 等待出售状态确认
                                self.log_message.emit("⏳ 等待出售状态确认...")
                                while not self.check_waiting_status() and not self.should_stop:
                                    time.sleep(1)
                                self.log_message.emit("✅ 出售状态确认完成")
                                break
                        
                        time.sleep(0.1)
                    
                    if success_count >= target_count:
                        self.log_message.emit("✅ 出售操作完成")
                    else:
                        self.log_message.emit("⚠️ 出售操作未完全完成")
                else:
                    self.log_message.emit("❌ 出售操作失败")
            else:
                self.log_message.emit("❌ 点击仓库失败")
                
        except Exception as e:
            self.log_message.emit(f"❌ 出售流程异常: {e}")
    
    def execute_next_round(self):
        """执行下一轮准备"""
        try:
            self.log_message.emit("🔄 准备下一轮任务...")
            
            # 预处理操作
            self.main_delta.click_ratio(0.9036, 0.0855)
            time.sleep(2)
            self.main_delta.click_ratio(0.1082, 0.8782)
            time.sleep(3)
            self.main_delta.click_ratio(0.1082, 0.8782)
            time.sleep(1)
            pyautogui.press('esc')
            time.sleep(3)
            
            # 点击开始游戏
            if self.main_delta.goto("开始游戏"):
                self.log_message.emit("✅ 点击开始游戏")
                time.sleep(5)
                self.log_message.emit("🚀 开始下一轮任务...")
            else:
                self.log_message.emit("❌ 点击开始游戏失败")
                
        except Exception as e:
            self.log_message.emit(f"❌ 下一轮准备异常: {e}")
    
    def initialize_manager(self):
        """初始化DeltaForceManager"""
        try:
            # 如果没有提供窗口句柄，从UI获取
            if not self.window_handles:
                from gui.window_utils import get_all_deltaforce_windows
                windows = get_all_deltaforce_windows()
                if not windows:
                    self.log_message.emit("❌ 未找到DeltaForce窗口")
                    return False
                self.window_handles = [window['hwnd'] for window in windows]
            
            # 创建管理器
            self.manager = DeltaForceManager(self.window_handles)
            
            if not self.manager.is_initialized:
                self.log_message.emit("❌ DeltaForceManager初始化失败")
                return False
            
            # 获取主辅实例
            self.main_delta = self.manager.get_main()
            self.aux_delta = self.manager.get_aux()
            
            if not self.main_delta:
                self.log_message.emit("❌ 未找到主窗口")
                return False
            
            # Test300主要使用主窗口
            self.log_message.emit("✅ 窗口管理器初始化成功，使用主窗口进行Test300操作")
            summary = self.manager.get_window_info_summary()
            if summary['main_window']:
                self.log_message.emit(f"   主窗口: {summary['main_window']['hwnd']} ({summary['main_window']['size']})")
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ 初始化管理器失败: {e}")
            return False
    
    def run(self):
        """主运行循环"""
        self.is_running = True
        self.status_changed.emit("running")
        
        try:
            # 初始化DeltaForceManager
            if not self.initialize_manager():
                return
            
            # 检查初始余额
            self.log_message.emit("💰 正在检查账户余额...")
            initial_balance = self.main_delta.get_balance()
            time.sleep(0.5)
            
            if initial_balance is not None:
                self.log_message.emit(f"💰 初始余额: {initial_balance}")
            else:
                self.log_message.emit("⚠️ 余额获取失败，继续运行程序")
            
            self.log_message.emit(f"🎯 程序启动 - 目标价格: {self.min_price}-{self.low_price}")
            
            # 主循环
            consecutive_failures = 0
            max_failures = 10
            
            while not self.should_stop:
                try:
                    # 执行主要处理流程
                    result = self.main_process()
                    
                    if result == "purchase_success":
                        consecutive_failures = 0
                        self.log_message.emit("🎉 购买成功！检查余额变化...")
                        
                        time.sleep(1)
                        current_balance = self.main_delta.get_balance()
                        time.sleep(0.5)
                        
                        if current_balance is not None and initial_balance is not None:
                            balance_change = initial_balance - current_balance
                            if balance_change > 0:
                                self.log_message.emit(f"✅ 余额变化: {initial_balance} → {current_balance} (消费: {balance_change})")
                                
                                # 执行后续流程
                                self.execute_selling_process()
                                if not self.should_stop:
                                    self.execute_next_round()
                                
                                # 更新初始余额
                                initial_balance = current_balance
                            else:
                                self.log_message.emit(f"⚠️ 余额未变化: {initial_balance} → {current_balance}")
                                initial_balance = current_balance
                        else:
                            self.log_message.emit("⚠️ 余额检查失败")
                    
                    elif result == "recognition_failed":
                        consecutive_failures += 1
                        self.log_message.emit(f"❌ 识别失败 ({consecutive_failures}/{max_failures})")
                        
                        if consecutive_failures >= max_failures:
                            self.log_message.emit(f"⚠️ 连续{max_failures}次识别失败，启用调和函数...")
                            if self.harmony_function():
                                self.log_message.emit("✅ 调和函数执行成功")
                                consecutive_failures = 0
                            else:
                                self.log_message.emit("❌ 调和函数执行失败")
                    
                    else:
                        consecutive_failures = 0
                    
                    # 循环间隔
                    if not self.should_stop:
                        time.sleep(0.05)
                        
                except Exception as e:
                    self.log_message.emit(f"❌ 循环异常: {e}")
                    time.sleep(1)
            
            self.log_message.emit("🛑 Test 300 交易已停止")
            
        except Exception as e:
            self.log_message.emit(f"❌ 运行异常: {e}")
        finally:
            self.is_running = False
            self.status_changed.emit("stopped")
            self.finished_signal.emit(not self.should_stop)  # True表示正常完成，False表示被中断
