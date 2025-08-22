# main.py
import sys
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                               QVBoxLayout, QPushButton, QFrame, QLabel, QMessageBox, QSizePolicy)


class DragBar(QWidget):
    """可拖拽的分割线控件（带安全父级检测）"""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window  # 直接引用主窗口
        self.setCursor(Qt.CursorShape.SplitHCursor)
        self.setFixedWidth(3)
        self.dragging = False
        self.start_pos = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.start_pos = event.globalPosition().toPoint()
            self.initial_left_width = self.main_window.left_panel.width()
            self.initial_right_width = self.main_window.right_panel.width()

    def mouseMoveEvent(self, event):
        if self.dragging:
            # 计算横向移动距离
            delta = event.globalPosition().toPoint().x() - self.start_pos.x()

            # 计算新宽度（限制最小尺寸）
            new_left = max(200, self.initial_left_width + delta)
            new_right = max(300, self.initial_right_width - delta)

            # 应用新宽度
            self.main_window.left_panel.setFixedWidth(new_left)
            self.main_window.right_panel.setFixedWidth(new_right)

    def mouseReleaseEvent(self, event):
        self.dragging = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("改进版可拖拽分栏界面")
        self.resize(1200, 800)

        # 初始化面板
        self.left_panel = QFrame()
        self.right_panel = QFrame()

        self._init_ui()
        self._load_style()

    def _load_style(self):
        with open("style.css", "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

    def _init_ui(self):
        # 主容器
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧面板初始化
        self.left_panel.setObjectName("LeftPanel")
        self._init_panel(self.left_panel, "主工作区", [
            ("📦 物品管理", None),
            ("📊 数据分析", None)
        ])
        self.left_panel.setMinimumWidth(200)
        main_layout.addWidget(self.left_panel)

        # 分割线（直接传递主窗口引用）
        self.drag_bar = DragBar(self)
        main_layout.addWidget(self.drag_bar)

        # 右侧面板初始化
        self.right_panel.setObjectName("RightPanel")
        self.right_panel.setMinimumWidth(300)
        self._init_panel(self.right_panel, "辅助面板", [
            ("📝 运行日志", None),
            ("⚙ 系统监控", None)
        ])
        main_layout.addWidget(self.right_panel)

        # 底部工具栏
        bottom_bar = QFrame()
        bottom_bar.setObjectName("BottomBar")
        self._init_bottom_bar(bottom_bar)

        # 主窗口布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(main_widget, stretch=1)
        layout.addWidget(bottom_bar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(central_widget)

    def _init_panel(self, panel, title, buttons):
        """统一面板初始化方法"""
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        panel.setLayout(QVBoxLayout())
        panel.layout().setContentsMargins(5, 5, 5, 5)
        panel.layout().setSpacing(10)

        btn_container = QWidget()
        btn_container.setLayout(QHBoxLayout())
        btn_container.layout().setContentsMargins(0, 0, 0, 0)
        btn_container.layout().setSpacing(8)

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setMinimumSize(120, 40)  # 设置最小尺寸
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if callback:
                btn.clicked.connect(callback)
            btn_container.layout().addWidget(btn)

        panel.layout().addWidget(btn_container)
        panel.layout().addStretch()  # 保持按钮在顶部


    def _init_bottom_bar(self, bar):
        """底部工具栏初始化"""
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 8, 20, 8)

        settings_btn = QPushButton("系统设置")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.clicked.connect(self.show_settings)

        layout.addStretch()
        layout.addWidget(settings_btn)

    def show_settings(self):
        QMessageBox.information(self, "设置", "系统设置功能已触发")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())