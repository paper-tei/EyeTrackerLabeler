"""
数据管理模块
负责录制数据的保存、打包和管理
"""
import os
import json
import zipfile
import shutil
import cv2
import numpy as np
from datetime import datetime
from typing import Optional
import logging


class RecordingSession:
    """录制会话管理类"""
    
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
        self.session_folder = None
        self.start_time = None
        self.image_count = 0
        self.logger = logging.getLogger(__name__)
        
        self._create_session_folder()
    
    def _create_session_folder(self):
        """创建录制会话文件夹"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{self.username}_{timestamp}"
        
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.session_folder = os.path.join(root_dir, folder_name)
        
        try:
            os.makedirs(self.session_folder, exist_ok=True)
            self.logger.info(f"录制目录创建成功: {self.session_folder}")
        except Exception as e:
            self.logger.error(f"创建录制目录失败: {e}")
            raise
    
    def start_session(self):
        """开始录制会话"""
        self.start_time = datetime.now()
        self.image_count = 0
        self.logger.info("录制会话开始")
    
    def save_image(self, image: np.ndarray, suffix: str = "") -> bool:
        """保存图像"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"img_{timestamp}_{self.image_count:06d}{suffix}_240x240.jpg"
            filepath = os.path.join(self.session_folder, filename)
            
            # 保存为JPG格式，高质量
            success = cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if success:
                self.image_count += 1
                return True
            else:
                self.logger.error(f"保存图像失败: {filepath}")
                return False
                
        except Exception as e:
            self.logger.error(f"保存图像异常: {e}")
            return False
    
    def create_package(self) -> Optional[str]:
        """创建录制数据包"""
        if self.image_count == 0:
            return None
        
        try:
            # 计算录制时长
            duration_minutes = 0
            if self.start_time:
                duration = datetime.now() - self.start_time
                duration_minutes = int(duration.total_seconds() / 60)
            
            # 生成压缩包名称
            duration_str = f"{duration_minutes}min" if duration_minutes > 0 else "unknown"
            zip_filename = f"{self.username}_{self.image_count}pics_{duration_str}.zip"
            zip_path = os.path.join(os.path.dirname(self.session_folder), zip_filename)
            
            # 创建压缩包
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                # 添加所有图片文件
                for root, dirs, files in os.walk(self.session_folder):
                    for file in files:
                        if file.lower().endswith('.jpg'):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.session_folder)
                            zipf.write(file_path, arcname)
                
                # 添加录制信息文件
                session_info = {
                    "username": self.username,
                    "email": self.email,
                    "recording_time": self.start_time.isoformat() if self.start_time else None,
                    "image_count": self.image_count,
                    "image_format": "jpg",
                    "capture_interval_ms": 100,
                    "duration_minutes": duration_minutes,
                    "target_size": "240x240"
                }
                
                info_json = json.dumps(session_info, indent=2, ensure_ascii=False)
                zipf.writestr("recording_info.json", info_json)
            
            # 删除原始文件夹
            shutil.rmtree(self.session_folder)
            
            self.logger.info(f"录制包创建成功: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"创建录制包失败: {e}")
            return None
    
    def get_session_info(self) -> dict:
        """获取会话信息"""
        duration_str = "00:00:00"
        if self.start_time:
            duration = datetime.now() - self.start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        return {
            "image_count": self.image_count,
            "duration": duration_str,
            "folder": self.session_folder
        }
