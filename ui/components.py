"""
自定义UI组件模块
包含现代化按钮、ROI选择器等组件
"""
from PyQt5.QtWidgets import QPushButton, QLabel, QDialogButtonBox, QDialog, QVBoxLayout, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor
from typing import Optional, Tuple


class ModernButton(QPushButton):
    """现代化按钮组件"""
    
    def __init__(self, text="", button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setup_style()
        
    def setup_style(self):
        """设置按钮样式"""
        styles = {
            "primary": {
                "bg": "#28a745",
                "hover": "#218838",
                "text": "white"
            },
            "danger": {
                "bg": "#dc3545", 
                "hover": "#c82333",
                "text": "white"
            },
            "secondary": {
                "bg": "#6c757d",
                "hover": "#5a6268", 
                "text": "white"
            },
            "info": {
                "bg": "#17a2b8",
                "hover": "#138496",
                "text": "white"
            },
            "warning": {
                "bg": "#ffc107",
                "hover": "#e0a800",
                "text": "#212529"
            }
        }
        
        style = styles.get(self.button_type, styles["primary"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {style["bg"]};
                color: {style["text"]};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: 600;
                min-height: 20px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {style["hover"]};
            }}
            QPushButton:pressed {{
                background-color: {style["hover"]};
            }}
            QPushButton:disabled {{
                background-color: #e9ecef;
                color: #6c757d;
            }}
        """)


class ROISelector(QLabel):
    """ROI选择器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = None
        self.end_point = None
        self.roi_rect = None
        self.is_selecting = False
        self.setMinimumSize(400, 300)
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.is_selecting = True
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting and self.start_point:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self.is_selecting = False
            
            # 计算ROI矩形
            if self.start_point and self.end_point:
                x1, y1 = self.start_point.x(), self.start_point.y()
                x2, y2 = self.end_point.x(), self.end_point.y()
                
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                
                if w > 10 and h > 10:  # 最小ROI尺寸
                    self.roi_rect = (x, y, w, h)
            
            self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        
        # 绘制ROI选择框
        if self.is_selecting and self.start_point and self.end_point:
            pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(pen)
            
            x1, y1 = self.start_point.x(), self.start_point.y()
            x2, y2 = self.end_point.x(), self.end_point.y()
            
            rect = QRect(min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))
            painter.drawRect(rect)
        
        # 绘制已确认的ROI
        elif self.roi_rect:
            pen = QPen(Qt.green, 3, Qt.SolidLine)
            painter.setPen(pen)
            
            x, y, w, h = self.roi_rect
            rect = QRect(x, y, w, h)
            painter.drawRect(rect)
            
            # 添加ROI信息文字
            painter.setPen(QPen(Qt.green, 1))
            painter.drawText(x, y-5, f"ROI: {w}×{h}")
    
    def get_roi_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """获取ROI矩形"""
        return self.roi_rect
    
    def clear_roi(self):
        """清除ROI选择"""
        self.roi_rect = None
        self.start_point = None
        self.end_point = None
        self.update()


class UserInfoDialog(QDialog):
    """用户信息设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 用户信息设置")
        self.setFixedSize(450, 280)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setup_ui()
        
    def setup_ui(self):
        """设置对话框界面"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("🎯 首次使用需要设置用户信息")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #495057;
                margin: 15px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        layout.addWidget(title)
        
        # 用户名输入
        username_label = QLabel("👤 用户名:")
        username_label.setStyleSheet("QLabel { font-size: 11pt; font-weight: 600; color: #495057; }")
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入您的用户名")
        self.username_input.setStyleSheet(self.get_input_style())
        layout.addWidget(self.username_input)
        
        # 邮箱输入
        email_label = QLabel("📧 邮箱:")
        email_label.setStyleSheet("QLabel { font-size: 11pt; font-weight: 600; color: #495057; }")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入您的邮箱地址")
        self.email_input.setStyleSheet(self.get_input_style())
        layout.addWidget(self.email_input)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                font-size: 11pt;
                font-weight: 600;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton[text="OK"] {
                background-color: #28a745;
                color: white;
                border: none;
            }
            QPushButton[text="OK"]:hover {
                background-color: #218838;
            }
            QPushButton[text="Cancel"] {
                background-color: #6c757d;
                color: white;
                border: none;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def get_input_style(self):
        """获取输入框样式"""
        return """
            QLineEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 12px 15px;
                font-size: 11pt;
                background-color: white;
                color: #495057;
            }
            QLineEdit:focus {
                border-color: #007bff;
                background-color: #f8f9ff;
            }
        """
    
    def get_user_info(self) -> dict:
        """获取用户信息"""
        return {
            'username': self.username_input.text().strip(),
            'email': self.email_input.text().strip()
        }
    
    def accept(self):
        """确认按钮处理"""
        user_info = self.get_user_info()
        if not user_info['username']:
            QMessageBox.warning(self, "⚠️ 提示", "请输入用户名！")
            return
        if not user_info['email']:
            QMessageBox.warning(self, "⚠️ 提示", "请输入邮箱地址！")
            return
        super().accept()
