from PyQt5.QtGui import QPainter, QPen, QFont, QImage, QPolygonF
from PyQt5.QtCore import Qt, QPointF
from typing import Optional, List
from .txt_manager import AllLabel
from .label_manager import OneLabel

class Painter:
    """绘制器类"""
    
    def __init__(self):
        self.painter_label: Optional[QPainter] = None
        self.pen_point = QPen(Qt.green, 4)
        self.pen_hexagon = QPen(Qt.red, 2)
        self.pen_free_point = QPen(Qt.blue, 4)
        self.pen_focus = QPen(Qt.yellow, 3)
        self.pen_text = QPen(Qt.white, 1)
        self.font = QFont("Arial", 10, QFont.Bold)
    
    def reset_painter(self, img: QImage):
        """重置画笔"""
        if self.painter_label:
            self.painter_label.end()
        self.painter_label = QPainter(img)
        self.painter_label.setRenderHint(QPainter.Antialiasing)
    
    def draw_point(self, point: QPointF, pen: QPen, radius: int = 3):
        """绘制点"""
        if self.painter_label:
            self.painter_label.setPen(pen)
            self.painter_label.drawEllipse(point, radius, radius)
    
    def draw_hexagon(self, points: List[QPointF]):
        """绘制六边形"""
        if self.painter_label and len(points) >= 6:
            self.painter_label.setPen(self.pen_hexagon)
            
            # 创建六边形多边形
            polygon = QPolygonF(points[:6])
            self.painter_label.drawPolygon(polygon)
    
    def draw_text(self, point: QPointF, text: str):
        """绘制文本"""
        if self.painter_label:
            self.painter_label.setFont(self.font)
            self.painter_label.setPen(self.pen_text)
            # 添加文本背景
            text_rect = self.painter_label.fontMetrics().boundingRect(text)
            text_rect.moveCenter(point.toPoint())
            text_rect.translate(0, -15)  # 向上偏移
            self.painter_label.fillRect(text_rect, Qt.black)
            self.painter_label.drawText(text_rect, Qt.AlignCenter, text)
    
    def draw_point_numbers(self, points: List[QPointF]):
        """绘制点的编号"""
        if self.painter_label:
            self.painter_label.setPen(self.pen_text)
            for i, point in enumerate(points):
                if i < 6:
                    # 六边形顶点编号
                    self.painter_label.drawText(point + QPointF(5, -5), str(i + 1))
                else:
                    # 游离点标记
                    self.painter_label.drawText(point + QPointF(5, -5), "F")
    
    def draw_label(self, label: OneLabel, label_index: int):
        """绘制单个标签"""
        if not label.label_points:
            return
        
        # 绘制六边形的前6个点
        hexagon_points = label.get_hexagon_points()
        
        # 绘制六边形顶点
        for point in hexagon_points:
            self.draw_point(point, self.pen_point)
        
        # 如果有足够的点，绘制六边形
        if len(hexagon_points) >= 6:
            self.draw_hexagon(hexagon_points)
        
        # 绘制游离点
        free_point = label.get_free_point()
        if free_point:
            self.draw_point(free_point, self.pen_free_point, 5)
        
        # 绘制标签信息
        if hexagon_points:
            self.draw_text(hexagon_points[0], f"Label {label_index + 1}")
        
        # 绘制点编号
        self.draw_point_numbers(label.label_points)
    
    def draw(self, all_label: AllLabel) -> bool:
        """绘制所有标签"""
        if not self.painter_label:
            return False
        
        success = False
        
        # 绘制已完成的标签
        for i, label in enumerate(all_label.labels_in_pic):
            self.draw_label(label, i)
            success = True
        
        # 绘制当前正在编辑的标签
        if not all_label.label_now.empty():
            current_points = all_label.label_now.label_points
            
            # 绘制已设置的点
            for i, point in enumerate(current_points):
                if i < 6:
                    self.draw_point(point, self.pen_point)
                else:
                    self.draw_point(point, self.pen_free_point, 5)
            
            # 如果有足够的点，绘制部分六边形
            if len(current_points) >= 2:
                self.painter_label.setPen(self.pen_hexagon)
                for i in range(min(6, len(current_points))):
                    next_i = (i + 1) % 6
                    if next_i < len(current_points):
                        self.painter_label.drawLine(current_points[i], current_points[next_i])
                    elif i == len(current_points) - 1 and len(current_points) == 6:
                        # 闭合六边形
                        self.painter_label.drawLine(current_points[i], current_points[0])
            
            # 绘制点编号
            self.draw_point_numbers(current_points)
            
            success = True
        
        return success
    
    def draw_focus(self, label: OneLabel) -> bool:
        """绘制焦点标签"""
        if not self.painter_label:
            return False
        
        # 绘制焦点六边形
        hexagon_points = label.get_hexagon_points()
        if len(hexagon_points) >= 6:
            self.painter_label.setPen(self.pen_focus)
            polygon = QPolygonF(hexagon_points)
            self.painter_label.drawPolygon(polygon)
        
        # 绘制焦点游离点
        free_point = label.get_free_point()
        if free_point:
            self.painter_label.setPen(self.pen_focus)
            self.painter_label.drawEllipse(free_point, 8, 8)
        
        # 绘制焦点标记
        for i, point in enumerate(label.label_points):
            self.painter_label.setPen(self.pen_focus)
            if i < 6:
                self.painter_label.drawText(point + QPointF(10, -10), f"H{i + 1}")
            else:
                self.painter_label.drawText(point + QPointF(10, -10), "FREE")
        
        return True