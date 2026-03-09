# utils/image_utils.py
import base64,mimetypes
import os
from pathlib import Path

def encode_image(image_path: str) -> str:
    # 1. 路径检查
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at: {image_path}")
    
    # 2. 类型检查
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None or not mime_type.startswith('image'):
        # 警告：但在某些无后缀的临时文件中可能识别失败，这里仅做 log 或放行，视具体情况而定
        print(f"Warning: Could not determine mime type for {image_path}, assuming generic image.")

    # 3. 读取并编码
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to read or encode image: {e}")