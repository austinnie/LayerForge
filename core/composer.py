# core/composer.py
import random
from typing import Dict, List

class PromptComposer:
    LAYER_ORDER = ["subject", "scene", "style", "lighting", "view", "quality"]
    def __init__(self, layers: Dict[str, List[str]]):
        self.layers = layers
        for key in self.LAYER_ORDER:
            if key not in self.layers or not self.layers[key]:
                print(f"   ⚠️ 警告: 层 '{key}' 为空")
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
