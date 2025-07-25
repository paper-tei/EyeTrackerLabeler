"""
录制器基类模块
包含录制器的基础功能和UI框架
"""
import sys
import logging
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
    QStatusBar, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage

# 导入模块
from core.config import config
from core.image_processor import ImageProcessor
from data.recording import RecordingSession
from ui.components import UserInfoDialog
from ui.panels import ControlPanelManager, PreviewManager
from ui.styles import get_main_stylesheet, get_scrollarea_stylesheet, apply_modern_theme

# 导入WebSocket客户端
from simple_websocket_client import WebSocketClient


class BaseRecorder(QMainWindow):
    """录制器基类"""
    
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
        self.current_image = None
        self.session_start_time = None
        self.current_session = None
        
        # 定时器
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self.update_duration)
        
        # 自动重连机制
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.auto_reconnect)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = config.max_reconnect_attempts
        
        # 防止递归断开连接的标志
        self._disconnecting = False
        
        # 用户信息
        self.user_info = config.get_user_info()
        
        # UI管理器
        self.panel_manager = ControlPanelManager(self)
        self.preview_manager = PreviewManager(self)
        
        # 图像处理器
        self.image_processor = ImageProcessor()
    
    def check_user_info(self):
        """检查并设置用户信息"""
        if not config.has_user_info():
            dialog = UserInfoDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                user_info = dialog.get_user_info()
                self.user_info = user_info
                config.save_user_info(user_info['username'], user_info['email'])
            else:
                sys.exit()
        else:
            self.user_info = config.get_user_info()
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("📷 PaperTracker 图像录制工具")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(*config.window_min_size)
        
        # 设置应用程序样式
        self.setStyleSheet(get_main_stylesheet())
        
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
        left_scroll.setFixedWidth(config.control_panel_width)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setStyleSheet(get_scrollarea_stylesheet())
        
        left_panel = self.panel_manager.create_control_panel(enhanced=False)
        left_scroll.setWidget(left_panel)
        main_layout.addWidget(left_scroll)
        
        # 右侧预览面板
        right_panel = self.panel_manager.create_preview_panel(enhanced=False)
        main_layout.addWidget(right_panel)
        
        # 设置比例
        main_layout.setStretch(0, 0)  # 控制面板固定
        main_layout.setStretch(1, 1)  # 预览面板可伸缩
        
        # 创建状态栏
        self.create_status_bar()
    
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
        # 从配置中获取默认URL
        default_url = config.get_default_websocket_url()
        self.device_input.setText(default_url)
    
    def connect_device(self):
        """连接设备"""
        # 重置断开连接标志
        self._disconnecting = False
        
        device_addr = self.device_input.text().strip()
        if not device_addr:
            QMessageBox.warning(self, "⚠️ 提示", "请输入设备地址！")
            return
        
        # 处理URL格式
        if not '/' in device_addr and ':' in device_addr:
            device_addr = device_addr + '/ws'
        elif not '/' in device_addr:
            device_addr = device_addr + '/ws'
        
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
            
            # 保存设备地址
            config.save_websocket_url(self.device_input.text().strip())
            
            # 更新UI状态
            self.connect_btn.setEnabled(False)
            self.connection_status.setText("🔄 连接中...")
            self.connection_status.setStyleSheet(self.panel_manager.status_styles["connecting"])
            
        except Exception as e:
            QMessageBox.critical(self, "❌ 连接失败", f"无法连接到设备:\\n{e}")
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
                pass
            
            # 然后断开WebSocket连接
            try:
                self.websocket_client.disconnect_from_device()
            except:
                pass
            
            self.websocket_client = None
        
        # 停止重连定时器
        self.reconnect_timer.stop()
        self.reconnect_attempts = 0
        
        # 更新UI状态
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.connection_status.setText("❌ 未连接")
        self.connection_status.setStyleSheet(self.panel_manager.status_styles["disconnected"])
        self.preview_label.setText("📷 设备已断开\\n\\n请重新连接设备")
        if hasattr(self, 'preview_timer'):
            self.preview_timer.stop()
        
        # 重置断开连接标志
        self._disconnecting = False
    
    def on_device_connected(self):
        """设备连接成功"""
        self.reconnect_attempts = 0
        self.reconnect_timer.stop()
        
        self.connection_status.setText("✅ 已连接")
        self.connection_status.setStyleSheet(self.panel_manager.status_styles["connected"])
        self.disconnect_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.preview_timer.start(1000 // config.preview_fps)  # 根据配置设置FPS
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
            self.reconnect_timer.start(config.reconnect_interval)
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
                import cv2
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
            # 应用图像处理（仅用于预览）
            preview_image = self.current_image.copy()
            
            # 如果是增强版，应用旋转等处理
            if hasattr(self, 'rotation_angle'):
                if self.image_processor.rotation_angle != 0:
                    preview_image = self.image_processor.rotate_image(
                        preview_image, self.image_processor.rotation_angle
                    )
            
            self.preview_manager.update_preview(preview_image)
    
    def start_recording(self):
        """开始录制"""
        if not self.websocket_client or not self.websocket_client.is_connected():
            QMessageBox.warning(self, "⚠️ 警告", "请先连接设备！")
            return
        
        # 创建新的录制会话
        self.current_session = RecordingSession(
            self.user_info['username'], 
            self.user_info['email']
        )
        self.current_session.start_session()
        
        self.is_recording = True
        self.session_start_time = datetime.now()
        
        # 更新UI状态
        self.recording_status.setText("🔴 录制中")
        self.recording_status.setStyleSheet(self.panel_manager.status_styles["recording"])
        
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
        self.recording_status.setStyleSheet(self.panel_manager.status_styles["standby"])
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 录制完成后打包
        if self.current_session and self.current_session.image_count > 0:
            package_path = self.current_session.create_package()
            if package_path:
                QMessageBox.information(
                    self, 
                    "✅ 打包完成", 
                    f"录制数据已打包完成！\\n\\n"
                    f"📦 文件: {package_path}\\n"
                    f"📊 图片数量: {self.current_session.image_count} 张"
                )
        
        if self.current_session:
            count = self.current_session.image_count
            self.statusBar().showMessage(f"✅ 录制完成，共保存 {count} 张图片")
            self.logger.info(f"录制停止，共保存 {count} 张图片")
        
        self.current_session = None
    
    def save_current_image(self):
        """保存当前图像"""
        if self.current_image is None or not self.current_session:
            return
        
        try:
            # 处理图像
            processed_image = self.process_image_for_saving(self.current_image)
            
            # 生成处理参数后缀
            suffix = self.image_processor.get_process_suffix()
            
            # 保存图像
            success = self.current_session.save_image(processed_image, suffix)
            
            if success:
                # 更新计数显示
                count = self.current_session.image_count
                self.image_count_label.setText(f"{count} 张")
            
        except Exception as e:
            self.logger.error(f"保存图像失败: {e}")
    
    def process_image_for_saving(self, image):
        """处理图像用于保存（子类可重写）"""
        return self.image_processor.process_image(image)
    
    def update_duration(self):
        """更新录制时长"""
        if self.session_start_time:
            duration = datetime.now() - self.session_start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            self.duration_label.setText(duration_str)
    
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
                "正在录制中，确定要退出吗？\\n录制数据将会保存。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.stop_recording()
        
        # 断开WebSocket连接
        if self.websocket_client:
            try:
                self.websocket_client.is_running = False
                self.websocket_client.is_connected_flag = False
                
                if hasattr(self.websocket_client, 'websocket'):
                    self.websocket_client.websocket = None
                
                if hasattr(self.websocket_client, 'status_timer'):
                    self.websocket_client.status_timer.stop()
                
                self.websocket_client = None
            except Exception as e:
                self.logger.error(f"关闭WebSocket时出错: {e}")
        
        # 强制退出应用
        event.accept()
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().quit()
