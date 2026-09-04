# utils/exif_injector.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXIF 信息注入器 - 为图片添加相机元数据
让 AI 生成的图片看起来更像真实照片
"""

import os
import subprocess
import json
from PIL import Image
from datetime import datetime
import random
from typing import Optional, Dict, Literal


from .logger import get_logger

logger = get_logger(__name__)
# ============================================================
# 相机预设配置
# ============================================================
CAMERA_PRESETS = {
    # ==================== Sony 系列 ====================
    "sony_a7iv": {
        "Make": "Sony",
        "Model": "ILCE-7M4",
        "ISO": [100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 105],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FE 24-70mm F2.8 GM"
    },
    "sony_a7iii": {
        "Make": "Sony",
        "Model": "ILCE-7M3",
        "ISO": [100, 200, 400, 800, 1600, 3200],
        "FNumber": [1.8, 2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 135],
        "Software": "Adobe Photoshop Lightroom Classic",
        "LensModel": "FE 24-105mm F4 G OSS"
    },
    "sony_a1": {
        "Make": "Sony",
        "Model": "ILCE-1",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000"],
        "FocalLength": [24, 35, 50, 85, 135, 200],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FE 24-70mm F2.8 GM II"
    },
    "sony_a7rv": {
        "Make": "Sony",
        "Model": "ILCE-7RM5",
        "ISO": [100, 200, 400, 800, 1600, 3200],
        "FNumber": [1.8, 2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 135],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FE 24-70mm F2.8 GM"
    },
    "sony_a9iii": {
        "Make": "Sony",
        "Model": "ILCE-9M3",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400, 12800],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000", "1/8000"],
        "FocalLength": [24, 35, 50, 85, 135, 200, 400],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FE 24-70mm F2.8 GM II"
    },
    "sony_a6700": {
        "Make": "Sony",
        "Model": "ILCE-6700",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [16, 23, 35, 50, 85],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "E 16-55mm F2.8 G"
    },

    # ==================== Canon 系列 ====================
    "canon_r5": {
        "Make": "Canon",
        "Model": "Canon EOS R5",
        "ISO": [100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 100],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "RF 24-70mm F2.8 L IS USM"
    },
    "canon_r6": {
        "Make": "Canon",
        "Model": "Canon EOS R6",
        "ISO": [100, 200, 400, 800, 1600, 3200],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 135],
        "Software": "Adobe Photoshop Lightroom Classic",
        "LensModel": "RF 24-105mm F4 L IS USM"
    },
    "canon_r3": {
        "Make": "Canon",
        "Model": "Canon EOS R3",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400, 12800],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000", "1/8000"],
        "FocalLength": [24, 35, 50, 85, 135, 200, 400],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "RF 24-70mm F2.8 L IS USM"
    },
    "canon_r6ii": {
        "Make": "Canon",
        "Model": "Canon EOS R6 Mark II",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [24, 35, 50, 85, 135],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "RF 24-105mm F4 L IS USM"
    },
    "canon_r8": {
        "Make": "Canon",
        "Model": "Canon EOS R8",
        "ISO": [100, 200, 400, 800, 1600, 3200],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "RF 24-50mm F4.5-6.3 IS STM"
    },

    # ==================== Nikon 系列 ====================
    "nikon_z8": {
        "Make": "Nikon",
        "Model": "NIKON Z 8",
        "ISO": [64, 100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 105],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "NIKKOR Z 24-70mm f/2.8 S"
    },
    "nikon_z9": {
        "Make": "Nikon",
        "Model": "NIKON Z 9",
        "ISO": [64, 100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000", "1/8000"],
        "FocalLength": [24, 35, 50, 85, 135, 200, 400],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "NIKKOR Z 24-70mm f/2.8 S"
    },
    "nikon_zf": {
        "Make": "Nikon",
        "Model": "NIKON Z f",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "NIKKOR Z 40mm f/2 SE"
    },
    "nikon_z6iii": {
        "Make": "Nikon",
        "Model": "NIKON Z 6III",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [24, 35, 50, 85, 135],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "NIKKOR Z 24-70mm f/4 S"
    },

    # ==================== Fujifilm 系列 ====================
    "fuji_x100v": {
        "Make": "FUJIFILM",
        "Model": "X100V",
        "ISO": [160, 200, 400, 800, 1600, 3200],
        "FNumber": [2.0, 2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [23],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FUJINON 23mm F2.0"
    },
    "fuji_xh2s": {
        "Make": "FUJIFILM",
        "Model": "X-H2S",
        "ISO": [160, 200, 400, 800, 1600, 3200, 6400, 12800],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000"],
        "FocalLength": [16, 23, 33, 56, 90],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "XF 16-55mm F2.8 R LM WR"
    },
    "fuji_xt5": {
        "Make": "FUJIFILM",
        "Model": "X-T5",
        "ISO": [160, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [16, 23, 33, 56, 90],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "XF 16-80mm F4 R OIS WR"
    },
    "fuji_gfx100ii": {
        "Make": "FUJIFILM",
        "Model": "GFX 100 II",
        "ISO": [64, 100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [23, 32, 45, 63, 80, 110],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "GF 32-64mm F4 R LM WR"
    },

    # ==================== Panasonic 系列 ====================
    "lumix_s5ii": {
        "Make": "Panasonic",
        "Model": "DC-S5M2",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 105],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "LUMIX S 24-70mm F2.8"
    },
    "lumix_gh6": {
        "Make": "Panasonic",
        "Model": "DC-GH6",
        "ISO": [100, 200, 400, 800, 1600, 3200, 6400, 12800],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [12, 15, 25, 42.5, 75],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "LEICA DG 12-35mm F2.8"
    },

    # ==================== Leica 系列 ====================
    "leica_m11": {
        "Make": "Leica Camera AG",
        "Model": "LEICA M11",
        "ISO": [64, 100, 200, 400, 800, 1600, 3200, 6400, 12500, 25000, 50000],
        "FNumber": [1.4, 2.0, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [28, 35, 50, 75, 90],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "Summicron-M 35mm F2 ASPH"
    },
    "leica_q3": {
        "Make": "Leica Camera AG",
        "Model": "LEICA Q3",
        "ISO": [50, 100, 200, 400, 800, 1600, 3200, 6400, 12500, 25000],
        "FNumber": [1.7, 2.0, 2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [28],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "Summilux 28mm F1.7 ASPH"
    },

    # ==================== Hasselblad 系列 ====================
    "hasselblad_x2d": {
        "Make": "Hasselblad",
        "Model": "X2D 100C",
        "ISO": [64, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600],
        "FNumber": [2.8, 4.0, 5.6, 8.0, 11.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [21, 28, 38, 45, 55, 90, 135],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "XCD 38mm F2.5 V"
    },

    # ==================== 手机系列 ====================
    "iphone_15": {
        "Make": "Apple",
        "Model": "iPhone 15 Pro Max",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200],
        "FNumber": [1.78, 2.2, 2.8],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [24, 48, 77],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "iPhone 15 Pro Max back triple camera"
    },
    "iphone_16": {
        "Make": "Apple",
        "Model": "iPhone 16 Pro Max",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200, 250],
        "FNumber": [1.78, 2.2, 2.8],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000", "1/4000"],
        "FocalLength": [24, 48, 77, 120],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "iPhone 16 Pro Max back triple camera"
    },
    "pixel_8": {
        "Make": "Google",
        "Model": "Pixel 8 Pro",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200],
        "FNumber": [1.68, 2.8, 3.5],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [25, 48, 113],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "Pixel 8 Pro back camera"
    },
    "pixel_9": {
        "Make": "Google",
        "Model": "Pixel 9 Pro XL",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200, 250],
        "FNumber": [1.68, 2.2, 2.8, 3.5],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000", "1/4000"],
        "FocalLength": [24, 48, 113],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "Pixel 9 Pro XL back camera"
    },
    "samsung_s24u": {
        "Make": "Samsung",
        "Model": "Galaxy S24 Ultra",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200, 250, 320],
        "FNumber": [1.7, 2.2, 2.4, 3.4],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000", "1/4000"],
        "FocalLength": [24, 48, 70, 120, 230],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "Galaxy S24 Ultra quad camera"
    },
}

# 照片风格
PHOTO_STYLES = {
    "portrait": {"ISO": [100, 200], "FNumber": [1.8, 2.8], "FocalLength": [50, 85, 105]},
    "landscape": {"ISO": [64, 100], "FNumber": [5.6, 8.0, 11.0], "FocalLength": [24, 35, 50]},
    "street": {"ISO": [200, 400, 800], "FNumber": [2.8, 4.0, 5.6], "FocalLength": [24, 35, 50]},
    "sports": {"ISO": [800, 1600, 3200], "FNumber": [2.8, 4.0], "FocalLength": [70, 85, 135]},
    "night": {"ISO": [1600, 3200, 6400], "FNumber": [1.8, 2.8], "FocalLength": [24, 35, 50]},
    "macro": {"ISO": [100, 200], "FNumber": [2.8, 4.0], "FocalLength": [85, 105, 135]},
    "wedding": {"ISO": [200, 400, 800], "FNumber": [1.8, 2.8, 4.0], "FocalLength": [24, 35, 50, 85]}
}


# ============================================================
# 核心函数
# ============================================================
def inject_exif(
    input_path: str,
    output_path: Optional[str] = None,
    camera: str = "sony_a7iv",
    style: str = "portrait",
    custom_params: Optional[Dict] = None,
    randomize: bool = True,
    date_time: Optional[str] = None
) -> str:
    """
    为图片注入 EXIF 元数据
    
    参数:
        input_path: 输入图片路径
        output_path: 输出路径（可选）
        camera: 相机预设 (sony_a7iv, canon_r5, nikon_z8, fuji_x100v, iphone_15, pixel_8)
        style: 照片风格 (portrait, landscape, street, sports, night, macro, wedding)
        custom_params: 自定义参数 (覆盖预设)
        randomize: 是否随机生成参数
        date_time: 自定义拍摄时间 (格式: "2026:07:05 14:32:10")
    
    返回:
        输出路径
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_with_exif.jpg"
    
    # 获取相机预设
    camera_preset = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["sony_a7iv"])
    style_preset = PHOTO_STYLES.get(style, PHOTO_STYLES["portrait"])
    
    # 构建 EXIF 参数
    exif_params = {}
    
    # 基础信息
    exif_params["Make"] = camera_preset.get("Make", "Sony")
    exif_params["Model"] = camera_preset.get("Model", "ILCE-7M4")
    exif_params["Software"] = camera_preset.get("Software", "Adobe Photoshop Lightroom 6.0")
    
    # ISO
    if custom_params and "ISO" in custom_params:
        exif_params["ISO"] = custom_params["ISO"]
    elif randomize:
        iso_list = camera_preset.get("ISO", [100, 200, 400])
        exif_params["ISO"] = random.choice(iso_list)
    else:
        exif_params["ISO"] = style_preset.get("ISO", [200])[0]
    
    # FNumber
    if custom_params and "FNumber" in custom_params:
        exif_params["FNumber"] = custom_params["FNumber"]
    elif randomize:
        f_list = camera_preset.get("FNumber", [1.8, 2.8, 4.0])
        exif_params["FNumber"] = random.choice(f_list)
    else:
        exif_params["FNumber"] = style_preset.get("FNumber", [2.8])[0]
    
    # ExposureTime
    if custom_params and "ExposureTime" in custom_params:
        exif_params["ExposureTime"] = custom_params["ExposureTime"]
    elif randomize:
        et_list = camera_preset.get("ExposureTime", ["1/125", "1/250", "1/500"])
        exif_params["ExposureTime"] = random.choice(et_list)
    else:
        exif_params["ExposureTime"] = "1/250"
    
    # FocalLength
    if custom_params and "FocalLength" in custom_params:
        exif_params["FocalLength"] = custom_params["FocalLength"]
    elif randomize:
        fl_list = camera_preset.get("FocalLength", [35, 50, 85])
        exif_params["FocalLength"] = random.choice(fl_list)
    else:
        exif_params["FocalLength"] = style_preset.get("FocalLength", [50])[0]
    
    # LensModel
    exif_params["LensModel"] = camera_preset.get("LensModel", "")
    
    # DateTimeOriginal
    if date_time:
        exif_params["DateTimeOriginal"] = date_time
    else:
        # 随机生成最近 30 天内的日期
        days_ago = random.randint(0, 30)
        hours = random.randint(8, 20)
        minutes = random.randint(0, 59)
        seconds = random.randint(0, 59)
        dt = datetime.now().replace(
            hour=hours, minute=minutes, second=seconds
        ) - __import__('datetime').timedelta(days=days_ago)
        exif_params["DateTimeOriginal"] = dt.strftime("%Y:%m:%d %H:%M:%S")
    
    # 额外参数
    exif_params["Artist"] = custom_params.get("Artist", "Photographer") if custom_params else "Photographer"
    exif_params["Copyright"] = custom_params.get("Copyright", "") if custom_params else ""
    
    # ==================== 🔥 绝杀修复 ====================
    # 不用 "exiftool"，而是找到这个程序在本地的真实路径！绕过CMD通配符解析！
    import shutil
    import os
    
    # 在系统 PATH 中查找 exiftool.exe 的绝对物理路径
    exiftool_executable = shutil.which("exiftool")
    
    # 如果死活找不到，直接跳过注入
    if exiftool_executable is None:
        logger.info(f"⚠️ 系统 PATH 中找不到 exiftool，跳过 EXIF 注入")
        return output_path if output_path else input_path
        
    # 严格标准化路径，防止歧义
    normalized_input = os.path.normpath(input_path)
    
    # 构建最终命令（使用找到的绝对路径调用）
    cmd = f'"{exiftool_executable}" -overwrite_original'
    
    for key, value in exif_params.items():
        if value:
            cmd += f' -{key}="{value}"'
    cmd += f' "{normalized_input}"'
    # ====================================================
    
    # 执行命令
    try:
        # 直接运行命令，不给任何 shell 介入的机会
        result = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.info(f"⚠️ EXIF 注入失败: {result.stderr}")
            # 即使失败也把图复制过去，确保不丢文件
            if output_path != input_path:
                shutil.copy2(input_path, output_path)
            return output_path
        
        # 如果输出路径不同，重命名
        if output_path != input_path:
            shutil.move(input_path, output_path)
        
        logger.info(f"✅ EXIF 已注入: {output_path}")
        logger.info(f"   📷 相机: {exif_params['Make']} {exif_params['Model']}")
        logger.info(f"   ⚙️  ISO: {exif_params['ISO']}  FNumber: {exif_params['FNumber']}")
        logger.info(f"   📸 焦距: {exif_params['FocalLength']}mm  快门: {exif_params['ExposureTime']}")
        
        return output_path
        
    except subprocess.TimeoutExpired:
        logger.info(f"⚠️ ExifTool 超时")
        if output_path != input_path:
            shutil.copy2(input_path, output_path)
        return output_path
    except Exception as e:
        logger.info(f"⚠️ EXIF 注入异常: {e}")
        if output_path != input_path:
            shutil.copy2(input_path, output_path)
        return output_path


# ============================================================
# 批量注入
# ============================================================
def batch_inject_exif(
    input_dir: str,
    output_dir: Optional[str] = None,
    camera: str = "sony_a7iv",
    style: str = "portrait",
    randomize: bool = True,
    extensions: tuple = ('.png', '.jpg', '.jpeg')
) -> list:
    """
    批量注入 EXIF 信息
    
    参数:
        input_dir: 输入目录
        output_dir: 输出目录（可选）
        camera: 相机预设
        style: 照片风格
        randomize: 是否随机参数
        extensions: 处理的扩展名
    
    返回:
        处理后的文件路径列表
    """
    if output_dir is None:
        output_dir = os.path.join(input_dir, "with_exif")
    
    os.makedirs(output_dir, exist_ok=True)
    
    injected_files = []
    
    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in extensions:
            continue
        
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        try:
            result = inject_exif(input_path, output_path, camera, style, randomize)
            injected_files.append(result)
        except Exception as e:
            logger.info(f"❌ 注入失败: {filename} - {e}")
    
    logger.info(f"✅ 批量注入完成: {len(injected_files)} 个文件")
    return injected_files


# ============================================================
# 获取相机预设列表
# ============================================================
def get_camera_list() -> list:
    """获取所有相机预设名称"""
    return list(CAMERA_PRESETS.keys())


def get_style_list() -> list:
    """获取所有照片风格"""
    return list(PHOTO_STYLES.keys())


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EXIF 信息注入工具")
    parser.add_argument("input", help="输入图片或目录")
    parser.add_argument("-o", "--output", help="输出路径")
    parser.add_argument("-c", "--camera", default="sony_a7iv", 
                        choices=get_camera_list(), help="相机预设")
    parser.add_argument("-s", "--style", default="portrait",
                        choices=get_style_list(), help="照片风格")
    parser.add_argument("-b", "--batch", action="store_true", help="批量模式")
    parser.add_argument("--no-random", action="store_true", help="不随机化参数")
    parser.add_argument("--date", help="自定义拍摄时间 (YYYY:MM:DD HH:MM:SS)")
    
    args = parser.parse_args()
    
    if args.batch:
        batch_inject_exif(
            args.input, args.output, 
            args.camera, args.style, 
            not args.no_random
        )
    else:
        inject_exif(
            args.input, args.output,
            args.camera, args.style,
            not args.no_random,
            args.date
        )