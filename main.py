import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

def main():
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("PaperTrackerEyeLabeler")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("PaperTrackerEyeLabeler Team")
    app.setOrganizationDomain("papertracker-eye.com")
    
    # 设置全局字体
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # 设置高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        print("开始创建主窗口...")
        
        # 延迟导入主窗口，避免循环导入问题
        from src.main_window import MainWindow
        
        # 创建主窗口
        window = MainWindow()
        
        # 检查是否成功初始化
        if hasattr(window, 'initialization_success') and window.initialization_success:
            print("主窗口创建成功，启动应用...")
            return app.exec_()
        else:
            print("主窗口初始化失败或用户取消了启动对话框")
            return 0
            
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 显示错误消息
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("启动错误")
        msg.setText(f"应用程序启动失败：\n{str(e)}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return 1

if __name__ == "__main__":
    sys.exit(main())