# labeler_websocket_widget.py
"""
标注工具WebSocket连接组件
集成到主要的labeler界面中，提供实时图像流功能
"""

import os
import cv2
import numpy as np
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTextEdit, QGroupBox, QGridLayout,
    QCheckBox, QSpinBox, QSlider, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QFont
import logging

from websocket_client import WebSocketManager


class WebSocketControlWidget(QWidget):
    """WebSocket控制面板组件"""
    
    # 定义信号
    image_received = pyqtSignal(np.ndarray)
    connection_status_changed = pyqtSignal(bool, str)
    save_image_requested = pyqtSignal(np.ndarray, str)  # 图像数据，文件名
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.websocket_manager = WebSocketManager(self)
        self.image_save_counter = 0
        self.is_auto_save = False
        self.save_directory = ""
        self.current_image = None
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化界面
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 连接设置组
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)
        
        # 图像显示组
        image_group = self.create_image_group()
        layout.addWidget(image_group)
        
        # 控制按钮组
        control_group = self.create_control_group()
        layout.addWidget(control_group)
        
        # 状态信息组
        status_group = self.create_status_group()
        layout.addWidget(status_group)
        
        # 设置整体样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
    
    def create_connection_group(self) -> QGroupBox:
        """创建连接设置组"""
        group = QGroupBox("WebSocket连接设置")
        layout = QGridLayout(group)
        
        # URL输入
        layout.addWidget(QLabel("设备地址:"), 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入设备IP地址或URL (例: 192.168.1.100)")
        layout.addWidget(self.url_input, 0, 1)
        
        # 设备类型选择
        layout.addWidget(QLabel("设备类型:"), 1, 0)
        self.device_type_combo = QComboBox()
        self.device_type_combo.addItems([
            "未知设备", "面捕设备", "左眼设备", "右眼设备"
        ])
        layout.addWidget(self.device_type_combo, 1, 1)
        
        # 连接按钮
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button, 2, 0, 1, 2)
        
        return group
    
    def create_image_group(self) -> QGroupBox:
        """创建图像显示组"""
        group = QGroupBox("实时图像流")
        layout = QVBoxLayout(group)
        
        # 图像显示标签
        self.image_label = QLabel()
        self.image_label.setMinimumSize(320, 240)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #cccccc;
                background-color: #f0f0f0;
                text-align: center;
            }
        """)
        self.image_label.setText("未连接到设备")
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # 图像信息
        info_layout = QHBoxLayout()
        self.image_info_label = QLabel("尺寸: - | 帧率: -")
        self.image_info_label.setFont(QFont("Arial", 9))
        info_layout.addWidget(self.image_info_label)
        info_layout.addStretch()
        
        # 电池电量显示
        self.battery_label = QLabel("电池: -%")
        self.battery_label.setFont(QFont("Arial", 9))
        info_layout.addWidget(self.battery_label)
        
        layout.addLayout(info_layout)
        
        return group
    
    def create_control_group(self) -> QGroupBox:
        """创建控制按钮组"""
        group = QGroupBox("图像控制")
        layout = QGridLayout(group)
        
        # 保存设置
        layout.addWidget(QLabel("保存目录:"), 0, 0)
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setPlaceholderText("选择图像保存目录")
        layout.addWidget(self.save_dir_input, 0, 1)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_save_directory)
        layout.addWidget(self.browse_button, 0, 2)
        
        # 自动保存设置
        self.auto_save_checkbox = QCheckBox("自动保存")
        self.auto_save_checkbox.toggled.connect(self.toggle_auto_save)
        layout.addWidget(self.auto_save_checkbox, 1, 0)
        
        # 保存间隔设置
        layout.addWidget(QLabel("间隔(秒):"), 1, 1)
        self.save_interval_spin = QSpinBox()
        self.save_interval_spin.setRange(1, 60)
        self.save_interval_spin.setValue(5)
        layout.addWidget(self.save_interval_spin, 1, 2)
        
        # 手动保存按钮
        self.save_button = QPushButton("保存当前图像")
        self.save_button.clicked.connect(self.save_current_image)
        self.save_button.setEnabled(False)
        layout.addWidget(self.save_button, 2, 0, 1, 3)
        
        return group
    
    def create_status_group(self) -> QGroupBox:
        """创建状态信息组"""
        group = QGroupBox("状态信息")
        layout = QVBoxLayout(group)
        
        # 连接状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("连接状态:"))
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 统计信息
        stats_layout = QGridLayout()
        stats_layout.addWidget(QLabel("已接收帧数:"), 0, 0)
        self.frame_count_label = QLabel("0")
        stats_layout.addWidget(self.frame_count_label, 0, 1)
        
        stats_layout.addWidget(QLabel("已保存图像:"), 0, 2)
        self.saved_count_label = QLabel("0")
        stats_layout.addWidget(self.saved_count_label, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # 日志输出
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        return group
    
    def setup_connections(self):
        """设置信号连接"""
        # WebSocket管理器信号
        self.websocket_manager.connection_status_changed.connect(
            self.on_connection_status_changed
        )
        self.websocket_manager.image_received.connect(
            self.on_image_received
        )
        self.websocket_manager.battery_status_changed.connect(
            self.on_battery_status_changed
        )
        
        # 自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_image)
        
        # 帧率计算定时器
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)  # 每秒更新一次
        
        # 帧计数
        self.frame_count = 0
        self.last_frame_count = 0
        self.saved_image_count = 0
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.websocket_manager.is_connected():
            self.disconnect_device()
        else:
            self.connect_device()
    
    def connect_device(self):
        """连接设备"""
        url = self.url_input.text().strip()
        if not url:
            self.log_message("请输入设备地址")
            return
        
        device_type = self.device_type_combo.currentIndex()
        self.log_message(f"正在连接到设备: {url}")
        
        if self.websocket_manager.connect_to_device(url, device_type):
            self.connect_button.setText("断开")
            self.connect_button.setEnabled(False)  # 连接过程中禁用按钮
        else:
            self.log_message("连接失败")
    
    def disconnect_device(self):
        """断开设备连接"""
        self.websocket_manager.disconnect_from_device()
        self.connect_button.setText("连接")
        self.save_button.setEnabled(False)
        self.image_label.setText("未连接到设备")
        self.log_message("已断开连接")
    
    def on_connection_status_changed(self, connected: bool, message: str):
        """连接状态变化处理"""
        if connected:
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_button.setText("断开")
            self.save_button.setEnabled(True)
            self.log_message("连接成功")
        else:
            self.status_label.setText("未连接")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_button.setText("连接")
            self.save_button.setEnabled(False)
            self.log_message(f"连接断开: {message}")
        
        self.connect_button.setEnabled(True)
        self.connection_status_changed.emit(connected, message)
    
    def on_image_received(self, image: np.ndarray):
        """图像接收处理"""
        self.current_image = image
        self.frame_count += 1
        
        # 更新图像显示
        self.update_image_display(image)
        
        # 更新图像信息
        height, width = image.shape[:2]
        self.image_info_label.setText(f"尺寸: {width}x{height} | 帧数: {self.frame_count}")
        
        # 发送图像信号
        self.image_received.emit(image)
        
        # 自动保存
        if self.is_auto_save and self.save_directory:
            # 检查是否需要保存（基于时间间隔）
            if not hasattr(self, '_last_auto_save_time'):
                self._last_auto_save_time = 0
            
            current_time = QTimer.singleShot(0, lambda: None)  # 获取当前时间
            interval = self.save_interval_spin.value() * 1000  # 转换为毫秒
            
            if hasattr(self, '_last_auto_save_time') and (current_time - self._last_auto_save_time) >= interval:
                self.auto_save_image()
                self._last_auto_save_time = current_time
    
    def update_image_display(self, image: np.ndarray):
        """更新图像显示"""
        try:
            # 转换颜色空间（OpenCV使用BGR，Qt使用RGB）
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 获取图像尺寸
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width
            
            # 创建QImage
            q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # 缩放图像以适应显示区域
            label_size = self.image_label.size()
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # 更新显示
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.logger.error(f"更新图像显示错误: {e}")
    
    def on_battery_status_changed(self, battery_level: float):
        """电池状态变化处理"""
        self.battery_label.setText(f"电池: {battery_level:.1f}%")
        
        # 根据电池电量设置颜色
        if battery_level > 50:
            color = "green"
        elif battery_level > 20:
            color = "orange"
        else:
            color = "red"
        
        self.battery_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def browse_save_directory(self):
        """浏览保存目录"""
        from PyQt5.QtWidgets import QFileDialog
        
        directory = QFileDialog.getExistingDirectory(
            self, "选择图像保存目录", self.save_directory
        )
        
        if directory:
            self.save_directory = directory
            self.save_dir_input.setText(directory)
            self.log_message(f"设置保存目录: {directory}")
    
    def toggle_auto_save(self, enabled: bool):
        """切换自动保存"""
        self.is_auto_save = enabled
        
        if enabled:
            if not self.save_directory:
                self.log_message("请先选择保存目录")
                self.auto_save_checkbox.setChecked(False)
                return
            
            interval = self.save_interval_spin.value() * 1000
            self.auto_save_timer.start(interval)
            self.log_message(f"启用自动保存，间隔: {self.save_interval_spin.value()}秒")
        else:
            self.auto_save_timer.stop()
            self.log_message("禁用自动保存")
    
    def save_current_image(self):
        """保存当前图像"""
        if self.current_image is None:
            self.log_message("没有可保存的图像")
            return
        
        if not self.save_directory:
            self.log_message("请先选择保存目录")
            return
        
        self.save_image(self.current_image)
    
    def auto_save_image(self):
        """自动保存图像"""
        if self.current_image is not None:
            self.save_image(self.current_image, auto_save=True)
    
    def save_image(self, image: np.ndarray, auto_save: bool = False):
        """保存图像到文件"""
        try:
            # 确保保存目录存在
            os.makedirs(self.save_directory, exist_ok=True)
            
            # 生成文件名
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}_{self.image_save_counter:04d}.jpg"
            filepath = os.path.join(self.save_directory, filename)
            
            # 保存图像
            success = cv2.imwrite(filepath, image)
            
            if success:
                self.image_save_counter += 1
                self.saved_image_count += 1
                self.saved_count_label.setText(str(self.saved_image_count))
                
                save_type = "自动保存" if auto_save else "手动保存"
                self.log_message(f"{save_type}成功: {filename}")
                
                # 发送保存信号
                self.save_image_requested.emit(image, filepath)
            else:
                self.log_message("保存图像失败")
                
        except Exception as e:
            self.logger.error(f"保存图像错误: {e}")
            self.log_message(f"保存图像错误: {e}")
    
    def update_fps(self):
        """更新帧率显示"""
        current_fps = self.frame_count - self.last_frame_count
        self.last_frame_count = self.frame_count
        
        if hasattr(self, 'image_info_label'):
            current_text = self.image_info_label.text()
            if '|' in current_text:
                size_part = current_text.split('|')[0].strip()
                self.image_info_label.setText(f"{size_part} | 帧率: {current_fps} FPS")
    
    def log_message(self, message: str):
        """添加日志消息"""
        import time
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_text.append(formatted_message)
        self.logger.info(message)
        
        # 限制日志长度
        if self.log_text.document().blockCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def get_current_image(self) -> Optional[np.ndarray]:
        """获取当前图像"""
        return self.current_image
    
    def set_save_directory(self, directory: str):
        """设置保存目录"""
        self.save_directory = directory
        self.save_dir_input.setText(directory)
    
    def get_connection_status(self) -> bool:
        """获取连接状态"""
        return self.websocket_manager.is_connected()
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        return {
            'url': self.url_input.text(),
            'device_type': self.device_type_combo.currentIndex(),
            'connected': self.websocket_manager.is_connected(),
            'battery_level': self.websocket_manager.get_battery_level(),
            'frame_count': self.frame_count,
            'saved_count': self.saved_image_count
        }


class WebSocketImageProvider(QThread):
    """WebSocket图像提供者线程"""
    
    image_ready = pyqtSignal(np.ndarray, str)  # 图像，文件路径
    
    def __init__(self, websocket_widget: WebSocketControlWidget, parent=None):
        super().__init__(parent)
        self.websocket_widget = websocket_widget
        self.is_running = False
        self.image_queue = []
        self.save_directory = ""
        
    def set_save_directory(self, directory: str):
        """设置保存目录"""
        self.save_directory = directory
        
    def start_capture(self):
        """开始捕获"""
        self.is_running = True
        self.start()
        
    def stop_capture(self):
        """停止捕获"""
        self.is_running = False
        self.wait()
        
    def run(self):
        """运行线程"""
        while self.is_running:
            if self.websocket_widget.get_connection_status():
                image = self.websocket_widget.get_current_image()
                if image is not None:
                    # 保存图像并发送信号
                    filename = self.save_image_to_temp(image)
                    if filename:
                        self.image_ready.emit(image, filename)
            
            self.msleep(100)  # 100ms间隔
            
    def save_image_to_temp(self, image: np.ndarray) -> Optional[str]:
        """保存图像到临时文件"""
        try:
            import tempfile
            import time
            
            timestamp = time.strftime("%Y%m%d_%H%M%S_%f")
            temp_dir = tempfile.gettempdir()
            filename = f"websocket_capture_{timestamp}.jpg"
            filepath = os.path.join(temp_dir, filename)
            
            success = cv2.imwrite(filepath, image)
            return filepath if success else None
            
        except Exception as e:
            logging.error(f"保存临时图像错误: {e}")
            return None