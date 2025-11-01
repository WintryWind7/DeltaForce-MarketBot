# -*- coding: utf-8 -*-
"""
单端价格刷新行为模块 - SPR919G
通过刷新机制检测低价子弹并自动购买
代码ID: SPR919G (Single Price Refresh 919G)
"""

import sys
import os
import time
import csv
from datetime import datetime
from PySide6.QtCore import QThread, Signal

# 添加路径以导入相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'DeltaForce'))

try:
    from DeltaForceClass import DeltaForceClass
except ImportError:
    print("警告: 无法导入 DeltaForceClass")
    DeltaForceClass = None

# 添加路径以导入 TaskLogger
try:
    from task_logger import get_task_logger
except ImportError:
    def get_task_logger():
        class DummyLogger:
            def add_task_record(self, *args, **kwargs):
                pass
        return DummyLogger()

# 行为信息定义
BEHAVIOR_INFO = {
    "code_id": "SPR919G",  # 内部代码ID
    "title": "单端价格刷新行为 - 919G",
    "description": "通过刷新机制检测低价子弹并自动购买。点击m2刷新，点击m1进入购买界面，识别价格后自动购买。",
    "version": "1.0.0",
    "author": "DeltaForce Team",
    "tags": ["单端", "刷新购买", "919G"],
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
        "ammo_quantity": {
            "type": "int",
            "label": "子弹数量",
            "default": 1500,
            "description": "用于计算单价的子弹数量"
        },
        "refresh_delay": {
            "type": "float",
            "label": "刷新延迟",
            "default": 0.1,
            "step": 0.1,
            "min": 0.0,
            "max": 2.0,
            "description": "刷新操作之间的延迟时间(秒)"
        },
        "ocr_delay": {
            "type": "float",
            "label": "OCR延迟",
            "default": 0.5,
            "step": 0.1,
            "min": 0.0,
            "max": 3.0,
            "description": "点击m1后等待多久才进行OCR识别，防止图像未加载完全(秒)"
        },
        "confirm_delay": {
            "type": "float",
            "label": "二次确认延迟",
            "default": 0.2,
            "step": 0.1,
            "min": 0.0,
            "max": 2.0,
            "description": "价格合理后，二次确认前的等待时间(秒)"
        },
        "debug_mode": {
            "type": "bool",
            "label": "调试模式",
            "default": False,
            "description": "启用调试模式，输出详细的OCR识别信息并保存识别图片"
        },
    }
}

class SinglePriceRefresh919GBehavior(QThread):
    """单端价格刷新行为线程 - SPR919G"""
    
    # 信号定义
    log_message = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self, window_handles, config=None):
        super().__init__()
        
        # 基本属性
        self.running = False
        self.should_stop = False
        self.is_running = False
        
        # 窗口句柄
        self.window_handles = window_handles
        
        # 配置参数
        self.config = config or {}
        self.target_price = self.config.get('target_price', 480)
        self.min_price_threshold = self.config.get('min_price_threshold', 200)
        self.ammo_quantity = self.config.get('ammo_quantity', 1500)
        self.refresh_delay = self.config.get('refresh_delay', 0.1)
        self.ocr_delay = self.config.get('ocr_delay', 0.5)
        self.confirm_delay = self.config.get('confirm_delay', 0.2)
        self.debug_mode = self.config.get('debug_mode', False)
        
        # 坐标定义
        self.m1_coord = (0.1032, 0.4857)  # 购买界面按钮
        self.m2_coord = (0.1075, 0.6262)  # 刷新按钮
        
        # 价格识别区域（基于test_300.py的区域）
        self.price_region = {
            'left_ratio': 0.8225,
            'top_ratio': 0.7962,
            'right_ratio': 0.9300,
            'bottom_ratio': 0.8200
        }
        
        # 统计数据
        self.refresh_count = 0
        self.purchase_count = 0
        self.recognition_success_count = 0
        self.recognition_total_count = 0
        
        # 余额相关
        self.initial_balance = None
        self.current_balance = None
        
        # 初始化DeltaForce实例
        self.delta = None
        try:
            if DeltaForceClass and window_handles:
                # 创建Delta实例并绑定到窗口
                self.delta = DeltaForceClass()
                if not self.delta.bind_to_window(window_handles[0]):
                    self.log_message.emit("❌ [SPR919G] 窗口绑定失败")
                    self.delta = None
                else:
                    # 设置日志回调
                    self.delta.set_log_callback(self.log_message.emit)
                    self.log_message.emit(f"✅ [SPR919G] DeltaForce实例初始化成功")
                    
                    # 检查GPU状态
                    try:
                        import torch
                        if torch.cuda.is_available():
                            gpu_name = torch.cuda.get_device_name(0)
                            self.log_message.emit(f"🚀 [SPR919G] OCR使用GPU加速: {gpu_name}")
                        else:
                            self.log_message.emit(f"⚠️ [SPR919G] GPU不可用，OCR使用CPU模式")
                    except ImportError:
                        self.log_message.emit(f"⚠️ [SPR919G] 无法检测GPU状态（PyTorch未安装）")
            else:
                self.log_message.emit(f"❌ [SPR919G] DeltaForce实例初始化失败：缺少必要参数")
        except Exception as e:
            self.delta = None
            self.log_message.emit(f"❌ [SPR919G] DeltaForce实例初始化异常: {e}")
        
        # 任务记录器
        self.task_logger = get_task_logger()
        
        # 日志文件路径
        self.log_file = self._create_log_file_path()
        
        self.log_message.emit(f"🎯 [SPR919G] 单端价格刷新行为初始化完成")
        self.log_message.emit(f"📋 目标价格: {self.target_price}")
        self.log_message.emit(f"📋 最低价格: {self.min_price_threshold}")
        self.log_message.emit(f"📋 子弹数量: {self.ammo_quantity}")
        self.log_message.emit(f"📋 刷新延迟: {self.refresh_delay}秒")
        self.log_message.emit(f"📋 OCR延迟: {self.ocr_delay}秒")
        self.log_message.emit(f"📋 二次确认延迟: {self.confirm_delay}秒")
    
    def _create_log_file_path(self):
        """创建日志文件路径"""
        try:
            # 确保log/pricedate目录存在
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "log", "pricedate")
            os.makedirs(log_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SPR919G_{timestamp}.csv"
            return os.path.join(log_dir, filename)
        except Exception as e:
            self.log_message.emit(f"❌ 创建日志文件路径失败: {e}")
            return None
    
    def stop(self):
        """停止行为"""
        self.should_stop = True
        self.log_message.emit("🛑 正在停止单端价格刷新行为...")
    
    def stop_behavior(self):
        """停止行为（兼容behavior_manager调用）"""
        self.stop()
        if self.isRunning():
            self.wait(5000)
        self.log_message.emit("✅ 行为已完全停止")
    
    
    def write_price_log(self, total_price, unit_price, action):
        """写入价格日志"""
        if not self.log_file:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_exists = os.path.exists(self.log_file)
            
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow(['时间戳', '总价', '单价', '行为', '配置'])
                
                config_info = f"目标价格:{self.target_price},最低价格:{self.min_price_threshold},子弹数量:{self.ammo_quantity}"
                writer.writerow([timestamp, total_price, unit_price, action, config_info])
                
        except Exception as e:
            self.log_message.emit(f"❌ 日志写入失败: {e}")
    
    def _save_debug_image(self, image_array, unit_price, total_price):
        """保存调试图片到log/images文件夹"""
        try:
            # 确保log/images目录存在
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            images_dir = os.path.join(project_root, "log", "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # 生成文件名：单价_总价.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
            filename = f"{unit_price}_{total_price}_{timestamp}.png"
            filepath = os.path.join(images_dir, filename)
            
            # 将numpy数组转换为PIL图像并保存
            from PIL import Image
            if len(image_array.shape) == 3:
                # 彩色图像 (H, W, C)
                image = Image.fromarray(image_array)
            else:
                # 灰度图像 (H, W)
                image = Image.fromarray(image_array, mode='L')
            
            image.save(filepath)
            # 静默保存，不输出任何提示信息
            
        except Exception as e:
            # 静默处理保存失败，不输出提示
            pass
    
    def perform_refresh_sequence(self):
        """执行刷新序列：m2 -> 延迟 -> m1 -> OCR延迟"""
        try:
            # 点击m2刷新
            if not self.delta.click_ratio(self.m2_coord[0], self.m2_coord[1]):
                self.log_message.emit("❌ 点击m2刷新失败")
                return False
            
            time.sleep(self.refresh_delay)
            
            # 点击m1进入购买界面
            if not self.delta.click_ratio(self.m1_coord[0], self.m1_coord[1]):
                return False
            
            # OCR延迟：等待图像完全加载
            if self.ocr_delay > 0:
                time.sleep(self.ocr_delay)
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ 刷新序列执行失败: {e}")
            return False
    
    def recognize_price(self, debug=False):
        """识别价格（使用test_300.py相同的方法）"""
        try:
            # 获取屏幕坐标（与test_300.py相同的方式）
            screen_left, screen_top = self.delta.ratio_to_screen_coords(
                self.price_region['left_ratio'], self.price_region['top_ratio']
            )
            screen_right, screen_bottom = self.delta.ratio_to_screen_coords(
                self.price_region['right_ratio'], self.price_region['bottom_ratio']
            )
            
            # 获取原始截图和预处理后的图像
            raw_screenshot = self.delta.ocr._screenshot((screen_left, screen_top), (screen_right, screen_bottom))
            processed_image = self.delta.ocr._preprocess_image(raw_screenshot, "peizhuang")
            
            # 使用正确的EasyOCR参数（与test_300.py保持一致）
            raw_results = self.delta.ocr.reader.readtext(
                processed_image, 
                allowlist='1234567890', 
                width_ths=0.7, 
                height_ths=0.7, 
                decoder='beamsearch', 
                text_threshold=0.5
            )
            
            self.recognition_total_count += 1
            
            # 合并文本（与test_300.py相同的方式）
            combined_text = "".join(text for _, text, _ in raw_results)
            
            if combined_text and combined_text.isdigit():
                self.recognition_success_count += 1
                total_price = int(combined_text)
                unit_price = total_price // self.ammo_quantity
                
                # 调试模式：只保存图片，不输出日志
                if debug:
                    self._save_debug_image(raw_screenshot, unit_price, total_price)
                
                return total_price, unit_price
            else:
                # 调试模式：识别失败时也保存图片
                if debug:
                    self._save_debug_image(raw_screenshot, "failed", combined_text if combined_text else "empty")
                return None, None
                
        except Exception as e:
            self.log_message.emit(f"❌ 价格识别异常: {e}")
            return None, None
    
    def is_price_valid(self, unit_price):
        """判断价格是否合理"""
        if unit_price is None:
            return False, "识别失败"
        
        if unit_price < self.min_price_threshold:
            return False, "价格过低(识别错误)"
        elif unit_price > self.target_price:
            return False, "价格过高"
        else:
            return True, "价格合理"
    
    def perform_purchase(self):
        """执行购买操作 - 使用delta.click_ratio()统一点击方法"""
        try:
            import pyautogui
            
            # 使用test_300.py中的m2坐标作为购买确认按钮
            purchase_button = (0.8727, 0.7888)  # test_300.py中的m2坐标
            
            # 连续点击5次，每次间隔0.2秒 - 使用delta.click_ratio()
            for i in range(5):
                if not self.delta.click_ratio(purchase_button[0], purchase_button[1]):
                    self.log_message.emit(f"❌ 购买确认第{i+1}次点击失败")
                    return False
                time.sleep(0.2)
            
            # 调和等待3秒
            time.sleep(3)
            
            # 执行2次仓库操作（仿照test_300.py）
            for i in range(2):
                if hasattr(self.delta, 'goto'):
                    self.delta.goto("仓库")
                    time.sleep(1)
                    pyautogui.press('esc')
                    time.sleep(1)
            
            self.log_message.emit("✅ 购买操作执行完成")
            self.purchase_count += 1
            return True
                
        except Exception as e:
            self.log_message.emit(f"❌ 购买操作异常: {e}")
            return False
    
    def check_initial_balance(self):
        """检查初始余额"""
        try:
            self.log_message.emit("💰 正在检查账户余额...")
            
            # 重试3次获取余额
            for attempt in range(3):
                if self.should_stop:
                    return False
                    
                self.initial_balance = self.delta.get_balance()
                time.sleep(0.5)
                
                if self.initial_balance is not None:
                    self.log_message.emit(f"💰 初始余额: {self.initial_balance}")
                    return True
                else:
                    if attempt < 2:  # 不是最后一次尝试
                        self.log_message.emit(f"⚠️ 余额获取失败，重试 ({attempt + 1}/3)")
                        # 分段等待1秒，提高响应性
                        for i in range(10):
                            if self.should_stop:
                                return False
                            time.sleep(0.1)
            
            self.log_message.emit("❌ 余额获取失败，继续运行程序")
            return False
                
        except Exception as e:
            self.log_message.emit(f"❌ 余额检查异常: {e}")
            return False
    
    def check_balance_change(self):
        """检查余额变化"""
        try:
            self.log_message.emit("💰 购买完成，检查余额变化...")
            time.sleep(1)  # 等待余额更新
            
            self.current_balance = self.delta.get_balance()
            time.sleep(0.5)
            
            if self.current_balance is not None and self.initial_balance is not None:
                balance_change = self.initial_balance - self.current_balance
                if balance_change > 0:
                    self.log_message.emit(f"✅ 余额已变化！初始: {self.initial_balance} → 当前: {self.current_balance} (消费: {balance_change})")
                    self.log_message.emit("🎉 购买成功，程序即将结束")
                    return True
                else:
                    self.log_message.emit(f"❌ 余额未变化：初始: {self.initial_balance} → 当前: {self.current_balance}")
                    return False
            else:
                self.log_message.emit("❌ 余额检查失败")
                return False
                
        except Exception as e:
            self.log_message.emit(f"❌ 余额变化检查异常: {e}")
            return False
    
    def press_l_key_sequence(self):
        """按L键序列：按L键 → 等待3秒（让L键生效）"""
        try:
            import pyautogui
            
            # 按下L键
            pyautogui.press('l')
            self.log_message.emit("⌨️ 按下L键")
            
            # 等待3秒（让L键生效，分段等待以提高响应性）
            self.log_message.emit("⏰ 等待3秒让L键生效...")
            for i in range(30):  # 分成30次，每次0.1秒，总共3秒
                if self.should_stop:
                    self.log_message.emit("🛑 检测到停止信号，中断等待")
                    return
                time.sleep(0.1)
            
            self.log_message.emit("✅ L键序列完成，准备开始m2+m1循环")
            
        except Exception as e:
            self.log_message.emit(f"❌ L键序列操作失败: {e}")
    
    def _collect_task_statistics(self):
        """收集任务统计数据"""
        recognition_accuracy = (self.recognition_success_count / self.recognition_total_count * 100) if self.recognition_total_count > 0 else 0
        
        return {
            'behavior_code': 'SPR919G',
            'refresh_count': self.refresh_count,
            'purchase_count': self.purchase_count,
            'recognition_total': self.recognition_total_count,
            'recognition_success': self.recognition_success_count,
            'recognition_accuracy': round(recognition_accuracy, 1),
            'target_price': self.target_price,
            'min_price_threshold': self.min_price_threshold,
            'ammo_quantity': self.ammo_quantity,
            'refresh_delay': self.refresh_delay,
            'ocr_delay': self.ocr_delay,
            'confirm_delay': self.confirm_delay,
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'balance_change': (self.initial_balance - self.current_balance) if (self.initial_balance and self.current_balance) else 0
        }
    
    def run(self):
        """主运行循环"""
        self.is_running = True
        self.running = True
        self.status_changed.emit("running")
        
        try:
            self.log_message.emit("🚀 [SPR919G] 单端价格刷新行为开始运行")
            self.log_message.emit("📋 正确流程: 检查余额 → 按L键 → 等待3秒 → 开始m2+m1循环 → 价格识别 → 购买 → 检查余额")
            self.log_message.emit("⚠️ 注意: 这是一次性脚本，购买成功后将自动结束")
            
            # 检查DeltaForce实例
            if not self.delta:
                self.log_message.emit("❌ DeltaForce实例未初始化，无法继续")
                return
            
            # 检查初始余额
            if not self.check_initial_balance():
                self.log_message.emit("⚠️ 初始余额检查失败，但继续运行程序")
            
            consecutive_failures = 0
            max_failures = 10
            
            # 第一次运行前：执行L键序列
            self.log_message.emit("🔄 初始化 | 执行L键序列")
            self.press_l_key_sequence()
            
            while not self.should_stop:
                try:
                    self.refresh_count += 1
                    
                    # 每次循环都执行刷新序列（从m2开始）
                    if not self.perform_refresh_sequence():
                        self.log_message.emit(f"🔄 第{self.refresh_count}次刷新 | ❌ 刷新序列失败")
                        consecutive_failures += 1
                        time.sleep(1)
                        continue
                    
                    # 识别价格调试模式逻辑：
                    # 1. 如果配置启用调试模式，则始终调试
                    # 2. 前3次刷新启用调试（帮助初始诊断）
                    # 3. 连续失败5次后启用调试（帮助问题排查）
                    # 4. 每50次刷新启用一次调试（定期检查）
                    debug_mode = (self.debug_mode or 
                                 self.refresh_count <= 3 or 
                                 consecutive_failures >= 5 or 
                                 self.refresh_count % 50 == 0)
                    total_price, unit_price = self.recognize_price(debug=debug_mode)
                    
                    if total_price is not None and unit_price is not None:
                        # 重置连续失败计数
                        consecutive_failures = 0
                        
                        # 判断价格是否合理
                        is_valid, reason = self.is_price_valid(unit_price)
                        
                        # 输出单行日志：刷新次数 + 单价与目标价格对比
                        if is_valid:
                            self.log_message.emit(f"🔄 第{self.refresh_count}次刷新 | 单价:{unit_price} ≤ 目标:{self.target_price} ✅ 价格合理，开始购买")
                            
                            # 二次确认
                            time.sleep(self.confirm_delay)
                            confirm_total, confirm_unit = self.recognize_price()
                            
                            if confirm_total is not None and confirm_unit is not None:
                                confirm_valid, confirm_reason = self.is_price_valid(confirm_unit)
                                
                                if confirm_valid:
                                    self.log_message.emit(f"✅ 二次确认通过！单价:{confirm_unit} ≤ 目标:{self.target_price}")
                                    
                                    # 执行购买
                                    if self.perform_purchase():
                                        self.write_price_log(confirm_total, confirm_unit, "购买成功")
                                        self.log_message.emit("🎉 购买操作完成！")
                                        
                                        # 检查余额变化
                                        if self.check_balance_change():
                                            # 余额有变化，购买成功，结束程序
                                            self.log_message.emit("✅ 购买成功确认，程序结束")
                                            self.should_stop = True
                                            break
                                        else:
                                            # 余额无变化，回到步骤2：点击L键+等待3秒
                                            self.log_message.emit("⚠️ 余额未变化，回到步骤2：执行L键序列后继续尝试")
                                            self.press_l_key_sequence()
                                    else:
                                        self.write_price_log(confirm_total, confirm_unit, "购买失败")
                                        self.log_message.emit("❌ 购买操作失败，继续循环")
                                else:
                                    self.log_message.emit(f"❌ 二次确认失败: 单价:{confirm_unit} > 目标:{self.target_price}")
                                    self.write_price_log(confirm_total, confirm_unit, f"二次确认失败-{confirm_reason}")
                            else:
                                self.log_message.emit("❌ 二次确认识别失败，继续循环")
                        else:
                            # 价格不合理，输出对比信息
                            if unit_price < self.min_price_threshold:
                                self.log_message.emit(f"🔄 第{self.refresh_count}次刷新 | 单价:{unit_price} < 最低:{self.min_price_threshold} ❌ 识别错误")
                            else:
                                self.log_message.emit(f"🔄 第{self.refresh_count}次刷新 | 单价:{unit_price} > 目标:{self.target_price} ❌ 价格过高")
                            self.write_price_log(total_price, unit_price, reason)
                    else:
                        # 识别失败，重新开始循环
                        consecutive_failures += 1
                        self.log_message.emit(f"🔄 第{self.refresh_count}次刷新 | OCR识别失败 ({consecutive_failures}/{max_failures}) - 重新开始循环")
                        
                        # 检查连续失败次数
                        if consecutive_failures >= max_failures:
                            self.log_message.emit(f"⚠️ 连续{max_failures}次识别失败，可能需要检查游戏状态")
                            consecutive_failures = 0  # 重置计数器
                            # 长时间等待（分段等待以提高响应性）
                            for i in range(50):  # 分成50次，每次0.1秒，总共5秒
                                if self.should_stop:
                                    break
                                time.sleep(0.1)
                        
                        # 识别失败时直接继续下一轮循环，不执行其他操作
                        continue
                    
                    
                except Exception as e:
                    self.log_message.emit(f"❌ 运行过程中发生异常: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            self.log_message.emit(f"❌ 主循环异常: {e}")
        finally:
            self.running = False
            self.is_running = False
            self.status_changed.emit("stopped")
            
            # 收集统计数据
            statistics = self._collect_task_statistics()
            
            # 记录任务完成
            if self.task_logger:
                self.task_logger.add_task_record(
                    script_id="SPR919G",
                    task_data=statistics
                )
            
            # 输出统计信息
            self.log_message.emit("📊 任务统计:")
            self.log_message.emit(f"   刷新次数: {statistics['refresh_count']}")
            self.log_message.emit(f"   购买次数: {statistics['purchase_count']}")
            self.log_message.emit(f"   识别准确率: {statistics['recognition_accuracy']}%")
            if statistics['initial_balance'] and statistics['final_balance']:
                self.log_message.emit(f"   初始余额: {statistics['initial_balance']}")
                self.log_message.emit(f"   最终余额: {statistics['final_balance']}")
                self.log_message.emit(f"   消费金额: {statistics['balance_change']}")
            
            self.log_message.emit("🏁 [SPR919G] 单端价格刷新行为已停止")

# 导出行为类
def get_behavior_class():
    """返回行为类"""
    return SinglePriceRefresh919GBehavior
