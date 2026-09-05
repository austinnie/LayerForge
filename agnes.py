#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Agnes AI 专用命令行工具 - 支持 6 层提示词"""

import sys
import os
import argparse
import random
from pathlib import Path
from datetime import datetime
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from core.api_engines import create_api_engine
from core.loader import load_all_layers
from core.composer import PromptComposer
from config import (
    AGNES_API_KEY,
    AGNES_BASE_URL,
    AGNES_IMAGE_MODEL,
    AGNES_TEXT_MODEL,
    AGNES_VIDEO_MODEL,
    AGNES_VISION_MODEL,
    OUTPUT_DIR,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    DEFAULT_NEGATIVE,
    DEFAULT_STEPS,
    DEFAULT_CFG,
)


class AgnesCLI:
    """Agnes AI 专用命令行工具 - 支持 6 层提示词"""

    def __init__(self):
        self._init_engine()
        self._init_layers()

    def _init_engine(self):
        if not AGNES_API_KEY:
            print("❌ 请设置 AGNES_API_KEY")
            print("   在 .env 中配置: AGNES_API_KEY=your_key")
            sys.exit(1)

        config = {
            "AGNES_API_KEY": AGNES_API_KEY,
            "AGNES_BASE_URL": AGNES_BASE_URL,
            "AGNES_IMAGE_MODEL": AGNES_IMAGE_MODEL,
            "AGNES_TEXT_MODEL": AGNES_TEXT_MODEL,
            "AGNES_VIDEO_MODEL": AGNES_VIDEO_MODEL,
            "AGNES_VISION_MODEL": AGNES_VISION_MODEL,
        }
        self.engine = create_api_engine("agnes", config)
        print(f"✅ Agnes AI 已连接")
        print(f"   📷 图像: {AGNES_IMAGE_MODEL}")
        print(f"   💬 文本: {AGNES_TEXT_MODEL}")

    def _init_layers(self):
        """加载 6 层提示词系统"""
        print(f"\n📚 加载 6 层提示词...")
        layers_dir = Path(__file__).parent / "layers"
        if not layers_dir.exists():
            print("   ⚠️ layers/ 目录不存在，分层功能不可用")
            self.composer = None
            return

        layers = load_all_layers(str(layers_dir))
        self.composer = PromptComposer(layers)
        total = self.composer.get_total_combinations()
        print(f"   ✅ 加载完成: {total:,} 种组合")

    def _load_preset(self, preset_name: str):
        """加载预设风格"""
        preset_path = Path(__file__).parent / "presets" / f"{preset_name}.py"
        if not preset_path.exists():
            print(f"❌ 预设不存在: {preset_name}")
            print(f"   可用预设:")
            for p in Path(__file__).parent.glob("presets/*.py"):
                if p.stem not in ["__init__", "index"]:
                    print(f"      - {p.stem}")
            return None

        import importlib.util
        spec = importlib.util.spec_from_file_location(preset_name, preset_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "PRESET"):
            return module.PRESET
        return None

    def _get_prompt_from_layer(self, index: int):
        """从 6 层组合获取提示词"""
        if not self.composer:
            return None
        return self.composer.compose_by_index(index)

    def _get_prompt_from_preset(self, preset_name: str, random: bool = True):
        """从预设获取提示词（覆盖 6 层），默认随机组合"""
        preset = self._load_preset(preset_name)
        if not preset:
            return None

        # 应用预设层
        self.composer.apply_preset(preset["layers"])
        if random:
            return self.composer.compose_random()
        else:
            return self.composer.compose_by_index(0)

    def _save_prompt_file(self, image_path: str, prompt: str, label: str = None, 
                          seed: int = None, layers_detail: dict = None):
        """保存提示词到同名 .txt 文件"""
        txt_path = image_path.replace('.png', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"【预设】: {label if label else '自定义'}\n")
            f.write(f"【提示词】: {prompt}\n")
            f.write(f"【种子】: {seed if seed else '随机'}\n")
            f.write(f"【尺寸】: {DEFAULT_WIDTH}x{DEFAULT_HEIGHT}\n")
            f.write(f"【模型】: {AGNES_IMAGE_MODEL}\n")
            f.write(f"【生成时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if layers_detail:
                f.write("\n【6层组合详情】:\n")
                for key, value in layers_detail.items():
                    f.write(f"  {key}: {value}\n")

    def generate(self, prompt: str, count: int = 1, seed: int = None, 
                 show_layers: bool = False, label: str = None):
        """文生图 - 支持分层提示词，自动保存提示词文件"""
        
        # 收集层详情（用于保存）
        layers_detail = {}
        if show_layers and self.composer:
            print(f"\n📋 6 层组合详情:")
            for key in self.composer.LAYER_ORDER:
                options = self.composer.layers.get(key, [])
                if options:
                    idx = 0
                    chosen = options[idx % len(options)]
                    layers_detail[key] = chosen
                    print(f"   {key}: {chosen[:60]}...")

        print(f"\n🎨 生成: {prompt[:80]}...")
        for i in range(count):
            try:
                current_seed = seed + i if seed else None
                image = self.engine.text_to_image(
                    prompt=prompt,
                    negative=DEFAULT_NEGATIVE,
                    width=DEFAULT_WIDTH,
                    height=DEFAULT_HEIGHT,
                    seed=current_seed,
                )
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(OUTPUT_DIR, f"agnes_{timestamp}_{i}.png")
                image.save(path)
                print(f"   ✅ [{i+1}/{count}] {path}")
                
                # ⭐ 保存提示词文件
                self._save_prompt_file(path, prompt, label, current_seed, layers_detail)
                print(f"   📝 提示词已保存: {path.replace('.png', '.txt')}")
                
            except Exception as e:
                print(f"   ❌ [{i+1}/{count}] {e}")

    # ==================== 命令实现 ====================

    def chat(self, message: str, system: str = None):
        """对话/推理"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        print(f"\n💬 问: {message}")
        print(f"\n🤖 答:")
        print("-" * 50)
        result = self.engine.chat(messages)
        print(result)
        print("-" * 50)

    def preset_gen(self, preset_name: str, count: int = 1, seed: int = None):
        """使用预设风格生成"""
        prompt = self._get_prompt_from_preset(preset_name)
        if prompt:
            print(f"📋 预设: {preset_name}")
            self.generate(prompt, count=count, seed=seed, 
                          show_layers=True, label=preset_name)

    def layer_gen(self, index: int, count: int = 1, seed: int = None):
        """使用分层索引生成"""
        prompt = self._get_prompt_from_layer(index)
        if prompt:
            print(f"📋 索引: {index}")
            self.generate(prompt, count=count, seed=seed, 
                          show_layers=True, label=f"layer_{index}")

    def random_gen(self, count: int = 1, seed: int = None):
        """随机分层组合生成"""
        if not self.composer:
            print("❌ 分层系统未加载")
            return
        for i in range(count):
            idx = random.randint(0, self.composer.get_total_combinations() - 1)
            prompt = self.composer.compose_by_index(idx)
            print(f"\n📋 随机组合 [{idx}]:")
            self.generate(prompt, count=1, seed=seed + i if seed else None, 
                          show_layers=True, label=f"random_{idx}")

    def describe(self, image_path: str):
        """图片反推"""
        if not os.path.exists(image_path):
            print(f"❌ 图片不存在: {image_path}")
            return
        image = Image.open(image_path)
        print(f"\n📷 分析图片: {image_path}")
        print("-" * 50)
        result = self.engine.image_to_text(image)
        print(result)
        print("-" * 50)

    def image_to_image(self, image_path: str, prompt: str, strength: float = 0.7):
        """图生图"""
        if not os.path.exists(image_path):
            print(f"❌ 图片不存在: {image_path}")
            return
        image = Image.open(image_path)
        print(f"\n🔄 图生图: {prompt}")
        print(f"   📷 参考图: {image_path}")
        try:
            result = self.engine.image_to_image(
                prompt=prompt,
                image=image,
                strength=strength,
                width=DEFAULT_WIDTH,
                height=DEFAULT_HEIGHT,
            )
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(OUTPUT_DIR, f"agnes_i2i_{timestamp}.png")
            result.save(path)
            # ⭐ 图生图也保存提示词
            self._save_prompt_file(path, prompt, label="image-to-image", seed=None)
            print(f"   ✅ {path}")
            print(f"   📝 提示词已保存: {path.replace('.png', '.txt')}")
        except Exception as e:
            print(f"   ❌ {e}")

    def mecha(self, count: int = 1, seed: int = None):
        """一键机甲 - 从预设读取"""
        self.preset_gen("mecha_glow", count=count, seed=seed)

    def interactive(self):
        """交互模式 - 支持分层命令"""
        print("\n" + "=" * 50)
        print("   🤖 Agnes AI 交互模式 (支持 6 层提示词)")
        print("=" * 50)
        print("\n命令:")
        print("  chat 消息              - 对话")
        print("  gen 描述              - 文生图（中文直接描述）")
        print("  preset 预设名         - 使用预设风格")
        print("  layer 索引            - 使用分层索引 (0~组合数)")
        print("  random                - 随机分层组合")
        print("  descr 图片            - 图片反推")
        print("  mecha                 - 一键机甲")
        print("  q                    - 退出")
        print("=" * 50)

        while True:
            try:
                cmd = input("\n> ").strip()
                if not cmd:
                    continue
                if cmd.lower() == 'q':
                    print("👋 再见!")
                    break

                parts = cmd.split(maxsplit=1)
                action = parts[0].lower()

                if action == 'chat':
                    if len(parts) < 2:
                        print("❌ 请输入消息: chat 你好")
                        continue
                    self.chat(parts[1])

                elif action == 'gen':
                    if len(parts) < 2:
                        print("❌ 请输入描述: gen 一只猫")
                        continue
                    self.generate(parts[1], label="custom")

                elif action == 'preset':
                    if len(parts) < 2:
                        print("❌ 请输入预设名: preset mecha_glow")
                        continue
                    self.preset_gen(parts[1])

                elif action == 'layer':
                    if len(parts) < 2:
                        print("❌ 请输入索引: layer 0")
                        continue
                    try:
                        idx = int(parts[1])
                        self.layer_gen(idx)
                    except ValueError:
                        print("❌ 索引必须是数字")

                elif action == 'random':
                    self.random_gen()

                elif action == 'descr':
                    if len(parts) < 2:
                        print("❌ 请指定图片路径: descr image.png")
                        continue
                    self.describe(parts[1])

                elif action == 'mecha':
                    self.mecha()

                else:
                    print(f"❌ 未知命令: {action}")

            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="Agnes AI 专用工具 - 支持 6 层提示词")
    parser.add_argument("command", nargs="?", help="chat | gen | preset | layer | random | descr | i2i | mecha | -i")
    parser.add_argument("arg", nargs="*", help="命令参数")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("-s", "--system", help="系统提示词（chat 模式）")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--strength", type=float, default=0.7, help="重绘强度（i2i 模式）")

    args = parser.parse_args()

    cli = AgnesCLI()

    # 交互模式
    if args.interactive or not args.command:
        cli.interactive()
        return

    cmd = args.command.lower()

    if cmd == "chat":
        if not args.arg:
            print("❌ 请输入消息: agnes.py chat 你好")
            return
        cli.chat(" ".join(args.arg), system=args.system)

    elif cmd == "gen":
        if not args.arg:
            print("❌ 请输入描述: agnes.py gen 一只猫")
            return
        cli.generate(" ".join(args.arg), count=args.count, seed=args.seed, label="custom")

    elif cmd == "preset":
        if not args.arg:
            print("❌ 请输入预设名: agnes.py preset mecha_glow")
            return
        cli.preset_gen(args.arg[0], count=args.count, seed=args.seed)

    elif cmd == "layer":
        if not args.arg:
            print("❌ 请输入索引: agnes.py layer 0")
            return
        try:
            idx = int(args.arg[0])
            cli.layer_gen(idx, count=args.count, seed=args.seed)
        except ValueError:
            print("❌ 索引必须是数字")

    elif cmd == "random":
        cli.random_gen(count=args.count, seed=args.seed)

    elif cmd == "descr":
        if not args.arg:
            print("❌ 请指定图片路径: agnes.py descr image.png")
            return
        cli.describe(args.arg[0])

    elif cmd == "i2i":
        if len(args.arg) < 2:
            print("❌ 用法: agnes.py i2i image.png 新风格描述")
            return
        cli.image_to_image(args.arg[0], " ".join(args.arg[1:]), strength=args.strength)

    elif cmd == "mecha":
        cli.mecha(count=args.count, seed=args.seed)

    else:
        print(f"❌ 未知命令: {cmd}")
        print("   可用: chat, gen, preset, layer, random, descr, i2i, mecha, -i")


if __name__ == "__main__":
    main()