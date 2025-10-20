# -*- coding: utf-8 -*-
"""
用户输入监控模块 - 监控Q键按下
"""

import time
import keyboard
from PySide6.QtCore import QThread, Signal

class UserInputMonitor(QThread):
    """用户输入监控线程"""
    
    # 信号定义
    user_input_detected = Signal(str)  # 检测到用户输入
    monitor_status = Signal(str)  # 监控状态
    
    def __init__(self, startup_delay=3.0):
        super().__init__()
        self.startup_delay = startup_delay  # 启动延迟
        self.is_monitoring = False
        self.should_stop = False
        
    def stop_monitoring(self):
        """停止监控"""
        self.should_stop = True
        self.is_monitoring = False
        # 清理键盘监听
        try:
            keyboard.unhook_all()
        except:
            pass
    
    def on_q_pressed(self, event):
        """Q键按下事件处理"""
        if self.is_monitoring:
            self.user_input_detected.emit("检测到Q键按下")
            self.stop_monitoring()
    
    def run(self):
        """监控主循环"""
        try:
            self.is_monitoring = True
            self.should_stop = False
            
            # 启动延迟，避免点击时的抖动
            self.monitor_status.emit(f"监控将在 {self.startup_delay} 秒后启动...")
            time.sleep(self.startup_delay)
            
            if self.should_stop:
                return
            
            self.monitor_status.emit("👁️ 键盘监控已启动 - 按Q键可退出")
            
            # 注册Q键监听
            keyboard.on_press_key('q', self.on_q_pressed)
            
            # 监控循环（只等待键盘输入）
            while self.is_monitoring and not self.should_stop:
                try:
                    time.sleep(0.1)  # 检查间隔
                    
                except Exception as e:
                    self.monitor_status.emit(f"监控异常: {e}")
                    break
            
            # 清理键盘监听
            keyboard.unhook_all()
            self.monitor_status.emit("👁️ 键盘监控已停止")
            
        except Exception as e:
            self.monitor_status.emit(f"监控线程异常: {e}")
        finally:
            self.is_monitoring = False
            try:
                keyboard.unhook_all()
            except:
                pass
