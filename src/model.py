import cv2
import numpy as np
from typing import List, Tuple, Optional
from PyQt5.QtCore import QPointF
from .label_manager import OneLabel

# 尝试导入ONNX Runtime，如果失败则使用模拟版本
try:
    import onnxruntime as ort
    ONNXRUNTIME_AVAILABLE = True
except ImportError:
    ONNXRUNTIME_AVAILABLE = False
    print("Warning: ONNX Runtime not available. Smart detection will be disabled.")

# 定义输出大小常量（根据C++代码中的EYE_OUTPUT_SIZE）
EYE_OUTPUT_SIZE = 7 * 2  # 7个点，每个点2个坐标

class Object:
    """检测对象"""
    def __init__(self):
        self.conf = 0.0
        self.points: List[Tuple[float, float]] = []
        self.rect = (0, 0, 0, 0)  # x, y, w, h

class SmartAdd:
    """智能标注类 - 基于C++版本的眼部推理实现"""
    
    def __init__(self):
        self.num_points = 7  # 固定为7个点
        self.model_path = ""
        
        # 根据C++代码设置输入尺寸
        self.input_width = 112
        self.input_height = 112
        self.input_channels = 1  # 灰度图
        
        self.conf_thresh = 0.6
        self.nms_thresh = 0.3
        
        # ONNX Runtime相关
        if ONNXRUNTIME_AVAILABLE:
            self.session = None
            self.input_name = None
            self.output_names = None
            self.input_shapes = []
            self.output_shapes = []
            self.memory_info = None
            
            # 预分配的缓冲区
            self.input_data = None
            self.gray_image = None
            self.processed_image = None
        else:
            self.session = None
    
    def set_num_points(self, points: int):
        """设置点数（固定为7，此方法保持兼容性）"""
        self.num_points = 7  # 始终为7个点
    
    def set_model(self, model_path: str) -> bool:
        """设置模型路径 - 基于C++的load_model实现"""
        if not ONNXRUNTIME_AVAILABLE:
            print("ONNX Runtime not available")
            return False
        
        try:
            self.model_path = model_path
            
            # 创建环境
            providers = ['CPUExecutionProvider']
            
            # 配置会话选项 - 与C++版本保持一致
            session_options = ort.SessionOptions()
            session_options.intra_op_num_threads = 2
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            session_options.add_session_config_entry("session.intra_op.allow_spinning", "0")
            
            # Python版本的内存选项
            session_options.enable_cpu_mem_arena = True
            session_options.enable_mem_pattern = False
            
            # 创建会话
            self.session = ort.InferenceSession(
                self.model_path, 
                sess_options=session_options,
                providers=providers
            )
            
            # 获取输入输出信息
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            # 获取输入形状
            input_shape = self.session.get_inputs()[0].shape
            self.input_shapes = [input_shape]
            
            # 获取输出形状
            self.output_shapes = [output.shape for output in self.session.get_outputs()]
            
            # 预分配缓冲区
            self.allocate_buffers()
            
            print(f"眼睛模型加载完成")
            print(f"Input shape: {input_shape}")
            print(f"Output shapes: {self.output_shapes}")
            
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def allocate_buffers(self):
        """预分配缓冲区"""
        if not ONNXRUNTIME_AVAILABLE or not self.session:
            return
        
        # 分配输入数据缓冲区
        self.input_data = np.zeros(
            (1, self.input_channels, self.input_height, self.input_width), 
            dtype=np.float32
        )
        
        # 预分配图像处理缓冲区
        self.gray_image = np.zeros((self.input_height, self.input_width), dtype=np.uint8)
        self.processed_image = np.zeros((self.input_height, self.input_width), dtype=np.float32)
    
    def preprocess_image_from_cv2(self, img: np.ndarray) -> np.ndarray:
        """预处理图像 - 基于C++的preprocess实现"""
        # 转换为灰度图（如果需要）
        if len(img.shape) == 3 and img.shape[2] == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif len(img.shape) == 3 and img.shape[2] == 1:
            gray = img[:, :, 0]
        else:
            gray = img
        
        # 调整大小 - 使用INTER_NEAREST与C++保持一致
        resized = cv2.resize(gray, (self.input_width, self.input_height), 
                           interpolation=cv2.INTER_NEAREST)
        
        # 归一化处理 - 转换为float32并除以255
        normalized = resized.astype(np.float32) / 255.0
        
        # 添加通道维度和批次维度 (H,W) -> (1,1,H,W)
        if len(normalized.shape) == 2:
            normalized = normalized[np.newaxis, np.newaxis, :, :]
        
        return normalized
    
    def run_inference(self, input_data: np.ndarray) -> Optional[np.ndarray]:
        """运行推理 - 基于C++的run_model实现"""
        if not self.session:
            return None
        
        try:
            # 运行推理
            outputs = self.session.run(
                self.output_names, 
                {self.input_name: input_data}
            )
            
            return outputs[0]  # 返回第一个输出
            
        except Exception as e:
            print(f"推理错误: {e}")
            return None
    
    def postprocess(self, output: np.ndarray, original_shape: Tuple[int, int]) -> List[Object]:
        """后处理输出 - 适配眼部7点检测"""
        objects = []
        
        # 确保输出形状正确
        output = output.flatten()
        
        # 如果输出正好是14个值（7个点的x,y坐标）
        if len(output) >= EYE_OUTPUT_SIZE:
            obj = Object()
            obj.conf = 1.0  # 如果模型不输出置信度，设置为1.0
            
            # 提取7个点的坐标
            scale_x = original_shape[1] / self.input_width
            scale_y = original_shape[0] / self.input_height
            
            for i in range(self.num_points):
                x_idx = i * 2
                y_idx = i * 2 + 1
                
                if y_idx < len(output):
                    # 假设输出是归一化坐标，需要反归一化
                    x = output[x_idx] * original_shape[1]
                    y = output[y_idx] * original_shape[0]
                    obj.points.append((x, y))
            
            if len(obj.points) == self.num_points:
                objects.append(obj)
        
        return objects
    
    def detect(self, img_path: str, target: List[OneLabel]) -> bool:
        """检测函数 - 基于C++的inference流程"""
        if not ONNXRUNTIME_AVAILABLE or not self.session:
            print("Model not loaded or ONNX Runtime not available")
            return False
        
        try:
            # 读取图像
            img = cv2.imread(img_path)
            if img is None:
                print(f"Failed to load image: {img_path}")
                return False
            
            original_shape = img.shape[:2]
            
            # 预处理
            input_data = self.preprocess_image_from_cv2(img)
            
            # 运行推理
            output = self.run_inference(input_data)
            if output is None:
                return False
            
            # 后处理
            objects = self.postprocess(output, original_shape)
            
            # 转换为OneLabel格式
            target.clear()
            for obj in objects:
                label = OneLabel(self.num_points)
                for point in obj.points:
                    label.set_point(QPointF(point[0], point[1]))
                if label.success():  # 确保7个点都设置成功
                    target.append(label)
            
            return len(target) > 0
            
        except Exception as e:
            print(f"Detection error: {e}")
            import traceback
            traceback.print_exc()
            return False