# pwa/api.py
"""
LayerForge PWA 后端 API (修复版：使用 LayerForge 核心 PromptComposer)
"""
import importlib.util
import io
import base64
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 1. 设置项目路径并加载 .env
PWA_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PWA_DIR.parent
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 2. 导入 LayerForge 核心模块
from core.loader import load_all_layers
from core.composer import PromptComposer
from core.api_engines import create_api_engine

# 3. 兜底配置加载 (适配 LayerForge config.py)
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

app = FastAPI(title="LayerForge PWA API")

# 4. 挂载静态文件
STATIC_DIR = PWA_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def read_root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "index.html not found"}

# 5. 预设加载逻辑
def list_available_presets() -> list:
    preset_dir = PROJECT_ROOT / "presets"
    if not preset_dir.exists():
        return []
    return [f.stem for f in preset_dir.glob("*.py") if f.name not in ("__init__.py", "index.py")]

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
    except Exception:
        pass
    return None

# 6. API 路由
@app.get("/api/presets")
async def get_presets():
    return list_available_presets()

class GenerateRequest(BaseModel):
    preset: str
    engine: str = "agnes"
    appraise: bool = False

@app.post("/api/generate")
async def generate_image(req: GenerateRequest):
    """生成图片并保存到 output 目录"""
    try:
        # 🔥 检查 Agnes Key
        config = load_config()
        if req.engine == "agnes" and not config.get("AGNES_API_KEY"):
            raise HTTPException(status_code=500, detail="❌ 未找到 AGNES_API_KEY，请检查根目录 .env 文件")

        #  加载预设
        preset_data = load_preset(req.preset)
        if not preset_data:
            raise HTTPException(status_code=400, detail=f"找不到预设: {req.preset}")
        
        # 🔥 使用 LayerForge 核心：加载 6 层 + 组合器
        layers_dir = str(PROJECT_ROOT / "layers")
        layers = load_all_layers(layers_dir)
        composer = PromptComposer(layers)
        
        # 应用预设层
        composer.apply_preset(preset_data.get("layers", {}))
        prompt = composer.compose_random()
        
        #  调用引擎生成
        engine = create_api_engine(req.engine, config)
        image = engine.generate_single(prompt=prompt)
        
        # 🔥 保存图片到 output 目录
        out_dir = PROJECT_ROOT / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pwa_{req.preset}_{timestamp}.png"
        save_path = out_dir / filename
        
        image.save(save_path, quality=95)
        print(f"💾 PWA 图片已保存: {save_path}")

        # 🔥 生成同名 .txt 元数据文件
        meta_path = save_path.with_suffix(".txt")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"【模式】: PWA Web\n")
            f.write(f"【API】: {req.engine}\n")
            f.write(f"【预设】: {req.preset}\n")
            f.write(f"【提示词】: {prompt}\n")
            f.write(f"【尺寸】: {image.size[0]}x{image.size[1]}\n")
            f.write(f"【生成时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f" 元数据已保存: {meta_path}")
        
        # 🔥 转为 Base64 返回给前端预览
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "status": "success",
            "prompt": prompt,
            "image": f"data:image/png;base64,{img_b64}",
            "saved_path": str(save_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"❌ PWA 生成异常:\n{tb}")
        raise HTTPException(status_code=500, detail=str(e))