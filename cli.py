#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LayerForge - 6层结构化 AI 生图工具"""

import argparse
import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.loader import load_all_layers
from core.composer import PromptComposer
from core.generator import SDGenerator
from config import *

# ==================== 预设加载函数 ====================

def load_preset(preset_name: str) -> dict:
    """动态加载 presets/ 目录下的预设文件"""
    preset_path = Path(__file__).parent / "presets" / f"{preset_name}.py"
    
    if not preset_path.exists():
        print(f"❌ 预设不存在: {preset_name}")
        print(f"   可用的预设: {', '.join(list_available_presets())}")
        return None
    
    try:
        spec = importlib.util.spec_from_file_location(preset_name, preset_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "PRESET"):
            return module.PRESET
        else:
            print(f"❌ 预设文件格式错误: {preset_name}，缺少 PRESET 变量")
            return None
    except Exception as e:
        print(f"❌ 加载预设失败: {e}")
        return None

def list_available_presets() -> list:
    """列出所有可用的预设名称"""
    preset_dir = Path(__file__).parent / "presets"
    if not preset_dir.exists():
        return []
    return [f.stem for f in preset_dir.glob("*.py") if f.name != "__init__.py"]

# ==================== 主函数 ====================

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
    parser.add_argument("--preset", type=str, help="使用预设风格 (mecha, chinese_ink, anime_portrait)")
    parser.add_argument("--list-presets", action="store_true", help="列出所有可用预设")
    args = parser.parse_args()

    print("\\n📚 加载提示词层 (LayerForge)...")
    layers = load_all_layers("layers")
    composer = PromptComposer(layers)

    # 列出预设
    if args.list_presets:
        presets = list_available_presets()
        if not presets:
            print("\n📚 没有找到任何预设文件")
            print("   请在 presets/ 目录下创建预设文件")
            return
        print("\n📚 可用预设风格:")
        for p in presets:
            preset_data = load_preset(p)
            if preset_data:
                print(f"   {p}: {preset_data.get('description', '无描述')}")
        return

    # 应用预设
    if args.preset:
        preset_data = load_preset(args.preset)
        if preset_data:
            print(f"\n🎯 应用预设: {preset_data['name']}")
            print(f"   {preset_data.get('description', '')}")
            composer.apply_preset(preset_data["layers"])
            total = composer.get_total_combinations()
            print(f"   📈 预设后总组合数: {total:,}")
        else:
            return

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