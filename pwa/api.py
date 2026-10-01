# pwa/api.py
"""
LayerForge PWA 后端 API (修复版)
"""
import importlib.util
import io
import base64
import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 1. 设置项目路径
PWA_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PWA_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 2. 兜底配置加载
def load_config() -> dict:
    try:
        from config import (
            AGNES_API_KEY, AGNES_BASE_URL, AGNES_IMAGE_MODEL,
            HF_API_TOKEN, HF_MODEL, TONGYI_API_KEY, TONGYI_MODEL,
            YIGE_API_KEY, YIGE_SECRET_KEY, HUNYUAN_SECRET_ID, HUNYUAN_SECRET_KEY,
            POLLINATIONS_MODEL, FREEAPI_MODEL
        )
        return {
            "AGNES_API_KEY": AGNES_API_KEY, "AGNES_BASE_URL": AGNES_BASE_URL,
            "AGNES_IMAGE_MODEL": AGNES_IMAGE_MODEL, "HF_API_TOKEN": HF_API_TOKEN,
            "HF_MODEL": HF_MODEL, "TONGYI_API_KEY": TONGYI_API_KEY,
            "TONGYI_MODEL": TONGYI_MODEL, "YIGE_API_KEY": YIGE_API_KEY,
            "YIGE_SECRET_KEY": YIGE_SECRET_KEY, "HUNYUAN_SECRET_ID": HUNYUAN_SECRET_ID,
            "HUNYUAN_SECRET_KEY": HUNYUAN_SECRET_KEY, "POLLINATIONS_MODEL": POLLINATIONS_MODEL,
            "FREEAPI_MODEL": FREEAPI_MODEL,
        }
    except ImportError:
        return {
            "AGNES_API_KEY": os.getenv("AGNES_API_KEY", ""),
            "AGNES_BASE_URL": os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1"),
            "AGNES_IMAGE_MODEL": os.getenv("AGNES_IMAGE_MODEL", "agnes-image-2.1-flash"),
            "HF_API_TOKEN": os.getenv("HF_API_TOKEN", ""), "HF_MODEL": os.getenv("HF_MODEL", "sdxl"),
            "TONGYI_API_KEY": os.getenv("TONGYI_API_KEY", ""), "TONGYI_MODEL": os.getenv("TONGYI_MODEL", "wanx-v1"),
            "YIGE_API_KEY": os.getenv("YIGE_API_KEY", ""), "YIGE_SECRET_KEY": os.getenv("YIGE_SECRET_KEY", ""),
            "HUNYUAN_SECRET_ID": os.getenv("HUNYUAN_SECRET_ID", ""), "HUNYUAN_SECRET_KEY": os.getenv("HUNYUAN_SECRET_KEY", ""),
            "POLLINATIONS_MODEL": os.getenv("POLLINATIONS_MODEL", "flux"),
            "FREEAPI_MODEL": os.getenv("FREEAPI_MODEL", "grok-imagine-image-lite"),
        }

from core.api_engines import create_api_engine
from core.loader import load_all_layers
from core.composer import PromptComposer

app = FastAPI(title="LayerForge PWA API")

# 3. 挂载静态文件
STATIC_DIR = PWA_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def read_root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "index.html not found"}

# 4. 预设加载逻辑 (🔥 核心修复：使用双下划线 __init__.py)
def list_available_presets() -> list:
    preset_dir = PROJECT_ROOT / "presets"
    print(f"[DEBUG] 正在扫描预设目录: {preset_dir}") # 增加调试日志
    
    if not preset_dir.exists():
        print("[ERROR] 预设目录不存在！")
        return []
    
    presets = [
        f.stem for f in preset_dir.glob("*.py")
        # 🔥 修复：必须是双下划线 __init__.py
        if f.name not in ("__init__.py", "index.py")
    ]
    print(f"[DEBUG] 找到 {len(presets)} 个预设: {presets}")
    return presets

def load_preset(preset_name: str) -> dict:
    preset_path = PROJECT_ROOT / "presets" / f"{preset_name}.py"
    if not preset_path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(preset_name, preset_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "PRESET"):
            return module.PRESET
    except Exception as e:
        print(f"[ERROR] 加载预设 {preset_name} 失败: {e}")
    return None

# 5. API 路由
@app.get("/api/presets")
async def get_presets():
    return list_available_presets()

class GenerateRequest(BaseModel):
    preset: str
    engine: str = "agnes"
    appraise: bool = False

@app.post("/api/generate")
async def generate_image(req: GenerateRequest):
    try:
        # 检查 Agnes Key
        config = load_config()
        if req.engine == "agnes" and not config.get("AGNES_API_KEY"):
            raise HTTPException(status_code=500, detail="❌ 未找到 AGNES_API_KEY，请检查根目录 .env 文件")

        # 加载预设
        preset_data = load_preset(req.preset)
        if not preset_data:
            raise HTTPException(status_code=400, detail=f"找不到预设: {req.preset}")
        
        # ✅ 使用 LayerForge 正确的 PromptComposer
        layers_dir = str(PROJECT_ROOT / "layers")
        layers = load_all_layers(layers_dir)
        composer = PromptComposer(layers)
        composer.apply_preset(preset_data.get("layers", {}))
        prompt = composer.compose_random()
        
        # 生成图片
        engine = create_api_engine(req.engine, config)
        image = engine.generate_single(prompt=prompt)
        
        # 转为 Base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "status": "success",
            "prompt": prompt,
            "image": f"data:image/png;base64,{img_b64}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))