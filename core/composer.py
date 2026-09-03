# core/composer.py（完整文件，已包含新方法）

import random
from typing import Dict, List

class PromptComposer:
    LAYER_ORDER = ["subject", "scene", "style", "lighting", "view", "quality"]
    
    def __init__(self, layers: Dict[str, List[str]]):
        self.layers = layers
        self._validate()
    
    def _validate(self):
        for key in self.LAYER_ORDER:
            if key not in self.layers or not self.layers[key]:
                print(f"   ⚠️ 警告: 层 '{key}' 为空")
    
    def apply_preset(self, preset_layers: Dict[str, List[str]]):
        """用预设层配置覆盖默认层（只覆盖存在的键）"""
        for key, values in preset_layers.items():
            if values and isinstance(values, list):
                self.layers[key] = values
                print(f"   🎯 预设锁定层: {key} -> {len(values)} 个选项")
        # 重新验证
        self._validate()
    
    def compose_by_index(self, index: int) -> str:
        parts = []
        for key in self.LAYER_ORDER:
            options = self.layers.get(key, [])
            if not options:
                continue
            parts.append(options[index % len(options)])
            index = index // len(options) if len(options) > 0 else index + 1
        return ", ".join(parts)
    
    def compose_random(self) -> str:
        parts = [random.choice(self.layers.get(key, ["empty"])) for key in self.LAYER_ORDER if self.layers.get(key)]
        return ", ".join(parts)
    
    def get_total_combinations(self) -> int:
        total = 1
        for key in self.LAYER_ORDER:
            count = len(self.layers.get(key, []))
            if count == 0:
                return 0
            total *= count
        return total