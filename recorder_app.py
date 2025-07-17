# papertracker_recorder.py
"""
PaperTracker 图像录制工具 - 完整优化版
专为小白用户设计的简洁录制界面
"""

import os
import sys
import cv2
import numpy as np
import json
import zipfile
import shutil
import time
from datetime import datetime
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QTextEdit,
    QGroupBox, QGridLayout, QMessageBox, QFileDialog,
    QStatusBar, QFrame, QSplitter, QScrollArea, QDialog,
    QDialogButtonBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSettings, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QImage, QFont, QPalette, QColor
import logging

# 导入WebSocket客户端
from simple_websocket_client import WebSocketClient


class UserInfoDialog(QDialog):
    """用户信息设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 用户信息设置")
        self.setFixedSize(450, 280)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setup_ui()
        
    def setup_ui(self):
        """设置对话框界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("🎯 首次使用需要设置用户信息")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #495057;
                margin: 15px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        layout.addWidget(title)
        
        # 用户名输入
        username_label = QLabel("👤 用户名:")
        username_label.setStyleSheet("QLabel { font-size: 11pt; font-weight: 600; color: #495057; }")
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入您的用户名")
        self.username_input.setStyleSheet(self.get_input_style())
        layout.addWidget(self.username_input)
        
        # 邮箱输入
        email_label = QLabel("📧 邮箱:")
        email_label.setStyleSheet("QLabel { font-size: 11pt; font-weight: 600; color: #495057; }")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入您的邮箱地址")
        self.email_input.setStyleSheet(self.get_input_style())
        layout.addWidget(self.email_input)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                font-size: 11pt;
                font-weight: 600;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton[text="OK"] {
                background-color: #28a745;
                color: white;
                border: none;
            }
            QPushButton[text="OK"]:hover {
                background-color: #218838;
            }
            QPushButton[text="Cancel"] {
                background-color: #6c757d;
                color: white;
                border: none;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def get_input_style(self):
        """获取输入框样式"""
        return """
            QLineEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 12px 15px;
                font-size: 11pt;
                background-color: white;
                color: #495057;
            }
            QLineEdit:focus {
                border-color: #007bff;
                background-color: #f8f9ff;
            }
        """
    
    def get_user_info(self):
        """获取用户信息"""
        return {
            'username': self.username_input.text().strip(),
            'email': self.email_input.text().strip()
        }
    
    def accept(self):
        """确认按钮处理"""
        user_info = self.get_user_info()
        if not user_info['username']:
            QMessageBox.warning(self, "⚠️ 提示", "请输入用户名！")
            return
        if not user_info['email']:
            QMessageBox.warning(self, "⚠️ 提示", "请输入邮箱地址！")
            return
        super().accept()


class ModernButton(QPushButton):
    """现代化按钮组件"""
    
    def __init__(self, text="", button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setup_style()
        
    def setup_style(self):
        """设置按钮样式"""
        styles = {
            "primary": {
                "bg": "#28a745",
                "hover": "#218838",
                "text": "white"
            },
            "danger": {
                "bg": "#dc3545", 
                "hover": "#c82333",
                "text": "white"
            },
            "secondary": {
                "bg": "#6c757d",
                "hover": "#5a6268", 
                "text": "white"
            }
        }
        
        style = styles.get(self.button_type, styles["primary"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {style["bg"]};
                color: {style["text"]};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: 600;
                min-height: 20px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {style["hover"]};
            }}
            QPushButton:pressed {{
                background-color: {style["hover"]};
            }}
            QPushButton:disabled {{
                background-color: #e9ecef;
                color: #6c757d;
            }}
        """)


class PaperTrackerRecorder(QMainWindow):
    """PaperTracker 图像录制主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.init_variables()
        self.check_user_info()
        self.setup_ui()
        self.setup_connections()
        self.setup_default_settings()
        
        self.logger.info("PaperTracker 图像录制工具启动完成")
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def init_variables(self):
        """初始化变量"""
        self.websocket_client = None
        self.is_recording = False
        self.recording_count = 0
        self.current_session_folder = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.current_image = None
        self.session_start_time = None
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self.update_duration)
        
        # 自动重连机制
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.auto_reconnect)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # 防止递归断开连接的标志
        self._disconnecting = False
        
        # 用户信息
        self.user_info = {'username': '', 'email': ''}
        
        # 设置对象
        self.settings = QSettings('PaperTracker', 'ImageRecorder')
    
    def check_user_info(self):
        """检查并设置用户信息"""
        saved_username = self.settings.value('username', '')
        saved_email = self.settings.value('email', '')
        
        if not saved_username or not saved_email:
            dialog = UserInfoDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                user_info = dialog.get_user_info()
                self.user_info = user_info
                self.settings.setValue('username', user_info['username'])
                self.settings.setValue('email', user_info['email'])
            else:
                sys.exit()
        else:
            self.user_info = {'username': saved_username, 'email': saved_email}
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("📷 PaperTracker 图像录制工具")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1400, 800)
        
        # 设置应用程序样式
        self.setStyleSheet(self.get_main_stylesheet())
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # 左侧控制面板 - 添加滚动支持
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(420)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setStyleSheet("""
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
        """)
        
        left_panel = self.create_control_panel()
        left_scroll.setWidget(left_panel)
        main_layout.addWidget(left_scroll)
        
        # 右侧预览面板
        right_panel = self.create_preview_panel()
        main_layout.addWidget(right_panel)
        
        # 设置比例
        main_layout.setStretch(0, 0)  # 控制面板固定
        main_layout.setStretch(1, 1)  # 预览面板可伸缩
        
        # 创建状态栏
        self.create_status_bar()
    
    def get_main_stylesheet(self):
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
    
    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        panel.setMinimumWidth(380)
        panel.setStyleSheet("QWidget { background-color: transparent; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # 应用标题
        title_group = self.create_title_section()
        layout.addWidget(title_group)
        
        # 设备连接组
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)
        
        # 录制控制组 - 最重要的部分
        control_group = self.create_simple_control_group()
        layout.addWidget(control_group)
        
        # 录制状态
        status_group = self.create_status_group()
        layout.addWidget(status_group)
        
        # 自动保存状态
        auto_save_group = self.create_auto_save_group()
        layout.addWidget(auto_save_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_title_section(self) -> QGroupBox:
        """创建标题区域"""
        group = QGroupBox("📊 PaperTracker 数据采集系统")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 欢迎信息
        welcome_label = QLabel(f"👋 欢迎，{self.user_info['username']}")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 13pt;
                font-weight: 600;
                color: #007bff;
                margin: 8px;
                padding: 5px;
            }
        """)
        layout.addWidget(welcome_label)
        
        # 说明文字
        desc_label = QLabel("📋 专业的实验数据采集与记录工具")
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                margin: 2px 8px;
                padding: 3px;
            }
        """)
        layout.addWidget(desc_label)
        
        group.setLayout(layout)
        return group
    
    def create_connection_group(self) -> QGroupBox:
        """创建连接设置组"""
        group = QGroupBox("🔗 设备连接")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # 设备地址输入
        addr_layout = QVBoxLayout()
        addr_label = QLabel("📱 设备地址:")
        addr_label.setStyleSheet("QLabel { font-weight: 600; font-size: 11pt; }")
        addr_layout.addWidget(addr_label)
        
        # 输入框容器
        input_container = QHBoxLayout()
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setSpacing(0)
        
        prefix_label = QLabel("ws://")
        prefix_label.setStyleSheet("""
            QLabel { 
                color: #6c757d; 
                font-weight: 600; 
                font-size: 10pt;
                padding: 10px 8px;
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-right: none;
                border-radius: 6px 0 0 6px;
                min-width: 40px;
            }
        """)
        
        self.device_input = QLineEdit()
        self.device_input.setPlaceholderText("192.168.1.100:8080")
        self.device_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e9ecef;
                border-left: none;
                border-radius: 0 6px 6px 0;
                padding: 10px 15px;
                font-size: 11pt;
                background-color: white;
                color: #495057;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #007bff;
                border-left-color: #007bff;
            }
        """)
        
        input_container.addWidget(prefix_label)
        input_container.addWidget(self.device_input, 1)
        
        addr_layout.addLayout(input_container)
        layout.addLayout(addr_layout)
        
        # 连接按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.connect_btn = ModernButton("🔌 连接", "primary")
        self.disconnect_btn = ModernButton("🔌 断开", "danger")
        self.disconnect_btn.setEnabled(False)
        
        # 调整按钮样式使其更紧凑
        for btn in [self.connect_btn, self.disconnect_btn]:
            btn.setStyleSheet(btn.styleSheet().replace("min-width: 140px", "min-width: 110px"))
            btn.setStyleSheet(btn.styleSheet().replace("padding: 12px 24px", "padding: 10px 20px"))
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        layout.addLayout(button_layout)
        
        # 连接状态
        self.connection_status = QLabel("❌ 未连接")
        self.connection_status.setStyleSheet("""
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
        """)
        layout.addWidget(self.connection_status)
        
        group.setLayout(layout)
        return group
    
    def create_simple_control_group(self) -> QGroupBox:
        """创建简化的录制控制组"""
        group = QGroupBox("🎬 录制控制")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # 录制按钮
        self.start_btn = ModernButton("▶️ 开始录制", "primary")
        self.start_btn.setStyleSheet("""
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
        """)
        
        self.stop_btn = ModernButton("⏹️ 停止录制", "danger")
        self.stop_btn.setStyleSheet("""
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
        """)
        self.stop_btn.setEnabled(False)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        
        group.setLayout(layout)
        return group
    
    def create_status_group(self) -> QGroupBox:
        """创建状态显示组"""
        group = QGroupBox("📊 录制状态")
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # 录制状态
        status_label = QLabel("状态:")
        status_label.setMinimumWidth(50)
        status_label.setStyleSheet("QLabel { font-weight: 600; }")
        layout.addWidget(status_label, 0, 0)
        
        self.recording_status = QLabel("⏸️ 待机中")
        self.recording_status.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 8px 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                color: #6c757d;
                border: 1px solid #dee2e6;
            }
        """)
        layout.addWidget(self.recording_status, 0, 1)
        
        # 录制时长
        duration_label = QLabel("时长:")
        duration_label.setStyleSheet("QLabel { font-weight: 600; }")
        layout.addWidget(duration_label, 1, 0)
        
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("""
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
        """)
        layout.addWidget(self.duration_label, 1, 1)
        
        # 图片数量
        count_label = QLabel("图片:")
        count_label.setStyleSheet("QLabel { font-weight: 600; }")
        layout.addWidget(count_label, 2, 0)
        
        self.image_count_label = QLabel("0 张")
        self.image_count_label.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                color: #28a745;
                padding: 8px 15px;
                background-color: #f0fff4;
                border-radius: 6px;
                border: 1px solid #b3e5b3;
            }
        """)
        layout.addWidget(self.image_count_label, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def create_auto_save_group(self) -> QGroupBox:
        """创建自动保存设置组"""
        group = QGroupBox("💾 保存设置")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 自动保存开关（默认开启）
        self.auto_save_checkbox = QCheckBox("✅ 自动保存图片（推荐）")
        self.auto_save_checkbox.setChecked(True)  # 默认开启
        self.auto_save_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: 600;
                color: #28a745;
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.auto_save_checkbox)
        
        # 保存信息
        info_label = QLabel("📂 格式: JPG (高质量)\n⏱️ 间隔: 100ms\n📁 位置: 程序根目录")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 6px;
                margin: 5px 0;
                border: 1px solid #e9ecef;
            }
        """)
        layout.addWidget(info_label)
        
        group.setLayout(layout)
        return group
    
    def create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 预览标题
        title = QLabel("📺 实时预览")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: 600;
                color: #495057;
                margin: 15px;
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 1px solid #dee2e6;
            }
        """)
        layout.addWidget(title)
        
        # 预览区域
        self.preview_label = QLabel("📷 等待设备连接...\n\n连接设备后将显示实时图像")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(500)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #dee2e6;
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #6c757d;
                font-size: 14pt;
                margin: 15px;
                padding: 30px;
            }
        """)
        layout.addWidget(self.preview_label)
        
        return panel
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("🌟 欢迎使用 PaperTracker 图像录制工具")
    
    def setup_connections(self):
        """设置信号连接"""
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
    
    def setup_default_settings(self):
        """设置默认参数"""
        # 固定设置
        self.image_format = 'jpg'  # 锁定为JPG格式
        self.capture_interval = 100  # 100ms间隔
        self.auto_save_enabled = True  # 默认开启自动保存
        
        # 创建录制目录
        self.create_recording_directory()
    
    def create_recording_directory(self):
        """创建录制目录"""
        # 在软件根目录创建以当前时间和用户名命名的文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        username = self.user_info['username']
        folder_name = f"{username}_{timestamp}"
        
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.current_session_folder = os.path.join(root_dir, folder_name)
        
        try:
            os.makedirs(self.current_session_folder, exist_ok=True)
            self.logger.info(f"录制目录创建成功: {self.current_session_folder}")
        except Exception as e:
            QMessageBox.critical(self, "❌ 错误", f"创建录制目录失败:\n{e}")
    
    def connect_device(self):
        """连接设备"""
        # 重置断开连接标志
        self._disconnecting = False
        
        device_addr = self.device_input.text().strip()
        if not '/' in device_addr and ':' in device_addr:
            device_addr = device_addr + '/ws'
        elif not '/' in device_addr:
            device_addr = device_addr + '/ws'
        if not device_addr:
            QMessageBox.warning(self, "⚠️ 提示", "请输入设备地址！")
            return
        
        # 处理URL - WebSocketClient会自动处理URL格式
        try:
            self.websocket_client = WebSocketClient()
            self.websocket_client.set_url(device_addr)
            
            # 连接信号
            self.websocket_client.connected.connect(self.on_device_connected)
            self.websocket_client.disconnected.connect(self.on_device_disconnected)
            self.websocket_client.image_received.connect(self.on_image_received)
            self.websocket_client.error_occurred.connect(self.on_connection_error)
            self.websocket_client.status_updated.connect(self.on_status_updated)
            
            # 开始连接
            self.websocket_client.connect_to_device()
            
            # 更新UI状态
            self.connect_btn.setEnabled(False)
            self.connection_status.setText("🔄 连接中...")
            self.connection_status.setStyleSheet("""
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
            """)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ 连接失败", f"无法连接到设备:\n{e}")
            self.connect_btn.setEnabled(True)

    def disconnect_device(self):
        """断开设备连接"""
        # 设置断开连接标志，防止递归
        self._disconnecting = True
        
        if self.is_recording:
            self.stop_recording()
        
        if self.websocket_client:
            # 先断开信号连接，防止触发回调
            try:
                self.websocket_client.disconnected.disconnect()
                self.websocket_client.connected.disconnect()
                self.websocket_client.error_occurred.disconnect()
                self.websocket_client.image_received.disconnect()
                self.websocket_client.status_updated.disconnect()
            except:
                pass  # 忽略断开信号时的错误
            
            # 然后断开WebSocket连接
            try:
                self.websocket_client.disconnect_from_device()
            except:
                pass  # 忽略断开连接时的错误
            
            self.websocket_client = None
        
        # 停止重连定时器
        self.reconnect_timer.stop()
        self.reconnect_attempts = 0
        
        # 更新UI状态
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.connection_status.setText("❌ 未连接")
        self.connection_status.setStyleSheet("""
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
        """)
        self.preview_label.setText("📷 设备已断开\n\n请重新连接设备")
        if hasattr(self, 'preview_timer'):
            self.preview_timer.stop()
        
        # 重置断开连接标志
        self._disconnecting = False
    
    def on_device_connected(self):
        """设备连接成功"""
        self.reconnect_attempts = 0
        self.reconnect_timer.stop()
        
        self.connection_status.setText("✅ 已连接")
        self.connection_status.setStyleSheet("""
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
        """)
        self.disconnect_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.preview_timer.start(33)  # 30fps预览
        self.statusBar().showMessage("✅ 设备连接成功，可以开始录制")
    
    def on_device_disconnected(self):
        """设备断开连接"""
        # 防止递归调用
        if self._disconnecting:
            return
            
        # 如果正在录制，尝试自动重连
        if self.is_recording and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.statusBar().showMessage(f"⚠️ 连接中断，尝试自动重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            self.reconnect_timer.start(5000)  # 5秒后重连
        else:
            # 停止录制
            if self.is_recording:
                self.stop_recording()
            self.disconnect_device()

    def on_connection_error(self, error_msg: str):
        """连接错误处理"""
        self.statusBar().showMessage(f"❌ 连接错误: {error_msg}")
        self.connect_btn.setEnabled(True)
    
    def on_status_updated(self, status: str):
        """状态更新"""
        self.statusBar().showMessage(f"📊 {status}")
    
    def auto_reconnect(self):
        """自动重连"""
        if self.is_recording and self.reconnect_attempts <= self.max_reconnect_attempts:
            self.statusBar().showMessage(f"🔄 正在重连... ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            self.connect_device()
    
    def on_image_received(self, image_data):
        """接收到图像数据"""
        try:
            # 如果接收到的是numpy数组（来自新的WebSocketClient）
            if isinstance(image_data, np.ndarray):
                self.current_image = image_data
            else:
                # 如果接收到的是字节数据（兼容旧版本）
                nparr = np.frombuffer(image_data, np.uint8)
                self.current_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if self.current_image is not None:
                # 自动保存图像（如果正在录制且自动保存开启）
                if self.is_recording and self.auto_save_checkbox.isChecked():
                    self.save_current_image()
                    
        except Exception as e:
            self.logger.error(f"处理图像数据失败: {e}")
    
    def update_preview(self):
        """更新预览显示"""
        if self.current_image is not None:
            try:
                # 转换为Qt格式并显示
                height, width, channel = self.current_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(self.current_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                
                # 缩放以适应预览区域
                preview_size = self.preview_label.size()
                scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                    preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                
            except Exception as e:
                self.logger.error(f"更新预览失败: {e}")
    
    def start_recording(self):
        """开始录制"""
        if not self.websocket_client or not self.websocket_client.is_connected():
            QMessageBox.warning(self, "⚠️ 警告", "请先连接设备！")
            return
        
        self.is_recording = True
        self.recording_count = 0
        self.session_start_time = datetime.now()
        
        # 更新UI状态
        self.recording_status.setText("🔴 录制中")
        self.recording_status.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 8px 15px;
                background-color: #f5c6cb;
                border-radius: 6px;
                color: #721c24;
                border: 1px solid #f1b0b7;
            }
        """)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.duration_timer.start(1000)  # 每秒更新时长
        
        self.statusBar().showMessage("🎬 正在录制，图片将自动保存...")
        self.logger.info("开始录制")
    
    def stop_recording(self):
        """停止录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.duration_timer.stop()
        
        # 更新UI状态
        self.recording_status.setText("⏸️ 待机中")
        self.recording_status.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 11pt;
                padding: 8px 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                color: #6c757d;
                border: 1px solid #dee2e6;
            }
        """)
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 录制完成后打包
        if self.recording_count > 0:
            self.create_recording_package()
        
        self.statusBar().showMessage(f"✅ 录制完成，共保存 {self.recording_count} 张图片")
        self.logger.info(f"录制停止，共保存 {self.recording_count} 张图片")
    
    def save_current_image(self):
        """保存当前图像"""
        if self.current_image is None:
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"img_{timestamp}_{self.recording_count:06d}.jpg"
            filepath = os.path.join(self.current_session_folder, filename)
            
            # 保存为JPG格式，质量90
            cv2.imwrite(filepath, self.current_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            # 更新计数
            self.recording_count += 1
            self.image_count_label.setText(f"{self.recording_count} 张")
            
        except Exception as e:
            self.logger.error(f"保存图像失败: {e}")
    
    def update_duration(self):
        """更新录制时长"""
        if self.session_start_time:
            duration = datetime.now() - self.session_start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            self.duration_label.setText(duration_str)
    
    def create_recording_package(self):
        """创建录制包（压缩并删除原文件夹）"""
        if not self.current_session_folder or self.recording_count == 0:
            return
        
        try:
            # 计算录制时长
            if self.session_start_time:
                duration = datetime.now() - self.session_start_time
                duration_minutes = int(duration.total_seconds() / 60)
                duration_str = f"{duration_minutes}min"
            else:
                duration_str = "unknown"
            
            # 生成压缩包名称：用户名_图片总张数_录制时间.zip
            username = self.user_info['username']
            zip_filename = f"{username}_{self.recording_count}pics_{duration_str}.zip"
            zip_path = os.path.join(os.path.dirname(self.current_session_folder), zip_filename)
            
            # 创建压缩包
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                # 添加所有图片文件
                for root, dirs, files in os.walk(self.current_session_folder):
                    for file in files:
                        if file.lower().endswith('.jpg'):
                            file_path = os.path.join(root, file)
                            # 在压缩包中使用相对路径
                            arcname = os.path.relpath(file_path, self.current_session_folder)
                            zipf.write(file_path, arcname)
                
                # 添加录制信息文件
                session_info = {
                    "username": username,
                    "email": self.user_info['email'],
                    "recording_time": self.session_start_time.isoformat() if self.session_start_time else None,
                    "image_count": self.recording_count,
                    "image_format": "jpg",
                    "capture_interval_ms": self.capture_interval,
                    "duration_minutes": duration_minutes if self.session_start_time else 0
                }
                
                info_json = json.dumps(session_info, indent=2, ensure_ascii=False)
                zipf.writestr("recording_info.json", info_json)
            
            # 删除原始文件夹
            shutil.rmtree(self.current_session_folder)
            
            # 显示成功消息
            QMessageBox.information(
                self, 
                "✅ 打包完成", 
                f"录制数据已打包完成！\n\n"
                f"📦 文件名: {zip_filename}\n"
                f"📊 图片数量: {self.recording_count} 张\n"
                f"⏱️ 录制时长: {duration_str}\n"
                f"📁 保存位置: {os.path.dirname(zip_path)}"
            )
            
            self.logger.info(f"录制包创建成功: {zip_path}")
            
            # 为下次录制准备新目录
            self.create_recording_directory()
            
        except Exception as e:
            self.logger.error(f"创建录制包失败: {e}")
            QMessageBox.critical(self, "❌ 错误", f"创建录制包失败:\n{e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止所有定时器
        if hasattr(self, 'preview_timer'):
            self.preview_timer.stop()
        if hasattr(self, 'duration_timer'):
            self.duration_timer.stop()
        if hasattr(self, 'reconnect_timer'):
            self.reconnect_timer.stop()
        
        # 如果正在录制，先询问用户
        if self.is_recording:
            reply = QMessageBox.question(
                self, 
                "🤔 确认退出", 
                "正在录制中，确定要退出吗？\n录制数据将会保存。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.stop_recording()
        
        # 断开WebSocket连接（同步方式）
        if self.websocket_client:
            try:
                # 设置停止标志
                self.websocket_client.is_running = False
                self.websocket_client.is_connected_flag = False
                
                # 直接设置websocket为None，避免异步关闭
                if hasattr(self.websocket_client, 'websocket'):
                    self.websocket_client.websocket = None
                
                # 停止状态检查定时器
                if hasattr(self.websocket_client, 'status_timer'):
                    self.websocket_client.status_timer.stop()
                
                self.websocket_client = None
            except Exception as e:
                self.logger.error(f"关闭WebSocket时出错: {e}")
        
        # 强制退出应用
        event.accept()
        QApplication.instance().quit()


def apply_modern_theme(app):
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


def main():
    """主函数"""
    # 在创建QApplication之前设置高DPI属性
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("PaperTracker图像录制工具")
    app.setApplicationVersion("3.0.0")
    app.setApplicationDisplayName("📷 PaperTracker 图像录制工具")
    
    # 应用现代主题
    apply_modern_theme(app)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(font)
    
    # 创建并显示主窗口
    window = PaperTrackerRecorder()
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