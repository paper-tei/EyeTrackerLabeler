import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFileDialog, QMessageBox, QGroupBox, 
                            QTextEdit, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class StartupDialog(QDialog):
    """启动对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_folder = ""
        self.dataset_folder = ""
        self.model_file = ""
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("PaperTrackerEyeLabeler - 启动配置")
        self.setFixedSize(750, 700)
        self.setModal(True)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #4a90e2;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 2px solid #666666;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                color: #ffffff;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #4a90e2;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #444444;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 6px;
                color: #ffffff;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 11px;
            }
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #555555;
                background-color: #3c3c3c;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #4a90e2;
                background-color: #4a90e2;
                border-radius: 3px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("PaperTrackerEyeLabeler")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #4a90e2; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("专业的眼部追踪标注工具")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #cccccc; font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(subtitle_label)
        
        # 必选配置组
        required_group = QGroupBox("必选配置")
        required_layout = QVBoxLayout(required_group)
        required_layout.setSpacing(8)
        required_layout.setContentsMargins(15, 15, 15, 15)
        
        # 图片文件夹选择
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)
        self.folder_button = QPushButton("📁 选择图片文件夹")
        self.folder_button.setMinimumHeight(35)
        self.folder_button.setMinimumWidth(140)
        self.folder_button.clicked.connect(self.select_image_folder)
        self.folder_label = QLabel("未选择图片文件夹")
        self.folder_label.setStyleSheet("color: #ff6b6b; font-style: italic;")
        self.folder_label.setWordWrap(True)
        self.folder_label.setMinimumHeight(35)
        folder_layout.addWidget(self.folder_button)
        folder_layout.addWidget(self.folder_label, 1)
        required_layout.addLayout(folder_layout)
        
        # 数据集保存文件夹选择
        dataset_layout = QHBoxLayout()
        dataset_layout.setSpacing(8)
        self.dataset_button = QPushButton("💾 选择数据集保存文件夹")
        self.dataset_button.setMinimumHeight(35)
        self.dataset_button.setMinimumWidth(140)
        self.dataset_button.clicked.connect(self.select_dataset_folder)
        self.dataset_label = QLabel("未选择数据集保存文件夹")
        self.dataset_label.setStyleSheet("color: #ff6b6b; font-style: italic;")
        self.dataset_label.setWordWrap(True)
        self.dataset_label.setMinimumHeight(35)
        dataset_layout.addWidget(self.dataset_button)
        dataset_layout.addWidget(self.dataset_label, 1)
        required_layout.addLayout(dataset_layout)
        
        layout.addWidget(required_group)
        
        # 可选配置组
        optional_group = QGroupBox("可选配置")
        optional_layout = QVBoxLayout(optional_group)
        optional_layout.setSpacing(8)
        optional_layout.setContentsMargins(15, 15, 15, 15)
        
        # 模型文件选择
        model_layout = QHBoxLayout()
        model_layout.setSpacing(8)
        self.model_button = QPushButton("🤖 选择模型文件")
        self.model_button.setMinimumHeight(35)
        self.model_button.setMinimumWidth(140)
        self.model_button.clicked.connect(self.select_model_file)
        self.model_label = QLabel("未选择模型（将禁用智能标注）")
        self.model_label.setStyleSheet("color: #feca57; font-style: italic;")
        self.model_label.setWordWrap(True)
        self.model_label.setMinimumHeight(35)
        model_layout.addWidget(self.model_button)
        model_layout.addWidget(self.model_label, 1)
        optional_layout.addLayout(model_layout)
        
        layout.addWidget(optional_group)
        
        # 使用说明
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout(help_group)
        help_layout.setContentsMargins(15, 15, 15, 15)
        
        help_text = QTextEdit()
        help_text.setMaximumHeight(110)
        help_text.setMinimumHeight(110)
        help_text.setReadOnly(True)
        help_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        help_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        help_text.setPlainText(
            "✅ 必选配置说明：\n"
            "• 图片文件夹：包含待标注图片的文件夹\n"
            "• 数据集保存文件夹：标注数据的保存位置\n\n"
            "📋 标注说明：\n"
            "• 支持的图片格式：JPG, PNG, BMP, TIFF\n"
            "• 每个标注包含7个点：前6个点构成六边形，第7个点为游离点\n"
            "• 标注顺序：从六边形最左侧顶点开始，按顺时针方向标注\n\n"
            "💾 数据保存：\n"
            "• 标注文件保存在 数据集文件夹/labels/ 下\n"
            "• 每行包含14个归一化坐标值（7个点×2个坐标）\n\n"
            "🤖 智能检测：\n"
            "• 模型文件可选，支持ONNX格式\n"
            "• 没有模型时仍可手动标注\n\n"
            "⌨️ 快捷键：\n"
            "• Space键：添加标签  • S键：智能检测  • Q/E键：切换图片"
        )
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        
        # 自动保存选项
        self.auto_save_checkbox = QCheckBox("✅ 启用自动保存")
        self.auto_save_checkbox.setChecked(True)
        layout.addWidget(self.auto_save_checkbox)
        
        # 添加一些弹性空间
        layout.addSpacing(10)
        
        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.ok_button = QPushButton("✅ 开始标注")
        self.ok_button.setMinimumHeight(40)
        self.ok_button.setMinimumWidth(120)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border-color: #4a90e2;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #444444;
            }
        """)
        
        self.cancel_button = QPushButton("❌ 取消")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
    def select_dataset_folder(self):
        """选择数据集保存文件夹"""
        print("用户点击选择数据集文件夹...")
        folder = QFileDialog.getExistingDirectory(self, "选择数据集保存文件夹")
        print(f"用户选择的数据集文件夹: {folder}")
        
        if folder:
            self.dataset_folder = folder
            folder_name = os.path.basename(folder)
            self.dataset_label.setText(f"✅ 已选择: {folder_name}")
            self.dataset_label.setStyleSheet("color: #48dbfb;")
            print(f"数据集文件夹设置为: {self.dataset_folder}")
            self.update_ok_button()
    
    def select_image_folder(self):
        """选择图片文件夹"""
        print("用户点击选择图片文件夹...")
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        print(f"用户选择的图片文件夹: {folder}")
        
        if folder:
            # 检查文件夹中是否有图片
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
            image_files = []
            
            try:
                for file_name in os.listdir(folder):
                    if any(file_name.lower().endswith(ext) for ext in image_extensions):
                        image_files.append(file_name)
                print(f"找到 {len(image_files)} 张图片")
            except Exception as e:
                print(f"读取文件夹失败: {e}")
                QMessageBox.warning(self, "错误", f"无法访问文件夹：{str(e)}")
                return
            
            if not image_files:
                print("文件夹中没有找到图片")
                QMessageBox.warning(
                    self, "警告", 
                    "所选文件夹中没有找到支持的图片文件！\n\n"
                    "支持的格式：JPG, PNG, BMP, TIFF"
                )
                return
            
            self.image_folder = folder
            folder_name = os.path.basename(folder)
            self.folder_label.setText(f"✅ 已选择: {folder_name}\n({len(image_files)} 张图片)")
            self.folder_label.setStyleSheet("color: #48dbfb;")
            print(f"图片文件夹设置为: {self.image_folder}")
            self.update_ok_button()
    
    def select_model_file(self):
        """选择模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "", "ONNX模型 (*.onnx);;所有文件 (*)"
        )
        if file_path:
            self.model_file = file_path
            model_name = os.path.basename(file_path)
            # 如果文件名太长，截断显示
            if len(model_name) > 25:
                display_name = model_name[:22] + "..."
            else:
                display_name = model_name
            self.model_label.setText(f"✅ 已选择: {display_name}")
            self.model_label.setStyleSheet("color: #48dbfb;")
    
    def update_ok_button(self):
        """更新开始按钮状态"""
        # 只有当图片文件夹和数据集文件夹都选择后才能开始
        can_start = bool(self.image_folder and self.dataset_folder)
        self.ok_button.setEnabled(can_start)
        print(f"按钮状态更新: image_folder={bool(self.image_folder)}, dataset_folder={bool(self.dataset_folder)}, can_start={can_start}")
    
    def get_config(self):
        """获取配置"""
        config = {
            'image_folder': self.image_folder,
            'dataset_folder': self.dataset_folder,
            'model_file': self.model_file,
            'auto_save': self.auto_save_checkbox.isChecked()
        }
        print(f"返回配置: {config}")
        return config