# core/generator.py

import os
import torch
import random
from datetime import datetime
from pathlib import Path
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
from safetensors.torch import load_file  # 新增，用于手动加载


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
        """加载所有 LoRA - 借鉴旧项目的稳健实现"""
        print(f"🔗 加载 {len(self.loras)} 个 LoRA...")
        
        for i, lora_info in enumerate(self.loras):
            path = lora_info.get("path")
            weight = lora_info.get("weight", 0.8)
            name = lora_info.get("name", os.path.basename(path))
            
            if not path or not os.path.exists(path):
                print(f"   ⚠️ LoRA 文件不存在: {path}")
                continue
            
            # ---- 方法1: 标准加载 (diffusers 原生) ----
            try:
                self.pipe.load_lora_weights(path)
                print(f"   ✅ LoRA {i+1}: {name} (权重: {weight})")
                continue  # 成功则继续下一个
            except Exception as e:
                print(f"   ⚠️ 标准加载失败: {e}")
            
            # ---- 方法2: 手动加载（绕过 PEFT 检查，参考旧项目） ----
            try:
                print(f"   🔧 尝试手动加载 LoRA...")
                self._load_lora_manual(path)
                print(f"   ✅ LoRA {i+1}: {name} (手动加载成功, 权重: {weight})")
            except Exception as e:
                print(f"   ❌ LoRA {i+1} 加载失败（手动也失败）: {e}")

    def _load_lora_manual(self, lora_path: str):
        """
        手动加载 LoRA（绕过 diffusers 的 PEFT 检查）
        参考自旧项目 core/pipeline.py 的 load_lora_manual
        """
        # 1. 加载 LoRA 权重
        state_dict = load_file(lora_path)
        
        # 2. 分离 UNet 和 Text Encoder 的权重
        unet_state_dict = {}
        te_state_dict = {}
        
        for key, value in state_dict.items():
            # 跳过 alpha 值
            if 'alpha' in key:
                continue
            
            if 'lora_te_' in key:
                # Text Encoder 权重
                te_state_dict[key] = value
            else:
                # UNet 权重
                unet_state_dict[key] = value
        
        # 3. 转换格式: lora_down -> lora_A, lora_up -> lora_B
        converted_unet = {}
        for key, value in unet_state_dict.items():
            if 'lora_down' in key:
                new_key = key.replace('lora_down', 'lora_A')
                converted_unet[new_key] = value
            elif 'lora_up' in key:
                new_key = key.replace('lora_up', 'lora_B')
                converted_unet[new_key] = value
            else:
                converted_unet[key] = value
        
        # 4. 加载到 UNet（strict=False 允许部分加载）
        if converted_unet:
            self.pipe.unet.load_state_dict(converted_unet, strict=False)
            print(f"         ✅ UNet LoRA 加载完成 ({len(converted_unet)} 个权重)")
        
        # 5. 转换 Text Encoder 权重
        converted_te = {}
        for key, value in te_state_dict.items():
            if 'lora_down' in key:
                new_key = key.replace('lora_down', 'lora_A')
                converted_te[new_key] = value
            elif 'lora_up' in key:
                new_key = key.replace('lora_up', 'lora_B')
                converted_te[new_key] = value
            else:
                converted_te[key] = value
        
        # 6. 加载到 Text Encoder
        if converted_te:
            self.pipe.text_encoder.load_state_dict(converted_te, strict=False)
            print(f"         ✅ Text Encoder LoRA 加载完成 ({len(converted_te)} 个权重)")
        
        print(f"      ✅ LoRA 手动加载完成")

    def _prepare_image(self, image_path: str, target_width: int = None, target_height: int = None):
        """加载并预处理参考图"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"参考图不存在: {image_path}")
        
        image = Image.open(image_path).convert("RGB")
        w, h = image.size
        
        if target_width and target_height:
            ratio = min(target_width / w, target_height / h)
            if ratio < 1:
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                new_w = ((new_w + 31) // 64) * 64
                new_h = ((new_h + 31) // 64) * 64
                image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                print(f"   📐 参考图缩放: {w}x{h} -> {new_w}x{new_h}")
        else:
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
        """图生图"""
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        
        print(f"   📷 加载参考图: {os.path.basename(image_path)}")
        image = self._prepare_image(image_path, width, height)
        
        if width is None or height is None:
            width, height = image.size
        width = ((width + 31) // 64) * 64
        height = ((height + 31) // 64) * 64
        
        generator = torch.Generator(self.device).manual_seed(seed)
        
        if isinstance(self.pipe, StableDiffusionXLPipeline):
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
        return torch.tensor([
            height, width,
            height, width,
            0, 0,
        ], dtype=torch.float32)

    def _save_result(self, image, seed: int) -> str:
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/{timestamp}_{seed}.png"
        image.save(output_path)
        print(f"   ✅ 已保存: {output_path} (种子: {seed})")
        return output_path