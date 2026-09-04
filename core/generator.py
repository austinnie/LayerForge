# core/generator.py

import os
import torch
import random
from datetime import datetime
from pathlib import Path
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline


class SDGenerator:
    def __init__(self, model_path: str, device: str = "cpu", loras: list = None):
        """初始化 SD 生成器"""
        self.device = device
        self.loras = loras or []
        
        print(f"📦 加载模型: {os.path.basename(model_path)}")
        self.pipe = self._load_pipeline(model_path)
        self.pipe.to(device)
        print("✅ 模型加载完成")
        
        if self.loras:
            self._load_loras()

    def _load_pipeline(self, model_path: str):
        """加载 pipeline（自动识别 SD1.5 / SDXL）"""
        model_path_lower = model_path.lower()
        if "sdxl" in model_path_lower or "xl" in model_path_lower:
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
                self.pipe.load_lora_weights(path)
                if hasattr(self.pipe, "set_adapters"):
                    try:
                        self.pipe.set_adapters([name], adapter_weights=[weight])
                    except:
                        pass
                print(f"   ✅ LoRA {i+1}: {name} (权重: {weight})")
            except Exception as e:
                print(f"   ⚠️ LoRA 加载失败: {e}")

    def _prepare_image(self, image_path: str, target_width: int = None, target_height: int = None):
        """
        加载并预处理参考图
        返回: PIL Image
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"参考图不存在: {image_path}")
        
        image = Image.open(image_path).convert("RGB")
        w, h = image.size
        
        # 如果指定了目标尺寸，缩放
        if target_width and target_height:
            # 保持宽高比，缩放到不超过目标尺寸
            ratio = min(target_width / w, target_height / h)
            if ratio < 1:
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                new_w = ((new_w + 31) // 64) * 64
                new_h = ((new_h + 31) // 64) * 64
                image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                print(f"   📐 参考图缩放: {w}x{h} -> {new_w}x{new_h}")
        else:
            # 如果图片太大，限制最大尺寸为 1024
            max_size = 1024
            if max(w, h) > max_size:
                ratio = max_size / max(w, h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                new_w = ((new_w + 31) // 64) * 64
                new_h = ((new_h + 31) // 64) * 64
                image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                print(f"   📐 参考图缩放: {w}x{h} -> {new_w}x{new_h}")
        
        return image

    def generate(
        self,
        prompt: str,
        negative: str,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        seed: int = None,
    ) -> str:
        """文生图"""
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
        
        return self._save_result(result.images[0], seed)

    def generate_from_image(
        self,
        prompt: str,
        negative: str,
        image_path: str,
        strength: float = 0.7,
        width: int = None,
        height: int = None,
        steps: int = 25,
        cfg: float = 7.5,
        seed: int = None,
    ) -> str:
        """
        图生图：基于参考图生成新图
        
        参数:
            prompt: 提示词
            negative: 负面提示词
            image_path: 参考图路径
            strength: 重绘强度 (0.0-1.0)，越大变化越大
            width: 输出宽度（默认使用参考图尺寸）
            height: 输出高度（默认使用参考图尺寸）
            steps: 迭代步数
            cfg: CFG 值
            seed: 随机种子
        """
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        
        # 加载参考图
        print(f"   📷 加载参考图: {os.path.basename(image_path)}")
        image = self._prepare_image(image_path, width, height)
        
        # 确定输出尺寸
        if width is None or height is None:
            width, height = image.size
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        
        generator = torch.Generator(self.device).manual_seed(seed)
        
        # SDXL 需要额外的参数
        if isinstance(self.pipe, StableDiffusionXLPipeline):
            # 构建 SDXL 的 added_cond_kwargs
            from diffusers import StableDiffusionXLPipeline
            added_cond_kwargs = {
                "text_embeds": None,
                "time_ids": self._get_time_ids(width, height),
            }
            
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=image,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
                added_cond_kwargs=added_cond_kwargs,
                width=width,
                height=height,
            )
        else:
            # SD1.5 图生图
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=image,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
            )
        
        return self._save_result(result.images[0], seed)

    def _get_time_ids(self, width: int, height: int):
        """获取 SDXL 的 time_ids"""
        return torch.tensor([
            height, width,
            height, width,
            0, 0,
        ], dtype=torch.float32)

    def _save_result(self, image, seed: int) -> str:
        """保存图片"""
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/{timestamp}_{seed}.png"
        image.save(output_path)
        print(f"   ✅ 已保存: {output_path} (种子: {seed})")
        return output_path