"""
PaperTracker 图像录制工具 - 主程序入口
专为小白用户设计的简洁录制界面
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont

# 导入录制器类
from core.base_recorder import BaseRecorder
from core.enhanced_recorder import EnhancedRecorder
from ui.styles import apply_modern_theme


def main():
    """主函数"""
    # 在创建QApplication之前设置高DPI属性
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("PaperTracker图像录制工具")
    app.setApplicationVersion("3.1.0")
    app.setApplicationDisplayName("📷 PaperTracker 图像录制工具")
    
    # 应用现代主题
    apply_modern_theme(app)
    
    # 选择录制器版本
    # 使用 BaseRecorder 创建简单版本
    # 使用 EnhancedRecorder 创建增强版本
    
    # 这里可以根据命令行参数或配置选择版本
    if len(sys.argv) > 1 and sys.argv[1] == '--enhanced':
        window = EnhancedRecorder()
        print("启动增强版录制器...")
    else:
        window = BaseRecorder()
        print("启动标准版录制器...")
    
    window.show()
    
    # 添加启动动画效果
    window.setWindowOpacity(0.0)
    fade_in = QPropertyAnimation(window, b"windowOpacity")
    fade_in.setDuration(500)
    fade_in.setStartValue(0.0)
    fade_in.setEndValue(1.0)
    fade_in.setEasingCurve(QEasingCurve.OutCubic)
    fade_in.start()
    
    # 运行应用程序
    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
