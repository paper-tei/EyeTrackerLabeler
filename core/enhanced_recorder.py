"""
增强版录制器模块
包含图像旋转、ROI选择等高级功能
"""
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from core.base_recorder import BaseRecorder
from ui.components import ROISelector


class EnhancedRecorder(BaseRecorder):
    """增强版录制器，包含旋转和ROI功能"""
    
    def __init__(self):
        super().__init__()
        self.setup_enhanced_features()
    
    def setup_enhanced_features(self):
        """设置增强功能"""
        # 连接增强功能的信号
        if hasattr(self, 'rotation_slider'):
            self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        if hasattr(self, 'angle_spinbox'):
            self.angle_spinbox.valueChanged.connect(self.on_angle_spinbox_changed)
        if hasattr(self, 'roi_checkbox'):
            self.roi_checkbox.stateChanged.connect(self.on_roi_enabled_changed)
        if hasattr(self, 'roi_select_btn'):
            self.roi_select_btn.clicked.connect(self.enable_roi_selection)
        if hasattr(self, 'roi_clear_btn'):
            self.roi_clear_btn.clicked.connect(self.clear_roi_selection)
    
    def setup_ui(self):
        """设置增强版用户界面"""
        self.setWindowTitle("📷 PaperTracker 图像录制工具 (增强版)")
        self.setGeometry(100, 100, 1600, 1000)
        
        from core.config import config
        self.setMinimumSize(*config.window_min_size)
        
        # 设置应用程序样式
        from ui.styles import get_main_stylesheet
        self.setStyleSheet(get_main_stylesheet())
        
        # 创建中央部件
        from PyQt5.QtWidgets import QWidget, QHBoxLayout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # 左侧控制面板 - 增强版
        from PyQt5.QtWidgets import QScrollArea
        from ui.styles import get_scrollarea_stylesheet
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(420)  # 增强版稍微宽一点
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setStyleSheet(get_scrollarea_stylesheet())
        
        left_panel = self.panel_manager.create_control_panel(enhanced=True)
        left_scroll.setWidget(left_panel)
        main_layout.addWidget(left_scroll)
        
        # 右侧预览面板 - 增强版
        right_panel = self.panel_manager.create_preview_panel(enhanced=True)
        main_layout.addWidget(right_panel)
        
        # 设置比例
        main_layout.setStretch(0, 0)  # 控制面板固定
        main_layout.setStretch(1, 1)  # 预览面板可伸缩
        
        # 创建状态栏
        self.create_status_bar()
    
    def setup_connections(self):
        """设置信号连接"""
        super().setup_connections()
        self.setup_enhanced_features()
    
    def set_rotation_angle(self, angle):
        """设置旋转角度"""
        self.image_processor.set_rotation_angle(angle)
        if hasattr(self, 'rotation_slider'):
            self.rotation_slider.setValue(angle)
        if hasattr(self, 'angle_spinbox'):
            self.angle_spinbox.setValue(angle)
    
    def on_rotation_changed(self, value):
        """旋转滑块变化"""
        self.image_processor.set_rotation_angle(value)
        if hasattr(self, 'angle_spinbox'):
            self.angle_spinbox.setValue(value)
    
    def on_angle_spinbox_changed(self, value):
        """角度输入框变化"""
        self.image_processor.set_rotation_angle(value)
        if hasattr(self, 'rotation_slider'):
            self.rotation_slider.setValue(value)
    
    def on_roi_enabled_changed(self, state):
        """ROI开关状态变化"""
        roi_enabled = bool(state)
        
        if roi_enabled:
            self.image_processor.roi_enabled = True
        else:
            self.image_processor.clear_roi()
        
        if hasattr(self, 'roi_select_btn'):
            self.roi_select_btn.setEnabled(roi_enabled)
        if hasattr(self, 'roi_clear_btn'):
            self.roi_clear_btn.setEnabled(roi_enabled)
        
        if not roi_enabled:
            self.clear_roi_selection()
    
    def enable_roi_selection(self):
        """启用ROI选择模式"""
        if hasattr(self.preview_label, 'clear_roi'):
            self.preview_label.clear_roi()
        self.statusBar().showMessage("🎯 请在预览区域拖拽选择ROI区域")
    
    def clear_roi_selection(self):
        """清除ROI选择"""
        self.image_processor.clear_roi()
        if hasattr(self.preview_label, 'clear_roi'):
            self.preview_label.clear_roi()
        if hasattr(self, 'roi_info_label'):
            self.roi_info_label.setText("未选择ROI区域")
        self.statusBar().showMessage("🗑️ ROI区域已清除")
    
    def update_preview(self):
        """更新增强版预览显示"""
        if self.current_image is not None:
            try:
                # 处理图像用于预览
                preview_image = self.current_image.copy()
                
                # 应用旋转（仅用于预览）
                if self.image_processor.rotation_angle != 0:
                    preview_image = self.image_processor.rotate_image(
                        preview_image, self.image_processor.rotation_angle
                    )
                
                # 转换为Qt格式并显示
                height, width, channel = preview_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(preview_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                
                # 缩放以适应预览区域
                preview_size = self.preview_label.size()
                scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                    preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                
                # 更新ROI信息
                if hasattr(self.preview_label, 'get_roi_rect'):
                    roi_rect = self.preview_label.get_roi_rect()
                    if roi_rect and hasattr(self, 'roi_info_label'):
                        x, y, w, h = roi_rect
                        self.roi_info_label.setText(f"ROI: {w}×{h} (起点: {x},{y})")
                        
                        # 转换ROI坐标到实际图像坐标系
                        preview_pixmap = self.preview_label.pixmap()
                        if preview_pixmap:
                            displayed_w = preview_pixmap.width()
                            displayed_h = preview_pixmap.height()
                            label_w = self.preview_label.width()
                            label_h = self.preview_label.height()
                            
                            offset_x = (label_w - displayed_w) // 2
                            offset_y = (label_h - displayed_h) // 2
                            
                            real_roi = self.image_processor.convert_roi_coordinates(
                                roi_rect,
                                (displayed_w, displayed_h),
                                (width, height),
                                (offset_x, offset_y)
                            )
                            
                            if real_roi:
                                self.image_processor.set_roi(*real_roi)
                
            except Exception as e:
                self.logger.error(f"更新预览失败: {e}")
    
    def process_image_for_saving(self, image):
        """处理图像用于保存（应用所有增强功能）"""
        return self.image_processor.process_image(image)
