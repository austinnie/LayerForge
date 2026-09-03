# config.py
"""LayerForge 全局配置 - 自动检测多盘符模型路径"""

import os
from pathlib import Path

# ==================== 自动检测模型路径 ====================
def find_model_path():
    """
    自动在多个盘符和常见目录中查找 SD 模型
    支持 D 盘、E 盘、F 盘，支持 SD1.5 和 SDXL
    """
    # 候选模型文件名（按优先级排序）
    model_names = [
        "anytimeRealistic_v10.safetensors",
        "henmixrealV10_henmixrealV10.safetensors",
        "sd-v1-5-tiny.safetensors",
        "aiiiiii01_v10.safetensors",
        "realisticmix_iiV12Version12.safetensors",
        "xlAsianRealisticMixNhiPNhChU_v10.safetensors",  # SDXL
        "perfectionAsianILXL_v10.safetensors",           # SDXL
    ]
    
    # 候选基础目录（按盘符扩展）
    drives = ["D:", "E:", "F:", "G:"]
    model_dirs = [
        "{drive}/SD_OpenVINO/models/sd-v1-5",
        "{drive}/SD_OpenVINO/models/sdxl",
        "{drive}/models/sd-v1-5",
        "{drive}/models/sdxl",
    ]
    
    # 生成所有候选路径
    candidates = []
    for drive in drives:
        for base in model_dirs:
            base_path = base.format(drive=drive)
            if os.path.exists(base_path):
                for name in model_names:
                    candidates.append(os.path.join(base_path, name))
    
    # 查找第一个存在的文件
    for path in candidates:
        if os.path.exists(path):
            print(f"✅ 自动检测到模型: {path}")
            return path
    
    # 如果都没找到，给出明确的错误提示
    print("❌ 未找到任何 SD 模型文件！")
    print("请检查以下候选路径：")
    for path in candidates[:5]:  # 打印前几个供参考
        print(f"   - {path}")
    print("\n💡 你可以手动修改 config.py 中的 MODEL_PATH")
    return None

# ==================== 全局配置 ====================
MODEL_PATH = find_model_path()

if MODEL_PATH is None:
    # 如果自动检测失败，你可以在这里手动写死路径
    # 取消下面一行的注释，并填入你的实际路径
    # MODEL_PATH = r"D:/SD_OpenVINO/models/sd-v1-5/anytimeRealistic_v10.safetensors"
    raise FileNotFoundError("请检查 config.py 中的模型路径配置")

OUTPUT_DIR = "./output"
DEFAULT_STEPS = 25
DEFAULT_CFG = 7.5
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 768
DEFAULT_NEGATIVE = "worst quality, low quality, ugly, deformed, blurry, bad anatomy"
ENABLE_POSTPROCESS = True