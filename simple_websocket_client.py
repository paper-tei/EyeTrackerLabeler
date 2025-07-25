# simple_websocket_client.py
"""
简化的WebSocket客户端 - 专门用于录制软件
基于现有的websocket_client.py，简化接口，专注于图像接收和保存
"""

import json
import logging
import asyncio
import threading
import time
from typing import Optional
import cv2
import numpy as np
import websockets
from PyQt5.QtCore import QObject, pyqtSignal, QTimer


class WebSocketClient(QObject):
    """简化的WebSocket客户端"""
    
    # 定义信号
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    image_received = pyqtSignal(np.ndarray)  # 发送图像数据
    status_updated = pyqtSignal(str)  # 状态更新
    
    def __init__(self, url: str = "", parent=None):
        super().__init__(parent)
        self.url = url
        self.websocket = None
        self.is_connected_flag = False
        self.is_running = False
        self.current_image = None
        self.connection_thread = None
        self.url_variants = []  # 添加URL变体列表
        self.current_url_index = 0  # 当前尝试的URL索引
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 状态检查定时器 - 完全禁用以避免干扰
        self.enable_status_check = False  # 完全禁用状态检查
        self.status_timer = None  # 不创建定时器
        
        # 图像接收计数
        self.image_count = 0
        self.last_image_time = 0
        
    def set_url(self, url: str):
        """设置WebSocket URL"""
        self.url = url
        
    def enable_status_monitoring(self, enabled: bool = True):
        """启用或禁用状态监控 - 完全禁用此功能"""
        self.logger.info("状态监控功能已完全禁用以防止连接问题")
        
    def get_url(self) -> str:
        """获取当前URL"""
        return self.url
        
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.is_connected_flag
        
    def get_current_image(self) -> Optional[np.ndarray]:
        """获取当前图像"""
        return self.current_image
        
    def connect_to_device(self):
        """连接到设备"""
        if not self.url:
            self.error_occurred.emit("请先设置设备地址")
            return
            
        if self.is_connected_flag:
            self.logger.warning("设备已经连接")
            return
            
        self.is_running = True
        
        # 智能URL处理 - 如果URL不以ws://开头，自动添加
        url = self.url.strip()
        if not url.startswith(('ws://', 'wss://')):
            if url.startswith('http://'):
                url = url.replace('http://', 'ws://')
            elif url.startswith('https://'):
                url = url.replace('https://', 'wss://')
            else:
                # 如果只是IP地址，添加ws://前缀
                url = f"ws://{url}"
        
        # 如果URL没有路径，尝试添加/ws路径
        self.url_variants = [url]
        if not url.endswith('/ws') and not url.endswith('/'):
            self.url_variants.append(f"{url}/ws")
        elif url.endswith('/'):
            self.url_variants.append(f"{url}ws")
        
        self.current_url_index = 0
        
        # 在新线程中启动连接
        self.connection_thread = threading.Thread(target=self._run_connection)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        
        # 完全不启动状态检查定时器
        
    def disconnect_from_device(self):
        """断开设备连接"""
        self.is_running = False
        self.is_connected_flag = False
        
        # 不需要停止状态检查定时器（因为已经禁用）
        
        # 温和地关闭WebSocket连接
        if self.websocket:
            try:
                # 设置关闭标志，让接收循环自然结束
                self.websocket = None
            except Exception as e:
                self.logger.error(f"关闭WebSocket连接时出错: {e}")
        
        self.current_image = None
        self.logger.info("设备连接已断开")
        self.disconnected.emit()
        
    async def _close_websocket(self):
        """异步关闭WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
    def _run_connection(self):
        """在线程中运行连接"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 尝试所有URL变体
            for i, url in enumerate(self.url_variants):
                if not self.is_running:
                    break
                    
                try:
                    self.logger.info(f"尝试连接到: {url}")
                    # 运行WebSocket连接
                    loop.run_until_complete(self._websocket_handler(url))
                    break  # 如果连接成功，跳出循环
                except Exception as e:
                    self.logger.error(f"连接到 {url} 失败: {e}")
                    if i == len(self.url_variants) - 1:  # 最后一个URL也失败了
                        self.error_occurred.emit(f"所有连接尝试都失败了")
                    continue
            
        except Exception as e:
            self.logger.error(f"连接线程错误: {e}")
            self.error_occurred.emit(f"连接失败: {e}")
        finally:
            self.is_connected_flag = False
            self.is_running = False
            
    async def _websocket_handler(self, url: str):
        """WebSocket连接处理器"""
        try:
            self.logger.info(f"正在连接到: {url}")
            
            # 连接到WebSocket服务器 - 禁用心跳检测和超时
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    url,
                    ping_interval=None,  # 禁用ping心跳
                    ping_timeout=None,   # 禁用ping超时
                    close_timeout=None,  # 禁用关闭超时
                    max_size=None,       # 禁用消息大小限制
                    max_queue=None       # 禁用队列大小限制
                ), 
                timeout=10.0  # 只保留连接建立超时
            )
            
            self.is_connected_flag = True
            self.logger.info(f"成功连接到设备: {url} (心跳检测已禁用)")
            self.connected.emit()
            
            # 开始接收数据
            await self._receive_messages()
            
        except asyncio.TimeoutError:
            error_msg = f"连接超时: {url}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"连接错误: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
            
        finally:
            self.is_connected_flag = False
            if self.is_running:  # 只有在预期运行时才发送断开信号
                self.disconnected.emit()
                
    async def _receive_messages(self):
        """接收WebSocket消息 - 优化以防止超时断开"""
        try:
            # 设置更宽松的接收循环，完全移除对closed属性的检查
            while self.is_running and self.websocket:
                try:
                    # 不设置超时，让recv()永久等待直到有消息或连接断开
                    message = await self.websocket.recv()
                    
                    if isinstance(message, bytes):
                        # 处理图像数据
                        self._process_image_data(message)
                    else:
                        # 处理文本消息
                        self._process_text_message(message)
                        
                except websockets.exceptions.ConnectionClosed:
                    self.logger.info("WebSocket连接已关闭")
                    break
                except Exception as e:
                    self.logger.error(f"接收消息时发生错误: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"接收消息主循环出错: {e}")
            self.error_occurred.emit(f"接收数据时出错: {e}")
            
    def _process_image_data(self, data: bytes):
        """处理图像数据"""
        try:
            # 检查数据长度
            if len(data) < 100:  # 太小的数据可能不是有效图像
                self.logger.warning(f"接收到的数据太小: {len(data)} bytes")
                return
                
            # 使用OpenCV解码图像
            nparr = np.frombuffer(data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is not None:
                # 更新当前图像
                self.current_image = image
                self.image_count += 1
                self.last_image_time = time.time()
                
                # 发送图像信号
                self.image_received.emit(image)
                
                # 记录图像信息
                height, width = image.shape[:2]
                self.logger.debug(f"接收到图像: {width}x{height}, 总计: {self.image_count}")
                
            else:
                self.logger.warning("无法解码图像数据")
                
        except Exception as e:
            self.logger.error(f"处理图像数据时出错: {e}")
            
    def _process_text_message(self, message: str):
        """处理文本消息"""
        try:
            data = json.loads(message)
            self.logger.debug(f"收到文本消息: {data}")
            
            # 处理状态信息
            if 'status' in data:
                status = data['status']
                self.status_updated.emit(status)
                
            # 处理其他信息（电池、亮度等）
            info_parts = []
            if 'battery' in data:
                battery = data['battery']
                info_parts.append(f"电池: {battery}%")
                
            if 'brightness' in data:
                brightness = data['brightness']
                info_parts.append(f"亮度: {brightness}")
                
            if info_parts:
                info = " | ".join(info_parts)
                self.status_updated.emit(info)
                
        except json.JSONDecodeError:
            self.logger.warning(f"无法解析JSON消息: {message}")
        except Exception as e:
            self.logger.error(f"处理文本消息时出错: {e}")
            
    def check_connection_status(self):
        """检查连接状态 - 完全禁用连接状态检查，避免访问可能不存在的属性"""
        if not self.is_running:
            return
            
        current_time = time.time()
        
        # 只检查图像接收超时，不检查WebSocket连接状态
        if self.last_image_time > 0 and (current_time - self.last_image_time) > 60.0:
            self.logger.warning("长时间未收到图像数据")
            self.status_updated.emit("警告: 长时间未收到图像数据")
            
        # 完全移除WebSocket连接状态检查，避免属性访问错误
            
    def get_connection_info(self) -> dict:
        """获取连接信息"""
        return {
            "url": self.url,
            "connected": self.is_connected_flag,
            "running": self.is_running,
            "image_count": self.image_count,
            "last_image_time": self.last_image_time,
            "has_current_image": self.current_image is not None
        }
        
    def send_command(self, command: dict):
        """发送命令到设备"""
        if not self.is_connected_flag or not self.websocket:
            self.logger.warning("设备未连接，无法发送命令")
            return False
            
        try:
            # 在新任务中发送命令
            asyncio.create_task(self._send_command_async(command))
            return True
        except Exception as e:
            self.logger.error(f"发送命令时出错: {e}")
            return False
            
    async def _send_command_async(self, command: dict):
        """异步发送命令"""
        try:
            message = json.dumps(command)
            await self.websocket.send(message)
            self.logger.debug(f"发送命令: {command}")
        except Exception as e:
            self.logger.error(f"异步发送命令时出错: {e}")
