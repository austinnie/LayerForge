# gui/gradio_app.py
"""
LayerForge Gradio GUI 启动入口 (已修复：支持自动保存图片及元数据 + 图生图)
用法: python gui/gradio_app.py
"""
import sys
import os
import socket
import importlib.util
from pathlib import Path
from datetime import datetime
from PIL import Image  # 🔥 核心修复：必须导入 PIL.Image 才能处理参考图

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# LayerForge 核心模块
from config import list_available_loras
from core.loader import load_all_layers
from core.composer import PromptComposer
from core.api_engines import create_api_engine

def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

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

def get_api_config() -> dict:
    """手动构建 API 配置字典（适配 LayerForge config.py）"""
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

if __name__ == "__main__":
    import gradio as gr
    
    presets = list_available_presets()
    lan_ip = get_lan_ip()

    print()
    print("=" * 64)
    print("   🎨 LayerForge Gradio GUI")
    print("=" * 64)
    print(f"   🖥️ 本机访问:   http://127.0.0.1:7860")
    print(f"   📱 局域网访问: http://{lan_ip}:7860")
    print("=" * 64)
    print()


    def generate_image(preset_name, engine_name, ref_image_file):
        try:
            # 1. 加载预设与组合 Prompt
            preset_data = load_preset(preset_name)
            if not preset_data:
                return None, "❌ 预设不存在或格式错误"
            layers = load_all_layers("layers")
            composer = PromptComposer(layers)
            composer.apply_preset(preset_data.get("layers", {}))
            prompt = composer.compose_random()
            
            # 2. 准备引擎并生成
            config = get_api_config()
            engine = create_api_engine(engine_name, config)
            
            # 🔥 核心修复 1：安全提取 Gradio File 组件的路径
            ref_img_obj = None
            if ref_image_file and engine_name == "agnes":
                # 兼容 Gradio 不同版本返回的 File 对象类型
                file_path = ref_image_file.name if hasattr(ref_image_file, 'name') else ref_image_file
                ref_img_obj = Image.open(file_path).convert("RGB")
                print(f"📷 检测到参考图，切换为图生图模式")
                
            # 🔥 核心修复 2：根据引擎能力动态选择文生图或图生图
            if ref_img_obj and hasattr(engine, 'image_to_image'):
                image = engine.image_to_image(
                    prompt=prompt,
                    image=ref_img_obj,
                    strength=0.7
                )
            else:
                if ref_img_obj:
                    print("⚠️ 当前引擎不支持图生图，已切换为文生图模式")
                image = engine.generate_single(prompt=prompt)
                
            # 3. 【保留】保存图片到 output 目录
            out_dir = PROJECT_ROOT / "output"
            out_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_i2i" if ref_img_obj else ""
            filename = f"gradio_{preset_name}{suffix}_{timestamp}.png"
            save_path = out_dir / filename
            image.save(save_path, quality=95)
            print(f"💾 Gradio 图片已保存: {save_path}")
            
            # 4. 【保留】生成同名 .txt 元数据文件
            meta_path = save_path.with_suffix(".txt")
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(f"【模式】: {'Gradio Web (图生图)' if ref_img_obj else 'Gradio Web'}\n")
                f.write(f"【API】: {engine_name}\n")
                f.write(f"【预设】: {preset_name}\n")
                f.write(f"【提示词】: {prompt}\n")
                f.write(f"【尺寸】: {image.size[0]}x{image.size[1]}\n")
                f.write(f"【生成时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(f" 元数据已保存: {meta_path}")
            
            mode_desc = "(图生图)" if ref_img_obj else ""
            return image, f"✅ 生成成功并已保存 {mode_desc}\nPrompt: {prompt}"
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return None, f"❌ 错误: {str(e)}\n\n{tb}"

    with gr.Blocks(title="LayerForge Web GUI") as demo:
        gr.Markdown("# 🎨 LayerForge · 6层结构化 AI 生图工具")
        
        with gr.Row():
            with gr.Column():
                p_preset = gr.Dropdown(choices=presets, label="选择预设", value=presets[0] if presets else None)
                p_engine = gr.Dropdown(
                    choices=["agnes", "pollinations", "tongyi", "yige", "hunyuan", "huggingface", "freeapi"], 
                    label="API 引擎", value="agnes"
                )
                
                # 🔥 新增：参考图上传组件
                p_ref_image = gr.File(label="参考图 (仅 Agnes 引擎生效)", file_types=["image"])
                
                btn = gr.Button("🚀 生成图片", variant="primary")
            with gr.Column():
                img_out = gr.Image(label="生成结果", type="pil")
                log_out = gr.Textbox(label="执行日志", lines=5)
        
        btn.click(generate_image, inputs=[p_preset, p_engine, p_ref_image], outputs=[img_out, log_out])

    demo.launch(server_name="0.0.0.0", server_port=7860, inbrowser=True)