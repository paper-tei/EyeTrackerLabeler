# recorder_app_optimized.py
"""
图像录制软件 - 优化版UI界面
现代化设计，提升用户体验
"""

import os
import sys
import cv2
import numpy as np
import json
import time
from datetime import datetime
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QCheckBox, QTextEdit,
    QGroupBox, QGridLayout, QProgressBar, QMessageBox, QFileDialog,
    QStatusBar, QComboBox, QFrame, QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSettings, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QPalette, QColor, QPainter, QPen
import logging

# 导入WebSocket客户端
from simple_websocket_client import WebSocketClient


class ModernButton(QPushButton):
    """现代化按钮组件"""
    
    def __init__(self, text="", button_type="default", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setup_style()
        
    def setup_style(self):
        """设置按钮样式"""
        styles = {
            "primary": {
                "bg": "#007bff",
                "hover": "#0056b3",
                "active": "#004085",
                "text": "white"
            },
            "success": {
                "bg": "#28a745",
                "hover": "#218838",
                "active": "#1e7e34",
                "text": "white"
            },
            "danger": {
                "bg": "#dc3545",
                "hover": "#c82333",
                "active": "#bd2130",
                "text": "white"
            },
            "warning": {
                "bg": "#ffc107",
                "hover": "#e0a800",
                "active": "#d39e00",
                "text": "#212529"
            },
            "info": {
                "bg": "#17a2b8",
                "hover": "#138496",
                "active": "#117a8b",
                "text": "white"
            },
            "default": {
                "bg": "#f8f9fa",
                "hover": "#e2e6ea",
                "active": "#dae0e5",
                "text": "#495057"
            }
        }
        
        style = styles.get(self.button_type, styles["default"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {style["bg"]};
                color: {style["text"]};
                border: 2px solid {style["bg"]};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 10pt;
                font-weight: 600;
                min-height: 16px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {style["hover"]};
                border-color: {style["hover"]};
                border-width: 3px;
            }}
            QPushButton:pressed {{
                background-color: {style["active"]};
                border-color: {style["active"]};
                border-width: 1px;
                padding: 11px 21px 9px 19px;
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
                border-color: #6c757d;
                color: #adb5bd;
            }}
        """)


class StatusIndicator(QLabel):
    """状态指示器组件"""
    
    def __init__(self, text="", status="neutral", parent=None):
        super().__init__(text, parent)
        self.status = status
        self.setup_style()
        
    def setup_style(self):
        """设置状态指示器样式"""
        colors = {
            "success": {"bg": "#d4edda", "border": "#c3e6cb", "text": "#155724"},
            "danger": {"bg": "#f8d7da", "border": "#f5c6cb", "text": "#721c24"},
            "warning": {"bg": "#fff3cd", "border": "#ffeaa7", "text": "#856404"},
            "info": {"bg": "#cce8f4", "border": "#b3d7ff", "text": "#0c5460"},
            "neutral": {"bg": "#f8f9fa", "border": "#dee2e6", "text": "#6c757d"}
        }
        
        color = colors.get(self.status, colors["neutral"])
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color["bg"]};
                color: {color["text"]};
                border: 1px solid {color["border"]};
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 9pt;
            }}
        """)
        
    def set_status(self, status, text=None):
        """更新状态"""
        self.status = status
        if text:
            self.setText(text)
        self.setup_style()


class ModernGroupBox(QGroupBox):
    """现代化分组框"""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置分组框样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 11pt;
                color: #2c3e50;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
                background-color: white;
                border-radius: 4px;
            }
        """)


class ModernLineEdit(QLineEdit):
    """现代化输入框"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setup_style()
        
    def setup_style(self):
        """设置输入框样式"""
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 10pt;
                background-color: white;
                color: #495057;
                selection-background-color: #007bff;
            }
            QLineEdit:focus {
                border-color: #007bff;
                background-color: #f8f9ff;
            }
            QLineEdit:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
        """)


class ImageRecorderWindow(QMainWindow):
    """图像录制主窗口 - 优化版"""
    
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.init_variables()
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        self.logger.info("图像录制软件启动完成")
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def init_variables(self):
        """初始化变量"""
        self.websocket_client = None
        self.is_recording = False
        self.recording_count = 0
        self.save_directory = os.path.dirname(os.path.abspath(__file__))
        self.current_session_folder = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.current_image = None
        
        # 录制统计
        self.session_start_time = None
        self.total_saved_images = 0
        self.last_save_time = 0
        
        # 连接质量监控
        self.image_receive_count = 0
        self.last_fps_check_time = 0
        self.current_fps = 0
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("📷 PaperTracker 图像录制工具 v2.0")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # 设置应用程序样式
        self.setStyleSheet(self.get_main_stylesheet())
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 使用分割器布局
        splitter = QSplitter(Qt.Horizontal)
        central_widget_layout = QHBoxLayout(central_widget)
        central_widget_layout.setContentsMargins(15, 15, 15, 15)
        central_widget_layout.addWidget(splitter)
        
        # 左侧控制面板
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # 右侧预览面板
        right_panel = self.create_preview_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([400, 800])
        splitter.setStretchFactor(0, 0)  # 控制面板固定宽度
        splitter.setStretchFactor(1, 1)  # 预览面板可伸缩
        
        # 创建状态栏
        self.create_status_bar()
    
    def get_main_stylesheet(self):
        """获取主样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fc, stop:1 #e9ecef);
                font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
            }
            QWidget {
                font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
                font-size: 9pt;
            }
            QLabel {
                color: #495057;
                font-size: 9pt;
            }
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: #ffffff;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9pt;
                color: #495057;
                padding: 10px;
                selection-background-color: #007bff;
            }
            QTextEdit:focus {
                border-color: #007bff;
            }
            QComboBox, QSpinBox {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: white;
                font-size: 10pt;
                color: #495057;
                min-height: 20px;
            }
            QComboBox:focus, QSpinBox:focus {
                border-color: #007bff;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                margin-right: 8px;
            }
            QCheckBox {
                font-size: 10pt;
                color: #495057;
                spacing: 8px;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #0056b3;
            }
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                text-align: center;
                font-size: 9pt;
                font-weight: 600;
                color: white;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007bff, stop:1 #0056b3);
                border-radius: 6px;
            }
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-top: 1px solid #dee2e6;
                font-size: 9pt;
                color: #6c757d;
                padding: 5px;
            }
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #007bff;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
    
    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumWidth(420)
        scroll_area.setMinimumWidth(400)
        
        # 主面板内容
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # 标题区域
        title_widget = self.create_title_section()
        layout.addWidget(title_widget)
        
        # 连接设置组
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)
        
        # 录制设置组
        recording_group = self.create_recording_group()
        layout.addWidget(recording_group)
        
        # 录制控制组
        control_group = self.create_control_group()
        layout.addWidget(control_group)
        
        # 统计信息组
        stats_group = self.create_stats_group()
        layout.addWidget(stats_group)
        
        # 日志显示组
        log_group = self.create_log_group()
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        scroll_area.setWidget(panel)
        return scroll_area
    
    def create_title_section(self) -> QWidget:
        """创建标题区域"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 主标题
        title_label = QLabel("📷 图像录制工具")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18pt;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("专业的实时图像采集与录制系统")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 10pt;
                font-weight: 500;
            }
        """)
        layout.addWidget(subtitle_label)
        
        return widget
    
    def create_connection_group(self) -> QGroupBox:
        """创建连接设置组"""
        group = ModernGroupBox("🔗 设备连接")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        
        # WebSocket地址输入
        url_container = QWidget()
        url_layout = QVBoxLayout(url_container)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(8)
        
        url_label = QLabel("🌐 设备地址")
        url_label.setStyleSheet("font-weight: 600; color: #495057; font-size: 10pt;")
        url_layout.addWidget(url_label)
        
        self.url_input = ModernLineEdit("例: ws://192.168.1.100:8765")
        self.url_input.setText("ws://localhost:8765")
        url_layout.addWidget(self.url_input)
        
        layout.addWidget(url_container)
        
        # 连接状态
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        status_label = QLabel("📡 连接状态")
        status_label.setStyleSheet("font-weight: 600; color: #495057; font-size: 10pt;")
        status_layout.addWidget(status_label)
        
        self.connection_status_label = StatusIndicator("未连接", "danger")
        status_layout.addWidget(self.connection_status_label)
        
        layout.addWidget(status_container)
        
        # 连接按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.connect_btn = ModernButton("🔌 连接设备", "primary")
        self.connect_btn.clicked.connect(self.toggle_connection)
        buttons_layout.addWidget(self.connect_btn)
        
        self.test_btn = ModernButton("🧪 测试", "info")
        self.test_btn.clicked.connect(self.test_connection)
        buttons_layout.addWidget(self.test_btn)
        
        layout.addLayout(buttons_layout)
        
        return group
    
    def create_recording_group(self) -> QGroupBox:
        """创建录制设置组"""
        group = ModernGroupBox("⚙️ 录制设置")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        
        # 保存目录
        dir_container = QWidget()
        dir_layout = QVBoxLayout(dir_container)
        dir_layout.setContentsMargins(0, 0, 0, 0)
        dir_layout.setSpacing(8)
        
        dir_label = QLabel("📁 保存目录")
        dir_label.setStyleSheet("font-weight: 600; color: #495057; font-size: 10pt;")
        dir_layout.addWidget(dir_label)
        
        dir_input_layout = QHBoxLayout()
        dir_input_layout.setSpacing(10)
        
        self.save_dir_label = QLabel(self.save_directory)
        self.save_dir_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 9pt;
                padding: 10px;
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                min-height: 20px;
            }
        """)
        self.save_dir_label.setWordWrap(True)
        dir_input_layout.addWidget(self.save_dir_label, 1)
        
        self.browse_dir_btn = ModernButton("📂", "default")
        self.browse_dir_btn.clicked.connect(self.browse_save_directory)
        self.browse_dir_btn.setMaximumWidth(50)
        dir_input_layout.addWidget(self.browse_dir_btn)
        
        dir_layout.addLayout(dir_input_layout)
        layout.addWidget(dir_container)
        
        # 录制参数设置
        params_layout = QGridLayout()
        params_layout.setHorizontalSpacing(15)
        params_layout.setVerticalSpacing(12)
        
        # 图像格式
        format_label = QLabel("🖼️ 图像格式")
        format_label.setStyleSheet("font-weight: 600; color: #495057; font-size: 10pt;")
        params_layout.addWidget(format_label, 0, 0)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["jpg", "png", "bmp"])
        self.format_combo.setCurrentText("jpg")
        params_layout.addWidget(self.format_combo, 0, 1)
        
        # 图像质量
        quality_label = QLabel("⭐ 图像质量")
        quality_label.setStyleSheet("font-weight: 600; color: #495057; font-size: 10pt;")
        params_layout.addWidget(quality_label, 1, 0)
        
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(1, 100)
        self.quality_spinbox.setValue(95)
        self.quality_spinbox.setSuffix("%")
        params_layout.addWidget(self.quality_spinbox, 1, 1)
        
        # 保存间隔
        interval_label = QLabel("⏰ 保存间隔")
        interval_label.setStyleSheet("font-weight: 600; color: #495057; font-size: 10pt;")
        params_layout.addWidget(interval_label, 2, 0)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(100, 10000)
        self.auto_save_interval.setValue(1000)
        self.auto_save_interval.setSuffix(" ms")
        params_layout.addWidget(self.auto_save_interval, 2, 1)
        
        layout.addLayout(params_layout)
        
        # 自动保存开关
        self.auto_save_checkbox = QCheckBox("🔄 启用自动保存")
        self.auto_save_checkbox.setChecked(True)
        self.auto_save_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 10pt;
                font-weight: 600;
                color: #495057;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.auto_save_checkbox)
        
        return group
    
    def create_control_group(self) -> QGroupBox:
        """创建录制控制组"""
        group = ModernGroupBox("🎬 录制控制")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        
        # 录制状态显示
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        status_title = QLabel("📊 录制状态")
        status_title.setStyleSheet("font-weight: 600; color: #495057; font-size: 10pt;")
        status_layout.addWidget(status_title)
        
        self.recording_status_label = StatusIndicator("⏸️ 待机中", "neutral")
        status_layout.addWidget(self.recording_status_label)
        
        layout.addWidget(status_container)
        
        # 主要控制按钮
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.setSpacing(12)
        
        self.start_recording_btn = ModernButton("▶️ 开始录制", "success")
        self.start_recording_btn.clicked.connect(self.start_recording)
        self.start_recording_btn.setEnabled(False)
        main_buttons_layout.addWidget(self.start_recording_btn)
        
        self.stop_recording_btn = ModernButton("⏹️ 停止录制", "danger")
        self.stop_recording_btn.clicked.connect(self.stop_recording)
        self.stop_recording_btn.setEnabled(False)
        main_buttons_layout.addWidget(self.stop_recording_btn)
        
        layout.addLayout(main_buttons_layout)
        
        # 辅助按钮
        aux_buttons_layout = QHBoxLayout()
        aux_buttons_layout.setSpacing(12)
        
        self.capture_btn = ModernButton("📸 手动抓取", "info")
        self.capture_btn.clicked.connect(self.manual_capture)
        self.capture_btn.setEnabled(False)
        aux_buttons_layout.addWidget(self.capture_btn)
        
        self.new_session_btn = ModernButton("🆕 新建会话", "warning")
        self.new_session_btn.clicked.connect(self.new_recording_session)
        aux_buttons_layout.addWidget(self.new_session_btn)
        
        layout.addLayout(aux_buttons_layout)
        
        return group
    
    def create_stats_group(self) -> QGroupBox:
        """创建统计信息组"""
        group = ModernGroupBox("📈 录制统计")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(12)
        
        # 创建统计卡片布局
        stats_container = QWidget()
        stats_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        stats_layout = QGridLayout(stats_container)
        stats_layout.setSpacing(10)
        
        # 统计项样式
        def create_stat_item(title, value, icon):
            container = QWidget()
            container.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 8px;
                    padding: 10px;
                    border: 1px solid #e9ecef;
                }
            """)
            item_layout = QVBoxLayout(container)
            item_layout.setContentsMargins(5, 5, 5, 5)
            item_layout.setSpacing(5)
            
            title_label = QLabel(f"{icon} {title}")
            title_label.setStyleSheet("font-size: 9pt; font-weight: 600; color: #6c757d;")
            item_layout.addWidget(title_label)
            
            value_label = QLabel(value)
            value_label.setStyleSheet("""
                font-size: 14pt; 
                font-weight: bold; 
                color: #007bff;
                margin-top: 5px;
            """)
            item_layout.addWidget(value_label)
            
            return container, value_label
        
        # 当前会话
        session_widget, self.session_count_label = create_stat_item("当前会话", "0 张", "📷")
        stats_layout.addWidget(session_widget, 0, 0)
        
        # 总计保存
        total_widget, self.total_count_label = create_stat_item("总计保存", "0 张", "💾")
        stats_layout.addWidget(total_widget, 0, 1)
        
        # 录制时长
        duration_widget, self.duration_label = create_stat_item("录制时长", "00:00:00", "⏱️")
        stats_layout.addWidget(duration_widget, 1, 0, 1, 2)
        
        layout.addWidget(stats_container)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)
        
        return group
    
    def create_log_group(self) -> QGroupBox:
        """创建日志显示组"""
        group = ModernGroupBox("📋 操作日志")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(12)
        
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(160)
        self.log_display.setMinimumHeight(140)
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("📝 操作日志将在这里显示...")
        layout.addWidget(self.log_display)
        
        # 日志控制按钮
        log_buttons_layout = QHBoxLayout()
        log_buttons_layout.setSpacing(10)
        
        self.clear_log_btn = ModernButton("🗑️ 清除", "default")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setMaximumWidth(80)
        log_buttons_layout.addWidget(self.clear_log_btn)
        
        self.save_log_btn = ModernButton("💾 保存", "default")
        self.save_log_btn.clicked.connect(self.save_log)
        self.save_log_btn.setMaximumWidth(80)
        log_buttons_layout.addWidget(self.save_log_btn)
        
        log_buttons_layout.addStretch()
        layout.addLayout(log_buttons_layout)
        
        return group
    
    def create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 预览标题栏
        header_widget = self.create_preview_header()
        layout.addWidget(header_widget)
        
        # 预览显示区域
        preview_container = self.create_preview_display()
        layout.addWidget(preview_container)
        
        # 预览信息栏
        info_widget = self.create_preview_info()
        layout.addWidget(info_widget)
        
        return panel
    
    def create_preview_header(self) -> QWidget:
        """创建预览标题栏"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("🖼️ 实时预览")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px;
            }
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 预览控制开关
        self.preview_enable_checkbox = QCheckBox("🔍 启用预览")
        self.preview_enable_checkbox.setChecked(True)
        self.preview_enable_checkbox.toggled.connect(self.toggle_preview)
        self.preview_enable_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                font-weight: 600;
                color: #495057;
                spacing: 10px;
                padding: 8px 12px;
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
            }
            QCheckBox:hover {
                background-color: #e9ecef;
                border-color: #007bff;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
        """)
        layout.addWidget(self.preview_enable_checkbox)
        
        return widget
    
    def create_preview_display(self) -> QWidget:
        """创建预览显示区域"""
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 3px solid #dee2e6;
                border-radius: 15px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 预览图像显示
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(720, 540)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ced4da;
                background-color: #ffffff;
                border-radius: 12px;
                color: #6c757d;
                font-size: 14pt;
                font-weight: 600;
                padding: 20px;
            }
        """)
        self.preview_label.setText("📷 等待连接设备...\n\n请先连接设备以查看实时预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setScaledContents(False)
        layout.addWidget(self.preview_label)
        
        return container
    
    def create_preview_info(self) -> QWidget:
        """创建预览信息栏"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(20)
        
        # 图像信息
        self.image_info_label = QLabel("📐 分辨率: --")
        self.image_info_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 10pt;
                font-weight: 600;
                padding: 8px 15px;
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.image_info_label)
        
        layout.addStretch()
        
        # FPS显示
        self.fps_label = QLabel("⚡ FPS: --")
        self.fps_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 10pt;
                font-weight: 600;
                padding: 8px 15px;
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.fps_label)
        
        return widget
    
    def create_status_bar(self):
        """创建状态栏"""
        self.statusBar().showMessage('🚀 图像录制工具已启动，请连接设备开始录制')
        
        # 添加永久状态信息
        self.device_status = QLabel("📱 设备: 未连接")
        self.device_status.setStyleSheet("""
            QLabel {
                color: #dc3545;
                font-weight: 600;
                padding: 5px 10px;
                background-color: rgba(220, 53, 69, 0.1);
                border-radius: 5px;
                margin: 2px;
            }
        """)
        self.statusBar().addPermanentWidget(self.device_status)
        
        self.recording_indicator = QLabel("⏹️ 录制: 停止")
        self.recording_indicator.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-weight: 600;
                padding: 5px 10px;
                background-color: rgba(108, 117, 125, 0.1);
                border-radius: 5px;
                margin: 2px;
            }
        """)
        self.statusBar().addPermanentWidget(self.recording_indicator)
    
    def setup_connections(self):
        """设置信号连接"""
        # 定时器用于更新录制时长
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self.update_duration)
        
        # 添加自动重连定时器
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.attempt_reconnect)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
    
    def load_settings(self):
        """加载设置"""
        self.settings = QSettings('PaperTracker', 'ImageRecorder')
        
        # 恢复窗口状态
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        # 恢复设置
        url = self.settings.value('websocket_url', 'ws://localhost:8765')
        self.url_input.setText(url)
        
        save_dir = self.settings.value('save_directory', self.save_directory)
        if os.path.exists(save_dir):
            self.save_directory = save_dir
            self.save_dir_label.setText(save_dir)
        
        format_type = self.settings.value('image_format', 'jpg')
        self.format_combo.setCurrentText(format_type)
        
        quality = self.settings.value('image_quality', 95)
        self.quality_spinbox.setValue(int(quality))
        
        interval = self.settings.value('auto_save_interval', 1000)
        self.auto_save_interval.setValue(int(interval))
        
        auto_save = self.settings.value('auto_save_enabled', True, type=bool)
        self.auto_save_checkbox.setChecked(auto_save)
    
    def save_settings(self):
        """保存设置"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('websocket_url', self.url_input.text())
        self.settings.setValue('save_directory', self.save_directory)
        self.settings.setValue('image_format', self.format_combo.currentText())
        self.settings.setValue('image_quality', self.quality_spinbox.value())
        self.settings.setValue('auto_save_interval', self.auto_save_interval.value())
        self.settings.setValue('auto_save_enabled', self.auto_save_checkbox.isChecked())
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.is_recording:
            reply = QMessageBox.question(
                self, '🤔 确认关闭', 
                '正在录制中，确定要关闭程序吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.stop_recording()
        
        # 断开连接
        if self.websocket_client:
            self.disconnect_device()
        
        self.save_settings()
        event.accept()
    
    # 连接相关方法
    def toggle_connection(self):
        """切换连接状态"""
        if self.websocket_client and self.websocket_client.is_connected():
            self.disconnect_device()
        else:
            self.connect_device()
    
    def connect_device(self):
        """连接设备"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "⚠️ 警告", "请输入设备地址")
            return
        
        try:
            self.log_message(f"🔌 正在连接设备: {url}")
            
            # 智能URL处理
            processed_url = self.process_url(url)
            self.websocket_client = WebSocketClient(processed_url)
            
            # 连接信号
            self.websocket_client.connected.connect(self.on_device_connected)
            self.websocket_client.disconnected.connect(self.on_device_disconnected)
            self.websocket_client.image_received.connect(self.on_image_received)
            self.websocket_client.error_occurred.connect(self.on_connection_error)
            self.websocket_client.status_updated.connect(self.on_status_updated)
            
            # 尝试连接
            self.websocket_client.connect_to_device()
            
            # 更新UI状态
            self.connect_btn.setText("🔄 连接中...")
            self.connect_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            
        except Exception as e:
            self.log_message(f"❌ 连接失败: {e}")
            QMessageBox.critical(self, "🚫 连接错误", f"连接设备失败:\n{e}")
    
    def process_url(self, url: str) -> str:
        """处理和规范化URL"""
        url = url.strip()
        
        # 如果不包含协议，添加ws://
        if not url.startswith(('ws://', 'wss://', 'http://', 'https://')):
            url = f"ws://{url}"
        
        # 将HTTP协议转换为WebSocket协议
        if url.startswith('http://'):
            url = url.replace('http://', 'ws://')
        elif url.startswith('https://'):
            url = url.replace('https://', 'wss://')
        
        self.log_message(f"🔧 处理后的URL: {url}")
        return url
    
    def on_status_updated(self, status: str):
        """状态更新"""
        self.log_message(f"📊 设备状态: {status}")
    
    def disconnect_device(self):
        """断开设备连接"""
        if self.websocket_client:
            self.log_message("🔌 正在断开设备连接...")
            
            # 如果正在录制，先停止
            if self.is_recording:
                self.stop_recording()
            
            self.websocket_client.disconnect_from_device()
            self.websocket_client = None
            
            # 停止预览
            self.preview_timer.stop()
            self.preview_label.setText("📷 等待连接设备...\n\n请先连接设备以查看实时预览")
            self.preview_label.setPixmap(QPixmap())
    
    def test_connection(self):
        """测试连接"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "⚠️ 警告", "请输入设备地址")
            return
        
        self.log_message(f"🧪 测试连接: {url}")
        QMessageBox.information(self, "🧪 测试连接", f"正在测试连接到:\n{url}")
    
    def on_device_connected(self):
        """设备连接成功"""
        self.log_message("✅ 设备连接成功")
        
        # 重置重连计数
        self.reconnect_attempts = 0
        self.reconnect_timer.stop()
        
        # 更新UI状态
        self.connection_status_label.set_status("success", "✅ 已连接")
        
        self.connect_btn.setText("🔌 断开连接")
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        
        self.start_recording_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)
        
        self.device_status.setText("📱 设备: 已连接")
        self.device_status.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-weight: 600;
                padding: 5px 10px;
                background-color: rgba(40, 167, 69, 0.1);
                border-radius: 5px;
                margin: 2px;
            }
        """)
        
        # 开始预览
        if self.preview_enable_checkbox.isChecked():
            self.preview_timer.start(33)  # 约30fps
        
        self.statusBar().showMessage('✅ 设备连接成功，可以开始录制')
    
    def on_device_disconnected(self):
        """设备断开连接"""
        self.log_message("❌ 设备连接断开")
        
        # 更新UI状态
        self.connection_status_label.set_status("danger", "❌ 未连接")
        
        self.connect_btn.setText("🔌 连接设备")
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        
        self.start_recording_btn.setEnabled(False)
        self.stop_recording_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        
        self.device_status.setText("📱 设备: 未连接")
        self.device_status.setStyleSheet("""
            QLabel {
                color: #dc3545;
                font-weight: 600;
                padding: 5px 10px;
                background-color: rgba(220, 53, 69, 0.1);
                border-radius: 5px;
                margin: 2px;
            }
        """)
        
        # 停止预览和录制
        self.preview_timer.stop()
        if self.is_recording:
            self.stop_recording()
        
        self.preview_label.setText("📷 等待连接设备...\n\n请先连接设备以查看实时预览")
        self.preview_label.setPixmap(QPixmap())
        
        self.statusBar().showMessage('❌ 设备连接断开')
    
    def on_connection_error(self, error_message: str):
        """连接错误"""
        self.log_message(f"🚫 连接错误: {error_message}")
        
        # 重置连接按钮
        self.connect_btn.setText("🔌 连接设备")
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        
        # 如果是录制过程中断开，尝试自动重连
        if self.is_recording and self.reconnect_attempts < self.max_reconnect_attempts:
            self.log_message(f"🔄 录制中断开，将在5秒后尝试重连 (第{self.reconnect_attempts + 1}次)")
            self.reconnect_timer.start(5000)  # 5秒后重连
        else:
            QMessageBox.critical(self, "🚫 连接错误", f"设备连接失败:\n{error_message}")
    
    def attempt_reconnect(self):
        """尝试自动重连"""
        self.reconnect_timer.stop()
        self.reconnect_attempts += 1
        
        self.log_message(f"🔄 正在尝试自动重连... (第{self.reconnect_attempts}次)")
        
        # 如果超过最大重连次数，停止录制
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.log_message("⚠️ 已达到最大重连次数，停止录制")
            if self.is_recording:
                self.stop_recording()
            return
        
        # 尝试重新连接
        self.connect_device()
    
    def on_image_received(self, image_data: np.ndarray):
        """接收到图像数据"""
        self.current_image = image_data.copy()
        
        # 更新FPS统计
        current_time = time.time()
        self.image_receive_count += 1
        
        if current_time - self.last_fps_check_time >= 1.0:
            self.current_fps = self.image_receive_count
            self.fps_label.setText(f"⚡ FPS: {self.current_fps}")
            self.image_receive_count = 0
            self.last_fps_check_time = current_time
        
        # 如果正在录制且启用自动保存
        if self.is_recording and self.auto_save_checkbox.isChecked():
            current_time_ms = current_time * 1000
            interval = self.auto_save_interval.value()
            
            if current_time_ms - self.last_save_time >= interval:
                self.save_current_image()
                self.last_save_time = current_time_ms
    
    def update_preview(self):
        """更新预览显示"""
        if not self.preview_enable_checkbox.isChecked():
            return
        
        if self.current_image is not None:
            self.display_image_in_preview(self.current_image)
    
    def display_image_in_preview(self, image: np.ndarray):
        """在预览区域显示图像"""
        try:
            # 转换颜色空间 (BGR to RGB)
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # 转换为QImage
            height, width = rgb_image.shape[:2]
            if len(rgb_image.shape) == 3:
                bytes_per_line = 3 * width
                q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                bytes_per_line = width
                q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            
            # 缩放到预览区域大小
            preview_size = self.preview_label.size()
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # 显示图像
            self.preview_label.setPixmap(scaled_pixmap)
            
            # 更新图像信息
            self.image_info_label.setText(f"📐 分辨率: {width}x{height}")
            
        except Exception as e:
            self.logger.error(f"显示预览图像失败: {e}")
    
    # 录制相关方法
    def browse_save_directory(self):
        """浏览保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "📁 选择保存目录", self.save_directory
        )
        
        if directory:
            self.save_directory = directory
            self.save_dir_label.setText(directory)
            self.log_message(f"📁 保存目录已更改: {directory}")
    
    def new_recording_session(self):
        """新建录制会话"""
        if self.is_recording:
            reply = QMessageBox.question(
                self, '🤔 确认操作', 
                '正在录制中，确定要开始新会话吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            
            self.stop_recording()
        
        # 创建新的会话文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"recording_session_{timestamp}"
        self.current_session_folder = os.path.join(self.save_directory, session_name)
        
        try:
            os.makedirs(self.current_session_folder, exist_ok=True)
            self.recording_count = 0
            self.session_count_label.setText("0 张")
            
            self.log_message(f"🆕 新建录制会话: {session_name}")
            self.statusBar().showMessage(f'🆕 新建会话: {session_name}')
            
        except Exception as e:
            QMessageBox.critical(self, "🚫 错误", f"创建会话文件夹失败:\n{e}")
            self.logger.error(f"创建会话文件夹失败: {e}")
    
    def start_recording(self):
        """开始录制"""
        if not self.websocket_client or not self.websocket_client.is_connected():
            QMessageBox.warning(self, "⚠️ 警告", "请先连接设备")
            return
        
        # 如果没有会话文件夹，创建新会话
        if not self.current_session_folder:
            self.new_recording_session()
        
        self.is_recording = True
        self.session_start_time = datetime.now()
        
        # 更新UI状态
        self.recording_status_label.set_status("danger", "🔴 录制中")
        
        self.start_recording_btn.setEnabled(False)
        self.stop_recording_btn.setEnabled(True)
        
        self.recording_indicator.setText("🔴 录制: 进行中")
        self.recording_indicator.setStyleSheet("""
            QLabel {
                color: #dc3545;
                font-weight: 600;
                padding: 5px 10px;
                background-color: rgba(220, 53, 69, 0.1);
                border-radius: 5px;
                margin: 2px;
            }
        """)
        
        # 开始计时器
        self.duration_timer.start(1000)
        
        self.log_message("▶️ 开始录制图像")
        self.statusBar().showMessage('🎬 录制已开始，图像将自动保存')
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
    
    def stop_recording(self):
        """停止录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # 更新UI状态
        self.recording_status_label.set_status("neutral", "⏸️ 待机中")
        
        self.start_recording_btn.setEnabled(True)
        self.stop_recording_btn.setEnabled(False)
        
        self.recording_indicator.setText("⏹️ 录制: 停止")
        self.recording_indicator.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-weight: 600;
                padding: 5px 10px;
                background-color: rgba(108, 117, 125, 0.1);
                border-radius: 5px;
                margin: 2px;
            }
        """)
        
        # 停止计时器
        self.duration_timer.stop()
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 记录会话信息
        session_info = {
            "session_folder": self.current_session_folder,
            "start_time": self.session_start_time.isoformat() if self.session_start_time else None,
            "end_time": datetime.now().isoformat(),
            "image_count": self.recording_count,
            "image_format": self.format_combo.currentText(),
            "image_quality": self.quality_spinbox.value(),
        }
        
        # 保存会话信息到JSON文件
        if self.current_session_folder:
            info_file = os.path.join(self.current_session_folder, "session_info.json")
            try:
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(session_info, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.logger.error(f"保存会话信息失败: {e}")
        
        self.log_message(f"⏹️ 录制停止，本次会话保存了 {self.recording_count} 张图像")
        self.statusBar().showMessage(f'✅ 录制停止，共保存 {self.recording_count} 张图像')
    
    def manual_capture(self):
        """手动抓取图像"""
        if self.current_image is not None:
            self.save_current_image()
            self.log_message("📸 手动抓取图像")
        else:
            QMessageBox.warning(self, "⚠️ 警告", "当前没有可用的图像")
    
    def save_current_image(self):
        """保存当前图像"""
        if self.current_image is None:
            return
        
        # 如果没有会话文件夹，创建新会话
        if not self.current_session_folder:
            self.new_recording_session()
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            image_format = self.format_combo.currentText()
            filename = f"capture_{timestamp}_{self.recording_count:04d}.{image_format}"
            filepath = os.path.join(self.current_session_folder, filename)
            
            # 保存图像
            if image_format.lower() == 'jpg':
                quality = self.quality_spinbox.value()
                cv2.imwrite(filepath, self.current_image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(filepath, self.current_image)
            
            # 更新计数
            self.recording_count += 1
            self.total_saved_images += 1
            
            # 更新UI
            self.session_count_label.setText(f"{self.recording_count} 张")
            self.total_count_label.setText(f"{self.total_saved_images} 张")
            
            self.logger.info(f"图像已保存: {filename}")
            
        except Exception as e:
            self.logger.error(f"保存图像失败: {e}")
            QMessageBox.critical(self, "🚫 错误", f"保存图像失败:\n{e}")
    
    def toggle_preview(self, enabled: bool):
        """切换预览显示"""
        if enabled:
            if self.websocket_client and self.websocket_client.is_connected():
                self.preview_timer.start(33)
        else:
            self.preview_timer.stop()
            self.preview_label.setText("🚫 预览已禁用\n\n请启用预览开关以查看实时图像")
            self.preview_label.setPixmap(QPixmap())
    
    def update_duration(self):
        """更新录制时长"""
        if self.session_start_time:
            duration = datetime.now() - self.session_start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            self.duration_label.setText(duration_str)
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_display.append(log_entry)
        
        # 自动滚动到底部
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.End)
        self.log_display.setTextCursor(cursor)
        
        # 限制日志行数
        if self.log_display.document().blockCount() > 100:
            cursor = self.log_display.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
    
    def clear_log(self):
        """清除日志"""
        self.log_display.clear()
        self.log_message("🗑️ 日志已清除")
    
    def save_log(self):
        """保存日志到文件"""
        if not self.log_display.toPlainText().strip():
            QMessageBox.information(self, "💡 提示", "日志为空，无需保存")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recorder_log_{timestamp}.txt"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "💾 保存日志", filename, "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.log_display.toPlainText())
                QMessageBox.information(self, "✅ 成功", f"日志已保存到:\n{filepath}")
                self.log_message(f"💾 日志已保存到: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "🚫 错误", f"保存日志失败:\n{e}")


class AnimatedButton(ModernButton):
    """带动画效果的按钮"""
    
    def __init__(self, text="", button_type="default", parent=None):
        super().__init__(text, button_type, parent)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        # 可以添加悬停动画效果
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        # 可以添加离开动画效果


class ModernProgressBar(QProgressBar):
    """现代化进度条"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
    
    def setup_style(self):
        """设置进度条样式"""
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 12px;
                text-align: center;
                font-size: 10pt;
                font-weight: bold;
                color: white;
                background-color: #f8f9fa;
                min-height: 24px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007bff, stop:0.5 #0056b3, stop:1 #004085);
                border-radius: 10px;
                margin: 1px;
            }
            QProgressBar[orientation="horizontal"] {
                min-width: 200px;
            }
        """)


def apply_modern_theme(app):
    """应用现代主题"""
    # 设置应用程序调色板
    palette = QPalette()
    
    # 主要颜色
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


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("PaperTracker图像录制工具")
    app.setApplicationVersion("2.0.0")
    app.setApplicationDisplayName("📷 PaperTracker 图像录制工具")
    
    # 应用现代主题
    apply_modern_theme(app)
    
    # 设置高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon('recorder_icon.png'))
    
    # 设置全局字体
    font = QFont("Segoe UI", 9)
    font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(font)
    
    # 创建并显示主窗口
    window = ImageRecorderWindow()
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