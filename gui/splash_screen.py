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

class InitializationWorker(QThread):
    """初始化工作线程"""
    progress_updated = Signal(int, str)  # 进度值, 状态文本
    finished = Signal(object)  # 完成信号，传递初始化好的对象
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
    
    def run(self):
        """执行初始化任务"""
        try:
            # 步骤1: 导入必要模块
            self.progress_updated.emit(5, "正在导入系统模块...")
            import sys
            import os
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
            
            # 步骤8: 基本功能检查
            self.progress_updated.emit(95, "正在进行基本功能检查...")
            # 检查窗口枚举功能是否可用
            try:
                from DeltaForceWindow import enum_windows
                windows = enum_windows()
                self.progress_updated.emit(98, f"窗口功能检查完成，发现 {len(windows)} 个窗口")
            except Exception as check_error:
                self.progress_updated.emit(98, f"窗口功能检查警告: {str(check_error)}")
            
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
        
        # 版本信息
        version_label = QLabel("版本 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        frame_layout.addWidget(version_label)
        
        # 状态标签
        self.status_label = QLabel("正在启动...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: white; font-size: 14px; margin: 10px;")
        frame_layout.addWidget(self.status_label)
        
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
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        frame_layout.addWidget(self.progress_bar)
        
        # 底部信息
        footer_label = QLabel("© 2025 WintryWind")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #7f8c8d; font-size: 10px; margin-top: 10px;")
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
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
        
    def on_initialization_finished(self, delta):
        """初始化完成"""
        # 停止超时定时器
        if hasattr(self, 'timeout_timer'):
            self.timeout_timer.stop()
            
        self.delta = delta
        # 即使delta为None也继续启动GUI（离线模式）
        QTimer.singleShot(500, self.close_and_show_main)
    
    def on_initialization_timeout(self):
        """初始化超时处理"""
        self.timeout_timer.stop()
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
