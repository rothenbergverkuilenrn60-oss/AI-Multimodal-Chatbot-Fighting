import base64,mimetypes
import os
from pathlib import Path

def encode_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at: {image_path}")
    
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None or not mime_type.startswith('image'):
        print(f"Warning: Could not determine mime type for {image_path}, assuming generic image.")
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to read or encode image: {e}")