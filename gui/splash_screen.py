#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动加载界面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from collections import deque

class InitializationWorker(QThread):
    """初始化工作线程"""
    progress_updated = Signal(int, str)  # 进度值, 状态文本
    finished = Signal(object)  # 完成信号，传递初始化好的对象
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
    
    def run(self):
        """执行初始化任务 - 连续执行，无延迟"""
        try:
            # 步骤1: 导入必要模块
            self.progress_updated.emit(5, "正在导入系统模块...")
            import sys
            import os
            import time
            self.progress_updated.emit(10, "系统模块加载完成")
            
            # 步骤2: 添加路径
            self.progress_updated.emit(15, "正在配置路径...")
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'DeltaForce'))
            self.progress_updated.emit(20, "路径配置完成")
            
            # 步骤3: 导入核心依赖
            self.progress_updated.emit(25, "正在导入核心依赖...")
            import numpy as np
            self.progress_updated.emit(35, "NumPy 加载完成")
            
            # 步骤4: 导入OCR模块
            self.progress_updated.emit(40, "正在导入 OCR 模块...")
            import easyocr
            self.progress_updated.emit(50, "EasyOCR 加载完成")
            
            # 步骤5: 导入自动化模块
            self.progress_updated.emit(55, "正在导入自动化模块...")
            import pyautogui
            self.progress_updated.emit(60, "PyAutoGUI 加载完成")
            
            # 步骤6: 导入DeltaForce类
            self.progress_updated.emit(65, "正在导入 DeltaForce 类...")
            from DeltaForceClass import DeltaForceClass
            self.progress_updated.emit(75, "DeltaForce 类加载完成")
            
            # 步骤7: 延迟初始化DeltaForce（避免启动时卡死）
            self.progress_updated.emit(80, "正在初始化 DeltaForce 实例...")
            try:
                # 先只初始化基础OCR功能，不查找游戏窗口
                from DeltaForceRecognize import DeltaForceRecognize
                delta = DeltaForceRecognize()
                self.progress_updated.emit(85, "基础OCR功能初始化完成")
                
                # 添加一个延迟初始化的标记，让GUI启动后再进行完整初始化
                delta._needs_full_init = True
                delta._full_init_class = None
                
                # 导入完整类但不实例化
                from DeltaForceClass import DeltaForceClass
                delta._full_init_class = DeltaForceClass
                
                self.progress_updated.emit(90, "延迟初始化模式准备完成")
                    
            except Exception as delta_error:
                self.progress_updated.emit(85, f"初始化警告: {str(delta_error)}")
                # 最后的降级方案
                delta = None
                self.progress_updated.emit(90, "使用离线模式启动")
            
            # 步骤8: 基本功能检查（可选，失败不影响启动）
            self.progress_updated.emit(95, "正在进行基本功能检查...")
            # 跳过窗口枚举检查，避免阻塞启动流程
            # 这个检查不是必须的，窗口功能会在实际使用时按需初始化
            self.progress_updated.emit(98, "基本功能检查完成（跳过窗口枚举）")
            
            # 步骤9: 完成初始化
            self.progress_updated.emit(100, "初始化完成!")
            
            # 返回初始化好的对象
            self.finished.emit(delta)
            
        except Exception as e:
            self.progress_updated.emit(0, f"初始化失败: {str(e)}")
            self.finished.emit(None)

class SplashScreen(QWidget):
    """启动加载界面"""
    
    def __init__(self):
        super().__init__()
        self.delta = None
        
        # 消息队列和显示控制
        self.message_queue = deque()
        self.current_message = None
        self.message_start_time = None
        self.min_display_time = 300  # 每条消息最少显示300毫秒
        
        # 队列处理定时器
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_message_queue)
        self.queue_timer.start(50)  # 每50毫秒检查一次队列
        
        self.init_ui()
        self.start_initialization()
        
    def init_ui(self):
        """初始化界面"""
        # 设置窗口属性
        self.setWindowTitle("DeltaForce MarketBot - 启动中")
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 居中显示
        screen = self.screen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QFrame {
                border: 2px solid #3498db;
                border-radius: 10px;
                background-color: #34495e;
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建内容框架
        content_frame = QFrame()
        frame_layout = QVBoxLayout(content_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(15)
        
        # 应用标题
        title_label = QLabel("DeltaForce MarketBot")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #3498db; margin: 10px;")
        frame_layout.addWidget(title_label)
        
        # 版本信息 - 从应用程序属性中读取
        from PySide6.QtWidgets import QApplication
        app_version = QApplication.instance().applicationVersion()
        version_label = QLabel(f"版本 {app_version}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        frame_layout.addWidget(version_label)
        
        # 弹性空间，让状态文字和进度条保持在底部区域
        frame_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("正在启动...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #bdc3c7; 
                font-size: 12px;
                border: none;
                background: transparent;
                margin: 0px;
                margin-top: 5px;
                padding: 8px;
                min-height: 20px;
            }
        """)
        self.status_label.raise_()  # 提升到最顶层
        frame_layout.addWidget(self.status_label)
        
        # 适当间距，确保状态文字不被遮挡
        frame_layout.addSpacing(8)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                color: white;
                background-color: #2c3e50;
                margin-top: 0px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        frame_layout.addWidget(self.progress_bar)
        
        # 底部信息
        footer_label = QLabel("© WintryWind")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("""
            color: #7f8c8d; 
            font-size: 10px; 
            margin-top: 10px;
            border: none;
            background: transparent;
        """)
        frame_layout.addWidget(footer_label)
        
        main_layout.addWidget(content_frame)
        
    def start_initialization(self):
        """开始初始化过程"""
        self.worker = InitializationWorker()
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.on_initialization_finished)
        
        # 添加超时定时器，防止初始化卡死
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_initialization_timeout)
        self.timeout_timer.start(30000)  # 30秒超时
        
        self.worker.start()
        
    def update_progress(self, value, status):
        """接收工作线程的进度更新，加入队列"""
        print(f"🔄 收到进度更新: {value}% - {status}")  # 调试输出
        
        # 将消息加入队列
        import time
        self.message_queue.append({
            'value': value,
            'status': status,
            'timestamp': time.time()
        })
        
    def process_message_queue(self):
        """处理消息队列，确保每条消息至少显示指定时间"""
        import time
        current_time = time.time()
        
        # 检查当前消息是否已显示足够时间
        if self.current_message is not None:
            if self.message_start_time is not None:
                elapsed = (current_time - self.message_start_time) * 1000  # 转换为毫秒
                if elapsed < self.min_display_time:
                    return  # 当前消息还需要继续显示
        
        # 如果队列中有新消息，显示下一条
        if self.message_queue:
            message = self.message_queue.popleft()
            self.current_message = message
            self.message_start_time = current_time
            
            # 更新UI
            print(f"📺 显示消息: {message['value']}% - {message['status']}")  # 调试输出
            self.progress_bar.setValue(message['value'])
            self.status_label.setText(message['status'])
            self.status_label.repaint()  # 强制重绘
        
    def on_initialization_finished(self, delta):
        """初始化完成"""
        # 停止超时定时器
        if hasattr(self, 'timeout_timer'):
            self.timeout_timer.stop()
            
        # 停止队列处理定时器
        if hasattr(self, 'queue_timer'):
            self.queue_timer.stop()
            
        self.delta = delta
        # 即使delta为None也继续启动GUI（离线模式）
        QTimer.singleShot(500, self.close_and_show_main)
    
    def on_initialization_timeout(self):
        """初始化超时处理"""
        self.timeout_timer.stop()
        
        # 停止队列处理定时器
        if hasattr(self, 'queue_timer'):
            self.queue_timer.stop()
            
        self.worker.should_stop = True
        self.worker.terminate()  # 强制终止工作线程
        
        self.status_label.setText("初始化超时，使用离线模式启动...")
        self.status_label.setStyleSheet("color: #f39c12; font-size: 14px; margin: 10px;")
        self.progress_bar.setValue(100)
        
        # 使用空对象启动GUI
        self.delta = None
        QTimer.singleShot(1000, self.close_and_show_main)
            
    def close_and_show_main(self):
        """关闭启动界面并显示主窗口"""
        from gui.main_window import MainWindow
        
        # 创建主窗口并传递初始化好的delta对象
        self.main_window = MainWindow(delta=self.delta)
        self.main_window.show()
        
        # 关闭启动界面
        self.close()
        
    def get_main_window(self):
        """获取主窗口实例"""
        return getattr(self, 'main_window', None)
