#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''LayerForge - 6层结构化 AI 生图工具'''

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.loader import load_all_layers
from core.composer import PromptComposer
from core.generator import SDGenerator
from config import *

def main():
    parser = argparse.ArgumentParser(description="LayerForge - 6层提示词生图工具")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量")
    parser.add_argument("--seed", type=int, default=None, help="随机种子 (后续递增)")
    parser.add_argument("--random", action="store_true", help="随机组合 (否则按索引轮询)")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="迭代步数")
    parser.add_argument("--cfg", type=float, default=DEFAULT_CFG, help="CFG 值")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="宽度")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="高度")
    parser.add_argument("--dry-run", action="store_true", help="只显示提示词，不生成")
    parser.add_argument("--list-layers", action="store_true", help="显示当前各层选项数量")
    args = parser.parse_args()

    print("\n📚 加载提示词层 (LayerForge)...")
    layers = load_all_layers("layers")
    composer = PromptComposer(layers)

    if args.list_layers:
        print("\n📊 当前层配置:")
        for key in composer.LAYER_ORDER:
            count = len(layers.get(key, []))
            print(f"   {key}: {count} 个选项")
        print(f"\n📈 理论总组合数: {composer.get_total_combinations():,}")
        return

    total = composer.get_total_combinations()
    print(f"\n📈 理论总组合数: {total:,}")
    if total == 0:
        print("❌ 错误: 没有任何层数据，请检查 layers/ 目录")
        return

    prompts = []
    if args.random:
        for _ in range(args.count):
            prompts.append(composer.compose_random())
    else:
        for i in range(args.count):
            prompts.append(composer.compose_by_index(i))

    print("\n📝 生成的提示词:")
    for idx, p in enumerate(prompts):
        print(f"   [{idx+1}] {p[:100]}{'...' if len(p) > 100 else ''}")

    if args.dry_run:
        print("\n[干跑模式] 退出")
        return

    generator = SDGenerator(MODEL_PATH, device="cpu")
    print(f"\n🎨 开始生成 {len(prompts)} 张...")
    for idx, prompt in enumerate(prompts):
        print(f"\n   [{idx+1}/{len(prompts)}]")
        generator.generate(
            prompt=prompt,
            negative=DEFAULT_NEGATIVE,
            width=args.width,
            height=args.height,
            steps=args.steps,
            cfg=args.cfg,
            seed=args.seed + idx if args.seed else None,
        )
    print(f"\n✅ 全部完成！输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
