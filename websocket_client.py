# websocket_client.py
"""
WebSocket客户端组件 - 参考papertrackerqt实现
专门用于与ESP32设备进行WebSocket通信，接收图像数据
"""

import json
import logging
import queue
import threading
import time
from typing import Optional, Callable, Dict, Any
import asyncio
import websockets
import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QImage, QPixmap


class WebSocketImageStream(QObject):
    """WebSocket图像流处理类"""
    
    # 定义信号
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    image_received = pyqtSignal(np.ndarray)  # 发送OpenCV图像
    battery_updated = pyqtSignal(float)
    brightness_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.websocket = None
        self.is_running = False
        self.is_connected = False
        self.current_url = ""
        self.connection_urls = []
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.image_buffer_queue = queue.Queue(maxsize=10)
        self.image_not_receive_count = 0
        self.heartbeat_timer = None
        self.battery_percentage = 0.0
        self.brightness_value = 0
        
        # 设备类型常量
        self.DEVICE_TYPE_UNKNOWN = 0
        self.DEVICE_TYPE_FACE = 1
        self.DEVICE_TYPE_LEFT_EYE = 2
        self.DEVICE_TYPE_RIGHT_EYE = 3
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化心跳定时器
        self.init_heartbeat_timer()
    
    def init_heartbeat_timer(self):
        """初始化心跳定时器"""
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.check_heartbeat)
        self.heartbeat_timer.setInterval(50)  # 50ms检查一次
    
    def init(self, url: str, device_type: int = 0) -> bool:
        """
        初始化WebSocket连接
        
        Args:
            url: WebSocket连接地址
            device_type: 设备类型 (0:未知, 1:面捕, 2:左眼, 3:右眼)
            
        Returns:
            bool: 初始化是否成功
        """
        if not url and not self.current_url:
            self.logger.info("无法初始化WebSocket：URL为空")
            return False
        
        if url:
            self.current_url = url
            self.connection_urls.clear()
            self.connection_attempts = 0
            
            # 转换URL格式
            ws_urls = self._convert_to_websocket_urls(url)
            self.connection_urls.extend(ws_urls)
            
            # 根据设备类型添加mDNS地址
            mdns_urls = self._get_mdns_urls_by_device_type(device_type)
            self.connection_urls.extend(mdns_urls)
            
            self.logger.debug(f"初始化WebSocket视频流，URL列表: {self.connection_urls}")
        
        return True
    
    def _convert_to_websocket_urls(self, url: str) -> list:
        """转换URL为WebSocket格式"""
        urls = []
        
        # 如果已经是WebSocket URL，直接使用
        if url.startswith(('ws://', 'wss://')):
            urls.append(url)
            return urls
        
        # 转换HTTP URL为WebSocket URL
        if url.startswith('http://'):
            ws_url = url.replace('http://', 'ws://') + '/ws'
            urls.append(ws_url)
        elif url.startswith('https://'):
            ws_url = url.replace('https://', 'wss://') + '/ws'
            urls.append(ws_url)
        else:
            # 假设是IP地址或主机名
            ws_url = f"ws://{url}"
            if ':' not in url:
                ws_url += ':80'
            if not ws_url.endswith('/ws'):
                ws_url += '/ws'
            urls.append(ws_url)
        
        return urls
    
    def _get_mdns_urls_by_device_type(self, device_type: int) -> list:
        """根据设备类型获取mDNS地址"""
        mdns_urls = []
        
        if device_type == self.DEVICE_TYPE_FACE:
            mdns_urls.append("ws://paper1.local:80/ws")
        elif device_type == self.DEVICE_TYPE_LEFT_EYE:
            mdns_urls.append("ws://paper2.local:80/ws")
        elif device_type == self.DEVICE_TYPE_RIGHT_EYE:
            mdns_urls.append("ws://paper3.local:80/ws")
        
        return mdns_urls
    
    def start(self) -> bool:
        """开始WebSocket连接"""
        if not self.connection_urls and not self.current_url:
            self.logger.info("无法启动WebSocket连接：URL为空")
            return False
        
        if self.is_running:
            self.logger.warning("视频流已经在运行中")
            return False
        
        # 开始连接尝试
        self.connection_attempts = 0
        self._try_connect_to_next_address()
        
        # 启动心跳定时器
        if not self.heartbeat_timer.isActive():
            self.heartbeat_timer.start()
        
        return True
    
    def stop(self):
        """停止WebSocket连接"""
        self.logger.debug("停止WebSocket视频流")
        self.is_running = False
        self.is_connected = False
        
        # 停止心跳定时器
        if self.heartbeat_timer and self.heartbeat_timer.isActive():
            self.heartbeat_timer.stop()
        
        # 关闭WebSocket连接
        if self.websocket:
            asyncio.create_task(self.websocket.close())
            self.websocket = None
        
        # 清空图像队列
        while not self.image_buffer_queue.empty():
            try:
                self.image_buffer_queue.get_nowait()
            except queue.Empty:
                break
        
        self.disconnected.emit()
    
    def _try_connect_to_next_address(self):
        """尝试连接到下一个地址"""
        if self.connection_attempts >= len(self.connection_urls):
            self.logger.error("所有连接地址尝试失败")
            self.error_occurred.emit("所有连接地址尝试失败")
            return
        
        if self.connection_attempts < len(self.connection_urls):
            url = self.connection_urls[self.connection_attempts]
            self.connection_attempts += 1
            
            self.logger.info(f"尝试连接到: {url}")
            
            # 在新线程中进行连接
            thread = threading.Thread(target=self._connect_to_url, args=(url,))
            thread.daemon = True
            thread.start()
    
    def _connect_to_url(self, url: str):
        """连接到指定URL"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行连接
            loop.run_until_complete(self._websocket_connection(url))
            
        except Exception as e:
            self.logger.error(f"连接错误: {e}")
            self.error_occurred.emit(f"连接错误: {e}")
            # 尝试下一个地址
            self._try_connect_to_next_address()
    
    async def _websocket_connection(self, url: str):
        """WebSocket连接处理"""
        try:
            # 设置连接超时
            self.websocket = await asyncio.wait_for(
                websockets.connect(url),
                timeout=3.0
            )
            
            self.is_connected = True
            self.is_running = True
            self.image_not_receive_count = 0
            
            self.logger.info(f"成功连接到WebSocket: {url}")
            self.connected.emit()
            
            # 开始接收消息
            async for message in self.websocket:
                if not self.is_running:
                    break
                
                if isinstance(message, bytes):
                    # 处理二进制消息（图像数据）
                    self._handle_binary_message(message)
                else:
                    # 处理文本消息（JSON数据）
                    self._handle_text_message(message)
                    
        except asyncio.TimeoutError:
            self.logger.debug(f"连接到 {url} 超时")
            self._try_connect_to_next_address()
        except Exception as e:
            self.logger.error(f"WebSocket连接错误: {e}")
            self.error_occurred.emit(f"WebSocket连接错误: {e}")
            if self.is_running:
                self._try_connect_to_next_address()
    
    def _handle_binary_message(self, message: bytes):
        """处理二进制消息（图像数据）"""
        try:
            self.is_running = True
            self.image_not_receive_count = 0
            
            # 检查数据长度
            if len(message) < 10:
                self.logger.warning("接收到的数据太短，不可能是有效的图像")
                return
            
            # 使用OpenCV解码图像
            nparr = np.frombuffer(message, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                # 将图像放入队列
                if self.image_buffer_queue.full():
                    try:
                        self.image_buffer_queue.get_nowait()
                    except queue.Empty:
                        pass
                
                self.image_buffer_queue.put(img)
                self.image_received.emit(img)
                
        except Exception as e:
            self.logger.error(f"处理二进制消息错误: {e}")
    
    def _handle_text_message(self, message: str):
        """处理文本消息（JSON数据）"""
        try:
            data = json.loads(message)
            
            if 'battery' in data:
                self.battery_percentage = float(data['battery'])
                self.battery_updated.emit(self.battery_percentage)
                self.logger.debug(f"收到电池电量: {self.battery_percentage}%")
            
            if 'brightness' in data:
                self.brightness_value = int(data['brightness'])
                self.brightness_updated.emit(self.brightness_value)
                self.logger.debug(f"收到亮度值: {self.brightness_value}")
                
        except json.JSONDecodeError:
            self.logger.warning(f"无法解析JSON消息: {message}")
        except Exception as e:
            self.logger.error(f"处理文本消息错误: {e}")
    
    def check_heartbeat(self):
        """检查心跳"""
        if not self.current_url:
            if self.heartbeat_timer.isActive():
                self.heartbeat_timer.stop()
            return
        
        if self.image_not_receive_count > 50:  # 50 * 50ms = 2.5秒无数据
            self.image_not_receive_count = 0
            self.logger.warning("心跳检查失败，重新连接")
            self.is_running = False
            self.stop()
            self.start()
        else:
            self.image_not_receive_count += 1
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """获取最新的帧"""
        try:
            if self.image_buffer_queue.empty():
                return None
            
            # 取出最新的图像
            img = None
            while not self.image_buffer_queue.empty():
                img = self.image_buffer_queue.get_nowait()
            
            return img
            
        except queue.Empty:
            return None
    
    def is_streaming(self) -> bool:
        """检查是否正在流式传输"""
        return self.is_running and self.is_connected
    
    def get_battery_percentage(self) -> float:
        """获取电池电量百分比"""
        return self.battery_percentage
    
    def get_brightness_value(self) -> int:
        """获取亮度值"""
        return self.brightness_value


class WebSocketManager(QObject):
    """WebSocket连接管理器"""
    
    # 定义信号
    connection_status_changed = pyqtSignal(bool, str)  # 连接状态, 状态信息
    image_received = pyqtSignal(np.ndarray)
    battery_status_changed = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_stream = WebSocketImageStream(self)
        self.device_type = 0
        self.current_url = ""
        
        # 连接信号
        self.image_stream.connected.connect(self._on_connected)
        self.image_stream.disconnected.connect(self._on_disconnected)
        self.image_stream.error_occurred.connect(self._on_error)
        self.image_stream.image_received.connect(self.image_received)
        self.image_stream.battery_updated.connect(self.battery_status_changed)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def connect_to_device(self, url: str, device_type: int = 0) -> bool:
        """连接到设备"""
        self.current_url = url
        self.device_type = device_type
        
        if self.image_stream.init(url, device_type):
            return self.image_stream.start()
        return False
    
    def disconnect_from_device(self):
        """断开设备连接"""
        self.image_stream.stop()
    
    def get_latest_image(self) -> Optional[np.ndarray]:
        """获取最新图像"""
        return self.image_stream.get_latest_frame()
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.image_stream.is_streaming()
    
    def get_battery_level(self) -> float:
        """获取电池电量"""
        return self.image_stream.get_battery_percentage()
    
    def _on_connected(self):
        """连接成功回调"""
        self.logger.info("WebSocket连接成功")
        self.connection_status_changed.emit(True, "连接成功")
    
    def _on_disconnected(self):
        """断开连接回调"""
        self.logger.info("WebSocket连接断开")
        self.connection_status_changed.emit(False, "连接断开")
    
    def _on_error(self, error_msg: str):
        """错误回调"""
        self.logger.error(f"WebSocket错误: {error_msg}")
        self.connection_status_changed.emit(False, f"连接错误: {error_msg}")