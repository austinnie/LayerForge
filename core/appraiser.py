# core/appraiser.py
"""AI 图像鉴赏器 - 使用 BLIP + Ollama 生成点评文案"""

import os
import sys
import requests
from PIL import Image
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OLLAMA_HOST, OLLAMA_MODEL


class Appraiser:
    """AI 图像鉴赏器 - BLIP + Ollama"""
    
    def __init__(self, ollama_model: str = None):
        self.ollama_model = ollama_model or OLLAMA_MODEL
        self.ollama_host = OLLAMA_HOST
        self._blip_processor = None
        self._blip_model = None
        self._blip_loaded = False
        
        # 模型配置
        self.model_configs = {
            "qwen": {
                "language": "zh",
                "system_prompt": "你是一位资深的艺术评论家和摄影鉴赏家。",
                "temperature": 0.7,
                "max_tokens": 200
            },
            "phi": {
                "language": "en",
                "system_prompt": "You are an expert art critic and photographer.",
                "temperature": 0.7,
                "max_tokens": 200
            },
            "qwen2.5": {
                "language": "zh",
                "system_prompt": "你是一位专业艺术评论家，擅长用优美的文字描述艺术作品。",
                "temperature": 0.7,
                "max_tokens": 200
            },
            "tinyllama": {
                "language": "zh",
                "system_prompt": "你是一位艺术爱好者。",
                "temperature": 0.5,
                "max_tokens": 100
            }
        }
    
    def _ensure_blip_loaded(self):
        """加载 BLIP 模型"""
        if self._blip_loaded:
            return
        
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            
            # 尝试从缓存加载
            cache_dir = os.environ.get("HF_HOME", "~/.cache/huggingface")
            model_name = "Salesforce/blip-image-captioning-large"
            
            print("   📦 加载 BLIP 模型...")
            self._blip_processor = BlipProcessor.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )
            self._blip_model = BlipForConditionalGeneration.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )
            self._blip_loaded = True
            print("   ✅ BLIP 模型加载完成")
            
        except ImportError:
            print("   ⚠️ transformers 未安装，BLIP 不可用")
            print("   💡 安装: pip install transformers")
            self._blip_loaded = False
        except Exception as e:
            print(f"   ⚠️ BLIP 加载失败: {e}")
            self._blip_loaded = False
    
    def _llm_available(self) -> bool:
        """检查 Ollama 是否可用"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def _get_blip_caption(self, image_path: str) -> str:
        """使用 BLIP 生成图像描述"""
        if not self._blip_loaded or self._blip_model is None:
            return None
        
        try:
            image = Image.open(image_path).convert('RGB')
            inputs = self._blip_processor(image, return_tensors="pt")
            out = self._blip_model.generate(
                **inputs,
                max_length=80,
                num_beams=3,
                repetition_penalty=1.1,
                forced_bos_token_id=self._blip_processor.tokenizer.convert_tokens_to_ids("zh") if hasattr(self._blip_processor.tokenizer, "convert_tokens_to_ids") else None
            )
            caption = self._blip_processor.decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            print(f"   ⚠️ BLIP 推理失败: {e}")
            return None
    
    def _get_model_config(self):
        """根据模型名称获取配置"""
        model_lower = self.ollama_model.lower()
        for key, config in self.model_configs.items():
            if key in model_lower:
                return config
        return {
            "language": "zh",
            "system_prompt": "你是一位专业的艺术评论家。",
            "temperature": 0.7,
            "max_tokens": 200
        }
    
    def _enhance_with_llm(self, caption: str) -> str:
        """使用 Ollama 增强描述"""
        if not caption:
            return None
        
        try:
            config = self._get_model_config()
            language = config["language"]
            system_prompt = config["system_prompt"]
            temperature = config["temperature"]
            max_tokens = config["max_tokens"]
            
            if language == "zh":
                llm_prompt = f"""
{system_prompt}

请根据以下对这张图片的简短基础描述，写一段40字左右的摄影点评/文案。

要求：
1. 不要复述图片里有什么（不要堆砌名词）
2. 重点描写细节质感、光影氛围或整体意境
3. 语气要像专业人士，不要太像AI
4. 直接给出点评内容，不要有前缀

图片简述：{caption}
"""
            else:
                llm_prompt = f"""
{system_prompt}

Based on the following brief description of an image, write a short 30-40 word photography review/caption.

Requirements:
1. Don't just list what's in the image
2. Focus on texture, lighting, atmosphere, or overall artistic impression
3. Sound like a professional, not like an AI
4. Output only the review, no prefixes

Image description: {caption}
"""
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": llm_prompt,
                    "stream": False,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60,
                proxies={"http": None, "https": None},
            )
            
            if response.status_code == 200:
                result = response.json().get("response", caption).strip()
                if len(result) > 300:
                    result = result[:300] + "..."
                return result
            else:
                print(f"   ⚠️ Ollama 请求失败: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Ollama 请求超时 (60秒)")
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️ 无法连接到 Ollama")
        except Exception as e:
            print(f"   ⚠️ Ollama 分析失败: {e}")
        
        return None
    
    def appraise(self, image_path: str, prompt: str = None) -> str:
        """
        对图片进行鉴赏，返回鉴赏文字
        
        参数:
            image_path: 图片路径
            prompt: 原始提示词（作为备用）
        
        返回:
            鉴赏文字
        """
        # 1. 确保 BLIP 已加载
        self._ensure_blip_loaded()
        
        # 2. 使用 BLIP 生成描述
        caption = None
        if self._blip_loaded:
            caption = self._get_blip_caption(image_path)
        
        # 3. 如果 BLIP 失败，使用提示词作为备用
        if not caption:
            caption = prompt or "未生成图片描述"
            print(f"   📝 使用提示词作为备用描述")
        
        # 4. 使用 Ollama 润色
        if self._llm_available():
            enhanced = self._enhance_with_llm(caption)
            if enhanced:
                return enhanced
        
        # 5. 降级：返回 BLIP 原始描述
        return caption
    
    def set_model(self, model_name: str):
        """切换使用的 Ollama 模型"""
        self.ollama_model = model_name
        print(f"   🔄 已切换到 Ollama 模型: {model_name}")
    
    def list_available_models(self) -> list:
        """列出 Ollama 中可用的模型"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5, proxies={"http": None, "https": None})
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except:
            pass
        return []