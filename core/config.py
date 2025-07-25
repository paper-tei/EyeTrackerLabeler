"""
配置管理模块
负责应用程序的配置参数管理
"""
import os
from PyQt5.QtCore import QSettings


class AppConfig:
    """应用程序配置管理类"""
    
    def __init__(self):
        self.settings = QSettings('PaperTracker', 'ImageRecorder')
        self._setup_default_config()
    
    def _setup_default_config(self):
        """设置默认配置"""
        # 图像设置
        self.image_format = 'jpg'
        self.capture_interval = 100  # ms
        self.jpeg_quality = 95
        self.target_size = (240, 240)
        
        # WebSocket设置
        self.max_reconnect_attempts = 5
        self.reconnect_interval = 5000  # ms
        
        # UI设置
        self.preview_fps = 30
        self.window_min_size = (1400, 800)
        self.control_panel_width = 420
    
    def get_user_info(self):
        """获取用户信息"""
        return {
            'username': self.settings.value('username', ''),
            'email': self.settings.value('email', '')
        }
    
    def save_user_info(self, username, email):
        """保存用户信息"""
        self.settings.setValue('username', username)
        self.settings.setValue('email', email)
    
    def has_user_info(self):
        """检查是否有用户信息"""
        user_info = self.get_user_info()
        return bool(user_info['username'] and user_info['email'])
    
    def get_default_websocket_url(self):
        """获取默认WebSocket URL"""
        return self.settings.value('last_device_url', '192.168.1.100:8080')
    
    def save_websocket_url(self, url):
        """保存WebSocket URL"""
        self.settings.setValue('last_device_url', url)


# 全局配置实例
config = AppConfig()
