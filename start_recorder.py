"""
启动脚本示例
展示如何使用不同版本的录制器
"""

# 启动标准版录制器
import subprocess
import sys
import os

def start_enhanced():
    """启动增强版录制器"""
    script_path = os.path.join(os.path.dirname(__file__), "recorder_app_new.py")
    subprocess.run([sys.executable, script_path, "--enhanced"])

if __name__ == "__main__":
    print("PaperTracker 录制器启动选项:")

    start_enhanced()
