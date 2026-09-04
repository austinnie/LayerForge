# core/generator.py
import os
import torch
import random
from datetime import datetime
from pathlib import Path
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline


class SDGenerator:
    def __init__(self, model_path: str, device: str = "cpu", loras: list = None):
        """
        初始化 SD 生成器
        
        参数:
            model_path: 模型文件路径
            device: 运行设备 (cpu/cuda)
            loras: LoRA 列表 [{"path": "...", "weight": 0.8, "name": "..."}]
        """        
        self.device = device
        self.loras = loras or []
        
        print(f"📦 加载模型: {os.path.basename(model_path)}")
        self.pipe = self._load_pipeline(model_path)
        print("✅ 模型加载完成")
        
        # 加载 LoRA
        if self.loras:
            self._load_loras()

    def _load_pipeline(self, model_path: str):
        """加载 pipeline（自动识别 SD1.5 / SDXL）"""
        # 根据模型路径或文件名判断
        model_path_lower = model_path.lower()
        if "sdxl" in model_path_lower or "xl" in model_path_lower:
            from diffusers import StableDiffusionXLPipeline
            return StableDiffusionXLPipeline.from_single_file(
                model_path,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
        else:
            return StableDiffusionPipeline.from_single_file(
                model_path,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )

    def _load_loras(self):
        """加载所有 LoRA"""
        print(f"🔗 加载 {len(self.loras)} 个 LoRA...")
        
        for i, lora_info in enumerate(self.loras):
            path = lora_info.get("path")
            weight = lora_info.get("weight", 0.8)
            name = lora_info.get("name", os.path.basename(path))
            
            if not path or not os.path.exists(path):
                print(f"   ⚠️ LoRA 文件不存在: {path}")
                continue
            
            try:
                # 使用标准方法加载 LoRA
                self.pipe.load_lora_weights(path)
                # 设置权重（如果支持）
                if hasattr(self.pipe, "set_adapters"):
                    try:
                        self.pipe.set_adapters([name], adapter_weights=[weight])
                    except:
                        pass
                print(f"   ✅ LoRA {i+1}: {name} (权重: {weight})")
            except Exception as e:
                print(f"   ⚠️ LoRA 加载失败: {e}")
                
            
    def generate(self, prompt: str, negative: str, width: int, height: int, 
                 steps: int, cfg: float, seed: int = None) -> str:
        """生成图片"""
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        
        generator = torch.Generator(self.device).manual_seed(seed)
        
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=steps,
            guidance_scale=cfg,
            width=width,
            height=height,
            generator=generator,
        )
        
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/{timestamp}_{seed}.png"
        result.images[0].save(output_path)
        print(f"   ✅ 已保存: {output_path} (种子: {seed})")
        return output_path
