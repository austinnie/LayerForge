# gui/tk_app.py
"""
LayerForge Tkinter GUI（桌面版 - 支持多选 + AI 鉴赏）
用法: python gui/tk_app.py
"""
from __future__ import annotations
import os
import sys
import threading
import importlib.util
from pathlib import Path
from datetime import datetime
from tkinter import (
    Tk, ttk, StringVar, IntVar, BooleanVar,
    Frame, Label, Button, Text, Canvas, Scrollbar,
    END, BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y,
    DISABLED, NORMAL, filedialog, messagebox, EXTENDED,
)
import tkinter as tk 

# 🔥 核心修复：将项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# 🔥 严格使用 config.py 中实际存在的函数和变量
from config import list_available_loras
from core.loader import load_all_layers
from core.composer import PromptComposer
from core.generator import SDGenerator
from core.api_engines import create_api_engine
from core.appraiser import Appraiser

# 🔥 手动构建 API 配置字典（因为 config.py 中没有 load_config 函数）
def get_api_config() -> dict:
    try:
        from config import (
            TONGYI_API_KEY, TONGYI_MODEL,
            YIGE_API_KEY, YIGE_SECRET_KEY,
            HUNYUAN_SECRET_ID, HUNYUAN_SECRET_KEY,
            HF_API_TOKEN, HF_MODEL,
            POLLINATIONS_MODEL, FREEAPI_MODEL,
            AGNES_API_KEY, AGNES_BASE_URL, 
            AGNES_IMAGE_MODEL, AGNES_TEXT_MODEL,
            AGNES_VIDEO_MODEL, AGNES_VISION_MODEL
        )
        return {
            "TONGYI_API_KEY": TONGYI_API_KEY, "TONGYI_MODEL": TONGYI_MODEL,
            "YIGE_API_KEY": YIGE_API_KEY, "YIGE_SECRET_KEY": YIGE_SECRET_KEY,
            "HUNYUAN_SECRET_ID": HUNYUAN_SECRET_ID, "HUNYUAN_SECRET_KEY": HUNYUAN_SECRET_KEY,
            "HF_API_TOKEN": HF_API_TOKEN, "HF_MODEL": HF_MODEL,
            "POLLINATIONS_MODEL": POLLINATIONS_MODEL, "FREEAPI_MODEL": FREEAPI_MODEL,
            "AGNES_API_KEY": AGNES_API_KEY, "AGNES_BASE_URL": AGNES_BASE_URL,
            "AGNES_IMAGE_MODEL": AGNES_IMAGE_MODEL, "AGNES_TEXT_MODEL": AGNES_TEXT_MODEL,
            "AGNES_VIDEO_MODEL": AGNES_VIDEO_MODEL, "AGNES_VISION_MODEL": AGNES_VISION_MODEL,
        }
    except ImportError:
        # 兜底方案：直接从环境变量读取
        return {
            "AGNES_API_KEY": os.getenv("AGNES_API_KEY", ""),
            "AGNES_BASE_URL": os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1"),
            "AGNES_IMAGE_MODEL": os.getenv("AGNES_IMAGE_MODEL", "agnes-image-2.1-flash"),
            "AGNES_TEXT_MODEL": os.getenv("AGNES_TEXT_MODEL", "agnes-text-2.1-flash"),
            "AGNES_VIDEO_MODEL": os.getenv("AGNES_VIDEO_MODEL", "agnes-video-2.1-flash"),
            "AGNES_VISION_MODEL": os.getenv("AGNES_VISION_MODEL", "agnes-vision-2.1-flash"),
            "HF_API_TOKEN": os.getenv("HF_API_TOKEN", ""), "HF_MODEL": os.getenv("HF_MODEL", "sdxl"),
            "POLLINATIONS_MODEL": os.getenv("POLLINATIONS_MODEL", "flux"),
            "FREEAPI_MODEL": os.getenv("FREEAPI_MODEL", "grok-imagine-image-lite"),
        }

ENGINES = ["agnes", "pollinations", "tongyi", "yige", "hunyuan", "huggingface", "freeapi", "local_sd"]

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

class LayerForgeApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("LayerForge · 6层结构化 AI 生图工具")
        self.root.geometry("1200x800")
        
        self._presets = list_available_presets()
        self._loras = list_available_loras()
        self._preview_img = None
        
        self._build_ui()

    def _build_ui(self):
        left = ttk.Frame(self.root, width=320)
        left.pack(side=LEFT, fill=Y, padx=10, pady=10)
        left.pack_propagate(False)

        Label(left, text="预设风格 (按住 Ctrl/Shift 多选)", anchor="w").pack(fill=X, pady=(10, 2))
        preset_frame = ttk.Frame(left)
        preset_frame.pack(fill=X)
        preset_scroll = Scrollbar(preset_frame, orient="vertical")
        preset_scroll.pack(side=RIGHT, fill=Y)
        self.list_presets = tk.Listbox(preset_frame, selectmode=EXTENDED, height=8, yscrollcommand=preset_scroll.set)
        self.list_presets.pack(side=LEFT, fill=BOTH, expand=True)
        preset_scroll.config(command=self.list_presets.yview)
        for p in self._presets:
            self.list_presets.insert(END, p)
        if self._presets: self.list_presets.selection_set(0)

        Label(left, text="API 引擎", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_engine = StringVar(value="agnes")
        ttk.Combobox(left, textvariable=self.var_engine, values=ENGINES, state="readonly").pack(fill=X)

        Label(left, text="LoRA 模型 (可选)", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_lora = StringVar(value="None")
        lora_names = ["None"] + [l['name'] for l in self._loras]
        ttk.Combobox(left, textvariable=self.var_lora, values=lora_names, state="readonly").pack(fill=X)

        Label(left, text="生成数量", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_count = IntVar(value=1)
        ttk.Spinbox(left, from_=1, to=10, textvariable=self.var_count).pack(fill=X)

        Label(left, text="功能开关", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_appraise = BooleanVar(value=True)
        ttk.Checkbutton(left, text="生成后 AI 自动鉴赏 (BLIP)", variable=self.var_appraise).pack(anchor="w")

        self.btn_run = Button(left, text=" 开始生成", command=self._on_run, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.btn_run.pack(fill=X, pady=20)
        Button(left, text="📁 打开输出目录", command=lambda: os.startfile(PROJECT_ROOT / "output")).pack(fill=X)

        right = ttk.Frame(self.root)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        preview_frame = ttk.LabelFrame(right, text="图片预览")
        preview_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        self.canvas = Canvas(preview_frame, bg="#f0f0f0")
        self.canvas.pack(fill=BOTH, expand=True)
        
        log_frame = ttk.LabelFrame(right, text="执行日志 & AI 鉴赏")
        log_frame.pack(fill=BOTH, expand=False)
        self.log_text = Text(log_frame, height=12, font=("Consolas", 10))
        self.log_text.pack(fill=BOTH, expand=True)

    def _log(self, msg):
        self.log_text.insert(END, msg + "\n")
        self.log_text.see(END)
        self.root.update_idletasks()

    def _on_run(self):
        selected_presets = [self.list_presets.get(i) for i in self.list_presets.curselection()]
        if not selected_presets:
            messagebox.showwarning("提示", "请至少选择一个预设！")
            return

        params = {
            "presets": selected_presets,
            "engine": self.var_engine.get(),
            "lora": self.var_lora.get() if self.var_lora.get() != "None" else None,
            "count": self.var_count.get(),
            "appraise": self.var_appraise.get(),
        }

        self.btn_run.config(state=DISABLED, text="⏳ 生成中...")
        self.log_text.delete("1.0", END)
        self._log(f" 任务开始: 预设={params['presets']}, 引擎={params['engine']}")
        
        threading.Thread(target=self._worker, args=(params,), daemon=True).start()

    def _worker(self, params):
        try:
            self._log("📚 加载 6 层提示词架构...")
            layers = load_all_layers("layers")
            composer = PromptComposer(layers)

            # 🔥 使用正确的配置获取方式
            config = get_api_config()
            
            if params["lora"]:
                self._log(f" 挂载 LoRA: {params['lora']}")

            engine_name = params["engine"]
            if engine_name == "local_sd":
                from config import MODEL_PATH
                engine = SDGenerator(MODEL_PATH)
            else:
                engine = create_api_engine(engine_name, config)

            total = len(params["presets"]) * params["count"]
            idx = 0
            for preset_name in params["presets"]:
                for _ in range(params["count"]):
                    idx += 1
                    self._log(f"\n[{idx}/{total}] 生成预设: {preset_name}")
                    
                    preset_data = load_preset(preset_name)
                    if preset_data:
                        composer.apply_preset(preset_data.get("layers", {}))
                    
                    prompt = composer.compose_random()
                    self._log(f"   Prompt: {prompt[:60]}...")

                    image = engine.generate_single(prompt=prompt)
                    
                    out_dir = PROJECT_ROOT / "output"
                    out_dir.mkdir(exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_path = out_dir / f"lf_{preset_name}_{ts}.png"
                    image.save(out_path)
                    self._log(f"   ✅ 保存: {out_path.name}")

                    self.root.after(0, self._show_image, str(out_path))

                    if params["appraise"]:
                        self._log("   🧠 AI 鉴赏中 (BLIP)...")
                        try:
                            appraiser = Appraiser()
                            caption = appraiser.appraise(image)
                            self._log(f"   💬 点评: {caption}")
                        except Exception as e:
                            self._log(f"   ⚠️ 鉴赏失败: {e}")

            self._log("\n 全部任务完成！")
        except Exception as e:
            self._log(f"❌ 严重错误: {e}")
        finally:
            self.btn_run.config(state=NORMAL, text=" 开始生成")

    def _show_image(self, path: str):
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            cw = self.canvas.winfo_width() or 400
            ch = self.canvas.winfo_height() or 400
            img.thumbnail((cw, ch))
            self._preview_img = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(cw//2, ch//2, image=self._preview_img, anchor="center")
        except Exception as e:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = LayerForgeApp(root)
    root.mainloop()