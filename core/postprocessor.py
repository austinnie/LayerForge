# core/postprocessor.py
"""统一后处理模块"""

import os
from pathlib import Path
from utils.imagemeta_cleaner import smart_clean_image
from utils.photo_realistic import make_photo_realistic
from utils.exif_injector import inject_exif
from config import (
    ENABLE_POSTPROCESS,
    POSTPROCESS_MODE,
    REALISTIC_CAMERA,
    REALISTIC_STRENGTH,
    REALISTIC_NOISE,
    INJECT_EXIF,
    JPG_QUALITY,
)


def postprocess_image(image_path: str, is_sketch: bool = False) -> str:
    """
    统一后处理入口
    
    参数:
        image_path: 输入图片路径
        is_sketch: 是否为素描风格（素描不添加真实感效果）
    
    返回:
        处理后的图片路径
    """
    if not ENABLE_POSTPROCESS:
        return image_path
    
    if not os.path.exists(image_path):
        print(f"   ⚠️ 图片不存在，跳过后处理: {image_path}")
        return image_path
    
    result_path = image_path
    mode = POSTPROCESS_MODE
    
    print("   📷 后处理中...")
    
    try:
        # 1. 清除元数据 + 转 JPG（所有模式都执行）
        result_path = smart_clean_image(
            result_path,
            method='jpg',
            jpg_quality=JPG_QUALITY
        )
        print(f"      ✅ 元数据清除完成 -> JPG")
        
        # 2. 照片真实化（非素描 + full 或 realistic 模式）
        if not is_sketch and mode in ["full", "realistic"]:
            result_path = make_photo_realistic(
                result_path,
                result_path,
                camera=REALISTIC_CAMERA,
                strength=REALISTIC_STRENGTH,
                inject_exif_data=INJECT_EXIF,
                add_noise_flag=REALISTIC_NOISE
            )
            print(f"      ✅ 照片真实化完成")
        
        # 3. EXIF 注入（如果上面的步骤没有注入或者需要额外注入）
        if INJECT_EXIF and mode != "clean":
            result_path = inject_exif(
                result_path,
                result_path,
                camera=REALISTIC_CAMERA,
                randomize=True
            )
            print(f"      ✅ EXIF 注入完成")
        
        return result_path
        
    except Exception as e:
        print(f"   ⚠️ 后处理失败: {e}")
        return image_path