"""
UI面板模块
包含各种UI面板的创建和管理
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QGroupBox, QGridLayout, QCheckBox, QScrollArea, QTabWidget,
    QSlider, QSpinBox, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from .components import ModernButton, ROISelector
from .styles import (
    get_main_stylesheet, get_tab_widget_stylesheet, get_scrollarea_stylesheet,
    get_slider_stylesheet, get_spinbox_stylesheet, get_status_label_styles,
    get_button_styles
)


class ControlPanelManager:
    """控制面板管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.status_styles = get_status_label_styles()
        self.button_styles = get_button_styles()
    
    def create_control_panel(self, enhanced: bool = False) -> QWidget:
        """创建控制面板"""
        if enhanced:
            return self._create_enhanced_control_panel()
        else:
            return self._create_simple_control_panel()
    
    def _create_simple_control_panel(self) -> QWidget:
        """创建简单控制面板"""
        panel = QWidget()
        panel.setMinimumWidth(380)
        panel.setStyleSheet("QWidget { background-color: transparent; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # 应用标题
        title_group = self._create_title_section()
        layout.addWidget(title_group)
        
        # 设备连接组
        connection_group = self._create_connection_group()
        layout.addWidget(connection_group)
        
        # 录制控制组
        control_group = self._create_simple_control_group()
        layout.addWidget(control_group)
        
        # 录制状态
        status_group = self._create_status_group()
        layout.addWidget(status_group)
        
        # 自动保存状态
        auto_save_group = self._create_auto_save_group()
        layout.addWidget(auto_save_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def _create_enhanced_control_panel(self) -> QWidget:
        """创建增强版控制面板"""
        panel = QWidget()
        panel.setMinimumWidth(420)
        panel.setStyleSheet("QWidget { background-color: transparent; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # 应用标题
        title_group = self._create_title_section()
        layout.addWidget(title_group)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(get_tab_widget_stylesheet())
        
        # 连接设置选项卡
        connection_tab = QWidget()
        connection_layout = QVBoxLayout(connection_tab)
        connection_layout.addWidget(self._create_connection_group())
        connection_layout.addWidget(self._create_simple_control_group())
        connection_layout.addWidget(self._create_status_group())
        connection_layout.addStretch()
        
        # 图像处理选项卡
        processing_tab = QWidget()
        processing_layout = QVBoxLayout(processing_tab)
        processing_layout.addWidget(self._create_rotation_group())
        processing_layout.addWidget(self._create_roi_group())
        processing_layout.addStretch()
        
        # 保存设置选项卡
        save_tab = QWidget()
        save_layout = QVBoxLayout(save_tab)
        save_layout.addWidget(self._create_auto_save_group())
        save_layout.addStretch()
        
        tab_widget.addTab(connection_tab, "🔗 连接")
        tab_widget.addTab(processing_tab, "🔧 图像处理")
        tab_widget.addTab(save_tab, "💾 保存")
        
        layout.addWidget(tab_widget)
        layout.addStretch()
        
        return panel
    
    def _create_title_section(self) -> QGroupBox:
        """创建标题区域"""
        group = QGroupBox("📊 PaperTracker 数据采集系统")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 欢迎信息
        user_info = self.parent.user_info
        welcome_label = QLabel(f"👋 欢迎，{user_info['username']}")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 13pt;
                font-weight: 600;
                color: #007bff;
                margin: 8px;
                padding: 5px;
            }
        """)
        layout.addWidget(welcome_label)
        
        # 说明文字
        desc_label = QLabel("📋 专业的实验数据采集与记录工具")
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                margin: 2px 8px;
                padding: 3px;
            }
        """)
        layout.addWidget(desc_label)
        
        group.setLayout(layout)
        return group
    
    def _create_connection_group(self) -> QGroupBox:
        """创建连接设置组"""
        group = QGroupBox("🔗 设备连接")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # 设备地址输入
        addr_layout = QVBoxLayout()
        addr_label = QLabel("📱 设备地址:")
        addr_label.setStyleSheet("QLabel { font-weight: 600; font-size: 11pt; }")
        addr_layout.addWidget(addr_label)
        
        # 输入框容器
        input_container = QHBoxLayout()
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setSpacing(0)
        
        prefix_label = QLabel("ws://")
        prefix_label.setStyleSheet("""
            QLabel { 
                color: #6c757d; 
                font-weight: 600; 
                font-size: 10pt;
                padding: 10px 8px;
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-right: none;
                border-radius: 6px 0 0 6px;
                min-width: 40px;
            }
        """)
        
        self.parent.device_input = QLineEdit()
        self.parent.device_input.setPlaceholderText("192.168.1.100:8080")
        self.parent.device_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e9ecef;
                border-left: none;
                border-radius: 0 6px 6px 0;
                padding: 10px 15px;
                font-size: 11pt;
                background-color: white;
                color: #495057;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #007bff;
                border-left-color: #007bff;
            }
        """)
        
        input_container.addWidget(prefix_label)
        input_container.addWidget(self.parent.device_input, 1)
        
        addr_layout.addLayout(input_container)
        layout.addLayout(addr_layout)
        
        # 连接按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.parent.connect_btn = ModernButton("🔌 连接", "primary")
        self.parent.disconnect_btn = ModernButton("🔌 断开", "danger")
        self.parent.disconnect_btn.setEnabled(False)
        
        # 调整按钮样式使其更紧凑
        for btn in [self.parent.connect_btn, self.parent.disconnect_btn]:
            btn.setStyleSheet(btn.styleSheet().replace("min-width: 140px", "min-width: 110px"))
            btn.setStyleSheet(btn.styleSheet().replace("padding: 12px 24px", "padding: 10px 20px"))
        
        button_layout.addWidget(self.parent.connect_btn)
        button_layout.addWidget(self.parent.disconnect_btn)
        layout.addLayout(button_layout)
        
        # 连接状态
        self.parent.connection_status = QLabel("❌ 未连接")
        self.parent.connection_status.setStyleSheet(self.status_styles["disconnected"])
        layout.addWidget(self.parent.connection_status)
        
        group.setLayout(layout)
        return group
    
    def _create_simple_control_group(self) -> QGroupBox:
        """创建简化的录制控制组"""
        group = QGroupBox("🎬 录制控制")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # 录制按钮
        self.parent.start_btn = ModernButton("▶️ 开始录制", "primary")
        self.parent.start_btn.setStyleSheet(self.button_styles["large_primary"])
        
        self.parent.stop_btn = ModernButton("⏹️ 停止录制", "danger")
        self.parent.stop_btn.setStyleSheet(self.button_styles["large_danger"])
        self.parent.stop_btn.setEnabled(False)
        
        layout.addWidget(self.parent.start_btn)
        layout.addWidget(self.parent.stop_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_status_group(self) -> QGroupBox:
        """创建状态显示组"""
        group = QGroupBox("📊 录制状态")
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # 录制状态
        status_label = QLabel("状态:")
        status_label.setMinimumWidth(50)
        status_label.setStyleSheet("QLabel { font-weight: 600; }")
        layout.addWidget(status_label, 0, 0)
        
        self.parent.recording_status = QLabel("⏸️ 待机中")
        self.parent.recording_status.setStyleSheet(self.status_styles["standby"])
        layout.addWidget(self.parent.recording_status, 0, 1)
        
        # 录制时长
        duration_label = QLabel("时长:")
        duration_label.setStyleSheet("QLabel { font-weight: 600; }")
        layout.addWidget(duration_label, 1, 0)
        
        self.parent.duration_label = QLabel("00:00:00")
        self.parent.duration_label.setStyleSheet(self.status_styles["duration"])
        layout.addWidget(self.parent.duration_label, 1, 1)
        
        # 图片数量
        count_label = QLabel("图片:")
        count_label.setStyleSheet("QLabel { font-weight: 600; }")
        layout.addWidget(count_label, 2, 0)
        
        self.parent.image_count_label = QLabel("0 张")
        self.parent.image_count_label.setStyleSheet(self.status_styles["count"])
        layout.addWidget(self.parent.image_count_label, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_auto_save_group(self) -> QGroupBox:
        """创建自动保存设置组"""
        group = QGroupBox("💾 保存设置")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 自动保存开关（默认开启）
        self.parent.auto_save_checkbox = QCheckBox("✅ 自动保存图片（推荐）")
        self.parent.auto_save_checkbox.setChecked(True)
        self.parent.auto_save_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: 600;
                color: #28a745;
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.parent.auto_save_checkbox)
        
        # 保存信息
        info_label = QLabel("📂 格式: JPG (高质量)\n⏱️ 间隔: 100ms\n📁 位置: 程序根目录")
        info_label.setStyleSheet(self.status_styles["info"])
        layout.addWidget(info_label)
        
        group.setLayout(layout)
        return group
    
    def _create_rotation_group(self) -> QGroupBox:
        """创建旋转设置组"""
        group = QGroupBox("🔄 图像旋转")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # 旋转角度设置
        angle_layout = QHBoxLayout()
        angle_label = QLabel("旋转角度:")
        angle_label.setStyleSheet("QLabel { font-weight: 600; }")
        angle_layout.addWidget(angle_label)
        
        # 角度滑块
        self.parent.rotation_slider = QSlider(Qt.Horizontal)
        self.parent.rotation_slider.setRange(-180, 180)
        self.parent.rotation_slider.setValue(0)
        self.parent.rotation_slider.setStyleSheet(get_slider_stylesheet())
        angle_layout.addWidget(self.parent.rotation_slider)
        
        # 角度数值输入
        self.parent.angle_spinbox = QSpinBox()
        self.parent.angle_spinbox.setRange(-180, 180)
        self.parent.angle_spinbox.setValue(0)
        self.parent.angle_spinbox.setSuffix("°")
        self.parent.angle_spinbox.setStyleSheet(get_spinbox_stylesheet())
        angle_layout.addWidget(self.parent.angle_spinbox)
        
        layout.addLayout(angle_layout)
        
        # 快速旋转按钮
        quick_buttons_layout = QHBoxLayout()
        quick_buttons = [
            ("↺ -90°", -90),
            ("⟲ 0°", 0),
            ("↻ +90°", 90),
            ("↕ 180°", 180)
        ]
        
        for text, angle in quick_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(self.button_styles["compact"])
            btn.clicked.connect(lambda checked, a=angle: self.parent.set_rotation_angle(a))
            quick_buttons_layout.addWidget(btn)
        
        layout.addLayout(quick_buttons_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_roi_group(self) -> QGroupBox:
        """创建ROI设置组"""
        group = QGroupBox("✂️ ROI 区域选择")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # ROI开关
        self.parent.roi_checkbox = QCheckBox("启用 ROI 区域截取")
        self.parent.roi_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: 600;
                font-size: 11pt;
                color: #495057;
            }
        """)
        layout.addWidget(self.parent.roi_checkbox)
        
        # ROI选择器说明
        roi_label = QLabel("在预览区域拖拽选择ROI:")
        roi_label.setStyleSheet("QLabel { font-weight: 600; color: #6c757d; }")
        layout.addWidget(roi_label)
        
        # ROI操作按钮
        roi_buttons_layout = QHBoxLayout()
        
        self.parent.roi_select_btn = ModernButton("🎯 重新选择", "info")
        self.parent.roi_select_btn.setEnabled(False)
        
        self.parent.roi_clear_btn = ModernButton("🗑️ 清除", "warning")
        self.parent.roi_clear_btn.setEnabled(False)
        
        roi_buttons_layout.addWidget(self.parent.roi_select_btn)
        roi_buttons_layout.addWidget(self.parent.roi_clear_btn)
        layout.addLayout(roi_buttons_layout)
        
        # ROI信息显示
        self.parent.roi_info_label = QLabel("未选择ROI区域")
        self.parent.roi_info_label.setStyleSheet(self.status_styles["info"])
        layout.addWidget(self.parent.roi_info_label)
        
        # 输出尺寸信息
        output_info = QLabel("📐 输出尺寸: 240×240 像素")
        output_info.setStyleSheet(self.status_styles["count"])
        layout.addWidget(output_info)
        
        group.setLayout(layout)
        return group
    
    def create_preview_panel(self, enhanced: bool = False) -> QWidget:
        """创建预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 预览标题
        title = QLabel("📺 实时预览")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: 600;
                color: #495057;
                margin: 15px;
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 1px solid #dee2e6;
            }
        """)
        layout.addWidget(title)
        
        # 预览区域
        if enhanced:
            self.parent.preview_label = ROISelector()
            placeholder_text = "📷 等待设备连接...\n\n连接设备后将显示实时图像\n启用ROI后可拖拽选择区域"
        else:
            self.parent.preview_label = QLabel()
            placeholder_text = "📷 等待设备连接...\n\n连接设备后将显示实时图像"
        
        self.parent.preview_label.setText(placeholder_text)
        self.parent.preview_label.setAlignment(Qt.AlignCenter)
        self.parent.preview_label.setMinimumHeight(500)
        self.parent.preview_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #dee2e6;
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #6c757d;
                font-size: 14pt;
                margin: 15px;
                padding: 30px;
            }
        """)
        layout.addWidget(self.parent.preview_label)
        
        return panel


class PreviewManager:
    """预览管理器"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def update_preview(self, image):
        """更新预览显示"""
        if image is not None:
            try:
                # 转换为Qt格式并显示
                height, width, channel = image.shape
                bytes_per_line = 3 * width
                q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                
                # 缩放以适应预览区域
                preview_size = self.parent.preview_label.size()
                scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                    preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.parent.preview_label.setPixmap(scaled_pixmap)
                
            except Exception as e:
                self.parent.logger.error(f"更新预览失败: {e}")
