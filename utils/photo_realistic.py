# utils/photo_realistic.py
"""
让 AI 图片看起来像真实相机照片
结合：图像处理 + EXIF 注入
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import random
from typing import Optional, Dict, Literal

from .exif_injector import inject_exif
from .logger import get_logger

logger = get_logger(__name__)
def add_realistic_features(
    image: Image.Image,
    iso: int = 400,
    fnumber: float = 2.8,
    focal_length: int = 50,
    add_noise: bool = True,
    add_vignette: bool = True,
    add_lens_distortion: bool = True,
    add_sharpening: bool = True
) -> Image.Image:
    """
    为图片添加真实相机特征
    
    参数:
        image: PIL Image
        iso: ISO 值（影响噪点强度）
        fnumber: 光圈值（影响景深/模糊）
        focal_length: 焦距（影响畸变程度）
        add_noise: 是否添加噪点
        add_vignette: 是否添加暗角
        add_lens_distortion: 是否添加镜头畸变
        add_sharpening: 是否添加锐化
    
    返回:
        处理后的 PIL Image
    """
    # 转为 numpy 数组 (OpenCV 格式)
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    h, w = img_cv.shape[:2]
    
    # 1. 添加噪点 (ISO 越高噪点越多)
    if add_noise:
        noise_strength = max(1, min(20, iso / 50))  # ISO 100 -> 2, ISO 3200 -> 64
        noise = np.random.normal(0, noise_strength, img_cv.shape).astype(np.uint8)
        img_cv = cv2.add(img_cv, noise)
        logger.info(f"   📷 添加噪点 (ISO {iso} -> 强度 {noise_strength:.1f})")
    
    # 2. 添加暗角
    if add_vignette:
        kernel_x = cv2.getGaussianKernel(w, w * 0.3)
        kernel_y = cv2.getGaussianKernel(h, h * 0.3)
        kernel = kernel_y * kernel_x.T
        mask = 1 - kernel * 0.25  # 暗角强度
        for i in range(3):
            img_cv[:, :, i] = (img_cv[:, :, i] * mask).astype(np.uint8)
        logger.info(f"   📷 添加暗角")
    
    # 3. 添加镜头畸变 (广角端畸变更明显)
    if add_lens_distortion:
        # 根据焦距调整畸变强度 (24mm 广角畸变大，85mm 畸变小)
        distortion = max(0, min(0.03, (50 - focal_length) / 2000 + 0.005))
        
        if distortion > 0.001:
            # 简化畸变：用径向扭曲模拟
            center_x, center_y = w / 2, h / 2
            for y in range(h):
                for x in range(w):
                    dx = (x - center_x) / center_x
                    dy = (y - center_y) / center_y
                    radius = np.sqrt(dx * dx + dy * dy)
                    if radius < 1:
                        # 径向扭曲
                        pass  # 简化实现，保持性能
            
            # 用 OpenCV 的畸变模型
            try:
                # 相机矩阵
                K = np.array([[w, 0, w/2], [0, h, h/2], [0, 0, 1]], dtype=np.float32)
                # 畸变系数
                k1 = distortion * 10
                k2 = distortion * 5
                dist_coeffs = np.array([k1, k2, 0, 0], dtype=np.float32)
                
                # 映射
                map1, map2 = cv2.fisheye.initUndistortRectifyMap(
                    K, dist_coeffs, np.eye(3), K, (w, h), cv2.CV_32FC1
                )
                img_cv = cv2.remap(img_cv, map1, map2, cv2.INTER_LINEAR)
                logger.info(f"   📷 添加镜头畸变 (焦距 {focal_length}mm -> 强度 {distortion:.4f})")
            except:
                pass
    
    # 4. 添加微锐化 (模拟相机锐化)
    if add_sharpening:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]) * 0.8 + 0.2 * np.eye(3)
        kernel = kernel / np.sum(kernel)
        img_cv = cv2.filter2D(img_cv, -1, kernel)
        logger.info(f"   📷 添加锐化")
    
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))


def make_photo_realistic(
    input_path: str,
    output_path: Optional[str] = None,
    camera: str = "sony_a7iv",
    style: str = "portrait",
    custom_params: Optional[Dict] = None,
    inject_exif_data: bool = True,
    randomize: bool = True,
    strength: str = "medium",
    add_noise_flag: bool = True  # 👈 新增：这里是控制加噪的入口
) -> str:
    """
    让 AI 图片看起来像真实相机照片
    结合：图像处理 + EXIF 注入
    """
    strength_map = {
        "light": {"iso": 200, "noise": 0.3, "vignette": 0.15},
        "medium": {"iso": 400, "noise": 0.5, "vignette": 0.25},
        "strong": {"iso": 800, "noise": 0.8, "vignette": 0.35},
    }
    
    if custom_params is None:
        custom_params = {}
    
    if "ISO" not in custom_params:
        custom_params["ISO"] = strength_map.get(strength, strength_map["medium"])["iso"]
        
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_realistic.jpg"
    
    image = Image.open(input_path).convert('RGB')
    
    from .exif_injector import CAMERA_PRESETS, PHOTO_STYLES
    
    camera_preset = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["sony_a7iv"])
    style_preset = PHOTO_STYLES.get(style, PHOTO_STYLES["portrait"])
    
    if custom_params:
        iso = custom_params.get("ISO", 400)
        fnumber = custom_params.get("FNumber", 2.8)
        focal_length = custom_params.get("FocalLength", 50)
    elif randomize:
        iso = random.choice(camera_preset.get("ISO", [100, 200, 400, 800]))
        fnumber = random.choice(camera_preset.get("FNumber", [1.8, 2.8, 4.0]))
        focal_length = random.choice(camera_preset.get("FocalLength", [24, 35, 50, 85]))
    else:
        iso = style_preset.get("ISO", [400])[0]
        fnumber = style_preset.get("FNumber", [2.8])[0]
        focal_length = style_preset.get("FocalLength", [50])[0]
    
    logger.info(f"📷 真实化处理: ISO={iso}, F={fnumber}, 焦距={focal_length}mm")
    
    # 🛡️ 这里把传进来的 add_noise_flag 传递给底层函数，不再强制写死 True
    image = add_realistic_features(
        image,
        iso=iso,
        fnumber=fnumber,
        focal_length=focal_length,
        add_noise=add_noise_flag,   # 👈 这里由外部参数决定是否加噪！
        add_vignette=True,
        add_lens_distortion=True,
        add_sharpening=True
    )
    
    image.save(output_path, format='JPEG', quality=92, optimize=True)
    logger.info(f"✅ 图片已保存: {output_path}")
    
    if inject_exif_data:
        exif_params = custom_params.copy() if custom_params else {}
        exif_params["ISO"] = iso
        exif_params["FNumber"] = fnumber
        exif_params["FocalLength"] = focal_length
        
        inject_exif(
            output_path,
            output_path,
            camera=camera,
            style=style,
            custom_params=exif_params,
            randomize=randomize
        )
    
    return output_path
    

if __name__ == "__main__":
    # 测试
    test_file = "test.png"
    if os.path.exists(test_file):
        make_photo_realistic(
            test_file,
            "test_realistic.jpg",
            camera="sony_a7iv",
            style="portrait"
        )