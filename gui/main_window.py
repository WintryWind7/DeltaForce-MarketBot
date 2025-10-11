#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QStatusBar,
    QMenuBar, QMenu, QStackedWidget, QFrame, QGridLayout,
    QSpinBox, QDoubleSpinBox, QScrollArea, QFormLayout
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QFont, QAction

import sys
import os
import json
# 添加DeltaForce目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'DeltaForce'))
from DeltaForceClass import DeltaForceClass

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, delta=None):
        super().__init__()
        self.current_page = "action"  # 当前页面
        self.current_action = None  # 当前选中的行为
        
        # 使用传入的DeltaForce实例，如果没有则创建新的
        if delta is not None:
            self.delta = delta
        else:
            # 兼容直接启动主窗口的情况
            from DeltaForceClass import DeltaForceClass
            self.delta = DeltaForceClass()
        
        # 进程监控相关
        self.process_widgets = {}  # 存储进程显示组件
        self.last_processes = []   # 上次检测到的进程
        self.process_roles = {}    # 存储进程的主辅角色 {hwnd: 'main'/'aux'}
        
        # 创建定时器用于实时更新进程信息
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self.update_process_info)
        self.process_timer.start(2000)  # 每2秒更新一次
        
        # 移除脚本管理器，只使用behavior模块
        
        # 行为线程管理
        self.current_behavior = None
        self.input_monitor = None
        
        # 行为管理器
        from gui.behavior_manager import BehaviorManager
        self.behavior_manager = BehaviorManager()
        
        # 配置控件存储
        self.config_widgets = {}  # 存储各个行为的配置控件 {behavior_id: {param_name: widget}}
        
        # 配置文件路径
        self.config_file = "behavior_configs.json"
        
        # 加载保存的配置
        self.saved_configs = self.load_configs()
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口基本属性
        self.setWindowTitle("DeltaForce MarketBot")
        self.setMinimumSize(QSize(800, 600))
        self.resize(1000, 700)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局（水平布局：左侧导航栏 + 右侧内容区）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建左侧导航栏
        self.create_sidebar(main_layout)
        
        # 创建右侧内容区域
        self.create_main_content(main_layout)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
    def create_sidebar(self, parent_layout):
        """创建左侧导航栏"""
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(200)
        sidebar_widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                background-color: #34495e;
                border: none;
                color: white;
                padding: 15px;
                text-align: left;
                font-size: 14px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton[selected="true"] {
                background-color: #3498db;
                font-weight: bold;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # 应用标题
        title_label = QLabel("DeltaForce MarketBot")
        title_label.setFont(QFont("", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("padding: 20px; background-color: #1a252f; color: white;")
        sidebar_layout.addWidget(title_label)
        
        # 导航按钮
        self.nav_buttons = {}
        
        # 行为按钮（第一个）
        action_btn = QPushButton("⚡ 行为")
        action_btn.clicked.connect(lambda: self.switch_page("action"))
        action_btn.setProperty("selected", "true")
        self.nav_buttons["action"] = action_btn
        sidebar_layout.addWidget(action_btn)
        
        # 主页按钮
        main_btn = QPushButton("🏠 主页")
        main_btn.clicked.connect(lambda: self.switch_page("main"))
        self.nav_buttons["main"] = main_btn
        sidebar_layout.addWidget(main_btn)
        
        # 进程按钮
        process_btn = QPushButton("🖥️ 进程")
        process_btn.clicked.connect(lambda: self.switch_page("process"))
        self.nav_buttons["process"] = process_btn
        sidebar_layout.addWidget(process_btn)
        
        # 设置按钮
        settings_btn = QPushButton("⚙️ 设置")
        settings_btn.clicked.connect(lambda: self.switch_page("settings"))
        self.nav_buttons["settings"] = settings_btn
        sidebar_layout.addWidget(settings_btn)
        
        # 日志按钮
        log_btn = QPushButton("📋 日志")
        log_btn.clicked.connect(lambda: self.switch_page("log"))
        self.nav_buttons["log"] = log_btn
        sidebar_layout.addWidget(log_btn)
        
        # 关于按钮
        about_btn = QPushButton("ℹ️ 关于")
        about_btn.clicked.connect(lambda: self.switch_page("about"))
        self.nav_buttons["about"] = about_btn
        sidebar_layout.addWidget(about_btn)
        
        # 添加弹性空间
        sidebar_layout.addStretch()
        
        parent_layout.addWidget(sidebar_widget)
        
    def create_main_content(self, parent_layout):
        """创建右侧主内容区域"""
        # 创建堆叠窗口部件用于切换不同页面
        self.stacked_widget = QStackedWidget()
        
        # 创建各个页面
        self.create_action_page()
        self.create_main_page()
        self.create_process_page()
        self.create_settings_page()
        self.create_log_page()
        self.create_about_page()
        
        parent_layout.addWidget(self.stacked_widget)
        
    def create_action_page(self):
        """创建行为页面"""
        # 创建行为页面的堆叠窗口
        self.action_stacked = QStackedWidget()
        
        # 创建行为选择页面
        self.create_action_selection_page()
        
        # 创建具体行为设置页面
        self.create_action_detail_pages()
        
        self.stacked_widget.addWidget(self.action_stacked)
        
    def create_action_selection_page(self):
        """创建行为选择页面"""
        selection_page = QWidget()
        layout = QVBoxLayout(selection_page)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 页面标题
        title = QLabel("选择执行行为")
        title.setFont(QFont("", 18, QFont.Bold))
        layout.addWidget(title)
        
        # 行为列表容器
        actions_container = QWidget()
        actions_layout = QVBoxLayout(actions_container)
        
        # 从行为管理器获取行为列表
        behavior_list = self.behavior_manager.get_behavior_list()
        
        if not behavior_list:
            # 如果没有找到行为，显示提示
            no_behavior_label = QLabel("未找到可用的行为模块")
            no_behavior_label.setAlignment(Qt.AlignCenter)
            no_behavior_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 40px;")
            actions_layout.addWidget(no_behavior_label)
        else:
            # 创建行为卡片
            for behavior in behavior_list:
                # 为不同行为设置不同图标
                icon_map = {
                    "test_300_behavior": "💰",
                    "dual_window_919_behavior": "🔄",
                    "dual_window_919_record_behavior": "📹",
                    "custom_ammo_dual_behavior": "🎯",
                    "test_basic_behavior": "🔧",
                    "custom_behavior": "📝"
                }
                
                action_data = {
                    "id": behavior['id'],
                    "name": behavior['title'],
                    "description": behavior['description'],
                    "icon": icon_map.get(behavior['id'], "⚡"),
                    "version": behavior.get('version', '1.0.0'),
                    "author": behavior.get('author', 'Unknown')
                }
                
                action_card = self.create_action_card(action_data)
                actions_layout.addWidget(action_card)
        
        layout.addWidget(actions_container)
        layout.addStretch()
        
        self.action_stacked.addWidget(selection_page)
        
    def create_action_card(self, action):
        """创建行为卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 8px;
                margin: 2px;
                background-color: white;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # 左侧图标
        icon_label = QLabel(action["icon"])
        icon_label.setFont(QFont("", 20))
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("border: none; background-color: #ecf0f1; border-radius: 25px;")
        layout.addWidget(icon_label)
        
        # 右侧信息
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        name_label = QLabel(action["name"])
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(action["description"])
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 添加点击事件
        card.mousePressEvent = lambda event, action_id=action["id"]: self.select_action(action_id)
        
        return card
        
    def create_action_detail_pages(self):
        """创建具体行为的详细设置页面"""
        # 动态为所有behavior创建详细页面
        behavior_list = self.behavior_manager.get_behavior_list()
        
        for behavior in behavior_list:
            self.create_behavior_detail_page(behavior)
    
    def create_behavior_detail_page(self, behavior):
        """创建通用的行为详细设置页面"""
        detail_page = QWidget()
        layout = QVBoxLayout(detail_page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 返回按钮和标题
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← 返回选择")
        back_btn.clicked.connect(lambda: self.action_stacked.setCurrentIndex(0))
        back_btn.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; padding: 8px 15px; border-radius: 5px; }")
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        title = QLabel(f"{behavior['title']} 设置")
        title.setFont(QFont("", 18, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 行为描述
        desc_label = QLabel(behavior['description'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin: 10px 0px;")
        layout.addWidget(desc_label)
        
        # 版本和作者信息
        info_layout = QHBoxLayout()
        version_label = QLabel(f"版本: {behavior.get('version', '1.0.0')}")
        version_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        info_layout.addWidget(version_label)
        
        author_label = QLabel(f"作者: {behavior.get('author', 'Unknown')}")
        author_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        info_layout.addWidget(author_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(line)
        
        # 配置区域（支持自定义参数）
        config_label = QLabel("配置选项:")
        config_label.setFont(QFont("", 14, QFont.Bold))
        config_label.setStyleSheet("margin-top: 20px;")
        layout.addWidget(config_label)
        
        # 创建配置控件容器
        config_container = self.create_config_container(behavior)
        layout.addWidget(config_container)
        
        # 弹性空间
        layout.addStretch()
        
        # 执行按钮
        execute_btn = QPushButton(f"执行 {behavior['title']}")
        execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        execute_btn.clicked.connect(lambda: self.execute_action(behavior['id']))
        layout.addWidget(execute_btn)
        
        # 添加到堆栈
        self.action_stacked.addWidget(detail_page)
    
    def create_config_container(self, behavior):
        """创建配置参数容器"""
        behavior_info = self.behavior_manager.get_behavior_info(behavior['id'])
        
        # 检查是否有自定义配置
        if not behavior_info or 'module' not in behavior_info:
            # 没有自定义配置，显示默认提示
            config_info = QLabel("该行为使用默认配置运行。")
            config_info.setStyleSheet("color: #7f8c8d; font-size: 12px; margin: 10px 0px;")
            return config_info
        
        module = behavior_info['module']
        custom_config = getattr(module, 'BEHAVIOR_INFO', {}).get('custom_config', {})
        
        if not custom_config:
            # 没有自定义配置，显示默认提示
            config_info = QLabel("该行为使用默认配置运行。")
            config_info.setStyleSheet("color: #7f8c8d; font-size: 12px; margin: 10px 0px;")
            return config_info
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        
        # 创建配置表单
        config_widget = QWidget()
        form_layout = QFormLayout(config_widget)
        form_layout.setSpacing(10)
        
        # 初始化该行为的配置控件字典
        if behavior['id'] not in self.config_widgets:
            self.config_widgets[behavior['id']] = {}
        
        # 为每个配置参数创建控件
        for param_name, param_config in custom_config.items():
            param_type = param_config.get('type', 'int')
            label_text = param_config.get('label', param_name)
            default_value = param_config.get('default', 0)
            description = param_config.get('description', '')
            
            # 检查是否有保存的配置值
            if (behavior['id'] in self.saved_configs and 
                param_name in self.saved_configs[behavior['id']]):
                default_value = self.saved_configs[behavior['id']][param_name]
            
            # 创建标签
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            
            # 根据类型创建对应的控件
            if param_type == 'int':
                widget = QSpinBox()
                widget.setMinimum(param_config.get('min', 0))
                widget.setMaximum(param_config.get('max', 9999))
                widget.setValue(default_value)
                widget.setStyleSheet("""
                    QSpinBox {
                        padding: 5px;
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QSpinBox:focus {
                        border-color: #3498db;
                    }
                """)
            elif param_type == 'float':
                widget = QDoubleSpinBox()
                widget.setMinimum(param_config.get('min', 0.0))
                widget.setMaximum(param_config.get('max', 999.9))
                widget.setSingleStep(param_config.get('step', 0.1))
                widget.setDecimals(1)
                widget.setValue(default_value)
                widget.setStyleSheet("""
                    QDoubleSpinBox {
                        padding: 5px;
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QDoubleSpinBox:focus {
                        border-color: #3498db;
                    }
                """)
            else:
                # 默认使用整数控件
                widget = QSpinBox()
                # 如果没有指定范围，使用更大的范围以避免限制用户输入
                widget.setMinimum(param_config.get('min', 0))
                widget.setMaximum(param_config.get('max', 999999))
                widget.setValue(default_value)
            
            # 存储控件引用
            self.config_widgets[behavior['id']][param_name] = widget
            
            # 连接值变化信号，实现自动保存
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.on_config_changed)
            elif isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self.on_config_changed)
            
            # 创建描述标签
            if description:
                desc_label = QLabel(f"({description})")
                desc_label.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
                desc_label.setWordWrap(True)
                
                # 创建垂直布局包含控件和描述
                widget_container = QWidget()
                widget_layout = QVBoxLayout(widget_container)
                widget_layout.setContentsMargins(0, 0, 0, 0)
                widget_layout.setSpacing(2)
                widget_layout.addWidget(widget)
                widget_layout.addWidget(desc_label)
                
                form_layout.addRow(label, widget_container)
            else:
                form_layout.addRow(label, widget)
        
        scroll_area.setWidget(config_widget)
        return scroll_area
    
    def get_behavior_config(self, behavior_id):
        """获取行为的当前配置"""
        config = {}
        
        if behavior_id in self.config_widgets:
            for param_name, widget in self.config_widgets[behavior_id].items():
                if isinstance(widget, QSpinBox):
                    config[param_name] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    config[param_name] = widget.value()
        
        return config
    
    def load_configs(self):
        """加载保存的配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                    print(f"✅ 加载配置成功，包含 {len(configs)} 个行为的配置")
                    return configs
            else:
                print("📄 配置文件不存在，使用默认配置")
                return {}
        except Exception as e:
            print(f"⚠️ 加载配置失败: {e}")
            return {}
    
    def save_configs(self):
        """保存当前配置"""
        try:
            configs = {}
            
            # 收集所有行为的当前配置
            for behavior_id, widgets in self.config_widgets.items():
                behavior_config = {}
                for param_name, widget in widgets.items():
                    if isinstance(widget, QSpinBox):
                        behavior_config[param_name] = widget.value()
                    elif isinstance(widget, QDoubleSpinBox):
                        behavior_config[param_name] = widget.value()
                
                if behavior_config:  # 只保存非空配置
                    configs[behavior_id] = behavior_config
            
            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=2, ensure_ascii=False)
            
            print(f"💾 配置保存成功，包含 {len(configs)} 个行为的配置")
            return True
            
        except Exception as e:
            print(f"⚠️ 保存配置失败: {e}")
            return False
    
    def apply_saved_config(self, behavior_id):
        """应用保存的配置到控件"""
        if behavior_id in self.saved_configs and behavior_id in self.config_widgets:
            saved_config = self.saved_configs[behavior_id]
            widgets = self.config_widgets[behavior_id]
            
            applied_count = 0
            for param_name, saved_value in saved_config.items():
                if param_name in widgets:
                    widget = widgets[param_name]
                    try:
                        if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                            widget.setValue(saved_value)
                            applied_count += 1
                    except Exception as e:
                        print(f"⚠️ 应用配置 {param_name}={saved_value} 失败: {e}")
            
            if applied_count > 0:
                print(f"🔧 为行为 {behavior_id} 应用了 {applied_count} 个保存的配置")
    
    def on_config_changed(self):
        """配置变化时自动保存"""
        try:
            # 延迟保存，避免频繁写入
            if hasattr(self, '_save_timer'):
                self._save_timer.stop()
            
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self.save_configs)
            self._save_timer.start(1000)  # 1秒后保存
            
        except Exception as e:
            print(f"⚠️ 配置变化处理失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭时保存配置"""
        try:
            self.save_configs()
            print("👋 程序退出，配置已保存")
        except Exception as e:
            print(f"⚠️ 退出时保存配置失败: {e}")
        
        # 停止行为（如果正在运行）
        if hasattr(self, 'current_behavior') and self.current_behavior:
            try:
                self.current_behavior.stop()
            except:
                pass
        
        event.accept()
        
    def select_action(self, action_id):
        """选择具体的行为"""
        self.current_action = action_id
        
        # 动态查找行为对应的页面索引
        behavior_list = self.behavior_manager.get_behavior_list()
        
        # 页面索引：0是选择页面，1开始是详细页面
        for i, behavior in enumerate(behavior_list):
            if behavior['id'] == action_id:
                page_index = i + 1  # +1 因为索引0是选择页面
                self.action_stacked.setCurrentIndex(page_index)
                break
            
    def execute_action(self, action_id):
        """执行具体的行为"""
        # 切换到日志页面以便查看执行过程
        self.switch_page("log")
        
        # 清空日志
        self.log_text.clear()
        self.log_text.append(f"🎯 准备执行行为: {action_id}")
        
        # 使用behavior模块执行
        self.start_behavior(action_id)
        
    def create_main_page(self):
        """创建主页"""
        main_page = QWidget()
        layout = QVBoxLayout(main_page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 页面标题
        title = QLabel("主控制面板")
        title.setFont(QFont("", 18, QFont.Bold))
        layout.addWidget(title)
        
        # 控制区域
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box)
        control_layout = QVBoxLayout(control_frame)
        
        # 基础按钮
        self.start_button = QPushButton("启动程序")
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("QPushButton { font-size: 14px; background-color: #27ae60; color: white; }")
        self.start_button.clicked.connect(self.on_start_clicked)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止程序")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { font-size: 14px; background-color: #e74c3c; color: white; }")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        control_layout.addWidget(self.stop_button)
        
        # 状态显示
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QVBoxLayout(status_frame)
        
        status_label = QLabel("程序状态:")
        status_label.setFont(QFont("", 12, QFont.Bold))
        status_layout.addWidget(status_label)
        
        self.status_display = QLabel("未启动")
        self.status_display.setStyleSheet("QLabel { color: red; font-weight: bold; font-size: 16px; }")
        status_layout.addWidget(self.status_display)
        
        layout.addWidget(control_frame)
        layout.addWidget(status_frame)
        layout.addStretch()
        
        self.stacked_widget.addWidget(main_page)
        
    def create_process_page(self):
        """创建进程监控页面"""
        process_page = QWidget()
        layout = QVBoxLayout(process_page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 页面标题
        title = QLabel("进程监控")
        title.setFont(QFont("", 18, QFont.Bold))
        layout.addWidget(title)
        
        # 进程信息容器
        self.process_container = QWidget()
        process_layout = QVBoxLayout(self.process_container)
        
        # 无进程时的提示
        self.no_process_label = QLabel("未检测到 DeltaForce 进程")
        self.no_process_label.setAlignment(Qt.AlignCenter)
        self.no_process_label.setStyleSheet("color: gray; font-size: 14px; padding: 50px;")
        process_layout.addWidget(self.no_process_label)
        
        layout.addWidget(self.process_container)
        layout.addStretch()
        
        self.stacked_widget.addWidget(process_page)
        
    def create_settings_page(self):
        """创建设置页面"""
        settings_page = QWidget()
        layout = QVBoxLayout(settings_page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("设置")
        title.setFont(QFont("", 18, QFont.Bold))
        layout.addWidget(title)
        
        # 设置内容（暂时为空）
        content = QLabel("设置功能正在开发中...")
        content.setAlignment(Qt.AlignCenter)
        content.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(content)
        
        layout.addStretch()
        self.stacked_widget.addWidget(settings_page)
        
    def create_log_page(self):
        """创建日志页面"""
        log_page = QWidget()
        layout = QVBoxLayout(log_page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("运行日志")
        title.setFont(QFont("", 18, QFont.Bold))
        layout.addWidget(title)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.append("程序已启动，等待操作...")
        layout.addWidget(self.log_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 停止脚本按钮
        self.stop_script_button = QPushButton("🛑 停止脚本")
        self.stop_script_button.setMaximumWidth(120)
        self.stop_script_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; padding: 8px; border-radius: 5px; }")
        self.stop_script_button.clicked.connect(self.stop_current_script)
        button_layout.addWidget(self.stop_script_button)
        
        # 清除日志按钮
        clear_log_button = QPushButton("清除日志")
        clear_log_button.setMaximumWidth(100)
        clear_log_button.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_log_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.stacked_widget.addWidget(log_page)
        
    def create_about_page(self):
        """创建关于页面"""
        about_page = QWidget()
        layout = QVBoxLayout(about_page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("关于")
        title.setFont(QFont("", 18, QFont.Bold))
        layout.addWidget(title)
        
        # 关于内容
        about_text = QLabel("""
        <h3>DeltaForce MarketBot v1.0.0</h3>
        <p>一个用于DeltaForce游戏的自动化交易工具</p>
        <br>
        <p><b>功能特性：</b></p>
        <ul>
        <li>自动价格监控</li>
        <li>智能交易决策</li>
        <li>实时日志记录</li>
        <li>用户友好界面</li>
        </ul>
        <br>
        <p>© 2025 WintryWind</p>
        """)
        about_text.setWordWrap(True)
        about_text.setAlignment(Qt.AlignTop)
        layout.addWidget(about_text)
        
        layout.addStretch()
        self.stacked_widget.addWidget(about_page)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
    def switch_page(self, page_name):
        """切换页面"""
        # 更新按钮状态
        for name, button in self.nav_buttons.items():
            if name == page_name:
                button.setProperty("selected", "true")
                button.setStyleSheet(button.styleSheet())  # 刷新样式
            else:
                button.setProperty("selected", "false")
                button.setStyleSheet(button.styleSheet())  # 刷新样式
        
        # 切换页面
        page_index = {"action": 0, "main": 1, "process": 2, "settings": 3, "log": 4, "about": 5}
        if page_name in page_index:
            self.stacked_widget.setCurrentIndex(page_index[page_name])
            self.current_page = page_name
            self.status_bar.showMessage(f"当前页面: {page_name}")
            
            # 如果切换到行为页面，重置到选择界面
            if page_name == "action":
                self.action_stacked.setCurrentIndex(0)
        
    def on_start_clicked(self):
        """启动按钮点击事件"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_display.setText("运行中")
        self.status_display.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_bar.showMessage("程序运行中...")
        self.log_text.append("程序已启动")
        
    def on_stop_clicked(self):
        """停止按钮点击事件"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_display.setText("已停止")
        self.status_display.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.status_bar.showMessage("程序已停止")
        self.log_text.append("程序已停止")
        
    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        self.log_text.append("日志已清除")
        
    def stop_current_script(self):
        """停止当前运行的脚本"""
        # 停止用户输入监控
        if self.input_monitor and self.input_monitor.isRunning():
            self.input_monitor.stop_monitoring()
            self.input_monitor.wait(1000)  # 等待1秒
            self.log_text.append("✅ 输入监控已停止")
        
        # 停止行为线程
        if self.current_behavior and self.current_behavior.isRunning():
            self.current_behavior.stop_behavior()
            self.current_behavior.wait(3000)  # 等待3秒
            self.log_text.append("✅ 行为线程已停止")
        
        # 只使用behavior模块，无需脚本管理器
    
    def start_behavior(self, behavior_id):
        """启动指定的行为"""
        try:
            # 检查是否有行为正在运行
            if (self.current_behavior and self.current_behavior.isRunning()) or \
               (self.input_monitor and self.input_monitor.isRunning()):
                self.log_text.append("⚠️ 已有行为正在运行中")
                return
            
            # 新架构下不再需要Delta实例的延迟初始化
            # 窗口句柄将直接传递给行为脚本
            
            # 获取行为信息
            behavior_info = self.behavior_manager.get_behavior_info(behavior_id)
            if not behavior_info:
                self.log_text.append(f"❌ 未找到行为: {behavior_id}")
                return
            
            # 获取行为类
            behavior_class = self.behavior_manager.get_behavior_class(behavior_id)
            if not behavior_class:
                self.log_text.append(f"❌ 无法加载行为类: {behavior_id}")
                return
            
            # 创建用户输入监控
            from gui.user_input_monitor import UserInputMonitor
            self.input_monitor = UserInputMonitor(startup_delay=3.0)
            
            # 连接监控信号
            self.input_monitor.user_input_detected.connect(self.on_user_input_detected)
            self.input_monitor.monitor_status.connect(self.log_text.append)
            
            # 获取窗口句柄列表（新架构）
            window_handles = []
            try:
                processes = self.get_deltaforce_processes()
                window_handles = [process['hwnd'] for process in processes]
                self.log_text.append(f"📊 获取到 {len(window_handles)} 个窗口句柄: {window_handles}")
            except Exception as e:
                self.log_text.append(f"⚠️ 获取窗口句柄失败: {e}")
            
            # 获取自定义配置（如果有的话）
            custom_config = self.get_behavior_config(behavior_id)
            
            # 创建行为实例（传递窗口句柄和自定义配置）
            base_config = {
                'max_buy_number': 25*60,
                'low_price': 1680,
                'min_price': 900,
                'price_difference': 35
            }
            
            # 合并自定义配置
            config = {**base_config, **custom_config}
            
            if custom_config:
                self.log_text.append(f"🎛️ 使用自定义配置: {custom_config}")
            
            self.current_behavior = behavior_class(window_handles, config)
            
            # 连接行为信号
            self.current_behavior.log_message.connect(self.log_text.append)
            self.current_behavior.status_changed.connect(self.on_behavior_status_changed)
            self.current_behavior.finished_signal.connect(self.on_behavior_finished)
            
            # 同时启动监控和行为线程
            self.input_monitor.start()
            self.current_behavior.start()
            
            self.log_text.append(f"🚀 {behavior_info['title']} 已启动")
            self.log_text.append("👁️ 用户输入监控已启动")
            
        except Exception as e:
            self.log_text.append(f"❌ 启动行为失败: {e}")
    
    
    def on_behavior_status_changed(self, status):
        """行为状态变化处理"""
        if status == "running":
            self.status_display.setText("运行中")
            self.status_display.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        elif status == "stopped":
            self.status_display.setText("已停止")
            self.status_display.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def on_behavior_finished(self, success):
        """行为完成处理"""
        if success:
            self.log_text.append("✅ 行为正常完成")
        else:
            self.log_text.append("⚠️ 行为被中断")
        
        # 停止监控线程
        if self.input_monitor and self.input_monitor.isRunning():
            self.input_monitor.stop_monitoring()
            self.input_monitor.wait(1000)
        
        self.current_behavior = None
        self.input_monitor = None
    
    def on_user_input_detected(self, message):
        """用户输入检测处理"""
        self.log_text.append(f"🛑 {message} - 正在停止所有线程...")
        
        # 停止行为线程
        if self.current_behavior and self.current_behavior.isRunning():
            self.current_behavior.stop_behavior()
        
        # 停止监控线程
        if self.input_monitor and self.input_monitor.isRunning():
            self.input_monitor.stop_monitoring()
        
        self.log_text.append("🛑 所有线程已停止")
        
    def get_deltaforce_processes(self):
        """获取所有DeltaForce进程信息"""
        try:
            # 使用独立的窗口获取函数
            from gui.window_utils import get_all_deltaforce_windows
            return get_all_deltaforce_windows()
        except Exception as e:
            print(f"获取进程信息失败: {e}")
            return []
    
    def is_window_minimized(self, process):
        """检查窗口是否被最小化（位置为负数）"""
        win_info = process['window_info']
        # 兼容不同的字段名
        x = win_info.get('x', win_info.get('left', 0))
        y = win_info.get('y', win_info.get('top', 0))
        return x < 0 and y < 0
    
    def classify_processes(self, processes):
        """根据窗口大小分类进程为主进程和辅进程，考虑最小化状态"""
        if len(processes) == 0:
            return [], []
        elif len(processes) == 1:
            # 单个进程时，保持或设置为主进程
            hwnd = processes[0]['hwnd']
            self.process_roles[hwnd] = 'main'
            return processes, []
        else:
            # 多个进程的情况
            # 检查是否有窗口被最小化
            minimized_processes = [p for p in processes if self.is_window_minimized(p)]
            normal_processes = [p for p in processes if not self.is_window_minimized(p)]
            
            # 如果有窗口被最小化，保持现有角色分配
            if minimized_processes:
                main_processes = []
                aux_processes = []
                
                for process in processes:
                    hwnd = process['hwnd']
                    # 如果之前有角色记录，保持不变
                    if hwnd in self.process_roles:
                        if self.process_roles[hwnd] == 'main':
                            main_processes.append(process)
                        else:
                            aux_processes.append(process)
                    else:
                        # 新进程，如果没有主进程则设为主进程
                        if not main_processes:
                            self.process_roles[hwnd] = 'main'
                            main_processes.append(process)
                        else:
                            self.process_roles[hwnd] = 'aux'
                            aux_processes.append(process)
                
                return main_processes, aux_processes
            
            else:
                # 所有窗口都正常显示，按窗口大小重新分类
                sorted_processes = sorted(processes, 
                                        key=lambda p: p['window_info']['width'] * p['window_info']['height'])
                
                # 最小的作为主进程，其余作为辅进程
                main_processes = [sorted_processes[0]]
                aux_processes = sorted_processes[1:]
                
                # 更新角色记录
                for process in main_processes:
                    self.process_roles[process['hwnd']] = 'main'
                for process in aux_processes:
                    self.process_roles[process['hwnd']] = 'aux'
                
                return main_processes, aux_processes
    
    def create_process_widget(self, process_info, is_main=True):
        """创建单个进程的显示组件"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("QFrame { border: 2px solid #ddd; border-radius: 8px; padding: 10px; margin: 5px; }")
        
        layout = QHBoxLayout(widget)
        
        # 左侧状态指示器
        status_widget = QLabel()
        status_widget.setFixedSize(60, 60)
        status_widget.setAlignment(Qt.AlignCenter)
        status_widget.setStyleSheet(f"""
            QLabel {{
                background-color: {'#f1c40f' if is_main else '#27ae60'};
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
            }}
        """)
        status_widget.setText("主" if is_main else "辅")
        layout.addWidget(status_widget)
        
        # 右侧信息区域
        info_layout = QVBoxLayout()
        
        # 进程标题
        title_label = QLabel(f"{'主进程' if is_main else '辅进程'}: {process_info['title']}")
        title_label.setFont(QFont("", 12, QFont.Bold))
        info_layout.addWidget(title_label)
        
        # 窗口句柄
        hwnd_label = QLabel(f"句柄: {process_info['hwnd']}")
        hwnd_label.setStyleSheet("color: #666; font-size: 10px; font-family: 'Consolas', monospace;")
        info_layout.addWidget(hwnd_label)
        
        # 窗口位置和大小
        win_info = process_info['window_info']
        pos_label = QLabel(f"位置: ({win_info['left']}, {win_info['top']})")
        size_label = QLabel(f"大小: {win_info['width']} × {win_info['height']}")
        
        # 统一样式设置
        for label in [pos_label, size_label]:
            label.setStyleSheet("color: #666; font-size: 10px; font-family: 'Consolas', monospace;")
            info_layout.addWidget(label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        return widget
    
    def update_process_info(self):
        """更新进程信息显示"""
        try:
            # 获取当前进程
            current_processes = self.get_deltaforce_processes()
            
            # 检查进程是否有变化
            current_hwnds = [p['hwnd'] for p in current_processes]
            last_hwnds = [p['hwnd'] for p in self.last_processes]
            
            if current_hwnds != last_hwnds:
                # 进程有变化，更新显示
                self.refresh_process_display(current_processes)
                self.last_processes = current_processes
                
        except Exception as e:
            print(f"更新进程信息失败: {e}")
    
    def refresh_process_display(self, processes):
        """刷新进程显示"""
        # 清除现有组件
        for widget in self.process_widgets.values():
            widget.setParent(None)
        self.process_widgets.clear()
        
        # 清理已消失进程的角色记录
        current_hwnds = [p['hwnd'] for p in processes]
        self.process_roles = {hwnd: role for hwnd, role in self.process_roles.items() 
                             if hwnd in current_hwnds}
        
        # 获取容器布局
        container_layout = self.process_container.layout()
        
        if len(processes) == 0:
            # 没有进程时显示提示
            self.no_process_label.show()
        else:
            # 隐藏提示标签
            self.no_process_label.hide()
            
            # 分类进程
            main_processes, aux_processes = self.classify_processes(processes)
            
            # 显示主进程
            for process in main_processes:
                widget = self.create_process_widget(process, is_main=True)
                self.process_widgets[process['hwnd']] = widget
                container_layout.addWidget(widget)
            
            # 显示辅进程
            for process in aux_processes:
                widget = self.create_process_widget(process, is_main=False)
                self.process_widgets[process['hwnd']] = widget
                container_layout.addWidget(widget)
        
    def show_about(self):
        """显示关于对话框"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self, 
            "关于 DeltaForce MarketBot",
            "DeltaForce MarketBot v1.0.0\n\n"
            "一个用于DeltaForce游戏的自动化交易工具\n\n"
            "© 2025 WintryWind"
        )
