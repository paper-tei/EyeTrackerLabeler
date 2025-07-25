"""
UI样式管理模块
负责应用的主题和样式定义
"""
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication


def get_main_stylesheet() -> str:
    """获取主样式表"""
    return """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f9fc, stop:1 #e9ecef);
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
        }
        QWidget {
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            font-size: 11pt;
        }
        QLabel {
            color: #495057;
            font-size: 11pt;
            padding: 2px;
        }
        QLineEdit {
            border: 2px solid #e9ecef;
            border-radius: 6px;
            padding: 10px 15px;
            font-size: 11pt;
            background-color: white;
            color: #495057;
            min-height: 20px;
        }
        QLineEdit:focus {
            border-color: #007bff;
            background-color: #f8f9ff;
        }
        QTextEdit {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            background-color: #ffffff;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 10pt;
            color: #495057;
            padding: 12px;
        }
        QGroupBox {
            font-size: 12pt;
            font-weight: 600;
            color: #495057;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 15px;
            background-color: rgba(255, 255, 255, 0.9);
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 20px;
            padding: 0 10px;
            background-color: white;
            border-radius: 4px;
        }
        QCheckBox {
            font-size: 11pt;
            color: #495057;
            font-weight: 500;
            padding: 5px;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
            border: 2px solid #ced4da;
            border-radius: 4px;
            background-color: white;
        }
        QCheckBox::indicator:checked {
            background-color: #007bff;
            border-color: #007bff;
        }
        QStatusBar {
            background: white;
            border-top: 1px solid #dee2e6;
            font-size: 10pt;
            color: #6c757d;
            padding: 8px;
        }
    """


def get_tab_widget_stylesheet() -> str:
    """获取选项卡样式"""
    return """
        QTabWidget::pane {
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background-color: white;
            margin-top: -1px;
        }
        QTabBar::tab {
            background-color: #f8f9fa;
            border: 2px solid #dee2e6;
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            margin-right: 2px;
            font-weight: 600;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid white;
        }
        QTabBar::tab:hover {
            background-color: #e9ecef;
        }
    """


def get_scrollarea_stylesheet() -> str:
    """获取滚动区域样式"""
    return """
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        QScrollBar:vertical {
            border: none;
            background: #f8f9fa;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #dee2e6;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #adb5bd;
        }
    """


def get_slider_stylesheet() -> str:
    """获取滑块样式"""
    return """
        QSlider::groove:horizontal {
            border: 1px solid #dee2e6;
            height: 8px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #007bff;
            border: 2px solid #0056b3;
            width: 20px;
            margin: -7px 0;
            border-radius: 10px;
        }
        QSlider::handle:horizontal:hover {
            background: #0056b3;
        }
    """


def get_spinbox_stylesheet() -> str:
    """获取数值输入框样式"""
    return """
        QSpinBox {
            border: 2px solid #e9ecef;
            border-radius: 6px;
            padding: 8px;
            font-weight: 600;
            min-width: 60px;
        }
        QSpinBox:focus {
            border-color: #007bff;
        }
    """


def get_status_label_styles() -> dict:
    """获取状态标签样式"""
    return {
        "connected": """
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 10px 15px;
                background-color: #d4edda;
                border-radius: 6px;
                color: #155724;
                border: 1px solid #c3e6cb;
                margin: 5px 0;
            }
        """,
        "connecting": """
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 10px 15px;
                background-color: #fff3cd;
                border-radius: 6px;
                color: #856404;
                border: 1px solid #ffeaa7;
                margin: 5px 0;
            }
        """,
        "disconnected": """
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 10px 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                color: #dc3545;
                border: 1px solid #f5c6cb;
                margin: 5px 0;
            }
        """,
        "recording": """
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 8px 15px;
                background-color: #f5c6cb;
                border-radius: 6px;
                color: #721c24;
                border: 1px solid #f1b0b7;
            }
        """,
        "standby": """
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 8px 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                color: #6c757d;
                border: 1px solid #dee2e6;
            }
        """,
        "duration": """
            QLabel {
                font-family: "Consolas", monospace;
                font-weight: 600;
                font-size: 12pt;
                color: #007bff;
                padding: 8px 15px;
                background-color: #f0f8ff;
                border-radius: 6px;
                border: 1px solid #b3d7ff;
            }
        """,
        "count": """
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                color: #28a745;
                padding: 8px 15px;
                background-color: #f0fff4;
                border-radius: 6px;
                border: 1px solid #b3e5b3;
            }
        """,
        "info": """
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                background-color: #f8f9fa;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #e9ecef;
            }
        """
    }


def get_button_styles() -> dict:
    """获取按钮样式定义"""
    return {
        "large_primary": """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 18px 30px;
                font-size: 13pt;
                font-weight: 700;
                min-height: 30px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """,
        "large_danger": """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 18px 30px;
                font-size: 13pt;
                font-weight: 700;
                min-height: 30px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """,
        "compact": """
            QPushButton {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """
    }


def apply_modern_theme(app: QApplication):
    """应用现代主题"""
    palette = QPalette()
    
    # 设置调色板
    palette.setColor(QPalette.Window, QColor(248, 249, 252))
    palette.setColor(QPalette.WindowText, QColor(73, 80, 87))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(233, 236, 239))
    palette.setColor(QPalette.ToolTipBase, QColor(0, 123, 255))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(73, 80, 87))
    palette.setColor(QPalette.Button, QColor(248, 249, 250))
    palette.setColor(QPalette.ButtonText, QColor(73, 80, 87))
    palette.setColor(QPalette.BrightText, QColor(220, 53, 69))
    palette.setColor(QPalette.Link, QColor(0, 123, 255))
    palette.setColor(QPalette.Highlight, QColor(0, 123, 255))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(font)
