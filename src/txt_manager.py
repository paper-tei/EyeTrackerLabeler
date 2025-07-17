import os
from typing import List, Optional
from PyQt5.QtCore import QPointF
from .label_manager import OneLabel

class AllLabel:
    """所有标签管理类"""
    
    def __init__(self, num_points: int = 7):
        self.num_points = 7  # 固定为7个点
        self.label_now = OneLabel(7)
        self.labels_in_pic: List[OneLabel] = []
        self.image_width = 0
        self.image_height = 0
        self.folder_path = ""
        self.image_name = ""
    
    def set_point(self, point: QPointF) -> bool:
        """设置点"""
        return self.label_now.set_point(point)
    
    def complete_current_label(self) -> bool:
        """完成当前标签"""
        if self.label_now.success():
            self.labels_in_pic.append(self.label_now)
            self.label_now = OneLabel(7)
            return True
        return False
    
    def get_num(self) -> int:
        return self.num_points
    
    def reset(self):
        """重置所有标签"""
        self.labels_in_pic.clear()
        self.label_now.reset()
    
    def set_num(self, num: int):
        """设置点数（固定为7，此方法保持兼容性）"""
        self.num_points = 7
        self.label_now = OneLabel(7)
    
    def set_pic_size(self, height: int, width: int):
        """设置图片尺寸"""
        self.image_height = height
        self.image_width = width
    
    def set_label_path(self, folder_path: str):
        """设置标签文件夹路径"""
        self.folder_path = os.path.join(folder_path, "labels")
        return True
    
    def empty(self) -> bool:
        return len(self.labels_in_pic) == 0
    
    def erase_last(self):
        """删除最后一个元素"""
        if self.label_now.erase_last():
            return
        elif self.labels_in_pic:
            self.labels_in_pic.pop()
    
    def erase_focus(self, index: int):
        """删除指定索引的标签"""
        if 0 <= index < len(self.labels_in_pic):
            self.labels_in_pic.pop(index)
    
    def set_image_name(self, name: str):
        """设置图片名称并读取对应的txt文件"""
        self.image_name = name
        if self.folder_path:
            txt_path = os.path.join(self.folder_path, f"{name}.txt")
            if os.path.exists(txt_path):
                self.read_data_from_txt(txt_path)
    
    def read_data_from_txt(self, path: str):
        """从txt文件读取标注数据"""
        self.labels_in_pic.clear()
        
        try:
            with open(path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 14:  # 7个点 × 2个坐标 = 14个数值
                        continue
                    
                    label = OneLabel(7)
                    
                    # 读取7个点的坐标
                    for i in range(7):
                        x = float(parts[i * 2]) * self.image_width
                        y = float(parts[i * 2 + 1]) * self.image_height
                        label.set_point(QPointF(x, y))
                    
                    self.labels_in_pic.append(label)
        except Exception as e:
            print(f"Error reading txt file {path}: {e}")
    
    def save_as_txt(self):
        """保存为txt文件"""
        if not self.folder_path or not self.image_name:
            print("Error: path not set")
            return
        
        # 确保labels文件夹存在
        os.makedirs(self.folder_path, exist_ok=True)
        
        file_path = os.path.join(self.folder_path, f"{self.image_name}.txt")
        
        try:
            if not self.empty():
                with open(file_path, 'w') as f:
                    for label in self.labels_in_pic:
                        if len(label.label_points) == 7:  # 确保有7个点
                            coord_strings = []
                            for point in label.label_points:
                                x_norm = point.x() / self.image_width
                                y_norm = point.y() / self.image_height
                                coord_strings.append(f"{x_norm:.6f}")
                                coord_strings.append(f"{y_norm:.6f}")
                            f.write(" ".join(coord_strings) + "\n")
            else:
                # 如果没有标签，删除文件（如果存在）
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error saving txt file: {e}")
    
    def get_label_info(self, index: int) -> str:
        """获取标签信息字符串"""
        if 0 <= index < len(self.labels_in_pic):
            return f"Label {index + 1}"
        return "Unknown"