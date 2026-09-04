# utils/watermark.py
"""水印检测与去除工具"""

import os
import cv2
import numpy as np
from PIL import Image


def remove_watermark(image_path: str, output_path: str = None) -> Image.Image:
    """
    检测并去除图片水印
    
    参数:
        image_path: 输入图片路径
        output_path: 输出路径（可选，默认覆盖原图）
    
    返回:
        PIL Image 对象
    """
    print("\n[AI预处理] 检测并去除图片水印...")
    
    try:
        # 读取图片
        with open(image_path, 'rb') as f:
            img_bytes = np.frombuffer(f.read(), np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            # 降级使用 PIL
            pil_img = Image.open(image_path).convert('RGB')
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            if img is None:
                raise ValueError("无法读取图片")
    except Exception as e:
        print(f"⚠️ 读取图片失败，跳过水印检测: {e}")
        return Image.open(image_path).convert('RGB')
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 检测白色/亮色区域（水印常见特征）
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    white_pixel_ratio = np.sum(mask > 0) / mask.size
    
    # 如果白色区域比例异常（0.01~0.2 之间可能是水印）
    if white_pixel_ratio < 0.01 or white_pixel_ratio > 0.2:
        print("✅ 未检测到明显水印")
        return Image.open(image_path).convert('RGB')
    
    print("⚠️ 检测到水印，正在使用 OpenCV 修复去除...")
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    print("✅ 水印去除完成！")
    
    # 保存结果
    if output_path is None:
        output_path = image_path
    
    result_img = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    result_img.save(output_path, quality=95)
    
    return result_img


def has_watermark(image_path: str) -> bool:
    """
    检测图片是否包含水印
    
    参数:
        image_path: 图片路径
    
    返回:
        是否包含水印
    """
    try:
        with open(image_path, 'rb') as f:
            img_bytes = np.frombuffer(f.read(), np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            return False
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
        
        white_pixel_ratio = np.sum(mask > 0) / mask.size
        return 0.01 <= white_pixel_ratio <= 0.2
        
    except Exception as e:
        print(f"⚠️ 水印检测失败: {e}")
        return False