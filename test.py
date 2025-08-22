# main.py
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QTextEdit, QTabWidget, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal


class ScriptThread(QThread):
    update_log = Signal(str)
    status_changed = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True

    def run(self):
        self.status_changed.emit("运行中")
        while self.running:
            # 这里整合之前的抢购逻辑
            self.update_log.emit("尝试购买商品...")
            # 虚拟点击操作
            # 监控逻辑
            self.msleep(self.config['interval'])

    def stop(self):
        self.running = False
        self.status_changed.emit("已停止")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.script_thread = None

    def init_ui(self):
        # 主窗口设置
        self.setWindowTitle("Delta交易助手 v1.0")
        self.setGeometry(100, 100, 800, 600)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 配置选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # 基础配置页
        basic_tab = QWidget()
        self.setup_basic_tab(basic_tab)
        tab_widget.addTab(basic_tab, "核心设置")

        # 高级配置页
        advance_tab = QWidget()
        self.setup_advance_tab(advance_tab)
        tab_widget.addTab(advance_tab, "高级设置")

        # 状态显示区
        status_bar = QHBoxLayout()
        self.status_label = QLabel("就绪")
        status_bar.addWidget(self.status_label)
        layout.addLayout(status_bar)

        # 日志输出
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        # 控制按钮
        control_buttons = QHBoxLayout()
        self.btn_start = QPushButton("启动")
        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        control_buttons.addWidget(self.btn_start)
        control_buttons.addWidget(self.btn_stop)
        layout.addLayout(control_buttons)

        # 信号连接
        self.btn_start.clicked.connect(self.start_script)
        self.btn_stop.clicked.connect(self.stop_script)

    def setup_basic_tab(self, tab):
        layout = QVBoxLayout(tab)

        # 目标坐标设置
        coord_group = QHBoxLayout()
        coord_group.addWidget(QLabel("目标X坐标:"))
        self.input_x = QSpinBox()
        self.input_x.setRange(0, 65535)
        coord_group.addWidget(self.input_x)

        coord_group.addWidget(QLabel("目标Y坐标:"))
        self.input_y = QSpinBox()
        self.input_y.setRange(0, 65535)
        coord_group.addWidget(self.input_y)
        layout.addLayout(coord_group)

        # 点击频率
        freq_group = QHBoxLayout()
        freq_group.addWidget(QLabel("点击间隔(ms):"))
        self.input_interval = QSpinBox()
        self.input_interval.setRange(10, 5000)
        self.input_interval.setValue(100)
        freq_group.addWidget(self.input_interval)
        layout.addLayout(freq_group)

    def setup_advance_tab(self, tab):
        layout = QVBoxLayout(tab)

        # 安全区域设置
        self.chk_safe_zone = QCheckBox("启用安全区域监控")
        layout.addWidget(self.chk_safe_zone)

        # 多显示器支持
        self.chk_multi_monitor = QCheckBox("多显示器模式")
        layout.addWidget(self.chk_multi_monitor)

    def start_script(self):
        config = {
            'x': self.input_x.value(),
            'y': self.input_y.value(),
            'interval': self.input_interval.value(),
            'safe_zone': self.chk_safe_zone.isChecked()
        }

        self.script_thread = ScriptThread(config)
        self.script_thread.update_log.connect(self.update_log)
        self.script_thread.status_changed.connect(self.update_status)
        self.script_thread.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def stop_script(self):
        if self.script_thread:
            self.script_thread.stop()
            self.script_thread = None
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def update_log(self, message):
        self.log_area.append(f"[{QDateTime.currentDateTime().toString()}] {message}")

    def update_status(self, status):
        self.status_label.setText(status)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 加载QSS样式
    with open("style.qss", "r") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())