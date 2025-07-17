# enhanced_main_window.py
"""
增强版主窗口 - 集成WebSocket功能
在原有的标注功能基础上，添加实时图像流标注功能
"""

import os
import sys
import cv2
import numpy as np
from typing import Optional, List
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QLabel, QPushButton, QMessageBox, QFileDialog,
    QProgressBar, QStatusBar, QMenuBar, QAction, QToolBar,
    QGroupBox, QGridLayout, QCheckBox, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSettings
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont, QKeySequence
import logging

# 假设这些是原有的labeler组件
try:
    from src.main_window import MainWindow as OriginalMainWindow
    from src.draw_on_pic import DrawOnPic
    from src.txt_manager import AllLabel
    from src.startup_dialog import StartupDialog
    HAS_ORIGINAL_COMPONENTS = True
except ImportError:
    HAS_ORIGINAL_COMPONENTS = False
    print("警告: 无法导入原有组件，将使用简化版本")

# 导入WebSocket组件
from labeler_websocket_widget import WebSocketControlWidget, WebSocketImageProvider


class EnhancedLabelerMainWindow(QMainWindow):
    """增强版标注工具主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.setup_ui()
        self.setup_websocket()
        self.setup_connections()
        self.setup_shortcuts()
        self.load_settings()
        
        # 初始化变量
        self.current_mode = "file"  # "file" 或 "stream"
        self.stream_images = []
        self.current_stream_index = 0
        
        self.logger.info("增强版标注工具启动完成")
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("PaperTracker标注工具 - 增强版")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 中央标注区域
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([350, 700, 350])
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 2px solid #4CAF50;
            }
        """)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 模式选择
        mode_group = QGroupBox("工作模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.file_mode_radio = QCheckBox("文件标注模式")
        self.file_mode_radio.setChecked(True)
        self.file_mode_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.file_mode_radio)
        
        self.stream_mode_radio = QCheckBox("实时流标注模式")
        self.stream_mode_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.stream_mode_radio)
        
        layout.addWidget(mode_group)
        
        # 文件模式设置
        self.file_settings_group = self.create_file_settings_group()
        layout.addWidget(self.file_settings_group)
        
        # 快捷操作
        shortcuts_group = self.create_shortcuts_group()
        layout.addWidget(shortcuts_group)
        
        # 标注统计
        stats_group = self.create_stats_group()
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """创建中央面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 标注选项卡
        self.annotation_tab = self.create_annotation_tab()
        self.tab_widget.addTab(self.annotation_tab, "标注工作区")
        
        # 图像预览选项卡
        self.preview_tab = self.create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "图像预览")
        
        layout.addWidget(self.tab_widget)
        
        # 底部控制栏
        control_bar = self.create_control_bar()
        layout.addWidget(control_bar)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # WebSocket控制面板
        self.websocket_group = QGroupBox("实时设备连接")
        websocket_layout = QVBoxLayout(self.websocket_group)
        
        # 这里会在setup_websocket中添加WebSocket控件
        layout.addWidget(self.websocket_group)
        
        # 标注进度
        progress_group = self.create_progress_group()
        layout.addWidget(progress_group)
        
        # 当前标签信息
        labels_group = self.create_labels_group()
        layout.addWidget(labels_group)
        
        layout.addStretch()
        
        return panel
    
    def create_file_settings_group(self) -> QGroupBox:
        """创建文件设置组"""
        group = QGroupBox("文件设置")
        layout = QVBoxLayout(group)
        
        # 文件夹选择
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setStyleSheet("color: gray;")
        folder_layout.addWidget(self.folder_label)
        
        self.browse_folder_btn = QPushButton("浏览...")
        self.browse_folder_btn.clicked.connect(self.browse_image_folder)
        folder_layout.addWidget(self.browse_folder_btn)
        
        layout.addLayout(folder_layout)
        
        # 文件信息
        self.file_info_label = QLabel("文件: 0 / 0")
        layout.addWidget(self.file_info_label)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一张")
        self.prev_btn.clicked.connect(self.prev_image)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("下一张")
        self.next_btn.clicked.connect(self.next_image)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        return group
    
    def create_shortcuts_group(self) -> QGroupBox:
        """创建快捷操作组"""
        group = QGroupBox("快捷操作")
        layout = QVBoxLayout(group)
        
        # 标注操作
        self.add_label_btn = QPushButton("添加标签 (空格)")
        self.add_label_btn.clicked.connect(self.add_label)
        layout.addWidget(self.add_label_btn)
        
        self.smart_detect_btn = QPushButton("智能检测 (S)")
        self.smart_detect_btn.clicked.connect(self.smart_detect)
        layout.addWidget(self.smart_detect_btn)
        
        self.save_btn = QPushButton("保存标注 (Ctrl+S)")
        self.save_btn.clicked.connect(self.save_annotations)
        layout.addWidget(self.save_btn)
        
        # 分隔线
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #cccccc;")
        layout.addWidget(line)
        
        # 流模式专用按钮
        self.capture_btn = QPushButton("捕获当前帧")
        self.capture_btn.clicked.connect(self.capture_current_frame)
        self.capture_btn.setEnabled(False)
        layout.addWidget(self.capture_btn)
        
        return group
    
    def create_stats_group(self) -> QGroupBox:
        """创建统计信息组"""
        group = QGroupBox("标注统计")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("已标注:"), 0, 0)
        self.labeled_count_label = QLabel("0")
        layout.addWidget(self.labeled_count_label, 0, 1)
        
        layout.addWidget(QLabel("未标注:"), 1, 0)
        self.unlabeled_count_label = QLabel("0")
        layout.addWidget(self.unlabeled_count_label, 1, 1)
        
        layout.addWidget(QLabel("总计:"), 2, 0)
        self.total_count_label = QLabel("0")
        layout.addWidget(self.total_count_label, 2, 1)
        
        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar, 3, 0, 1, 2)
        
        return group
    
    def create_annotation_tab(self) -> QWidget:
        """创建标注选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 如果有原有组件，使用原有的DrawOnPic
        if HAS_ORIGINAL_COMPONENTS:
            try:
                self.draw_widget = DrawOnPic()
                layout.addWidget(self.draw_widget)
            except Exception as e:
                self.logger.error(f"创建DrawOnPic失败: {e}")
                self.draw_widget = self.create_simple_draw_widget()
                layout.addWidget(self.draw_widget)
        else:
            self.draw_widget = self.create_simple_draw_widget()
            layout.addWidget(self.draw_widget)
        
        return widget
    
    def create_simple_draw_widget(self) -> QWidget:
        """创建简单的绘图组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.image_display = QLabel()
        self.image_display.setMinimumSize(640, 480)
        self.image_display.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f8f8f8;
                text-align: center;
            }
        """)
        self.image_display.setText("请选择图像文件或连接设备")
        self.image_display.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.image_display)
        
        return widget
    
    def create_preview_tab(self) -> QWidget:
        """创建预览选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
        """)
        self.preview_label.setText("预览区域")
        self.preview_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.preview_label)
        
        return widget
    
    def create_control_bar(self) -> QWidget:
        """创建控制栏"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # 模式指示器
        self.mode_indicator = QLabel("模式: 文件标注")
        self.mode_indicator.setStyleSheet("font-weight: bold; color: #4CAF50;")
        layout.addWidget(self.mode_indicator)
        
        layout.addStretch()
        
        # 缩放控制
        layout.addWidget(QLabel("缩放:"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["25%", "50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        layout.addWidget(self.zoom_combo)
        
        return widget
    
    def create_progress_group(self) -> QGroupBox:
        """创建进度信息组"""
        group = QGroupBox("标注进度")
        layout = QVBoxLayout(group)
        
        self.current_progress_label = QLabel("当前: 0/7 点")
        layout.addWidget(self.current_progress_label)
        
        self.overall_progress_label = QLabel("总体: 0% 完成")
        layout.addWidget(self.overall_progress_label)
        
        return group
    
    def create_labels_group(self) -> QGroupBox:
        """创建标签信息组"""
        group = QGroupBox("当前标签")
        layout = QVBoxLayout(group)
        
        self.labels_info = QLabel("暂无标签")
        self.labels_info.setStyleSheet("color: gray;")
        layout.addWidget(self.labels_info)
        
        return group
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        open_action = QAction('打开文件夹(&O)', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.browse_image_folder)
        file_menu.addAction(open_action)
        
        save_action = QAction('保存标注(&S)', self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_annotations)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出(&Q)', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')
        
        smart_detect_action = QAction('智能检测(&D)', self)
        smart_detect_action.setShortcut('S')
        smart_detect_action.triggered.connect(self.smart_detect)
        tools_menu.addAction(smart_detect_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        
        # 文件操作
        open_action = QAction('打开', self)
        open_action.setToolTip('打开图像文件夹')
        open_action.triggered.connect(self.browse_image_folder)
        toolbar.addAction(open_action)
        
        save_action = QAction('保存', self)
        save_action.setToolTip('保存当前标注')
        save_action.triggered.connect(self.save_annotations)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 标注操作
        add_label_action = QAction('添加标签', self)
        add_label_action.setToolTip('添加新标签 (空格)')
        add_label_action.triggered.connect(self.add_label)
        toolbar.addAction(add_label_action)
        
        smart_detect_action = QAction('智能检测', self)
        smart_detect_action.setToolTip('AI智能检测 (S)')
        smart_detect_action.triggered.connect(self.smart_detect)
        toolbar.addAction(smart_detect_action)
        
        toolbar.addSeparator()
        
        # 导航操作
        prev_action = QAction('上一张', self)
        prev_action.setToolTip('上一张图片 (Q)')
        prev_action.triggered.connect(self.prev_image)
        toolbar.addAction(prev_action)
        
        next_action = QAction('下一张', self)
        next_action.setToolTip('下一张图片 (E)')
        next_action.triggered.connect(self.next_image)
        toolbar.addAction(next_action)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.statusBar().showMessage('准备就绪')
        
        # 添加永久状态信息
        self.connection_status = QLabel("设备: 未连接")
        self.statusBar().addPermanentWidget(self.connection_status)
        
        self.mode_status = QLabel("模式: 文件标注")
        self.statusBar().addPermanentWidget(self.mode_status)
    
    def setup_websocket(self):
        """设置WebSocket组件"""
        self.websocket_widget = WebSocketControlWidget()
        
        # 添加到右侧面板
        layout = self.websocket_group.layout()
        layout.addWidget(self.websocket_widget)
        
        # 创建图像提供者
        self.image_provider = WebSocketImageProvider(self.websocket_widget)
    
    def setup_connections(self):
        """设置信号连接"""
        # WebSocket连接
        self.websocket_widget.connection_status_changed.connect(
            self.on_websocket_status_changed
        )
        self.websocket_widget.image_received.connect(
            self.on_websocket_image_received
        )
        self.websocket_widget.save_image_requested.connect(
            self.on_websocket_image_saved
        )
        
        # 图像提供者连接
        self.image_provider.image_ready.connect(
            self.on_stream_image_ready
        )
        
        # 模式切换
        self.file_mode_radio.toggled.connect(self.update_ui_for_mode)
        self.stream_mode_radio.toggled.connect(self.update_ui_for_mode)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        from PyQt5.QtWidgets import QShortcut
        
        # 标注快捷键
        QShortcut(Qt.Key_Space, self, self.add_label)
        QShortcut(Qt.Key_S, self, self.smart_detect)
        QShortcut(QKeySequence.Save, self, self.save_annotations)
        
        # 导航快捷键
        QShortcut(Qt.Key_Q, self, self.prev_image)
        QShortcut(Qt.Key_E, self, self.next_image)
        
        # 流模式快捷键
        QShortcut(Qt.Key_C, self, self.capture_current_frame)
        QShortcut(Qt.Key_R, self, self.toggle_stream_recording)
    
    def load_settings(self):
        """加载设置"""
        self.settings = QSettings('PaperTracker', 'EnhancedLabeler')
        
        # 恢复窗口状态
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        # 恢复其他设置
        last_folder = self.settings.value('last_folder', '')
        if last_folder and os.path.exists(last_folder):
            self.load_image_folder(last_folder)
        
        device_url = self.settings.value('websocket_url', '')
        if device_url:
            self.websocket_widget.url_input.setText(device_url)
    
    def save_settings(self):
        """保存设置"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('websocket_url', self.websocket_widget.url_input.text())
        
        if hasattr(self, 'current_folder'):
            self.settings.setValue('last_folder', self.current_folder)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.save_settings()
        
        # 停止WebSocket连接
        if self.websocket_widget.get_connection_status():
            self.websocket_widget.disconnect_device()
        
        # 停止图像提供者
        if hasattr(self, 'image_provider'):
            self.image_provider.stop_capture()
        
        event.accept()
    
    def on_mode_changed(self):
        """模式改变处理"""
        if self.file_mode_radio.isChecked():
            self.current_mode = "file"
            self.stream_mode_radio.setChecked(False)
        elif self.stream_mode_radio.isChecked():
            self.current_mode = "stream"
            self.file_mode_radio.setChecked(False)
        
        self.update_ui_for_mode()
    
    def update_ui_for_mode(self):
        """根据模式更新UI"""
        is_file_mode = self.current_mode == "file"
        is_stream_mode = self.current_mode == "stream"
        
        # 更新按钮状态
        self.file_settings_group.setEnabled(is_file_mode)
        self.prev_btn.setEnabled(is_file_mode)
        self.next_btn.setEnabled(is_file_mode)
        
        self.capture_btn.setEnabled(is_stream_mode)
        self.websocket_group.setEnabled(is_stream_mode)
        
        # 更新状态栏
        mode_text = "文件标注" if is_file_mode else "实时流标注"
        self.mode_indicator.setText(f"模式: {mode_text}")
        self.mode_status.setText(f"模式: {mode_text}")
        
        # 更新标题
        title = "PaperTracker标注工具 - 增强版"
        if is_stream_mode:
            title += " (实时流模式)"
        self.setWindowTitle(title)
    
    def browse_image_folder(self):
        """浏览图像文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择图像文件夹", 
            self.settings.value('last_folder', '')
        )
        
        if folder:
            self.load_image_folder(folder)
    
    def load_image_folder(self, folder_path: str):
        """加载图像文件夹"""
        try:
            self.current_folder = folder_path
            
            # 支持的图像格式
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
            
            # 扫描图像文件
            self.image_files = []
            for ext in image_extensions:
                pattern = os.path.join(folder_path, f"*{ext}")
                import glob
                self.image_files.extend(glob.glob(pattern))
                # 添加大写扩展名
                pattern_upper = os.path.join(folder_path, f"*{ext.upper()}")
                self.image_files.extend(glob.glob(pattern_upper))
            
            self.image_files.sort()
            self.current_image_index = 0
            
            # 更新UI
            self.folder_label.setText(f"文件夹: {os.path.basename(folder_path)}")
            self.folder_label.setStyleSheet("color: black;")
            
            total_count = len(self.image_files)
            self.total_count_label.setText(str(total_count))
            self.file_info_label.setText(f"文件: 0 / {total_count}")
            
            # 启用导航按钮
            self.prev_btn.setEnabled(total_count > 0)
            self.next_btn.setEnabled(total_count > 0)
            
            # 加载第一张图片
            if self.image_files:
                self.load_current_image()
            
            self.statusBar().showMessage(f"加载了 {total_count} 张图片")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件夹失败: {e}")
            self.logger.error(f"加载文件夹失败: {e}")
    
    def load_current_image(self):
        """加载当前图片"""
        if not self.image_files or self.current_image_index >= len(self.image_files):
            return
        
        try:
            current_file = self.image_files[self.current_image_index]
            
            # 加载图像
            image = cv2.imread(current_file)
            if image is not None:
                self.display_image(image)
                
                # 更新文件信息
                total = len(self.image_files)
                current = self.current_image_index + 1
                self.file_info_label.setText(f"文件: {current} / {total}")
                
                # 更新标题
                filename = os.path.basename(current_file)
                self.setWindowTitle(f"PaperTracker标注工具 - {filename}")
                
                # 如果有原有组件，加载到DrawOnPic
                if hasattr(self, 'draw_widget') and hasattr(self.draw_widget, 'set_image'):
                    self.draw_widget.set_image(current_file)
                
                self.statusBar().showMessage(f"加载图片: {filename}")
            else:
                QMessageBox.warning(self, "警告", f"无法加载图片: {current_file}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载图片失败: {e}")
            self.logger.error(f"加载图片失败: {e}")
    
    def display_image(self, image: np.ndarray):
        """显示图像"""
        try:
            # 转换颜色空间
            if len(image.shape) == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # 转换为QImage
            height, width = rgb_image.shape[:2]
            if len(rgb_image.shape) == 3:
                bytes_per_line = 3 * width
                q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                bytes_per_line = width
                q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            
            # 缩放图像
            display_size = self.image_display.size()
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # 显示图像
            self.image_display.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.logger.error(f"显示图像失败: {e}")
    
    def prev_image(self):
        """上一张图片"""
        if self.current_mode == "file" and self.image_files:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            self.load_current_image()
        elif self.current_mode == "stream" and self.stream_images:
            self.current_stream_index = (self.current_stream_index - 1) % len(self.stream_images)
            self.load_current_stream_image()
    
    def next_image(self):
        """下一张图片"""
        if self.current_mode == "file" and self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.load_current_image()
        elif self.current_mode == "stream" and self.stream_images:
            self.current_stream_index = (self.current_stream_index + 1) % len(self.stream_images)
            self.load_current_stream_image()
    
    def add_label(self):
        """添加标签"""
        if hasattr(self, 'draw_widget') and hasattr(self.draw_widget, 'set_add_mode'):
            self.draw_widget.set_add_mode()
        self.statusBar().showMessage("标签添加模式")
    
    def smart_detect(self):
        """智能检测"""
        if hasattr(self, 'draw_widget') and hasattr(self.draw_widget, 'smart_detect'):
            self.draw_widget.smart_detect()
        self.statusBar().showMessage("执行智能检测")
    
    def save_annotations(self):
        """保存标注"""
        if hasattr(self, 'draw_widget') and hasattr(self.draw_widget, 'save_as_txt'):
            self.draw_widget.save_as_txt()
        self.statusBar().showMessage("标注已保存")
    
    def capture_current_frame(self):
        """捕获当前帧"""
        if self.current_mode == "stream":
            current_image = self.websocket_widget.get_current_image()
            if current_image is not None:
                # 添加到流图像列表
                self.stream_images.append(current_image)
                self.current_stream_index = len(self.stream_images) - 1
                
                # 显示图像
                self.display_image(current_image)
                
                # 更新统计
                self.total_count_label.setText(str(len(self.stream_images)))
                
                self.statusBar().showMessage(f"捕获帧 {len(self.stream_images)}")
    
    def toggle_stream_recording(self):
        """切换流录制"""
        if hasattr(self, 'image_provider'):
            if self.image_provider.isRunning():
                self.image_provider.stop_capture()
                self.statusBar().showMessage("停止录制")
            else:
                self.image_provider.start_capture()
                self.statusBar().showMessage("开始录制")
    
    def on_websocket_status_changed(self, connected: bool, message: str):
        """WebSocket状态改变"""
        if connected:
            self.connection_status.setText("设备: 已连接")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("设备: 未连接")
            self.connection_status.setStyleSheet("color: red;")
        
        self.statusBar().showMessage(message)
    
    def on_websocket_image_received(self, image: np.ndarray):
        """WebSocket图像接收"""
        if self.current_mode == "stream":
            # 在预览选项卡中显示实时图像
            self.update_preview_image(image)
    
    def on_websocket_image_saved(self, image: np.ndarray, filepath: str):
        """WebSocket图像保存"""
        self.statusBar().showMessage(f"图像已保存: {os.path.basename(filepath)}")
    
    def on_stream_image_ready(self, image: np.ndarray, filepath: str):
        """流图像准备就绪"""
        # 可以在这里添加自动标注逻辑
        pass
    
    def update_preview_image(self, image: np.ndarray):
        """更新预览图像"""
        try:
            # 转换颜色空间
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 转换为QImage
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # 缩放图像
            preview_size = self.preview_label.size()
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # 显示图像
            self.preview_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.logger.error(f"更新预览图像失败: {e}")
    
    def load_current_stream_image(self):
        """加载当前流图像"""
        if self.stream_images and self.current_stream_index < len(self.stream_images):
            image = self.stream_images[self.current_stream_index]
            self.display_image(image)
            
            # 更新信息
            total = len(self.stream_images)
            current = self.current_stream_index + 1
            self.file_info_label.setText(f"流帧: {current} / {total}")
    
    def on_zoom_changed(self, zoom_text: str):
        """缩放改变"""
        try:
            zoom_value = int(zoom_text.replace('%', ''))
            # 这里可以实现缩放逻辑
            self.statusBar().showMessage(f"缩放: {zoom_value}%")
        except ValueError:
            pass
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
            "PaperTracker标注工具 - 增强版\n"
            "版本: 2.0.0\n"
            "支持文件标注和实时流标注\n"
            "集成WebSocket连接功能\n\n"
            "开发团队: PaperTracker Team"
        )


def main():
    """主函数"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("PaperTracker标注工具")
    app.setApplicationVersion("2.0.0")
    
    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon('icon.png'))
    
    window = EnhancedLabelerMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()