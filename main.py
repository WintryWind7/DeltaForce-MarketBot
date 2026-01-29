# -*- coding: utf-8 -*-
"""
DeltaForce MarketBot GUI 主入口
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from gui.splash_screen import SplashScreen

def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("DeltaForce MarketBot")
    app.setApplicationVersion("0.5.1")
    app.setOrganizationName("DeltaForce")
    
    # 设置高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建并显示启动界面
    splash = SplashScreen()
    splash.show()
    
    # 运行应用程序
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()
