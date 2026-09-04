# config.py
"""LayerForge 全局配置"""

import os
import json
import time
from pathlib import Path
from typing import Optional

MODEL_CONFIG_FILE = Path(__file__).parent / ".model_config"
LORA_CONFIG_FILE = Path(__file__).parent / ".lora_config"
CACHE_FILE = Path(__file__).parent / ".cache.json"

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


def list_available_models(use_cache: bool = True, force_refresh: bool = False) -> list:
    """列出所有可用的模型文件（带缓存）"""
    if force_refresh:
        set_cache("models", None)

    if use_cache and not force_refresh:
        cached = get_cache("models")
        if cached is not None:
            if validate_cache_paths(cached, "path"):
                return cached
            else:
                print("   🔄 缓存中的模型文件已被删除，重新扫描...")

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

    if not found:
        print("\n❌ 未找到任何模型文件！")
        print("   请检查以下目录是否存在模型文件:")
        for drive in drives:
            print(f"   - {drive}/SD_OpenVINO/models/sd-v1-5/")
            print(f"   - {drive}/SD_OpenVINO/models/sdxl/")
        return []

    set_cache("models", found)
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

    save_model_path(target["path"])
    print(f"✅ 默认模型已切换为: {target['name']}")
    print(f"   📁 {target['path']}")
    print(f"   📊 类型: {target['type']} | 大小: {target['size']} GB")
    return True


# ==================== LoRA 管理 ====================

def get_lora_dirs() -> list:
    """动态生成 LoRA 搜索路径"""
    drives = ["D:", "E:", "F:", "G:"]
    lora_subdirs = ["sd15-lora", "sdxl-lora"]
    base_paths = [
        "{drive}/SD_OpenVINO/models/{sub}",
        "{drive}/models/{sub}",
        "./models/{sub}",
    ]

    dirs = []
    for drive in drives:
        for base in base_paths:
            for sub in lora_subdirs:
                if base.startswith("./"):
                    dirs.append(base.format(sub=sub))
                else:
                    dirs.append(base.format(drive=drive, sub=sub))

    unique_dirs = []
    seen = set()
    for d in dirs:
        if d not in seen:
            seen.add(d)
            if os.path.exists(d):
                unique_dirs.append(d)
                print(f"   📁 找到 LoRA 目录: {d}")

    return unique_dirs

LORA_DIRS = get_lora_dirs()


def parse_lora_spec(spec: str) -> tuple:
    """解析 LoRA 规格: 'name@0.8' 或 'path@0.8'"""
    if '@' in spec:
        path_or_name, weight_str = spec.rsplit('@', 1)
        try:
            weight = float(weight_str)
        except:
            weight = 0.8
        return path_or_name.strip(), weight
    return spec.strip(), 0.8


def find_lora_file(name_or_path: str, model_type: str = None) -> str:
    """在标准目录中查找 LoRA 文件"""
    if os.path.exists(name_or_path):
        return name_or_path

    name_lower = name_or_path.lower()

    for lora_dir in LORA_DIRS:
        if not os.path.exists(lora_dir):
            continue

        if model_type:
            if model_type == "sd15" and "sdxl" in lora_dir.lower():
                continue
            if model_type == "sdxl" and "sd15" in lora_dir.lower():
                continue

        for ext in [".safetensors", ".ckpt", ".pt"]:
            for filepath in Path(lora_dir).glob(f"*{ext}"):
                if name_lower in filepath.stem.lower():
                    return str(filepath)
    return None


def list_available_loras(use_cache: bool = True, force_refresh: bool = False) -> list:
    """列出所有可用的 LoRA 文件（带缓存）"""
    if force_refresh:
        set_cache("loras", None)

    if use_cache and not force_refresh:
        cached = get_cache("loras")
        if cached is not None:
            if validate_cache_paths(cached, "path"):
                return cached
            else:
                print("   🔄 缓存中的 LoRA 文件已被删除，重新扫描...")

    found = []
    seen_names = set()

    for lora_dir in get_lora_dirs():
        if not os.path.exists(lora_dir):
            continue
        for ext in [".safetensors", ".ckpt", ".pt"]:
            for filepath in Path(lora_dir).glob(f"*{ext}"):
                name = filepath.stem
                if name in seen_names:
                    continue
                seen_names.add(name)
                size_mb = filepath.stat().st_size / (1024**2)
                model_type = "SDXL" if "sdxl" in str(filepath) else "SD1.5"
                found.append({
                    "name": name,
                    "path": str(filepath).replace("\\", "/"),
                    "size": round(size_mb, 2),
                    "type": model_type,
                })
    found.sort(key=lambda x: x["name"])

    if not found:
        print("\n❌ 未找到任何 LoRA 文件！")
        print("   请检查以下目录:")
        for d in get_lora_dirs():
            print(f"   - {d}")
        return []

    set_cache("loras", found)
    return found


def resolve_loras(lora_specs: list, model_type: str = None) -> list:
    """解析 LoRA 规格列表，返回完整的 LoRA 信息"""
    if not lora_specs:
        return []

    result = []
    for spec in lora_specs:
        name_or_path, weight = parse_lora_spec(spec)
        lora_path = find_lora_file(name_or_path, model_type)
        if lora_path:
            result.append({
                "path": lora_path,
                "weight": weight,
                "name": Path(lora_path).stem,
            })
        else:
            print(f"   ⚠️ 未找到 LoRA: {name_or_path}")

    return result


def get_saved_lora() -> Optional[str]:
    """从 .lora_config 读取上次保存的 LoRA"""
    if LORA_CONFIG_FILE.exists():
        try:
            return LORA_CONFIG_FILE.read_text(encoding="utf-8").strip()
        except:
            pass
    return None


def save_lora(lora_spec: str):
    """保存 LoRA 到 .lora_config"""
    LORA_CONFIG_FILE.write_text(lora_spec, encoding="utf-8")


# ==================== 缓存管理 ====================

def get_cache(key: str):
    """
    读取缓存（永不过期，只验证文件是否存在）
    返回: 缓存数据，如果无效返回 None
    """
    if not CACHE_FILE.exists():
        return None

    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if key not in data:
            return None
        return data[key]
    except:
        return None


def set_cache(key: str, value):
    """写入缓存"""
    data = {}
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    data[key] = value
    data[f"{key}_time"] = time.time()
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def clear_cache():
    """清除缓存"""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        return True
    return False


def validate_cache_paths(cached_list: list, path_key: str = "path") -> bool:
    """
    验证缓存中的文件路径是否都有效
    返回: True 全部有效, False 有文件被删除
    """
    if not cached_list:
        return False
    for item in cached_list:
        path = item.get(path_key)
        if path and not os.path.exists(path):
            return False
    return True


# ==================== 模型路径 ====================
MODEL_PATH = find_model_path()

# 如果自动检测失败，手动指定（取消注释并修改）：
# if MODEL_PATH is None:
#     MODEL_PATH = r"D:/SD_OpenVINO/models/sd-v1-5/anytimeRealistic_v10.safetensors"

MODEL_TYPE = detect_model_type(MODEL_PATH) if MODEL_PATH else "sd15"
MAX_TOKENS = 77 if MODEL_TYPE == "sd15" else 154

# ==================== 其他配置 ====================
OUTPUT_DIR = "./output"
DEFAULT_STEPS = 15
DEFAULT_CFG = 7.5
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 768
DEFAULT_NEGATIVE = "worst quality, low quality, ugly, deformed, blurry, bad anatomy"

# ==================== 后处理配置 ====================
ENABLE_POSTPROCESS = True           # 总开关
POSTPROCESS_MODE = "full"           # clean / realistic / full
# - clean: 仅清除元数据 + 转 JPG
# - realistic: 清除元数据 + 真实感效果
# - full: 全部

# ==================== 完整相机预设列表（31 个） ====================
# 在 config.py 中设置 REALISTIC_CAMERA = "预设名称"

## ---- Sony 系列 (6个) ----
REALISTIC_CAMERA = "sony_a7iv"      # Sony α7 IV
#REALISTIC_CAMERA = "sony_a7iii"     # Sony α7 III
#REALISTIC_CAMERA = "sony_a1"        # Sony α1
#REALISTIC_CAMERA = "sony_a7rv"      # Sony α7R V
#REALISTIC_CAMERA = "sony_a9iii"     # Sony α9 III
#REALISTIC_CAMERA = "sony_a6700"     # Sony α6700
#
## ---- Canon 系列 (5个) ----
#REALISTIC_CAMERA = "canon_r5"       # Canon EOS R5
#REALISTIC_CAMERA = "canon_r6"       # Canon EOS R6
#REALISTIC_CAMERA = "canon_r3"       # Canon EOS R3
#REALISTIC_CAMERA = "canon_r6ii"     # Canon EOS R6 Mark II
#REALISTIC_CAMERA = "canon_r8"       # Canon EOS R8
#
## ---- Nikon 系列 (4个) ----
#REALISTIC_CAMERA = "nikon_z8"       # Nikon Z 8
#REALISTIC_CAMERA = "nikon_z9"       # Nikon Z 9
#REALISTIC_CAMERA = "nikon_zf"       # Nikon Z f
#REALISTIC_CAMERA = "nikon_z6iii"    # Nikon Z6 III
#
## ---- Fujifilm 系列 (4个) ----
#REALISTIC_CAMERA = "fuji_x100v"     # Fujifilm X100V
#REALISTIC_CAMERA = "fuji_xh2s"      # Fujifilm X-H2S
#REALISTIC_CAMERA = "fuji_xt5"       # Fujifilm X-T5
#REALISTIC_CAMERA = "fuji_gfx100ii"  # Fujifilm GFX 100 II
#
## ---- Panasonic 系列 (2个) ----
#REALISTIC_CAMERA = "lumix_s5ii"     # Panasonic Lumix S5 II
#REALISTIC_CAMERA = "lumix_gh6"      # Panasonic Lumix GH6
#
## ---- Leica 系列 (2个) ----
#REALISTIC_CAMERA = "leica_m11"      # Leica M11
#REALISTIC_CAMERA = "leica_q3"       # Leica Q3
#
## ---- Hasselblad 系列 (1个) ----
#REALISTIC_CAMERA = "hasselblad_x2d" # Hasselblad X2D 100C
#
## ---- 手机系列 (6个) ----
#REALISTIC_CAMERA = "iphone_15"      # Apple iPhone 15 Pro Max
#REALISTIC_CAMERA = "iphone_16"      # Apple iPhone 16 Pro Max
#REALISTIC_CAMERA = "pixel_8"        # Google Pixel 8 Pro
#REALISTIC_CAMERA = "pixel_9"        # Google Pixel 9 Pro XL
#REALISTIC_CAMERA = "samsung_s24u"   # Samsung Galaxy S24 Ultra
#REALISTIC_CAMERA = "samsung_s24u"   # Samsung Galaxy S24 Ultra

REALISTIC_STRENGTH = "medium"       # light / medium / strong
REALISTIC_NOISE = True              # 是否添加噪点
INJECT_EXIF = True                  # 是否注入 EXIF
JPG_QUALITY = 92                    # JPG 质量


# ==================== Ollama 配置 ====================
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_TEMPERATURE = 0.7
OLLAMA_MAX_TOKENS = 200
OLLAMA_DYNAMIC_PROMPT_ENABLED = True

# ==================== AI 图像鉴赏配置 ====================
AI_APPRECIATION_ENGINE = "llm"   # blip / llm / prompt
# - blip: 仅使用 BLIP 生成描述
# - llm: BLIP + Ollama 润色（推荐）
# - prompt: 仅返回原始提示词

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
    "list_available_loras",
    "resolve_loras",
    "clear_cache",
    "get_saved_lora",
    "save_lora",
    "parse_lora_spec",
    "find_lora_file",
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
    "OLLAMA_TEMPERATURE",
    "OLLAMA_MAX_TOKENS",
    "OLLAMA_DYNAMIC_PROMPT_ENABLED",    
]