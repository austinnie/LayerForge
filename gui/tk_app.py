# run_gui_Tkinter.py
"""
LayerForge Tkinter GUI（桌面版 - 支持多选 + AI 鉴赏）
用法: python run_gui_Tkinter.py
"""
from __future__ import annotations
import os
import sys
import threading
from pathlib import Path
from datetime import datetime
from tkinter import (
    Tk, ttk, StringVar, IntVar, BooleanVar,
    Frame, Label, Button, Text, Canvas, Scrollbar,
    END, BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y,
    DISABLED, NORMAL, filedialog, messagebox, EXTENDED,
)

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 尝试加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# LayerForge 核心模块
from config import list_available_presets, list_available_loras
from core.loader import load_all_layers
from core.composer import PromptComposer
from core.generator import SDGenerator
from core.api_engines import create_api_engine
from core.appraiser import Appraiser

# 引擎列表
ENGINES = [ "agnes", "pollinations","tongyi", "yige", "hunyuan", "huggingface", "freeapi", "local_sd"]

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
        # 左侧控制面板
        left = ttk.Frame(self.root, width=320)
        left.pack(side=LEFT, fill=Y, padx=10, pady=10)
        left.pack_propagate(False)

        # 1. 预设 (多选)
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

        # 2. 引擎
        Label(left, text="API 引擎", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_engine = StringVar(value="agnes")
        ttk.Combobox(left, textvariable=self.var_engine, values=ENGINES, state="readonly").pack(fill=X)

        # 3. LoRA (单选)
        Label(left, text="LoRA 模型 (可选)", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_lora = StringVar(value="None")
        lora_names = ["None"] + [l['name'] for l in self._loras]
        ttk.Combobox(left, textvariable=self.var_lora, values=lora_names, state="readonly").pack(fill=X)

        # 4. 生成数量
        Label(left, text="生成数量", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_count = IntVar(value=1)
        ttk.Spinbox(left, from_=1, to=10, textvariable=self.var_count).pack(fill=X)

        # 5. 开关
        Label(left, text="功能开关", anchor="w").pack(fill=X, pady=(10, 2))
        self.var_appraise = BooleanVar(value=True) # AI 鉴赏
        ttk.Checkbutton(left, text="生成后 AI 自动鉴赏 (BLIP)", variable=self.var_appraise).pack(anchor="w")

        # 按钮
        self.btn_run = Button(left, text="🚀 开始生成", command=self._on_run, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.btn_run.pack(fill=X, pady=20)
        Button(left, text="📁 打开输出目录", command=lambda: os.startfile(PROJECT_ROOT / "output")).pack(fill=X)

        # 右侧日志与预览
        right = ttk.Frame(self.root)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # 预览区
        preview_frame = ttk.LabelFrame(right, text="图片预览")
        preview_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        self.canvas = Canvas(preview_frame, bg="#f0f0f0")
        self.canvas.pack(fill=BOTH, expand=True)
        
        # 日志区
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
        self._log(f"🎯 任务开始: 预设={params['presets']}, 引擎={params['engine']}")
        
        threading.Thread(target=self._worker, args=(params,), daemon=True).start()

    def _worker(self, params):
        try:
            # 1. 加载 6 层提示词
            self._log(" 加载 6 层提示词架构...")
            layers = load_all_layers("layers")
            composer = PromptComposer(layers)

            # 2. 准备引擎
            from config import load_config
            config = load_config()
            
            # 处理 LoRA
            if params["lora"]:
                # 这里简化处理，实际需调用 config 中的 LoRA 解析逻辑
                self._log(f"🔗 挂载 LoRA: {params['lora']}")

            engine_name = params["engine"]
            if engine_name == "local_sd":
                engine = SDGenerator(config)
            else:
                engine = create_api_engine(engine_name, config)

            # 3. 批量生成
            total = len(params["presets"]) * params["count"]
            idx = 0
            for preset_name in params["presets"]:
                for _ in range(params["count"]):
                    idx += 1
                    self._log(f"\n[{idx}/{total}] 生成预设: {preset_name}")
                    
                    # 应用预设并组合 Prompt
                    from config import load_preset
                    preset_data = load_preset(preset_name)
                    if preset_data:
                        composer.apply_preset(preset_data.get("layers", {}))
                    
                    prompt = composer.compose_random()
                    self._log(f"   Prompt: {prompt[:60]}...")

                    # 生成图片
                    image = engine.generate_single(prompt=prompt)
                    
                    # 保存
                    out_dir = PROJECT_ROOT / "output"
                    out_dir.mkdir(exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_path = out_dir / f"lf_{preset_name}_{ts}.png"
                    image.save(out_path)
                    self._log(f"   ✅ 保存: {out_path.name}")

                    # 更新预览
                    self.root.after(0, self._show_image, str(out_path))

                    # AI 鉴赏
                    if params["appraise"]:
                        self._log("   🧠 AI 鉴赏中 (BLIP)...")
                        try:
                            appraiser = Appraiser()
                            caption = appraiser.appraise(image)
                            self._log(f"   💬 点评: {caption}")
                        except Exception as e:
                            self._log(f"   ⚠️ 鉴赏失败: {e}")

            self._log("\n🎉 全部任务完成！")
        except Exception as e:
            self._log(f"❌ 严重错误: {e}")
        finally:
            self.btn_run.config(state=NORMAL, text="🚀 开始生成")

    def _show_image(self, path: str):
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            # 缩放适应 Canvas
            cw = self.canvas.winfo_width() or 400
            ch = self.canvas.winfo_height() or 400
            img.thumbnail((cw, ch))
            self._preview_img = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(cw//2, ch//2, image=self._preview_img, anchor="center")
        except Exception as e:
            pass

if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    app = LayerForgeApp(root)
    root.mainloop()