#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Agnes AI 专用命令行工具 - 简化版

用法:
    python agnes.py chat "你好"                    # 对话
    python agnes.py gen "一只猫"                   # 文生图
    python agnes.py descr image.png               # 图片反推
    python agnes.py i2i image.png "新风格"        # 图生图
    python agnes.py mecha                         # 一键生成机甲
    python agnes.py -i                            # 交互模式
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from core.api_engines import create_api_engine
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
    """Agnes AI 专用命令行工具"""

    def __init__(self):
        self._init_engine()

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

    def generate(self, prompt: str, preset: str = None, count: int = 1):
        """文生图"""
        print(f"\n🎨 生成: {prompt}")
        for i in range(count):
            try:
                image = self.engine.text_to_image(
                    prompt=prompt,
                    negative=DEFAULT_NEGATIVE,
                    width=DEFAULT_WIDTH,
                    height=DEFAULT_HEIGHT,
                )
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(OUTPUT_DIR, f"agnes_{timestamp}_{i}.png")
                image.save(path)
                print(f"   ✅ [{i+1}/{count}] {path}")
            except Exception as e:
                print(f"   ❌ [{i+1}/{count}] {e}")

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
            print(f"   ✅ {path}")
        except Exception as e:
            print(f"   ❌ {e}")

    def mecha(self):
        """一键生成机甲风格"""
        prompts = [
            "cybernetic anime girl with long hair, sleek futuristic full-body suit, intricate mechanical components, android face with realistic eyes",
            "mecha warrior girl, silver and white armor, glowing blue energy core, sci-fi battle suit",
            "gundam style mecha girl, mechanical wings, futuristic combat armor, sleek design",
        ]
        import random
        prompt = random.choice(prompts)
        self.generate(prompt)

    def interactive(self):
        """交互模式"""
        print("\n" + "=" * 50)
        print("   🤖 Agnes AI 交互模式")
        print("=" * 50)
        print("\n命令: [chat|gen|descr|mecha|q]")
        print("  chat 消息   - 对话")
        print("  gen 描述    - 文生图")
        print("  descr 图片  - 图片反推")
        print("  mecha       - 一键机甲")
        print("  q           - 退出")
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
                    self.generate(parts[1])

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
    parser = argparse.ArgumentParser(description="Agnes AI 专用工具")
    parser.add_argument("command", nargs="?", help="chat | gen | descr | i2i | mecha | -i")
    parser.add_argument("arg", nargs="*", help="命令参数")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("-s", "--system", help="系统提示词（chat 模式）")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量（gen 模式）")
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
        cli.generate(" ".join(args.arg), count=args.count)

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
        cli.mecha()

    else:
        print(f"❌ 未知命令: {cmd}")
        print("   可用: chat, gen, descr, i2i, mecha, -i")


if __name__ == "__main__":
    main()