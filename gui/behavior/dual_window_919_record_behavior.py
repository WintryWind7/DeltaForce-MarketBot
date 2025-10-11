# -*- coding: utf-8 -*-
"""
双端满仓919行为模块 - 录制版
实现主辅两个窗口的自动切换聚焦，针对录制场景优化延迟
"""

# 行为信息定义
BEHAVIOR_INFO = {
    "title": "双端满仓919 - 录制版",
    "description": "自动在主辅两个DeltaForce窗口之间切换聚焦状态，专为录制场景优化，延迟调整为0.6秒以确保录制稳定性。",
    "version": "1.0.0",
    "author": "DeltaForce Team"
}

import os
import sys
import time
import threading
from PySide6.QtCore import QThread, Signal

# 添加DeltaForce路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'DeltaForce'))

# 导入新的管理器
from DeltaForceManager import DeltaForceManager

class DualWindow919RecordBehavior(QThread):
    """双端满仓919行为线程 - 录制版"""
    
    # 信号定义
    log_message = Signal(str)  # 日志消息
    status_changed = Signal(str)  # 状态变化
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
        self.switch_interval = self.config.get('switch_interval', 2.0)  # 切换间隔，默认2秒
        
        # 窗口状态
        self.current_focus = "main"  # 当前聚焦的窗口：main/aux
        
        # 子线程管理
        self.child_threads = []  # 存储所有子线程
        self.thread_lock = threading.Lock()  # 线程锁
        
        # click_ammo线程控制
        self.click_ammo_thread = None
        self.click_ammo_active = threading.Event()  # 控制click_ammo线程的启停
        self.click_ammo_stop = threading.Event()    # 停止click_ammo线程
        
        # 识别准确率统计
        self.recognition_stats = {
            'total_count': 0,       # 总识别次数
            'normal_count': 0,      # 正常识别次数
            'error_count': 0,       # 识别错误次数（低于最低价）
            'none_count': 0         # None次数（未识别到）
        }
        self.min_valid_price = 200  # 最低有效价格，低于此价格认为是识别错误
        
        # 特殊操作后的调和状态
        self.harmony_mode = False  # 是否处于调和模式
        self.harmony_count = 0     # 调和模式下的操作计数
        
    def stop_behavior(self):
        """停止行为"""
        self.should_stop = True
        self.log_message.emit("🛑 正在停止双端满仓919录制版...")
        
        # 先停止click_ammo线程
        self.stop_click_ammo()
        
        # 停止所有子线程
        self.stop_all_child_threads()
        
        # 输出识别准确率统计
        self.output_recognition_stats()
    
    def update_recognition_stats(self, price):
        """
        更新识别统计数据
        
        Args:
            price: 识别到的价格，可能是数字、字符串或None
        """
        self.recognition_stats['total_count'] += 1
        
        if price is None:
            # 未识别到
            self.recognition_stats['none_count'] += 1
        else:
            try:
                price_int = int(price)
                if price_int < self.min_valid_price:
                    # 识别错误（低于最低有效价格）
                    self.recognition_stats['error_count'] += 1
                else:
                    # 正常识别
                    self.recognition_stats['normal_count'] += 1
            except (ValueError, TypeError):
                # 转换失败，认为是识别错误
                self.recognition_stats['error_count'] += 1
    
    def output_recognition_stats(self):
        """输出识别准确率统计"""
        stats = self.recognition_stats
        total = stats['total_count']
        
        if total == 0:
            self.log_message.emit("📊 无识别统计数据")
            return
        
        # 计算百分比
        normal_rate = (stats['normal_count'] / total) * 100
        error_rate = (stats['error_count'] / total) * 100
        none_rate = (stats['none_count'] / total) * 100
        
        self.log_message.emit("=" * 50)
        self.log_message.emit("📊 识别准确率统计报告 - 录制版")
        self.log_message.emit("=" * 50)
        self.log_message.emit(f"📈 总识别次数: {total}")
        self.log_message.emit(f"✅ 正常识别: {stats['normal_count']} 次 ({normal_rate:.1f}%)")
        self.log_message.emit(f"❌ 识别错误: {stats['error_count']} 次 ({error_rate:.1f}%)")
        self.log_message.emit(f"⚪ 未识别到: {stats['none_count']} 次 ({none_rate:.1f}%)")
        self.log_message.emit(f"🔍 最低有效价格阈值: {self.min_valid_price}")
        self.log_message.emit("=" * 50)
    
    def write_price_log(self, price, action):
        """写入价格日志到本地文件 - 基于test_300.py的实现"""
        import datetime
        import csv
        import os
        
        log_file = "deltaforce_919_record_price_log.csv"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 检查文件是否存在，不存在则创建并写入表头
        file_exists = os.path.exists(log_file)
        
        try:
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 如果文件不存在，写入表头
                if not file_exists:
                    writer.writerow(['时间戳', '价格', '行为'])
                
                # 写入数据
                writer.writerow([timestamp, price, action])
                
        except Exception as e:
            self.log_message.emit(f"⚠️ 写入价格日志失败: {e}")
    
    def create_child_thread(self, target_function, *args, **kwargs):
        """
        创建并管理子线程
        
        Args:
            target_function: 线程要执行的函数
            *args, **kwargs: 传递给目标函数的参数
            
        Returns:
            threading.Thread: 创建的线程对象
        """
        def wrapped_function(*args, **kwargs):
            try:
                target_function(*args, **kwargs)
            except Exception as e:
                self.log_message.emit(f"⚠️ 子线程异常: {e}")
        
        # 创建daemon线程，主程序结束时自动终止
        thread = threading.Thread(
            target=wrapped_function, 
            args=args, 
            kwargs=kwargs, 
            daemon=True  # 关键：设置为daemon线程
        )
        
        # 添加到管理列表
        with self.thread_lock:
            self.child_threads.append(thread)
        
        return thread
    
    def stop_all_child_threads(self):
        """停止所有子线程"""
        with self.thread_lock:
            active_threads = [t for t in self.child_threads if t.is_alive()]
            if active_threads:
                self.log_message.emit(f"🛑 正在停止 {len(active_threads)} 个子线程...")
                
                # 设置停止标志（如果子线程检查should_stop的话）
                for thread in active_threads:
                    if hasattr(thread, 'should_stop'):
                        thread.should_stop = True
                
                # 等待线程结束（最多等待3秒）
                for thread in active_threads:
                    thread.join(timeout=3.0)
                    if thread.is_alive():
                        self.log_message.emit(f"⚠️ 线程 {thread.name} 未能正常结束")
                
                self.child_threads.clear()
                self.log_message.emit("✅ 所有子线程已停止")
    
    def start_click_ammo_thread(self):
        """启动click_ammo线程"""
        if self.click_ammo_thread is None or not self.click_ammo_thread.is_alive():
            self.click_ammo_stop.clear()
            self.click_ammo_active.set()  # 开始时设为激活状态
            self.click_ammo_thread = self.create_child_thread(self.click_ammo_worker)
            self.click_ammo_thread.start()
            self.log_message.emit("🔫 click_ammo线程已启动")
    
    def pause_click_ammo(self):
        """暂停click_ammo线程"""
        self.click_ammo_active.clear()
        self.log_message.emit("⏸️ click_ammo线程已暂停")
    
    def resume_click_ammo(self):
        """恢复click_ammo线程"""
        self.click_ammo_active.set()
        self.log_message.emit("▶️ click_ammo线程已恢复")
    
    def stop_click_ammo(self):
        """停止click_ammo线程"""
        self.click_ammo_stop.set()
        self.click_ammo_active.set()  # 确保线程能够检查到停止信号
        if self.click_ammo_thread and self.click_ammo_thread.is_alive():
            self.click_ammo_thread.join(timeout=2.0)
        self.log_message.emit("🛑 click_ammo线程已停止")
    
    def click_ammo_worker(self):
        """click_ammo工作线程"""
        while not self.should_stop and not self.click_ammo_stop.is_set():
            try:
                # 等待激活信号
                self.click_ammo_active.wait()
                
                # 检查是否需要停止
                if self.should_stop or self.click_ammo_stop.is_set():
                    break
                
                # 执行click_ammo（使用辅助窗口）
                if self.aux_delta and hasattr(self.aux_delta, 'click_ammo'):
                    self.aux_delta.click_ammo()
                
                # 短暂延迟，避免过于频繁的点击
                time.sleep(0.1)
                
            except Exception as e:
                self.log_message.emit(f"⚠️ click_ammo线程异常: {e}")
                time.sleep(0.1)
    
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
            
            if not self.aux_delta:
                self.log_message.emit("⚠️ 未找到辅助窗口，将以单窗口模式运行")
            
            # 输出窗口信息
            summary = self.manager.get_window_info_summary()
            self.log_message.emit(f"✅ 窗口管理器初始化成功")
            if summary['main_window']:
                self.log_message.emit(f"   主窗口: {summary['main_window']['hwnd']} ({summary['main_window']['size']})")
            if summary['aux_window']:
                self.log_message.emit(f"   辅窗口: {summary['aux_window']['hwnd']} ({summary['aux_window']['size']})")
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ 初始化管理器失败: {e}")
            return False
    
    def main_logic_worker(self):
        """919主逻辑工作线程 - 录制版（新架构）"""
        try:
            # 初始化DeltaForceManager
            if not self.initialize_manager():
                return
            
            # 启动click_ammo线程
            self.start_click_ammo_thread()
            
            # 聚焦到辅助窗口开始操作
            if self.aux_delta:
                self.manager.focus_aux()
                self.log_message.emit("🔄 已聚焦到辅助窗口")
            
            # 主循环
            cycle_count = 0
            while not self.should_stop:
                try:
                    cycle_count += 1
                    
                    # 主程序逻辑：get_ammo_price(4) -> 延迟0.01 -> esc -> 延迟0.6 (录制版延迟) (目标价格200-480)
                    if self.aux_delta and hasattr(self.aux_delta, 'get_ammo_price'):
                        price = self.aux_delta.get_ammo_price(4)
                        
                        # 更新识别统计
                        self.update_recognition_stats(price)
                        
                        if price is not None:
                            # 检查是否处于调和模式
                            if self.harmony_mode:
                                self.harmony_count += 1
                                self.log_message.emit(f"[{cycle_count}] 识别数字: {price} (调和模式 {self.harmony_count}/2)")
                                
                                # 调和模式下强制视为不满足条件
                                self.write_price_log(price, f"调和模式-强制不满足条件({self.harmony_count}/2)")
                                
                                # 检查是否完成调和
                                if self.harmony_count >= 2:
                                    self.harmony_mode = False
                                    self.harmony_count = 0
                                    self.log_message.emit("🎵 调和模式完成，恢复正常判断")
                            else:
                                self.log_message.emit(f"[{cycle_count}] 识别数字: {price}")
                                
                                # 将价格转换为整数进行比较
                                try:
                                    price_int = int(price)
                                    # 检查价格是否在200-480区间内
                                    if 200 <= price_int <= 480:
                                        self.log_message.emit(f"🎯 价格 {price} 在目标区间内，执行特殊操作")
                                        
                                        # 记录满足条件的价格
                                        self.write_price_log(price, "满足条件-执行特殊操作")
                                        
                                        # 停止click_ammo线程
                                        self.pause_click_ammo()
                                        
                                        # 切换到主端
                                        if self.main_delta:
                                            if self.manager.focus_main():
                                                self.log_message.emit("🔄 已切换到主端")
                                                
                                                # 窗口切换后缓冲延迟
                                                time.sleep(0.1)
                                                
                                                # 先点击预备位置 (0.0711, 0.1985)
                                                self.main_delta.click_ratio(0.0711, 0.1985)
                                                self.log_message.emit("🖱️ 主端预备点击完成")
                                                time.sleep(0.02)
                                                
                                                # 循环点击0.8511，0.7994 3次，每次延迟0.05s
                                                for i in range(3):
                                                    if self.should_stop:
                                                        break
                                                    self.main_delta.click_ratio(0.8511, 0.7994)
                                                    self.log_message.emit(f"🖱️ 主端点击 {i+1}/3")
                                                    time.sleep(0.05)
                                                
                                                # 延迟1s
                                                time.sleep(1.0)
                                                
                                                # 切换回辅端
                                                if self.manager.focus_aux():
                                                    self.log_message.emit("🔄 已切换回辅助端")
                                                    
                                                    # 恢复click_ammo线程
                                                    self.resume_click_ammo()
                                                    
                                                    # 延迟1s
                                                    time.sleep(1.0)
                                                    
                                                    # 特殊操作完成后，也需要执行ESC来恢复辅端状态
                                                    self.log_message.emit("🔄 特殊操作完成，执行ESC恢复辅端状态")
                                                    import pyautogui
                                                    pyautogui.press('esc')
                                                    time.sleep(0.6)  # 录制版延迟：0.45 -> 0.6
                                                    
                                                    # 启用调和模式，前2次操作视为不满足条件
                                                    self.harmony_mode = True
                                                    self.harmony_count = 0
                                                    self.log_message.emit("🎵 启用调和模式，前2次操作将视为不满足条件")
                                                    
                                                    # 跳过下面的常规ESC操作
                                                    continue
                                                else:
                                                    self.log_message.emit("❌ 切换回辅助端失败")
                                            else:
                                                self.log_message.emit("❌ 切换到主端失败")
                                    else:
                                        # 记录不满足条件的价格
                                        if price_int < 200:
                                            self.write_price_log(price, "价格过低-识别错误")
                                        else:
                                            self.write_price_log(price, "价格过高-不满足条件")
                                            
                                except (ValueError, TypeError) as e:
                                    self.log_message.emit(f"🔢 价格转换失败: {price} -> {e}")
                                    self.write_price_log(price, "转换失败-识别错误")
                        else:
                            self.log_message.emit(f"[{cycle_count}] 识别数字: None (未识别到)")
                            self.write_price_log("None", "未识别到-延迟错误")
                    
                    # 延迟0.01s
                    time.sleep(0.01)
                    
                    # 按ESC键 - 与test文件保持一致
                    import pyautogui
                    pyautogui.press('esc')
                    
                    # 延迟0.6s (录制版延迟：0.45 -> 0.6)
                    time.sleep(0.6)
                    
                except Exception as e:
                    self.log_message.emit(f"⚠️ 主逻辑异常: {e}")
                    time.sleep(0.5)
                    
        except Exception as e:
            self.log_message.emit(f"❌ 919主逻辑启动失败: {e}")
        finally:
            # 确保停止click_ammo线程
            self.stop_click_ammo()
    
    
    
    def run(self):
        """主运行循环 - 专门执行919逻辑 - 录制版"""
        self.is_running = True
        self.status_changed.emit("running")
        
        try:
            self.log_message.emit("🚀 双端满仓919录制版 开始运行...")
            self.log_message.emit("🎥 录制版特性：延迟优化为0.6秒，确保录制稳定性")
            
            # 每次执行都有启动延迟，防止意外触发
            startup_delay = 3.0
            self.log_message.emit(f"⏳ 启动延迟 {startup_delay} 秒，准备中...")
            self.log_message.emit("💡 这个延迟每次执行都会有，确保操作安全")
            for i in range(int(startup_delay * 10)):
                if self.should_stop:
                    return
                time.sleep(0.1)
            
            # 初始检查将在main_logic_worker中的initialize_manager中进行
            self.log_message.emit("🔍 开始检测DeltaForce窗口...")
            
            # 直接运行919逻辑，不启动额外的子线程
            self.main_logic_worker()
            
        except Exception as e:
            self.log_message.emit(f"❌ 运行异常: {e}")
        finally:
            # 输出识别准确率统计
            self.output_recognition_stats()
            
            self.is_running = False
            self.status_changed.emit("stopped")
            self.finished_signal.emit(not self.should_stop)  # True表示正常完成，False表示被中断

