#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立版本地 SD 生图脚本 (适配你的本地环境)
基础模型：DreamShaper_8
支持：6层提示词、预设、多LoRA叠加
"""

import os
import random
import argparse
from datetime import datetime
from pathlib import Path

# PyTorch & Diffusers
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

# ==================== 配置区 ====================
OUTPUT_DIR = "./outputs"
# 你的绝对路径（DreamShaper）
MODEL_PATH = "E:/SD_OpenVINO/models/sd-v1-5/DreamShaper_8_pruned.safetensors"

# 全局负面提示词
DEFAULT_NEGATIVE = "(worst quality, low quality:1.4), bad anatomy, bad hands, missing fingers, extra digits, deformed, blurry, text, watermark"

# ==================== 内置提示词层 (Layers) ====================
# 终极精简版：只保留核心动作/材质/画风，绝对不超 77 Token 上限
LAYERS = {
    "subject": [
        "cybernetic anime girl, long white hair, translucent silver skin, exposed gears, floating blades, blue eyes",
        "android girl, semi-transparent body, dual long blades, white grey palette",
        "white cyborg, glowing blue core, exposed joints, floating sharp weapons"
    ],
    "scene": [
        "industrial floor, grey background, studio lighting",
        "grey backdrop, soft fog"
    ],
    "style": [
        "translucent render, 3D CGI, octane",
        "3D render, metallic texture"
    ],
    "lighting": [
        "soft glow, diffused daylight",
        "cinematic lighting, cool tone"
    ],
    "view": [
        "eye-level shot, symmetric",
        "three-quarter view"
    ],
    "quality": [
        "8k, sharp focus, masterpiece",
        "4k, intricate details"
    ],
}

# ==================== 内置预设 (Presets) ====================
PRESETS = {
    "mecha_glow_v2": {
        "description": "白色半透明机甲少女，悬浮双刃，冷色调 (推荐)",
        "subject": LAYERS["subject"][0],
        "scene": LAYERS["scene"][0],
        "style": LAYERS["style"][0],
        "lighting": LAYERS["lighting"][0],
        "view": LAYERS["view"][0],
        "quality": LAYERS["quality"][0],
    },
    "mecha_sketch": {
        "description": "白模铅笔素描风机甲",
        "subject": "pencil sketch of anime girl, long white hair, mecha armor, grey shading",
        "scene": "white background",
        "style": "fine linework, 2D illustration",
        "lighting": "ethereal, soft",
        "view": "full body",
        "quality": "masterpiece",
    }
}

# ==================== 核心生成引擎 ====================
# ==================== 核心生成引擎 ====================
class LocalSDGenerator:
    def __init__(self, model_path, loras=None):
        print(f"🚀 正在加载本地模型: {Path(model_path).name}")
        print("    (如果模型较大，首次加载可能需要几分钟...)")
        
        # 检测设备
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        
        # 使用单文件加载（兼容 Safetensors）
        pipe = StableDiffusionPipeline.from_single_file(
            model_path, 
            torch_dtype=dtype, 
            safety_checker=None
        )
        
        # 使用更稳定的采样器
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe = pipe.to(device)
        
        if device == "cuda":
            pipe.enable_xformers_memory_efficient_attention()
            
        self.pipe = pipe
        self.device = device
        print(f"✅ 模型加载完成，运行设备: {device.upper()}")
        
        # ====== 手动加载多个 LoRA (借鉴 cli.py 的思路) ======
        if loras:
            print(f"🔗 正在手动加载 {len(loras)} 个 LoRA...")
            lora_weights = []
            for lora_name, weight in loras:
                lora_path = f"E:/SD_OpenVINO/models/sd15-lora/{lora_name}.safetensors"
                if os.path.exists(lora_path):
                    try:
                        # 1. 尝试标准的 diffusers 加载
                        self.pipe.load_lora_weights(lora_path, adapter_name=lora_name, use_safetensors=True)
                        lora_weights.append((lora_name, weight))
                        print(f"   ✅ 标准加载成功: {lora_name} @ {weight}")
                    except Exception as e:
                        print(f"   ⚠️ 标准加载失败: {e}")
                        print(f"   🔧 尝试手动加载 LoRA...")
                        try:
                            # 2. 手动加载：直接读取 safetensors 权重并注入
                            from safetensors.torch import load_file
                            import torch as pt
                            
                            # 读取权重
                            lora_state_dict = load_file(lora_path)
                            
                            # 注入 UNet
                            unet_lora_keys = {k.replace("lora_unet_", ""): v for k, v in lora_state_dict.items() if k.startswith("lora_unet_")}
                            if unet_lora_keys:
                                self.pipe.unet.load_state_dict(unet_lora_keys, strict=False)
                                print(f"         ✅ UNet LoRA 加载完成 ({len(unet_lora_keys)} 个权重)")
                            
                            # 注入 Text Encoder
                            te_lora_keys = {k.replace("lora_te_", ""): v for k, v in lora_state_dict.items() if k.startswith("lora_te_")}
                            if te_lora_keys:
                                self.pipe.text_encoder.load_state_dict(te_lora_keys, strict=False)
                                print(f"         ✅ Text Encoder LoRA 加载完成 ({len(te_lora_keys)} 个权重)")
                            
                            # 手动记录权重供后续使用（注意：手动注入无法动态调整权重，它是直接覆盖基础模型权重的）
                            lora_weights.append((lora_name, weight))
                            print(f"      ✅ LoRA 手动加载完成: {lora_name} (权重: {weight})")
                            
                        except Exception as e2:
                            print(f"   ❌ 手动加载也失败了: {e2}")
                else:
                    print(f"   ❌ 未找到 LoRA 文件: {lora_path}")
            
            # 统一设置权重 (仅对标准加载有效的 LoRA 生效)
            if lora_weights:
                adapter_names = [x[0] for x in lora_weights]
                weights = [x[1] for x in lora_weights]
                try:
                    self.pipe.set_adapters(adapter_names, adapter_weights=weights)
                except:
                    print("   ⚠️ 手动注入的 LoRA 无法通过 set_adapters 调整权重，已采用默认全量强度。")

    def generate(self, prompt, negative_prompt=DEFAULT_NEGATIVE, width=640, height=960, steps=30, cfg=7.5, seed=None):
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        print(f"🎲 使用种子 (Seed): {seed}")
        
        generator = torch.Generator(device=self.device).manual_seed(seed)
        print("🎨 开始生成图片...")
        
        image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=generator,
        ).images[0]
        
        # ⭐ 保存图片和提示词
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(OUTPUT_DIR, f"mecha_{timestamp}.png")
        image.save(path)
        
        # ⭐ 保存同名 .txt 文件
        txt_path = path.replace('.png', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"【提示词】: {prompt}\n")
            f.write(f"【负面提示词】: {negative_prompt}\n")
            f.write(f"【种子】: {seed}\n")
            f.write(f"【尺寸】: {width}x{height}\n")
            f.write(f"【步数】: {steps}\n")
            f.write(f"【CFG】: {cfg}\n")
            f.write(f"【模型】: {Path(MODEL_PATH).name}\n")
            f.write(f"【生成时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"   ✅ 已保存至: {path}")
        print(f"   📝 提示词已保存: {txt_path}")
        return image
    
# ==================== 提示词合成器 ====================
class PromptComposer:
    def __init__(self, layers):
        self.layers = layers
        self.LAYER_ORDER = list(layers.keys())
        
    def compose_by_index(self, index):
        prompt_parts = []
        for i, key in enumerate(self.LAYER_ORDER):
            options = self.layers[key]
            selected = options[index % len(options)]
            prompt_parts.append(selected)
        return ", ".join(prompt_parts)
    
    def compose_random(self):
        prompt_parts = []
        for key in self.LAYER_ORDER:
            options = self.layers[key]
            selected = random.choice(options)
            prompt_parts.append(selected)
        return ", ".join(prompt_parts)

    def apply_preset(self, preset_data):
        for key in self.LAYER_ORDER:
            if key in preset_data and preset_data[key]:
                self.layers[key] = [preset_data[key]]

# ==================== 主程序 ====================
def main():
    parser = argparse.ArgumentParser(description="本地SD生图工具 (DreamShaper + Mecha LoRA 特化版)")
    parser.add_argument("--preset", type=str, default="mecha_glow_v2", help="使用预设: mecha_glow_v2, mecha_sketch")
    parser.add_argument("--prompt", type=str, help="直接输入完整提示词")
    parser.add_argument("--count", type=int, default=1, help="生成数量")
    parser.add_argument("--steps", type=int, default=30, help="采样步数")
    parser.add_argument("--cfg", type=float, default=7.0, help="CFG Scale (建议5.5-7.5)")
    parser.add_argument("--seed", type=int, default=None, help="固定种子")
    parser.add_argument("--random", action="store_true", help="随机组合6层提示词")
    parser.add_argument("--list-presets", action="store_true", help="列出可用预设")
    parser.add_argument("--width", type=int, default=640, help="宽度 (SD1.5建议640)")
    parser.add_argument("--height", type=int, default=960, help="高度 (SD1.5建议960)")
    
    # 新增：支持多个 LoRA 加载
    parser.add_argument("--lora", action="append", help="加载 LoRA (格式: name@weight, 例如: MechaGirlFigure_v1@0.8)")

    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.list_presets:
        print("可用预设:")
        for name, data in PRESETS.items():
            print(f"  - {name}: {data['description']}")
        return

    # 解析多个 LoRA
    loras = []
    if args.lora:
        for item in args.lora:
            if "@" in item:
                name, weight = item.split("@")
                loras.append((name.strip(), float(weight)))
            else:
                loras.append((item.strip(), 0.7)) # 默认 0.7 权重

    # 构建提示词
    composer = PromptComposer(LAYERS)
    prompt = None

    if args.prompt:
        prompt = args.prompt
    elif args.preset in PRESETS:
        preset_data = PRESETS[args.preset]
        composer.apply_preset(preset_data)
        if args.random:
            prompt = composer.compose_random()
        else:
            prompt = composer.compose_by_index(0)
    else:
        print("❌ 未知预设！请使用 --list-presets 查看")
        return

    print(f"✅ 提示词: {prompt}\n")

    # 初始化引擎并生成
    gen = LocalSDGenerator(MODEL_PATH, loras)
    
    for i in range(args.count):
        print(f"\n[生成 {i+1}/{args.count}]")
        try:
            img = gen.generate(
                prompt=prompt, 
                width=args.width, 
                height=args.height, 
                steps=args.steps, 
                cfg=args.cfg, 
                seed=args.seed + i if args.seed else None
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(OUTPUT_DIR, f"mecha_{timestamp}_{i}.png")
            img.save(path)
            print(f"   ✅ 已保存至: {path}")
        except Exception as e:
            print(f"   ❌ 生成出错: {e}")

if __name__ == "__main__":
    main()



# #使用完美预设    
# python local_mecha_gen.py --preset mecha_glow_v2 --count 4
# #使用自带的其他预设
# python local_mecha_gen.py --preset mecha_sketch --count 2
# # 每次运行随机组合不同层
# python local_mecha_gen.py --random 
# #直接输入你自己的完整英文提示词：
# python local_mecha_gen.py --prompt "1girl, mecha, white armor, floating swords, 8k..."


# # 完美版：应用预设 + 挂载最契合的机甲LoRA
# python local_mecha_gen.py --preset mecha_glow_v2 --lora "MechaGirlFigure_v1@0.8" --lora "AMechaSSS@0.7" --count 4
# 
# # 素描版：应用预设 + 挂载轻微细节增强
# python local_mecha_gen.py --preset mecha_sketch --lora "MechaGirlFigure_v1@0.6" --count 2
# 
# # 直接输入完整提示词 + 挂载机甲LoRA
# python local_mecha_gen.py --prompt "1girl, mecha, white armor, floating swords, 8k..." --lora "MechaGirl_v1@0.8" --count 1


# python local_mecha_gen.py --preset mecha_glow_v2 --lora "MechaGirlFigure_v1@0.8" --lora "AMechaSSS@0.7" --count 4
# 命令解析：
# 
# --preset mecha_glow_v2：调用了半透明白甲+悬浮双刃的提示词组合。
# 
# --lora "MechaGirlFigure_v1@0.8"：加载了最贴合机甲少女的 LoRA（权重0.8）。
# 
# --lora "AMechaSSS@0.7"：加载了增加精密机械质感（齿轮、线缆）的 LoRA（权重0.7）。
# 
# --count 4：生成4张让你挑选。
    