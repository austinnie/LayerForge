# utils/imagemeta_cleaner.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片元数据清理工具 - 清除 AI 生成痕迹
清除 PNG tEXt 块 | EXIF 数据 | 转 JPG 去除所有元数据
默认不开启，需要时手动调用
"""

import os
import subprocess
import shutil
from PIL import Image
from typing import Optional, Literal, List


from .logger import get_logger

logger = get_logger(__name__)
# ============================================================
# 方法1: 重新保存 PNG（清除 tEXt 块）
# ============================================================
def clean_png_metadata(input_path: str, output_path: Optional[str] = None) -> str:
    """
    清除 PNG 所有元数据（tEXt 块、EXIF 等）
    
    参数:
        input_path: 输入图片路径
        output_path: 输出路径（可选）
    
    返回:
        输出路径
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"
    
    img = Image.open(input_path)
    # 重新保存，不保留任何元数据
    img.save(output_path, format='PNG', optimize=True)
    logger.info(f"✅ [方法1] PNG 元数据已清除: {output_path}")
    return output_path


# ============================================================
# 方法2: 转 JPG（元数据自动丢失）
# ============================================================
def convert_to_jpg(input_path: str, output_path: Optional[str] = None, quality: int = 92) -> str:
    """
    将图片转换为 JPG（所有元数据自动丢失）
    
    参数:
        input_path: 输入图片路径
        output_path: 输出路径（可选）
        quality: JPG 质量 (1-100)，推荐 88-92
    
    返回:
        输出路径
    """
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}.jpg"
    
    img = Image.open(input_path).convert('RGB')
    img.save(output_path, format='JPEG', quality=quality, optimize=True)
    logger.info(f"✅ [方法2] 已转换为 JPG，元数据已清除: {output_path}")
    return output_path


# ============================================================
# 方法3: ExifTool 删除所有元数据
# ============================================================
def remove_with_exiftool(input_path: str, output_path: Optional[str] = None) -> str:
    """
    使用 ExifTool 删除所有元数据（需要安装 exiftool）
    
    参数:
        input_path: 输入图片路径
        output_path: 输出路径（可选）
    
    返回:
        输出路径
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"
    
    try:
        # 检查 exiftool 是否可用
        result = subprocess.run(
            "exiftool -ver",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            logger.info(f"⚠️ ExifTool 未安装，降级到方法1")
            return clean_png_metadata(input_path, output_path)
        
        # 删除所有元数据
        cmd = f'exiftool -all= -overwrite_original "{input_path}"'
        subprocess.run(cmd, shell=True, check=True)
        
        # 如果输出路径不同，复制文件
        if output_path != input_path:
            shutil.copy2(input_path, output_path)
        
        logger.info(f"✅ [方法3] ExifTool 已清除元数据: {output_path}")
        return output_path
        
    except subprocess.TimeoutExpired:
        logger.info(f"⚠️ ExifTool 超时，降级到方法1")
        return clean_png_metadata(input_path, output_path)
    except Exception as e:
        logger.info(f"⚠️ ExifTool 失败: {e}，降级到方法1")
        return clean_png_metadata(input_path, output_path)


# ============================================================
# 方法4: 完整清理（组合方法）
# ============================================================
def remove_all_metadata(input_path: str, output_path: Optional[str] = None) -> str:
    """
    彻底清除所有元数据（组合方法）
    优先使用 ExifTool，失败则降级
    
    参数:
        input_path: 输入图片路径
        output_path: 输出路径（可选）
    
    返回:
        输出路径
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"
    
    try:
        return remove_with_exiftool(input_path, output_path)
    except:
        return clean_png_metadata(input_path, output_path)


# ============================================================
# 智能清理 - 自动选择最佳方法
# ============================================================
def smart_clean_image(
    input_path: str,
    output_path: Optional[str] = None,
    method: Literal['png', 'jpg', 'exiftool', 'auto'] = 'auto',
    jpg_quality: int = 92
) -> str:
    """
    智能清理图片元数据
    
    参数:
        input_path: 输入图片路径
        output_path: 输出路径（可选）
        method: 清理方法
            - 'png': 重新保存 PNG（清除 tEXt）
            - 'jpg': 转 JPG（最彻底）
            - 'exiftool': 使用 ExifTool
            - 'auto': 自动选择（PNG 用 PNG 清理，其他转 JPG）
        jpg_quality: JPG 质量 (1-100)
    
    返回:
        输出路径
    """
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_clean.jpg"
    
    ext = os.path.splitext(input_path)[1].lower()
    
    if method == 'auto':
        if ext == '.png':
            return clean_png_metadata(input_path, output_path)
        else:
            return convert_to_jpg(input_path, output_path, jpg_quality)
    
    if method == 'png':
        return clean_png_metadata(input_path, output_path)
    
    if method == 'jpg':
        return convert_to_jpg(input_path, output_path, jpg_quality)
    
    if method == 'exiftool':
        return remove_with_exiftool(input_path, output_path)
    
    return clean_png_metadata(input_path, output_path)


# ============================================================
# 批量清理
# ============================================================
def batch_clean_images(
    input_dir: str,
    output_dir: Optional[str] = None,
    method: Literal['png', 'jpg', 'exiftool', 'auto'] = 'auto',
    extensions: tuple = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
) -> List[str]:
    """
    批量清理目录下所有图片的元数据
    
    参数:
        input_dir: 输入目录
        output_dir: 输出目录（可选）
        method: 清理方法
        extensions: 处理的扩展名
    
    返回:
        清理后的文件路径列表
    """
    if output_dir is None:
        output_dir = os.path.join(input_dir, "cleaned")
    
    os.makedirs(output_dir, exist_ok=True)
    
    cleaned_files = []
    
    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in extensions:
            continue
        
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        try:
            result = smart_clean_image(input_path, output_path, method)
            cleaned_files.append(result)
        except Exception as e:
            logger.info(f"❌ 清理失败: {filename} - {e}")
    
    logger.info(f"✅ 批量清理完成: {len(cleaned_files)} 个文件")
    return cleaned_files


# ============================================================
# 检查图片是否有元数据
# ============================================================
def has_metadata(input_path: str) -> bool:
    """
    检查图片是否包含元数据
    
    参数:
        input_path: 图片路径
    
    返回:
        是否包含元数据
    """
    try:
        from PIL import Image
        img = Image.open(input_path)
        
        # 检查 PNG tEXt 块
        if hasattr(img, 'text') and img.text:
            return True
        
        # 检查 EXIF
        if hasattr(img, '_getexif') and img._getexif():
            return True
        
        return False
    except:
        return False


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="图片元数据清理工具")
    parser.add_argument("input", help="输入图片或目录")
    parser.add_argument("-o", "--output", help="输出路径")
    parser.add_argument("-m", "--method", choices=['png', 'jpg', 'exiftool', 'auto'], 
                        default='jpg', help="清理方法")
    parser.add_argument("-q", "--quality", type=int, default=92, help="JPG 质量")
    parser.add_argument("-b", "--batch", action="store_true", help="批量模式")
    
    args = parser.parse_args()
    
    if args.batch:
        batch_clean_images(args.input, args.output, args.method)
    else:
        smart_clean_image(args.input, args.output, args.method, args.quality)