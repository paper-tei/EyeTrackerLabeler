from typing import List, Optional
from PyQt5.QtCore import QPointF

class OneLabel:
    """单个标签管理类"""
    
    def __init__(self, num_points: int = 7):
        self.num_points = num_points
        self.label_points: List[QPointF] = []
        self.has_points = False
    
    def set_point(self, point: QPointF) -> bool:
        """设置点"""
        if len(self.label_points) >= self.num_points:
            return False
        self.label_points.append(point)
        if len(self.label_points) == self.num_points:
            self.has_points = True
        return True
    
    def set_point_flexible(self, point: QPointF):
        """灵活设置点（可变数量）"""
        self.label_points.append(point)
        self.num_points = len(self.label_points)
        self.has_points = True
    
    def get_num(self) -> int:
        return self.num_points
    
    def size(self) -> int:
        return len(self.label_points)
    
    def success(self) -> bool:
        """检查标签是否完成（7个点都已设置）"""
        return self.has_points and len(self.label_points) == 7
    
    def reset(self):
        """重置标签"""
        self.label_points.clear()
        self.has_points = False
    
    def empty(self) -> bool:
        return len(self.label_points) == 0
    
    def erase_last(self) -> bool:
        """删除最后一个点"""
        if not self.label_points:
            return False
        self.label_points.pop()
        if len(self.label_points) < self.num_points:
            self.has_points = False
        return True
    
    def get_hexagon_points(self) -> List[QPointF]:
        """获取六边形的6个点"""
        if len(self.label_points) >= 6:
            return self.label_points[:6]
        return self.label_points
    
    def get_free_point(self) -> Optional[QPointF]:
        """获取游离点（第7个点）"""
        if len(self.label_points) >= 7:
            return self.label_points[6]
        return None
    
    def __getitem__(self, index: int) -> QPointF:
        return self.label_points[index]
    
    def __setitem__(self, index: int, value: QPointF):
        self.label_points[index] = value