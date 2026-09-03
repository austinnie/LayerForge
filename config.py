# config.py（正确版本，不会被修改）
"""LayerForge 全局配置"""

import os
from pathlib import Path

MODEL_CONFIG_FILE = Path(__file__).parent / ".model_config"

# ==================== 读取或写入模型路径 ====================

def get_saved_model_path():
    """从 .model_config 读取上次保存的模型路径"""
    if MODEL_CONFIG_FILE.exists():
        try:
            path = MODEL_CONFIG_FILE.read_text(encoding="utf-8").strip()
            if path and os.path.exists(path):
                return path
        except:
            pass
    return None

def save_model_path(path: str):
    """保存模型路径到 .model_config"""
    MODEL_CONFIG_FILE.write_text(path, encoding="utf-8")

# ==================== 自动检测模型路径 ====================

def find_model_path():
    # 1. 优先使用保存的模型路径
    saved = get_saved_model_path()
    if saved:
        print(f"✅ 使用已保存的模型: {saved}")
        return saved

    # 2. 否则自动检测
    model_names = [
        "anytimeRealistic_v10.safetensors",
        "henmixrealV10_henmixrealV10.safetensors",
        "sd-v1-5-tiny.safetensors",
        "aiiiiii01_v10.safetensors",
        "realisticmix_iiV12Version12.safetensors",
        "xlAsianRealisticMixNhiPNhChU_v10.safetensors",
        "perfectionAsianILXL_v10.safetensors",
    ]
    drives = ["D:", "E:", "F:", "G:"]
    model_dirs = [
        "{drive}/SD_OpenVINO/models/sd-v1-5",
        "{drive}/SD_OpenVINO/models/sdxl",
        "{drive}/models/sd-v1-5",
        "{drive}/models/sdxl",
    ]
    candidates = []
    for drive in drives:
        for base in model_dirs:
            base_path = base.format(drive=drive)
            if os.path.exists(base_path):
                for name in model_names:
                    candidates.append(os.path.join(base_path, name))
    for path in candidates:
        if os.path.exists(path):
            print(f"✅ 自动检测到模型: {path}")
            return path
    print("❌ 未找到任何 SD 模型文件！")
    return None


def list_available_models():
    drives = ["D:", "E:", "F:", "G:"]
    model_dirs = [
        "{drive}/SD_OpenVINO/models/sd-v1-5",
        "{drive}/SD_OpenVINO/models/sdxl",
        "{drive}/models/sd-v1-5",
        "{drive}/models/sdxl",
    ]
    found = []
    seen_names = set()
    extensions = [".safetensors", ".ckpt", ".pt"]
    for drive in drives:
        for base in model_dirs:
            base_path = base.format(drive=drive)
            if not os.path.exists(base_path):
                continue
            for ext in extensions:
                for filepath in Path(base_path).glob(f"*{ext}"):
                    name = filepath.name
                    if name in seen_names:
                        continue
                    seen_names.add(name)
                    size_gb = filepath.stat().st_size / (1024**3)
                    model_type = "SDXL" if "sdxl" in str(filepath) or "xl" in name.lower() else "SD1.5"
                    found.append({
                        "name": name,
                        "path": str(filepath).replace("\\", "/"),
                        "size": round(size_gb, 2),
                        "type": model_type,
                    })
    found.sort(key=lambda x: x["name"])
    return found

def detect_model_type(model_path: str) -> str:
    """检测模型类型：sd15 / sdxl"""
    model_path_lower = model_path.lower()
    if "sdxl" in model_path_lower or "xl" in model_path_lower:
        return "sdxl"
    return "sd15"
    
def set_default_model(model_name: str) -> bool:
    models = list_available_models()
    if not models:
        print("❌ 没有找到任何模型文件")
        return False

    target = None
    search = model_name.lower()
    for m in models:
        if search in m["name"].lower():
            target = m
            break

    if not target:
        print(f"❌ 未找到匹配的模型: {model_name}")
        print("   可用模型:")
        for m in models:
            print(f"   - {m['name']}")
        return False

    # ⭐ 保存到独立文件，不修改 config.py
    save_model_path(target["path"])

    print(f"✅ 默认模型已切换为: {target['name']}")
    print(f"   📁 {target['path']}")
    print(f"   📊 类型: {target['type']} | 大小: {target['size']} GB")
    return True


# ==================== 模型路径 ====================
MODEL_PATH = find_model_path()

# 如果自动检测失败，手动指定（取消注释并修改）：
# if MODEL_PATH is None:
#     MODEL_PATH = r"D:/SD_OpenVINO/models/sd-v1-5/anytimeRealistic_v10.safetensors"

# 在 MODEL_PATH 确定后自动检测
MODEL_TYPE = detect_model_type(MODEL_PATH) if MODEL_PATH else "sd15"
MAX_TOKENS = 77 if MODEL_TYPE == "sd15" else 154  # SDXL 可以更多

# ==================== 其他配置 ====================
OUTPUT_DIR = "./output"
DEFAULT_STEPS = 25
DEFAULT_CFG = 7.5
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 768
DEFAULT_NEGATIVE = "worst quality, low quality, ugly, deformed, blurry, bad anatomy"
ENABLE_POSTPROCESS = True

__all__ = [
    "MODEL_PATH",
    "OUTPUT_DIR",
    "DEFAULT_STEPS",
    "DEFAULT_CFG",
    "DEFAULT_WIDTH",
    "DEFAULT_HEIGHT",
    "DEFAULT_NEGATIVE",
    "ENABLE_POSTPROCESS",
    "find_model_path",
    "list_available_models",
    "set_default_model",
]