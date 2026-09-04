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
from config import (
    MODEL_PATH,
    MODEL_TYPE,
    MAX_TOKENS,
    OUTPUT_DIR,
    DEFAULT_STEPS,
    DEFAULT_CFG,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    DEFAULT_NEGATIVE,
    list_available_models,
    set_default_model,
    list_available_loras,
    resolve_loras,
    clear_cache,
    get_saved_lora,
    save_lora,
    parse_lora_spec,
    find_lora_file,
)

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
    return [f.stem for f in preset_dir.glob("*.py") if f.name != "__init__.py" and f.name != "index.py"]

# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="LayerForge - 6层提示词生图工具")
    
    # 生成参数
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量")
    parser.add_argument("--seed", type=int, default=None, help="随机种子 (后续递增)")
    parser.add_argument("--random", action="store_true", help="随机组合 (否则按索引轮询)")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="迭代步数")
    parser.add_argument("--cfg", type=float, default=DEFAULT_CFG, help="CFG 值")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="宽度")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="高度")
    parser.add_argument("--dry-run", action="store_true", help="只显示提示词，不生成")
    
    # 层和预设
    parser.add_argument("--list-layers", action="store_true", help="显示当前各层选项数量")
    parser.add_argument("--preset", type=str, help="使用预设风格 (mecha_glow, tiger_sketch, 等)")
    parser.add_argument("--list-presets", action="store_true", help="列出所有可用预设")
    
    # 模型管理
    parser.add_argument("--list-models", action="store_true", help="列出所有可用的本地模型")
    parser.add_argument("--set-model", type=str, help="设置默认模型 (从 --list-models 中选择)")
    
    # LoRA 管理
    parser.add_argument("--list-loras", action="store_true", help="列出所有可用的 LoRA 文件")
    parser.add_argument("--lora", action="append", help="加载 LoRA (格式: name@weight 或 path@weight)")
    parser.add_argument("--set-lora", type=str, help="设置默认 LoRA (格式: name@weight 或 path@weight)")
    
    # 缓存管理
    parser.add_argument("--refresh-cache", action="store_true", help="强制刷新缓存（重新扫描模型和 LoRA）")
    
    args = parser.parse_args()

    # ==================== 缓存刷新 ====================
    if args.refresh_cache:
        print("🔄 强制刷新缓存...")
        clear_cache()
        models = list_available_models(use_cache=False, force_refresh=True)
        loras = list_available_loras(use_cache=False, force_refresh=True)
        print(f"✅ 缓存已刷新: {len(models)} 个模型, {len(loras)} 个 LoRA")
        return

    # ==================== 模型管理 ====================
    if args.list_models:
        models = list_available_models()
        if not models:
            print("\n❌ 没有找到任何模型文件")
            print("   请检查 D:/SD_OpenVINO/models/sd-v1-5/ 或 E:/SD_OpenVINO/models/sdxl/")
            return
        
        print("\n📦 本地可用模型:")
        print("=" * 70)
        for i, m in enumerate(models):
            current = " 👈 当前使用" if m["path"] == MODEL_PATH else ""
            print(f"   [{i}] {m['name']}")
            print(f"       路径: {m['path']}")
            print(f"       大小: {m['size']} GB | 类型: {m['type']}{current}")
            print()
        return

    if args.set_model:
        set_default_model(args.set_model)
        return

    # ==================== LoRA 管理 ====================
    if args.list_loras:
        loras = list_available_loras()
        if not loras:
            print("\n❌ 没有找到任何 LoRA 文件")
            print("   请检查以下目录:")
            for d in ["E:/SD_OpenVINO/models/sd15-lora/", "E:/SD_OpenVINO/models/sdxl-lora/"]:
                print(f"   - {d}")
            return
        
        print(f"\n📚 可用 LoRA (共 {len(loras)} 个):")
        print("=" * 70)
        for i, l in enumerate(loras):
            print(f"   [{i}] {l['name']}")
            print(f"       路径: {l['path']}")
            print(f"       大小: {l['size']} MB | 类型: {l['type']}")
            print()
        return

    if args.set_lora:
        name_or_path, weight = parse_lora_spec(args.set_lora)
        lora_path = find_lora_file(name_or_path, MODEL_TYPE)
        if lora_path:
            save_lora(f"{lora_path}@{weight}")
            print(f"✅ 默认 LoRA 已设置为: {Path(lora_path).stem} (权重: {weight})")
        else:
            print(f"❌ 未找到 LoRA: {name_or_path}")
        return

    # ==================== 加载提示词层 ====================
    print("\n📚 加载提示词层 (LayerForge)...")
    layers = load_all_layers("layers")
    composer = PromptComposer(layers)

    # ==================== 预设管理 ====================
    if args.list_presets:
        presets = list_available_presets()
        if not presets:
            print("\n📚 没有找到任何预设文件")
            print("   请在 presets/ 目录下创建预设文件")
            return
        print(f"\n📚 可用预设 (共 {len(presets)} 个):")
        print("=" * 60)
        for p in sorted(presets):
            preset_data = load_preset(p)
            if preset_data:
                desc = preset_data.get('description', '无描述')
                print(f"   {p}: {desc}")
            else:
                print(f"   {p}")
        return

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

    # ==================== 显示层配置 ====================
    if args.list_layers:
        print("\n📊 当前层配置:")
        for key in composer.LAYER_ORDER:
            count = len(layers.get(key, []))
            print(f"   {key}: {count} 个选项")
        print(f"\n📈 理论总组合数: {composer.get_total_combinations():,}")
        return

    # ==================== 生成提示词 ====================
    total = composer.get_total_combinations()
    print(f"\n📈 理论总组合数: {total:,}")
    if total == 0:
        print("❌ 错误: 没有任何层数据，请检查 layers/ 目录")
        return

    prompts = []
    if args.random:
        for _ in range(args.count):
            prompts.append(composer.compose_random(max_tokens=MAX_TOKENS))
    else:
        for i in range(args.count):
            prompts.append(composer.compose_by_index(i, max_tokens=MAX_TOKENS))

    print("\n📝 生成的提示词:")
    for idx, p in enumerate(prompts):
        print(f"   [{idx+1}] {p[:100]}{'...' if len(p) > 100 else ''}")

    if args.dry_run:
        print("\n[干跑模式] 退出")
        return

    # ==================== 生成图片 ====================
    if not MODEL_PATH or not Path(MODEL_PATH).exists():
        print(f"\n❌ 模型文件不存在: {MODEL_PATH}")
        print("   请检查 config.py 中的 MODEL_PATH 配置")
        print("   或使用 --list-models 查看可用模型")
        return

    # 解析 LoRA
    lora_list = []
    if args.lora:
        # 临时 LoRA（覆盖默认）
        lora_list = resolve_loras(args.lora, MODEL_TYPE)
    else:
        # 使用默认 LoRA
        saved_lora = get_saved_lora()
        if saved_lora:
            print(f"🔗 使用默认 LoRA: {saved_lora}")
            lora_list = resolve_loras([saved_lora], MODEL_TYPE)

    generator = SDGenerator(MODEL_PATH, device="cpu", loras=lora_list)
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