# src/__init__.py
"""
PaperTrackerEyeLabeler - Python版本
专业的眼部追踪标注工具

主要组件:
- MainWindow: 主界面
- DrawOnPic: 图像显示和标注组件
- AllLabel: 标签数据管理
- OneLabel: 单个标签管理
- Painter: 图像绘制器
- SmartAdd: AI智能检测
- StartupDialog: 启动配置对话框
"""

__version__ = "2.0.0"
__author__ = "PaperTrackerEyeLabeler Team"
__email__ = "support@papertracker-eye.com"

# 导入主要类，方便外部使用
from .main_window import MainWindow
from .draw_on_pic import DrawOnPic
from .label_manager import OneLabel
from .txt_manager import AllLabel
from .qt_painter import Painter
from .model import SmartAdd
from .index_list import IndexQListWidgetItem
from .startup_dialog import StartupDialog

# 定义公共API
__all__ = [
    'MainWindow',
    'DrawOnPic', 
    'OneLabel',
    'AllLabel',
    'Painter',
    'SmartAdd',
    'IndexQListWidgetItem',
    'StartupDialog',
    # 常量
    'MOVE',
    'ADD',
]

# 导入常量
from .draw_on_pic import MOVE, ADD

# 包级别的配置
DEFAULT_CONFIG = {
    'default_num_points': 7,
    'default_conf_thresh': 0.6,
    'default_nms_thresh': 0.3,
    'supported_image_formats': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'],
    'supported_model_formats': ['.onnx'],
    'annotation_type': 'hexagon_with_free_point',
    'hexagon_points': 6,
    'free_points': 1,
    'total_points': 7,
    'app_name': 'PaperTrackerEyeLabeler',
    'app_description': 'Professional eye tracking annotation tool',
}

def get_version():
    """获取版本信息"""
    return __version__

def get_config():
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()

# 可选：添加包初始化逻辑
def _check_dependencies():
    """检查依赖是否满足"""
    missing_deps = []
    
    try:
        import PyQt5
    except ImportError:
        missing_deps.append('PyQt5')
    
    try:
        import cv2
    except ImportError:
        missing_deps.append('opencv-python')
    
    try:
        import numpy
    except ImportError:
        missing_deps.append('numpy')
    
    # ONNX Runtime是可选的
    try:
        import onnxruntime
    except ImportError:
        import warnings
        warnings.warn("ONNX Runtime not found. Smart detection will be disabled.", 
                     UserWarning)
    
    if missing_deps:
        raise ImportError(f"Missing required dependencies: {', '.join(missing_deps)}")

# 在包导入时检查依赖
_check_dependencies()

# 包级别的日志配置
import logging

def setup_logging(level=logging.INFO):
    """设置日志配置"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('helios_label.log')
        ]
    )

# 创建包级别的日志器
logger = logging.getLogger(__name__)
logger.info(f"PaperTrackerEyeLabeler v{__version__} initialized - Professional eye tracking annotation tool")