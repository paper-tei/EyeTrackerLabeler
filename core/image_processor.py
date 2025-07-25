"""
图像处理模块
负责图像的旋转、ROI提取、缩放等处理功能
"""
import cv2
import numpy as np
from typing import Optional, Tuple


class ImageProcessor:
    """图像处理器类"""
    
    def __init__(self):
        self.rotation_angle = 0
        self.roi_enabled = False
        self.roi_coords = None  # (x, y, w, h)
        self.target_size = (240, 240)
    
    def set_rotation_angle(self, angle: int):
        """设置旋转角度"""
        self.rotation_angle = angle
    
    def set_roi(self, x: int, y: int, w: int, h: int):
        """设置ROI区域"""
        self.roi_coords = (x, y, w, h)
        self.roi_enabled = True
    
    def clear_roi(self):
        """清除ROI设置"""
        self.roi_coords = None
        self.roi_enabled = False
    
    def rotate_image(self, image: np.ndarray, angle: int) -> np.ndarray:
        """旋转图像"""
        if angle == 0:
            return image
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # 计算旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 计算旋转后的图像尺寸
        cos_val = abs(rotation_matrix[0, 0])
        sin_val = abs(rotation_matrix[0, 1])
        new_width = int((height * sin_val) + (width * cos_val))
        new_height = int((height * cos_val) + (width * sin_val))
        
        # 调整旋转矩阵的平移部分
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # 执行旋转
        rotated_image = cv2.warpAffine(image, rotation_matrix, (new_width, new_height))
        return rotated_image
    
    def extract_roi(self, image: np.ndarray, roi_rect: Tuple[int, int, int, int]) -> np.ndarray:
        """提取ROI区域"""
        if roi_rect is None:
            return image
        
        x, y, w, h = roi_rect
        height, width = image.shape[:2]
        
        # 确保ROI坐标在图像范围内
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        
        return image[y:y+h, x:x+w]
    
    def resize_image(self, image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """调整图像尺寸"""
        return cv2.resize(image, size, interpolation=cv2.INTER_LANCZOS4)
    
    def process_image(self, image: np.ndarray) -> np.ndarray:
        """完整的图像处理流程"""
        processed_image = image.copy()
        
        # 1. 应用旋转
        if self.rotation_angle != 0:
            processed_image = self.rotate_image(processed_image, self.rotation_angle)
        
        # 2. 提取ROI区域
        if self.roi_enabled and self.roi_coords:
            processed_image = self.extract_roi(processed_image, self.roi_coords)
        
        # 3. 调整到目标尺寸
        processed_image = self.resize_image(processed_image, self.target_size)
        
        return processed_image
    
    def get_process_suffix(self) -> str:
        """获取处理参数的后缀字符串"""
        suffix_parts = []
        if self.rotation_angle != 0:
            suffix_parts.append(f"rot{self.rotation_angle}")
        if self.roi_enabled and self.roi_coords:
            suffix_parts.append("roi")
        return "_" + "_".join(suffix_parts) if suffix_parts else ""
    
    def convert_roi_coordinates(self, preview_roi: Tuple[int, int, int, int], 
                             preview_size: Tuple[int, int], 
                             actual_size: Tuple[int, int],
                             offset: Tuple[int, int] = (0, 0)) -> Tuple[int, int, int, int]:
        """
        转换ROI坐标从预览尺寸到实际图像尺寸
        
        Args:
            preview_roi: 预览图像中的ROI坐标 (x, y, w, h)
            preview_size: 预览图像显示尺寸 (width, height)
            actual_size: 实际图像尺寸 (width, height)
            offset: 预览图像在控件中的偏移 (offset_x, offset_y)
        
        Returns:
            实际图像中的ROI坐标 (x, y, w, h)
        """
        x, y, w, h = preview_roi
        preview_w, preview_h = preview_size
        actual_w, actual_h = actual_size
        offset_x, offset_y = offset
        
        # 调整坐标（减去偏移）
        adjusted_x = x - offset_x
        adjusted_y = y - offset_y
        
        # 确保调整后的坐标在有效范围内
        if adjusted_x < 0 or adjusted_y < 0 or adjusted_x + w > preview_w or adjusted_y + h > preview_h:
            return None
        
        # 计算缩放比例
        scale_x = actual_w / preview_w
        scale_y = actual_h / preview_h
        
        # 转换到实际图像坐标系
        real_x = int(adjusted_x * scale_x)
        real_y = int(adjusted_y * scale_y)
        real_w = int(w * scale_x)
        real_h = int(h * scale_y)
        
        # 边界检查
        real_x = max(0, min(real_x, actual_w - 1))
        real_y = max(0, min(real_y, actual_h - 1))
        real_w = max(1, min(real_w, actual_w - real_x))
        real_h = max(1, min(real_h, actual_h - real_y))
        
        return (real_x, real_y, real_w, real_h)
