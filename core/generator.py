# core/generator.py
import os
import torch
import random
from datetime import datetime
from diffusers import StableDiffusionPipeline

class SDGenerator:
    def __init__(self, model_path: str, device: str = "cpu"):
        self.device = device
        print(f"📦 加载模型: {os.path.basename(model_path)}")
        self.pipe = StableDiffusionPipeline.from_single_file(
            model_path,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
        )
        self.pipe.to(device)
        print("✅ 模型加载完成")
    def generate(self, prompt: str, negative: str, width: int, height: int, steps: int, cfg: float, seed: int = None) -> str:
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        generator = torch.Generator(self.device).manual_seed(seed)
        result = self.pipe(
            prompt=prompt, negative_prompt=negative,
            num_inference_steps=steps, guidance_scale=cfg,
            width=width, height=height, generator=generator,
        )
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/{timestamp}_{seed}.png"
        result.images[0].save(output_path)
        print(f"   ✅ 已保存: {output_path} (种子: {seed})")
        return output_path
