import os
from typing import List, Optional
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QListWidget, QListWidgetItem, QFileDialog,
                            QCheckBox, QSlider, QLabel, QMessageBox, QApplication,
                            QGroupBox, QProgressBar, QTextEdit, QSplitter, QFrame)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QKeyEvent, QFont, QPalette, QColor
from .draw_on_pic import DrawOnPic
from .index_list import IndexQListWidgetItem
from .startup_dialog import StartupDialog

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化主窗口"""
        super().__init__(parent)
        self.focus_index = -1
        self.current_folder = ""
        self.dataset_folder = ""
        self.model_file = ""
        self.has_images = False
        self.has_model = False
        self.initialization_success = False
        
        try:
            # 显示启动对话框
            if not self.show_startup_dialog():
                self.initialization_success = False
                return
            
            print("启动对话框完成，开始初始化UI...")
            
            self.init_ui()
            print("UI初始化完成")
            
            self.connect_signals()
            print("信号连接完成")
            
            self.setup_status_timer()
            print("状态定时器设置完成")
            
            # 设置焦点以接收键盘事件
            self.setFocusPolicy(Qt.StrongFocus)
            
            # 设置样式
            self.setStyleSheet(self.get_stylesheet())
            print("样式设置完成")
            
            # 加载图片
            self.load_images_from_folder()
            print("图片加载完成")
            
            # 更新UI状态
            self.update_ui_state()
            print("UI状态更新完成")
            
            # 显示窗口
            self.show()
            print("窗口显示完成")
            
            # 使用QTimer延迟加载第一张图片
            QTimer.singleShot(100, self.load_first_image)
            
            self.initialization_success = True
            print("主窗口初始化成功")
            
        except Exception as e:
            print(f"主窗口初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self.initialization_success = False

    def load_first_image(self):
        """延迟加载第一张图片"""
        if self.has_images and self.file_list.count() > 0:
            first_item = self.file_list.item(0)
            if first_item:
                print("正在加载第一张图片...")
                self.image_label.set_current_file(first_item.text())
                self.refresh_label_list()
                # 强制更新显示
                self.image_label.update()

    def show_startup_dialog(self) -> bool:
        """显示启动对话框"""
        dialog = StartupDialog(self)
        if dialog.exec_() == StartupDialog.Accepted:
            config = dialog.get_config()
            self.current_folder = config['image_folder']
            self.dataset_folder = config['dataset_folder']
            self.model_file = config['model_file']
            self.has_model = bool(self.model_file)
            
            # 设置自动保存
            self.auto_save_enabled = config['auto_save']
            if hasattr(self, 'image_label'):
                self.image_label.auto_save = self.auto_save_enabled
            return True
        return False
    def load_images_from_folder(self):
        """从文件夹加载图片"""
        if not self.current_folder:
            return
            
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        
        # 清空列表
        self.file_list.clear()
        
        # 获取图片文件
        image_files = []
        try:
            for file_name in os.listdir(self.current_folder):
                if any(file_name.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(self.current_folder, file_name))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取文件夹：{str(e)}")
            return
        
        # 排序并添加到列表
        image_files.sort()
        for idx, file_path in enumerate(image_files):
            item = IndexQListWidgetItem(file_path, idx)
            self.file_list.addItem(item)
        
        self.has_images = len(image_files) > 0
        
        # 设置滑块范围
        if image_files:
            self.file_slider.setMinimum(1)
            self.file_slider.setMaximum(len(image_files))
            self.file_slider.setValue(1)
            self.file_list.setCurrentRow(0)
            
            # 设置标签文件夹 - 使用数据集文件夹而不是图片文件夹
            self.image_label.set_label_path(self.dataset_folder)
            
            # 如果有模型文件，加载它
            if self.model_file:
                self.image_label.set_model_file(self.model_file)
            
            # 不在这里加载第一张图片，改为在延迟函数中加载

    
    def update_ui_state(self):
        """更新UI状态"""
        # 更新图片相关控件状态
        self.file_slider.setEnabled(self.has_images)
        self.file_list.setEnabled(self.has_images)
        
        # 更新标注相关按钮状态
        self.add_label_button.setEnabled(self.has_images)
        self.save_button.setEnabled(self.has_images)
        
        # 更新智能检测按钮状态
        self.smart_button.setEnabled(self.has_images and self.has_model)
        self.smart_all_button.setEnabled(self.has_images and self.has_model)
        
        # 更新图像标签状态
        self.image_label.set_enabled(self.has_images)
        
        # 更新按钮文本提示
        if not self.has_model:
            self.smart_button.setText("🔍 智能检测 (需要模型)")
            self.smart_all_button.setText("🚀 全部智能检测 (需要模型)")
            self.smart_button.setToolTip("请先加载模型文件才能使用智能检测功能")
            self.smart_all_button.setToolTip("请先加载模型文件才能使用智能检测功能")
        else:
            self.smart_button.setText("🔍 智能检测 (S)")
            self.smart_all_button.setText("🚀 全部智能检测")
            self.smart_button.setToolTip("使用AI模型自动检测标注点")
            self.smart_all_button.setToolTip("对所有图片进行智能检测")
        
        if not self.has_images:
            self.add_label_button.setText("✏️ 添加标签 (需要图片)")
            self.save_button.setText("💾 保存 (需要图片)")
            self.add_label_button.setToolTip("请先加载图片文件夹")
            self.save_button.setToolTip("请先加载图片文件夹")
        else:
            self.add_label_button.setText("✏️ 添加标签 (Space)")
            self.save_button.setText("💾 保存")
            self.add_label_button.setToolTip("开始标注新的七边形")
            self.save_button.setToolTip("保存当前标注到文件")
        
        # 更新状态显示
        if not self.has_images:
            self.status_label.setText("请选择包含图片的文件夹")
        elif not self.has_model:
            self.status_label.setText("图片已加载，智能检测功能不可用（未加载模型）")
        else:
            self.status_label.setText("就绪 - 图片和模型均已加载")
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("PaperTrackerEyeLabeler - 眼部追踪标注工具")
        self.setGeometry(100, 100, 1800, 1000)
        self.setMinimumSize(1400, 800)  # 设置最小窗口尺寸
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)  # 防止面板被完全折叠
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 中央图像显示区域
        self.image_label = DrawOnPic()
        self.image_label.setMinimumSize(600, 400)  # 减小最小尺寸以提高灵活性
        self.image_label.setSizePolicy(self.image_label.sizePolicy().Expanding, self.image_label.sizePolicy().Expanding)
        splitter.addWidget(self.image_label)
        self.image_label.auto_save = getattr(self, 'auto_save_enabled', True)
    
        # 右侧信息面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例和约束
        splitter.setStretchFactor(0, 0)  # 左侧面板不拉伸
        splitter.setStretchFactor(1, 1)  # 中央区域主要拉伸
        splitter.setStretchFactor(2, 0)  # 右侧面板不拉伸
        splitter.setSizes([280, 1000, 280])  # 初始尺寸
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        panel.setMaximumWidth(320)
        panel.setMinimumWidth(260)
        panel.setSizePolicy(panel.sizePolicy().Fixed, panel.sizePolicy().Expanding)
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 重新配置组
        reconfig_group = QGroupBox("重新配置")
        reconfig_layout = QVBoxLayout(reconfig_group)
        reconfig_layout.setSpacing(6)
        
        self.reconfig_button = QPushButton("⚙️ 重新选择文件夹")
        self.reconfig_button.setMinimumHeight(35)
        self.reconfig_button.clicked.connect(self.reconfigure)
        reconfig_layout.addWidget(self.reconfig_button)
        
        self.load_model_button = QPushButton("🤖 加载模型文件")
        self.load_model_button.setMinimumHeight(35)
        self.load_model_button.clicked.connect(self.load_model)
        reconfig_layout.addWidget(self.load_model_button)
        
        layout.addWidget(reconfig_group)
        
        # 图片导航组
        nav_group = QGroupBox("图片导航")
        nav_layout = QVBoxLayout(nav_group)
        nav_layout.setSpacing(6)
        
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(4)
        self.file_slider = QSlider(Qt.Horizontal)
        self.file_label = QLabel("[0/0]")
        self.file_label.setMinimumWidth(50)
        self.file_label.setMaximumWidth(60)
        self.file_label.setStyleSheet("font-weight: bold; color: #4a90e2;")
        slider_layout.addWidget(self.file_slider)
        slider_layout.addWidget(self.file_label)
        nav_layout.addLayout(slider_layout)
        
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(180)
        self.file_list.setMinimumHeight(120)
        nav_layout.addWidget(self.file_list)
        
        layout.addWidget(nav_group)
        
        # 标注操作组
        annotation_group = QGroupBox("标注操作")
        annotation_layout = QVBoxLayout(annotation_group)
        annotation_layout.setSpacing(6)
        
        self.add_label_button = QPushButton("✏️ 添加标签 (Space)")
        self.add_label_button.setMinimumHeight(32)
        self.add_label_button.setMaximumHeight(40)
        annotation_layout.addWidget(self.add_label_button)
        
        self.smart_button = QPushButton("🔍 智能检测 (S)")
        self.smart_button.setMinimumHeight(32)
        self.smart_button.setMaximumHeight(40)
        annotation_layout.addWidget(self.smart_button)
        
        self.smart_all_button = QPushButton("🚀 全部智能检测")
        self.smart_all_button.setMinimumHeight(32)
        self.smart_all_button.setMaximumHeight(40)
        annotation_layout.addWidget(self.smart_all_button)
        
        self.save_button = QPushButton("💾 保存")
        self.save_button.setMinimumHeight(32)
        self.save_button.setMaximumHeight(40)
        annotation_layout.addWidget(self.save_button)
        
        self.auto_save_checkbox = QCheckBox("✅ 自动保存")
        self.auto_save_checkbox.setChecked(getattr(self, 'auto_save_enabled', True))
        annotation_layout.addWidget(self.auto_save_checkbox)
        
        layout.addWidget(annotation_group)
        
        # 状态信息组
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(4)
        
        self.image_folder_info_label = QLabel("图片文件夹: 未选择")
        self.image_folder_info_label.setWordWrap(True)
        self.image_folder_info_label.setMinimumHeight(20)
        status_layout.addWidget(self.image_folder_info_label)
        
        self.dataset_folder_info_label = QLabel("数据集文件夹: 未选择")
        self.dataset_folder_info_label.setWordWrap(True)
        self.dataset_folder_info_label.setMinimumHeight(20)
        status_layout.addWidget(self.dataset_folder_info_label)
        
        self.model_info_label = QLabel("模型: 未加载")
        self.model_info_label.setWordWrap(True)
        self.model_info_label.setMinimumHeight(20)
        status_layout.addWidget(self.model_info_label)
        
        layout.addWidget(status_group)
        
        # 操作说明
        help_group = QGroupBox("操作说明")
        help_layout = QVBoxLayout(help_group)
        help_layout.setSpacing(4)
        
        help_text = QTextEdit()
        help_text.setMaximumHeight(130)
        help_text.setMinimumHeight(100)
        help_text.setReadOnly(True)
        help_text.setPlainText(
            "键盘快捷键：\n"
            "Space - 添加标签\n"
            "S - 智能检测\n"
            "Q - 上一张图片\n"
            "E - 下一张图片\n\n"
            "鼠标操作：\n"
            "左键 - 添加点/拖拽点\n"
            "右键 - 拖拽图像\n"
            "滚轮 - 缩放图像\n"
            "右键双击 - 删除标签"
        )
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        panel.setMaximumWidth(320)
        panel.setMinimumWidth(260)
        panel.setSizePolicy(panel.sizePolicy().Fixed, panel.sizePolicy().Expanding)
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 标注进度组
        progress_group = QGroupBox("标注进度")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(6)
        
        self.progress_label = QLabel("当前进度：0/7 点")
        self.progress_label.setStyleSheet("font-weight: bold; color: #4a90e2;")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # 当前标签列表
        labels_group = QGroupBox("当前标签")
        labels_layout = QVBoxLayout(labels_group)
        labels_layout.setSpacing(4)
        
        self.label_now_list = QListWidget()
        self.label_now_list.setMaximumHeight(250)
        self.label_now_list.setMinimumHeight(150)
        labels_layout.addWidget(self.label_now_list)
        
        layout.addWidget(labels_group)
        
        # 标注说明
        info_group = QGroupBox("标注说明")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(4)
        
        info_text = QTextEdit()
        info_text.setMaximumHeight(180)
        info_text.setMinimumHeight(140)
        info_text.setReadOnly(True)
        info_text.setPlainText(
            "七边形标注说明：\n\n"
            "1. 前6个点：按顺时针方向标注六边形的6个顶点\n"
            "2. 第7个点：标注一个游离的特殊点\n\n"
            "标注顺序：\n"
            "- 从六边形最左侧顶点开始\n"
            "- 按顺时针方向标注6个顶点\n"
            "- 最后标注游离点\n\n"
            "颜色说明：\n"
            "🟢 绿色：六边形顶点\n"
            "🔵 蓝色：游离点\n"
            "🔴 红色：六边形边框\n"
            "🟡 黄色：选中的标签"
        )
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return panel
    
    def get_stylesheet(self) -> str:
        """获取样式表"""
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #3c3c3c;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QPushButton {
            background-color: #4a4a4a;
            border: 2px solid #666666;
            border-radius: 5px;
            padding: 8px;
            font-weight: bold;
            color: #ffffff;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background-color: #5a5a5a;
            border-color: #777777;
        }
        
        QPushButton:pressed {
            background-color: #3a3a3a;
        }
        
        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #666666;
        }
        
        QListWidget {
            background-color: #3c3c3c;
            border: 2px solid #555555;
            border-radius: 5px;
            padding: 5px;
            color: #ffffff;
        }
        
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #555555;
        }
        
        QListWidget::item:selected {
            background-color: #4a90e2;
        }
        
        QListWidget::item:hover {
            background-color: #4a4a4a;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #555555;
            height: 8px;
            background: #3c3c3c;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal {
            background: #4a90e2;
            border: 1px solid #555555;
            width: 18px;
            border-radius: 9px;
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
        }
        
        QCheckBox::indicator:checked {
            border: 2px solid #4a90e2;
            background-color: #4a90e2;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        QProgressBar {
            border: 2px solid #555555;
            border-radius: 5px;
            text-align: center;
            color: #ffffff;
            font-weight: bold;
        }
        
        QProgressBar::chunk {
            background-color: #4a90e2;
            border-radius: 3px;
        }
        
        QTextEdit {
            background-color: #3c3c3c;
            border: 2px solid #555555;
            border-radius: 5px;
            color: #ffffff;
            font-family: "Consolas", "Monaco", monospace;
        }
        """
    
    def setup_status_timer(self):
        """设置状态更新定时器"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)  # 每500ms更新一次状态
    
    def update_status(self):
        """更新状态显示"""
        if hasattr(self.image_label, 'get_current_progress'):
            progress_text = self.image_label.get_current_progress()
            self.progress_label.setText(progress_text)
            
            # 更新状态栏
            if self.image_label.current_file:
                file_name = os.path.basename(self.image_label.current_file)
                self.status_label.setText(f"当前文件: {file_name} | {progress_text}")
        
        # 更新文件夹和模型信息
        if self.current_folder:
            folder_name = os.path.basename(self.current_folder)
            image_count = self.file_list.count()
            self.image_folder_info_label.setText(f"图片文件夹: {folder_name} ({image_count} 张图片)")
            self.image_folder_info_label.setStyleSheet("color: #48dbfb;")
        else:
            self.image_folder_info_label.setText("图片文件夹: 未选择")
            self.image_folder_info_label.setStyleSheet("color: #ff6b6b;")
        
        if self.dataset_folder:
            dataset_name = os.path.basename(self.dataset_folder)
            self.dataset_folder_info_label.setText(f"数据集文件夹: {dataset_name}")
            self.dataset_folder_info_label.setStyleSheet("color: #48dbfb;")
        else:
            self.dataset_folder_info_label.setText("数据集文件夹: 未选择")
            self.dataset_folder_info_label.setStyleSheet("color: #ff6b6b;")
        
        if self.model_file:
            model_name = os.path.basename(self.model_file)
            self.model_info_label.setText(f"模型: {model_name}")
            self.model_info_label.setStyleSheet("color: #48dbfb;")
        else:
            self.model_info_label.setText("模型: 未加载")
            self.model_info_label.setStyleSheet("color: #feca57;")
    
    def reconfigure(self):
        """重新配置"""
        reply = QMessageBox.question(
            self, "重新配置", 
            "重新配置将丢失当前未保存的标注，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.show_startup_dialog():
                self.load_images_from_folder()
                self.update_ui_state()
    
    def load_model(self):
        """加载模型"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "", "ONNX模型 (*.onnx);;所有文件 (*)"
        )
        
        if file_path:
            success = self.image_label.set_model_file(file_path)
            if success:
                self.model_file = file_path
                self.has_model = True
                self.update_ui_state()
                QMessageBox.information(self, "成功", "模型加载成功！")
            else:
                QMessageBox.warning(self, "错误", "模型加载失败，请检查文件格式。")
    
    def connect_signals(self):
        """连接信号和槽"""
        # 按钮信号
        self.reconfig_button.clicked.connect(self.reconfigure)
        self.load_model_button.clicked.connect(self.load_model)
        self.add_label_button.clicked.connect(self.on_add_label_clicked)
        self.save_button.clicked.connect(self.on_save_clicked)
        self.smart_button.clicked.connect(self.on_smart_detect_clicked)
        self.smart_all_button.clicked.connect(self.on_smart_all_clicked)
        
        # 复选框信号
        self.auto_save_checkbox.clicked.connect(self.image_label.auto_save_toggle)
        
        # 列表信号
        self.file_list.currentItemChanged.connect(self.on_file_list_changed)
        self.label_now_list.itemClicked.connect(self.on_label_now_clicked)
        
        # 滑块信号
        self.file_slider.valueChanged.connect(self.on_slider_changed)
        self.file_slider.rangeChanged.connect(self.on_slider_range_changed)
        
        # 图像标签信号
        self.image_label.doubleClicked.connect(self.refresh_label_list)
    
    def on_add_label_clicked(self):
        """添加标签按钮点击"""
        if self.has_images:
            self.image_label.set_add_mode()
        else:
            QMessageBox.warning(self, "警告", "请先选择包含图片的文件夹！")
    
    def on_save_clicked(self):
        """保存按钮点击"""
        if self.has_images:
            self.image_label.save_as_txt()
        else:
            QMessageBox.warning(self, "警告", "请先选择包含图片的文件夹！")
    
    def on_smart_detect_clicked(self):
        """智能检测按钮点击"""
        if not self.has_images:
            QMessageBox.warning(self, "警告", "请先选择包含图片的文件夹！")
        elif not self.has_model:
            QMessageBox.warning(self, "警告", "请先加载模型文件！")
        else:
            self.image_label.smart_detect()
    
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_file_list_changed(self, current, previous):
        """文件列表改变"""
        if current is None or not self.has_images:
            return
        
        self.image_label.set_current_file(current.text())
        self.refresh_label_list()
        
        # 更新滑块
        if isinstance(current, IndexQListWidgetItem):
            self.file_slider.setValue(current.get_index() + 1)
    
    @pyqtSlot(QListWidgetItem)
    def on_label_now_clicked(self, item):
        """当前标签列表点击"""
        if item is None or not self.has_images:
            return
        
        self.focus_index = self.label_now_list.row(item)
        self.image_label.draw_focus(self.focus_index)
    
    @pyqtSlot(int)
    def on_slider_changed(self, value):
        """滑块值改变"""
        self.file_label.setText(f"[{value}/{self.file_slider.maximum()}]")
        if 1 <= value <= self.file_list.count() and self.has_images:
            self.file_list.setCurrentRow(value - 1)
    
    @pyqtSlot(int, int)
    def on_slider_range_changed(self, min_val, max_val):
        """滑块范围改变"""
        current = self.file_slider.value()
        self.file_label.setText(f"[{current}/{max_val}]")
    
    @pyqtSlot()
    def on_smart_all_clicked(self):
        """全部智能检测"""
        if not self.has_images:
            QMessageBox.warning(self, "警告", "请先选择包含图片的文件夹！")
            return
        
        if not self.has_model:
            QMessageBox.warning(self, "警告", "请先加载模型文件！")
            return
        
        total = self.file_list.count()
        if total == 0:
            return
        
        reply = QMessageBox.question(
            self, "确认", 
            f"将对 {total} 张图片进行智能检测，这可能需要一些时间。是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            
            for i in range(total):
                self.progress_bar.setValue(i)
                self.file_list.setCurrentRow(i)
                self.image_label.smart_detect()
                QApplication.processEvents()
            
            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "完成", "全部智能检测完成！")
    
    def refresh_label_list(self):
        """刷新标签列表"""
        labels = self.image_label.get_labels_now()
        self.label_now_list.clear()
        
        for i, label in enumerate(labels):
            item_text = f"标签 {i + 1} ({len(label.label_points)}/7 点)"
            self.label_now_list.addItem(QListWidgetItem(item_text))
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        if not self.has_images:
            return
        
        key = event.key()
        current_row = self.file_list.currentRow()
        
        if key == Qt.Key_Q:  # 上一张图片
            if current_row > 0:
                self.file_list.setCurrentRow(current_row - 1)
        elif key == Qt.Key_E:  # 下一张图片
            if current_row < self.file_list.count() - 1:
                self.file_list.setCurrentRow(current_row + 1)
        elif key == Qt.Key_S:  # 智能检测
            if self.has_model:
                self.image_label.smart_detect()
        elif key == Qt.Key_Space:  # 添加标签
            self.image_label.set_add_mode()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        if hasattr(self.image_label, 'auto_save') and self.image_label.auto_save:
            self.image_label.save_as_txt()
        super().closeEvent(event)