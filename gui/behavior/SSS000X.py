"""
SSS000X - 单端枪皮行为脚本

该脚本实现单端枪皮操作，通过在两个指定坐标域内随机点击来执行操作。
支持自定义双击延迟和循环间延迟参数。

作者: AI Assistant
版本: 1.0
代码ID: SSS000X
"""

import random
import time
import threading
from datetime import datetime
from PySide6.QtCore import QThread, Signal


# 行为信息配置
BEHAVIOR_INFO = {
    "title": "单端枪皮",
    "description": "在两个坐标域内随机点击，支持双击延迟和循环间延迟控制",
    "code_id": "SSS000X",
    "tags": ["单端", "枪皮"],
    "custom_config": {
        "ocr_check_interval": {
            "type": "float",
            "label": "OCR检测间隔",
            "default": 0.5,
            "step": 0.1,
            "min": 0.1,
            "max": 2.0,
            "description": "OCR识别检测的间隔时间(秒)"
        },
        "auto_click": {
            "type": "bool",
            "label": "自动左键",
            "default": False,
            "description": "启用自动左键点击功能"
        }
    }
}


class SSS000XBehavior(QThread):
    """
    SSS000X - 单端枪皮行为类
    
    执行流程：
    1. 在第一坐标域(0.8250,0.8400)到(0.8650,0.8550)随机选择点m1
    2. 在第二坐标域(0.6000,0.6500)到(0.6600,0.6600)随机选择点m2
    3. 按配置的次数点击m1坐标，每次点击间有延迟
    4. 按配置的次数点击m2坐标，每次点击间有延迟
    5. 循环延迟后重复下一轮，直到按q键退出
    """
    
    # 信号定义
    log_message = Signal(str)
    status_update = Signal(str)
    status_changed = Signal(str)
    finished_signal = Signal(bool)
    
    def __init__(self, window_handles, config=None):
        super().__init__()
        
        # 窗口句柄（单端只需要一个）
        self.window_handles = window_handles
        self.delta = None
        
        # 配置参数
        self.config = config or {}
        self.ocr_check_interval = self.config.get('ocr_check_interval', 0.5)
        self.auto_click = self.config.get('auto_click', False)
        
        # 运行状态
        self.running = False
        self.paused = False
        self.should_stop = False
        
        # 坐标域定义
        self.coord_area1 = {
            'x_min': 0.8250, 'y_min': 0.8400,
            'x_max': 0.8650, 'y_max': 0.8550
        }
        self.coord_area2 = {
            'x_min': 0.6000, 'y_min': 0.6500,
            'x_max': 0.6600, 'y_max': 0.6600
        }
        
        # OCR识别区域
        self.ocr_area = {
            'x_min': 0.8000, 'y_min': 0.8363,
            'x_max': 0.8800, 'y_max': 0.8600
        }
        
        # 预生成的随机坐标（程序开始时确定）
        self.m1_coord = None
        self.m2_coord = None
        
        # 统计数据
        self.cycle_count = 0
        self.click_count = 0
        self.start_time = None
        self.m2_cycle_count = 0  # m2循环次数计数器
        
        # 任务统计数据
        self.task_start_time = datetime.now()
        self.task_data = {
            'start_time': self.task_start_time.isoformat(),
            'status': 'running',
            'statistics': {},
            'summary': ''
        }
        
        # 日志文件 - 保存到 log/pricedate 目录
        self.log_file = self._create_log_file_path()
        
        self.log_message.emit(f"🎯 [SSS000X] OCR识别行为初始化完成")
        self.log_message.emit(f"📋 OCR检测间隔: {self.ocr_check_interval}秒")
        self.log_message.emit(f"📋 自动左键: {'启用' if self.auto_click else '禁用'}")
        self.log_message.emit(f"📋 m1坐标域: ({self.coord_area1['x_min']:.4f},{self.coord_area1['y_min']:.4f}) 到 ({self.coord_area1['x_max']:.4f},{self.coord_area1['y_max']:.4f})")
        self.log_message.emit(f"📋 m2坐标域: ({self.coord_area2['x_min']:.4f},{self.coord_area2['y_min']:.4f}) 到 ({self.coord_area2['x_max']:.4f},{self.coord_area2['y_max']:.4f})")
        self.log_message.emit(f"📋 OCR识别区域: ({self.ocr_area['x_min']:.4f},{self.ocr_area['y_min']:.4f}) 到 ({self.ocr_area['x_max']:.4f},{self.ocr_area['y_max']:.4f})")
        self.log_message.emit(f"⚠️ 按 'Q' 键可随时退出")
    
    def __del__(self):
        """析构函数，确保线程正确停止"""
        try:
            # 强制停止所有活动
            if hasattr(self, 'running'):
                self.running = False
            if hasattr(self, 'should_stop'):
                self.should_stop = True
        except:
            pass  # 忽略析构时的所有错误
    
    def _create_log_file_path(self):
        """创建日志文件路径"""
        import os
        
        # 创建 log/pricedate 目录
        log_dir = os.path.join(os.getcwd(), "log", "pricedate")
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成文件名：SSS000X_YYYYMMDD_HHMMSS.csv
        timestamp = self.task_start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"SSS000X_{timestamp}.csv"
        
        return os.path.join(log_dir, filename)
    
    def _generate_coordinates(self):
        """生成m1和m2的随机坐标"""
        # 生成m1坐标（在m1坐标域内随机）
        self.m1_coord = self._get_random_coord(self.coord_area1)
        # 生成m2坐标（在m2坐标域内随机）
        self.m2_coord = self._get_random_coord(self.coord_area2)
        
        self.log_message.emit(f"🎯 [坐标生成] m1坐标: ({self.m1_coord[0]:.4f}, {self.m1_coord[1]:.4f})")
        self.log_message.emit(f"🎯 [坐标生成] m2坐标: ({self.m2_coord[0]:.4f}, {self.m2_coord[1]:.4f})")
    
    def initialize_delta(self):
        """初始化Delta实例"""
        try:
            if not self.window_handles:
                self.log_message.emit("❌ 未提供窗口句柄")
                return False
            
            # 导入DeltaForceClass
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'DeltaForce'))
            from DeltaForceClass import DeltaForceClass
            
            # 创建Delta实例并绑定到窗口
            self.delta = DeltaForceClass()
            if not self.delta.bind_to_window(self.window_handles[0]):
                self.log_message.emit("❌ 窗口绑定失败")
                return False
            
            # 设置日志回调
            self.delta.set_log_callback(self.log_message.emit)
            
            self.log_message.emit(f"✅ 成功绑定到窗口 {self.window_handles[0]}")
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ Delta初始化失败: {e}")
            return False
    
    def _get_random_coord(self, area):
        """在指定坐标域内生成随机坐标"""
        x = random.uniform(area['x_min'], area['x_max'])
        y = random.uniform(area['y_min'], area['y_max'])
        return (x, y)
    
    # def _move_coordinate(self, coord, coord_name):
    #     """移动到指定坐标"""
    #     try:
    #         x, y = coord
    #         # 使用 move_ratio 方法移动鼠标到目标位置
    #         move_success = self.delta.move_ratio(x, y)
    #         if move_success:
    #             self.click_count += 1
    #             self.log_message.emit(f"🖱️ 移动到{coord_name}: ({x:.4f}, {y:.4f}) - 成功")
    #             return True
    #         else:
    #             self.log_message.emit(f"❌ 移动到{coord_name}: ({x:.4f}, {y:.4f}) - 失败")
    #             return False
    #     except Exception as e:
    #         self.log_message.emit(f"❌ 移动到{coord_name}时发生错误: {e}")
    #         return False
    
    def _move_to_coordinate(self, coord, coord_name):
        """移动到指定坐标"""
        try:
            x, y = coord
            # 使用 move_ratio 方法移动鼠标到目标位置
            move_success = self.delta.move_ratio(x, y)
            if move_success:
                self.log_message.emit(f"🖱️ 移动到{coord_name}: ({x:.4f}, {y:.4f}) - 成功")
                return True
            else:
                self.log_message.emit(f"❌ 移动到{coord_name}: ({x:.4f}, {y:.4f}) - 失败")
                return False
        except Exception as e:
            self.log_message.emit(f"❌ 移动到{coord_name}时发生错误: {e}")
            return False
    
    def _perform_ocr_recognition(self):
        """执行OCR识别"""
        try:
            # 使用Delta的recognize方法进行OCR识别
            top_left = (self.ocr_area['x_min'], self.ocr_area['y_min'])
            bottom_right = (self.ocr_area['x_max'], self.ocr_area['y_max'])
            
            # 执行OCR识别
            result = self.delta.recognize(top_left, bottom_right, save=False, allow_list=None, return_image=False)
            
            if result and len(result) > 0:
                # 提取识别到的文本
                recognized_texts = []
                for detection in result:
                    # 安全地提取文本，处理不同的返回格式
                    try:
                        if isinstance(detection, (list, tuple)) and len(detection) >= 2:
                            text = detection[1]  # OCR结果格式: [bbox, text, confidence]
                        elif isinstance(detection, str):
                            text = detection  # 直接是文本
                        else:
                            continue  # 跳过无法处理的格式
                        
                        if text and str(text).strip():  # 确保文本不为空
                            recognized_texts.append(str(text).strip())
                    except (IndexError, TypeError) as e:
                        self.log_message.emit(f"⚠️ [OCR] 处理检测结果时出错: {e}")
                        continue
                
                if recognized_texts:
                    combined_text = " ".join(recognized_texts)
                    self.log_message.emit(f"🔍 [OCR] 识别到内容: {combined_text}")
                    return True, combined_text
                else:
                    self.log_message.emit(f"🔍 [OCR] 识别结果为空")
                    return False, ""
            else:
                self.log_message.emit(f"🔍 [OCR] 未识别到任何内容")
                return False, ""
                
        except Exception as e:
            self.log_message.emit(f"❌ [OCR] 识别过程发生错误: {e}")
            return False, ""
    
    # def _click_thread_worker(self):
    #     """左键点击线程工作函数"""
    #     import pyautogui
    #     
    #     self.log_message.emit("🖱️ [点击线程] 左键点击线程已启动")
    #     
    #     while self.click_thread_running and self.running:
    #         try:
    #             # 检查是否暂停
    #             if self.paused:
    #                 time.sleep(0.1)
    #                 continue
    #             
    #             # 执行左键点击
    #             pyautogui.click()
    #             
    #             # 分段等待，以便更快响应停止信号
    #             wait_time = self.click_delay
    #             step = 0.05  # 每50ms检查一次
    #             while wait_time > 0 and self.click_thread_running and self.running:
    #                 sleep_time = min(step, wait_time)
    #                 time.sleep(sleep_time)
    #                 wait_time -= sleep_time
    #             
    #         except Exception as e:
    #             self.log_message.emit(f"❌ [点击线程] 点击线程发生错误: {e}")
    #             break
    #     
    #     self.log_message.emit("🛑 [点击线程] 左键点击线程已停止")
    # 
    # def _start_click_thread(self):
    #     """启动左键点击线程"""
    #     if not self.click_thread_running:
    #         self.click_thread_running = True
    #         self.click_thread = threading.Thread(target=self._click_thread_worker, daemon=True)
    #         self.click_thread.start()
    #         self.log_message.emit(f"✅ [点击线程] 启动成功，点击延迟: {self.click_delay}秒")
    # 
    # def _stop_click_thread(self):
    #     """停止左键点击线程"""
    #     if hasattr(self, 'click_thread_running') and self.click_thread_running:
    #         self.click_thread_running = False
    #         
    #         # 等待线程结束
    #         if hasattr(self, 'click_thread') and self.click_thread and self.click_thread.is_alive():
    #             try:
    #                 # 多次尝试停止线程
    #                 for attempt in range(3):
    #                     self.click_thread.join(timeout=0.5)  # 每次等待0.5秒
    #                     if not self.click_thread.is_alive():
    #                         break
    #                     if attempt < 2:  # 不是最后一次尝试
    #                         time.sleep(0.1)
    #                 
    #                 if self.click_thread.is_alive():
    #                     # 线程仍在运行，强制设置为daemon并放弃等待
    #                     self.click_thread.daemon = True
    #                     if hasattr(self, 'log_message'):
    #                         self.log_message.emit("⚠️ [点击线程] 线程未能停止，设置为daemon模式")
    #                 else:
    #                     if hasattr(self, 'log_message'):
    #                         self.log_message.emit("✅ [点击线程] 已正常停止")
    #                         
    #             except Exception as e:
    #                 if hasattr(self, 'log_message'):
    #                     self.log_message.emit(f"❌ [点击线程] 停止线程时发生错误: {e}")
    #         
    #         # 清理线程引用
    #         self.click_thread = None
    
    def _execute_main_logic(self):
        """执行主要逻辑 - 基于OCR识别的条件执行"""
        try:
            # 如果启用自动左键，在OCR识别前点击
            if self.auto_click:
                if self.delta.click():
                    self.log_message.emit(f"🖱️ [自动左键] 在OCR识别前执行点击")
                else:
                    self.log_message.emit(f"❌ [自动左键] 点击失败")
            
            # 执行OCR识别
            has_content, recognized_text = self._perform_ocr_recognition()
            
            if has_content:
                # 识别到内容，继续运行
                self.log_message.emit(f"✅ [逻辑] 识别到内容，继续运行: {recognized_text}")
                return True
            else:
                # 识别结果为空，进入m2循环逻辑
                return self._handle_empty_ocr_result()
            
        except Exception as e:
            self.log_message.emit(f"❌ [逻辑] 执行主逻辑时发生错误: {e}")
            return False
    
    def _handle_empty_ocr_result(self):
        """处理OCR识别结果为空的情况，最多循环3次"""
        try:
            self.m2_cycle_count += 1
            self.log_message.emit(f"⚠️ [逻辑] 识别结果为空，开始第{self.m2_cycle_count}次m2循环 (最多3次)")
            
            # 移动到m2坐标
            if not self._move_to_coordinate(self.m2_coord, "m2"):
                self.log_message.emit(f"❌ [逻辑] 移动到m2坐标失败")
                return False
            
            self.log_message.emit(f"✅ [逻辑] 已移动到m2坐标")
            
            # 如果启用自动左键，在m2位置循环点击20次
            if self.auto_click:
                self._perform_m2_clicks()
            
            # 点击完成后，再次检测OCR
            self.log_message.emit(f"🔍 [逻辑] m2操作完成，重新检测OCR...")
            time.sleep(0.5)  # 短暂等待
            
            # 执行OCR识别
            has_content, recognized_text = self._perform_ocr_recognition()
            
            if has_content:
                # 识别到内容，移动回m1继续
                self.log_message.emit(f"✅ [逻辑] 重新识别到内容，移动回m1继续: {recognized_text}")
                if self._move_to_coordinate(self.m1_coord, "m1"):
                    self.log_message.emit(f"✅ [逻辑] 已移动回m1坐标")
                    self.m2_cycle_count = 0  # 重置m2循环计数器
                    return True  # 继续主循环
                else:
                    self.log_message.emit(f"❌ [逻辑] 移动回m1坐标失败")
                    return False
            else:
                # 仍然没有内容
                if self.m2_cycle_count >= 3:
                    # 已达到最大循环次数，结束任务
                    self.log_message.emit(f"⚠️ [逻辑] 已完成3次m2循环，仍无内容，任务结束")
                    return False
                else:
                    # 继续下一次m2循环
                    self.log_message.emit(f"⚠️ [逻辑] 第{self.m2_cycle_count}次m2循环后仍无内容，继续下一次循环")
                    return self._handle_empty_ocr_result()  # 递归调用进行下一次循环
            
        except Exception as e:
            self.log_message.emit(f"❌ [逻辑] 处理空OCR结果时发生错误: {e}")
            return False
    
    def _perform_m2_clicks(self):
        """在m2位置执行20次点击"""
        try:
            self.log_message.emit(f"🖱️ [自动左键] 开始在m2位置点击20次...")
            for i in range(20):
                if not self.running or self.should_stop:
                    self.log_message.emit(f"🛑 [自动左键] 检测到停止信号，已点击{i}次")
                    break
                
                if self.delta.click():
                    self.log_message.emit(f"🖱️ [自动左键] m2点击 {i+1}/20")
                else:
                    self.log_message.emit(f"❌ [自动左键] m2点击 {i+1}/20 失败")
                
                # 间隔0.05秒
                if i < 19:  # 最后一次不需要等待
                    time.sleep(0.05)
            
            if self.running and not self.should_stop:
                self.log_message.emit(f"✅ [自动左键] m2位置点击完成，共20次")
                
        except Exception as e:
            self.log_message.emit(f"❌ [自动左键] m2点击过程发生错误: {e}")
    
    
    def _collect_task_statistics(self):
        """收集任务统计数据"""
        end_time = datetime.now()
        duration = (end_time - self.task_start_time).total_seconds()
        
        # 计算平均值
        avg_clicks_per_cycle = self.click_count / max(self.cycle_count, 1)
        cycles_per_minute = (self.cycle_count / duration) * 60 if duration > 0 else 0
        
        statistics = {
            'cycle_count': self.cycle_count,
            'click_count': self.click_count,
            'duration': duration,
            'avg_clicks_per_cycle': round(avg_clicks_per_cycle, 2),
            'cycles_per_minute': round(cycles_per_minute, 2),
            'ocr_check_interval': self.ocr_check_interval,
            'auto_click': self.auto_click,
            'ocr_area': f"({self.ocr_area['x_min']:.4f},{self.ocr_area['y_min']:.4f})-({self.ocr_area['x_max']:.4f},{self.ocr_area['y_max']:.4f})",
            'coord_area1': f"({self.coord_area1['x_min']:.4f},{self.coord_area1['y_min']:.4f})-({self.coord_area1['x_max']:.4f},{self.coord_area1['y_max']:.4f})",
            'coord_area2': f"({self.coord_area2['x_min']:.4f},{self.coord_area2['y_min']:.4f})-({self.coord_area2['x_max']:.4f},{self.coord_area2['y_max']:.4f})",
            'm1_coord': f"({self.m1_coord[0]:.4f},{self.m1_coord[1]:.4f})" if self.m1_coord else "未生成",
            'm2_coord': f"({self.m2_coord[0]:.4f},{self.m2_coord[1]:.4f})" if self.m2_coord else "未生成",
            'm2_cycle_count': self.m2_cycle_count
        }
        
        return statistics
    
    def _save_task_record(self):
        """保存任务记录到task_logger"""
        try:
            import sys
            import os
            
            # 添加gui目录到Python路径
            gui_dir = os.path.join(os.getcwd(), 'gui')
            if gui_dir not in sys.path:
                sys.path.append(gui_dir)
            
            from task_logger import get_task_logger
            
            # 更新任务数据
            end_time = datetime.now()
            duration = (end_time - self.task_start_time).total_seconds()
            
            self.task_data.update({
                'end_time': end_time.isoformat(),
                'duration': duration,
                'status': 'completed' if self.running else 'interrupted',
                'statistics': self._collect_task_statistics(),
                'summary': f"运行时长: {duration:.1f}秒 | 循环次数: {self.cycle_count} | 点击次数: {self.click_count} | 平均每轮点击: {self.click_count/max(self.cycle_count,1):.1f} | 每分钟循环: {(self.cycle_count/duration)*60 if duration > 0 else 0:.1f}"
            })
            
            # 保存记录
            task_logger = get_task_logger()
            success = task_logger.add_task_record('SSS000X', self.task_data)
            
            if success:
                self.log_message.emit("📝 [SSS000X] 任务记录已保存")
            else:
                self.log_message.emit("⚠️ [SSS000X] 任务记录保存失败")
                
        except Exception as e:
            self.log_message.emit(f"❌ 保存任务记录时发生错误: {e}")
    
    def run(self):
        """运行行为脚本"""
        try:
            self.running = True
            self.start_time = datetime.now()
            
            # 初始化Delta实例
            if not self.initialize_delta():
                return
            
            self.log_message.emit("=" * 60)
            self.log_message.emit("🚀 [SSS000X] OCR识别行为开始运行")
            self.log_message.emit("=" * 60)
            
            # 生成m1和m2的随机坐标
            self._generate_coordinates()
            
            # 移动到m1坐标
            if self._move_to_coordinate(self.m1_coord, "m1"):
                self.log_message.emit(f"✅ [初始化] 已移动到m1坐标")
            else:
                self.log_message.emit(f"❌ [初始化] 移动到m1坐标失败，但继续运行")
            
            # 主循环
            while self.running and not self.should_stop:
                try:
                    # 检查是否暂停
                    while self.paused and self.running and not self.should_stop:
                        time.sleep(0.1)
                    
                    if not self.running or self.should_stop:
                        break
                    
                    # 执行主要逻辑
                    if not self._execute_main_logic():
                        self.log_message.emit("✅ 主逻辑完成，正常结束")
                        break
                    
                    # 等待下次检测
                    time.sleep(self.ocr_check_interval)
                
                except KeyboardInterrupt:
                    self.log_message.emit("🛑 检测到键盘中断，停止运行")
                    break
                except Exception as e:
                    self.log_message.emit(f"❌ 运行过程中发生错误: {e}")
                    break
            
        except Exception as e:
            self.log_message.emit(f"❌ 运行失败: {e}")
        
        finally:
            # 首先设置停止标志
            self.running = False
            self.should_stop = True
            
            self.status_update.emit("已停止")
            self.status_changed.emit("stopped")
            
            # 打印运行摘要
            self.print_run_summary()
            
            # 保存任务记录
            self._save_task_record()
            
            self.finished_signal.emit(True)  # True表示正常完成
            self.log_message.emit("🏁 [SSS000X] OCR识别行为已停止")
    
    def print_run_summary(self):
        """打印运行摘要"""
        if self.start_time:
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            self.log_message.emit("=" * 60)
            self.log_message.emit("📊 [SSS000X] 运行摘要")
            self.log_message.emit("=" * 60)
            self.log_message.emit(f"⏱️ 运行时长: {duration:.1f}秒")
            self.log_message.emit(f"🔄 完成循环: {self.cycle_count}轮")
            self.log_message.emit(f"🖱️ 总点击次数: {self.click_count}次")
            
            if self.cycle_count > 0:
                avg_clicks = self.click_count / self.cycle_count
                self.log_message.emit(f"📊 平均每轮点击: {avg_clicks:.1f}次")
            
            if duration > 0:
                cycles_per_minute = (self.cycle_count / duration) * 60
                clicks_per_minute = (self.click_count / duration) * 60
                self.log_message.emit(f"⚡ 每分钟循环: {cycles_per_minute:.1f}轮")
                self.log_message.emit(f"⚡ 每分钟点击: {clicks_per_minute:.1f}次")
            
            self.log_message.emit("=" * 60)
    
    def stop(self):
        """停止行为脚本"""
        self.log_message.emit("🛑 [SSS000X] 正在停止...")
        
        # 设置所有停止标志
        self.running = False
        self.should_stop = True
        
        # 等待主线程结束
        if self.isRunning():
            self.wait(1000)  # 等待最多1秒
    
    def pause(self):
        """暂停行为脚本"""
        self.paused = True
        self.log_message.emit("⏸️ [SSS000X] 已暂停")
    
    def resume(self):
        """恢复行为脚本"""
        self.paused = False
        self.log_message.emit("▶️ [SSS000X] 已恢复")


def create_behavior(window_handles, config=None):
    """创建行为实例的工厂函数"""
    return SSS000XBehavior(window_handles, config)
