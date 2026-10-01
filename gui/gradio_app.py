# gui/gradio_app.py
import gradio as gr
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.prompt_builder import PromptBuilder
from core.composer import PromptComposer
from core.loader import load_all_layers
from core.api_engines import create_api_engine
from config import load_config, list_available_presets, load_preset

def generate_image(preset_name, engine_name):
    try:
        # 加载预设
        preset_data = load_preset(preset_name)
        if not preset_data:
            return None, "❌ 预设不存在"
        
        # 组合 Prompt
        layers = load_all_layers("layers")
        composer = PromptComposer(layers)
        composer.apply_preset(preset_data["layers"])
        prompt = composer.compose_random()
        
        # 生成
        config = load_config()
        engine = create_api_engine(engine_name, config)
        image = engine.generate_single(prompt=prompt)
        
        return image, f"✅ 生成成功\nPrompt: {prompt[:100]}..."
    except Exception as e:
        return None, f"❌ 错误: {str(e)}"

# 构建界面
presets = list_available_presets()

with gr.Blocks(title="LayerForge Gradio") as demo:
    gr.Markdown("# 🎨 LayerForge Web GUI")
    
    with gr.Row():
        with gr.Column():
            preset_dropdown = gr.Dropdown(choices=presets, label="选择预设", value=presets[0] if presets else None)
            engine_dropdown = gr.Dropdown(choices=[ "agnes", "pollinations","huggingface"], label="API 引擎", value="pollinations")
            btn = gr.Button("🚀 生成图片", variant="primary")
        
        with gr.Column():
            image_output = gr.Image(label="生成结果", type="pil")
            log_output = gr.Textbox(label="日志", lines=5)
    
    btn.click(
        fn=generate_image,
        inputs=[preset_dropdown, engine_dropdown],
        outputs=[image_output, log_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7868)