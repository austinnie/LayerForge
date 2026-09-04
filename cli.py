#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LayerForge - 6层结构化 AI 生图工具"""

import argparse
import sys
import importlib.util
from pathlib import Path
import os
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core.loader import load_all_layers
from core.composer import PromptComposer
from core.generator import SDGenerator
from core.postprocessor import postprocess_image
from core.appraiser import Appraiser

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
    OLLAMA_HOST,
    OLLAMA_MODEL,
    AI_APPRECIATION_ENGINE
)

# ==================== 导入 API 引擎 ====================
from core.api_engines import create_api_engine
from config import (
    TONGYI_API_KEY,
    TONGYI_MODEL,
    YIGE_API_KEY,
    YIGE_SECRET_KEY,
    HUNYUAN_SECRET_ID,
    HUNYUAN_SECRET_KEY,
    HF_API_TOKEN,
    HF_MODEL,
    POLLINATIONS_MODEL,
    AGNES_API_KEY,
    AGNES_MODEL,
    FREEAPI_MODEL,
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

    # 图生图参数
    parser.add_argument("--image", "-i", type=str, help="参考图路径（图生图模式）")
    parser.add_argument("--strength", type=float, default=0.7, help="重绘强度 0.0-1.0（默认 0.7）")

    # 生成的图片后期处理
    parser.add_argument("--no-postprocess", action="store_true", help="关闭后处理")
    parser.add_argument("--postprocess-mode", choices=["clean", "realistic", "full"], default="full", help="后处理模式")

    # 动态提示词 (Ollama)
    parser.add_argument("--dynamic", "-d", action="store_true", help="动态提示词模式（交互式）")
    parser.add_argument("--prompt", "-p", type=str, help="动态提示词：直接指定画面描述")
    parser.add_argument("--style-hint", choices=["general", "anime", "realistic", "sketch", "mecha"],
                        default="general", help="动态提示词风格提示")
    parser.add_argument("--ollama-model", type=str, help="指定 Ollama 模型")
    
    # AI 图像鉴赏
    parser.add_argument("--appraise", action="store_true", help="生成图片后自动鉴赏")
    parser.add_argument("--appraise-only", type=str, help="单独鉴赏已有图片: --appraise-only output/image.png")
    parser.add_argument("--appraise-model", type=str, help="指定鉴赏用的 Ollama 模型")
    
    # 使用云端 API 生成图片
    parser.add_argument("--api", 
        choices=["tongyi", "yige", "hunyuan", "huggingface", "pollinations", "agnes", "freeapi"], 
        help="使用云端 API 生成图片")
    
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

    # ==================== 动态提示词 (Ollama) ====================
    # 标记：是否使用动态提示词
    use_dynamic_prompt = False
    dynamic_prompt_text = None
    
    if args.prompt or args.dynamic:
        use_dynamic_prompt = True
        print("\n🤖 动态提示词模式 (Ollama)")
        print("=" * 60)
        
        import requests
        
        # 检查 Ollama 是否可用
        ollama_available = False
        try:
            resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            ollama_available = resp.status_code == 200
            if ollama_available:
                print("✅ Ollama 服务连接成功")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
        
        if not ollama_available:
            print("💡 请确保 Ollama 正在运行: ollama serve")
            print("💡 安装: ollama pull qwen2.5:1.5b")
            return
        
        # 获取用户描述
        if args.dynamic and not args.prompt:
            print("\n💬 请输入画面描述 (支持中英文):")
            user_desc = input("> ").strip()
            if not user_desc:
                print("❌ 描述不能为空")
                return
        else:
            user_desc = args.prompt
        
        if not user_desc:
            print("❌ 请使用 --prompt 指定描述")
            return
        
        # 确定使用的模型
        model = args.ollama_model or OLLAMA_MODEL
        
        # 生成提示词
        print(f"\n⏳ 正在用 '{model}' 生成提示词...")
        dynamic_prompt_text = composer.generate_prompt_with_ollama(
            user_desc=user_desc,
            model=model,
            style_hint=args.style_hint,
            retry=2
        )
        
        print(f"\n✅ 生成的提示词:")
        print(f"   ─────────────────────────────────────────────────────")
        print(f"   {dynamic_prompt_text}")
        print(f"   ─────────────────────────────────────────────────────")
        
        if args.dry_run:
            print("\n[干跑模式] 退出")
            return

        if args.dynamic:
            confirm = input("\n是否使用此提示词生成? (y=生成 / n=取消 / r=重新描述): ").strip().lower()
            if confirm == 'r':
                return main()
            elif confirm != 'y':
                print("已取消")
                return
        
        # 如果 --dry-run 已处理，不会执行到这里
        # 继续使用动态提示词生成

    # ==================== AI 图像鉴赏（单独鉴赏） ====================
    if args.appraise_only:
        if not Path(args.appraise_only).exists():
            print(f"❌ 图片不存在: {args.appraise_only}")
            return
        
        print(f"\n📝 AI 鉴赏图片: {args.appraise_only}")
        appraiser = Appraiser(ollama_model=args.appraise_model or OLLAMA_MODEL)
        
        # 尝试读取原始提示词
        prompt_text = None
        for ext in ['.txt', '.json']:
            txt_file = args.appraise_only.replace('.png', ext).replace('.jpg', ext)
            if Path(txt_file).exists():
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '【提示词】' in content:
                        prompt_text = content.split('【提示词】')[1].split('\n')[0].strip()
                break
        
        caption = appraiser.appraise(args.appraise_only, prompt_text)
        print(f"\n   📝 {caption}")
        
        # 保存鉴赏结果
        txt_file = args.appraise_only.replace('.png', '.txt').replace('.jpg', '.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"【图片】: {Path(args.appraise_only).name}\n")
            if prompt_text:
                f.write(f"【提示词】: {prompt_text}\n")
            f.write(f"{'='*50}\n")
            f.write(f"【AI 鉴赏】:\n{caption}\n")
        print(f"   💾 已保存: {Path(txt_file).name}")
        return

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
    prompts = []
    
    if use_dynamic_prompt and dynamic_prompt_text:
        # ⭐ 动态提示词模式：直接使用生成的提示词
        prompts = [dynamic_prompt_text]
        print("\n📝 使用动态生成的提示词:")
        print(f"   [1] {dynamic_prompt_text[:100]}{'...' if len(dynamic_prompt_text) > 100 else ''}")
    else:
        # 常规模式：组合 6 层
        total = composer.get_total_combinations()
        print(f"\n📈 理论总组合数: {total:,}")
        if total == 0:
            print("❌ 错误: 没有任何层数据，请检查 layers/ 目录")
            return

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

    # ==================== 准备生成引擎 ====================
    # 判断是否使用云端 API
    use_api = args.api is not None

    # 如果使用 API，初始化 API 引擎
    api_engine = None
    if use_api:
        # 构建 API 配置
        api_config = {
            "TONGYI_API_KEY": TONGYI_API_KEY,
            "TONGYI_MODEL": TONGYI_MODEL,
            "YIGE_API_KEY": YIGE_API_KEY,
            "YIGE_SECRET_KEY": YIGE_SECRET_KEY,
            "HUNYUAN_SECRET_ID": HUNYUAN_SECRET_ID,
            "HUNYUAN_SECRET_KEY": HUNYUAN_SECRET_KEY,
            "HF_API_TOKEN": HF_API_TOKEN,
            "HF_MODEL": HF_MODEL,
            "POLLINATIONS_MODEL": POLLINATIONS_MODEL,
            "AGNES_API_KEY": AGNES_API_KEY,
            "AGNES_MODEL": AGNES_MODEL,
            "FREEAPI_MODEL": FREEAPI_MODEL,
        }
        
        # 检查 API Key（非免费 API 需要检查）
        if args.api == "tongyi" and not TONGYI_API_KEY:
            print("❌ 请设置 TONGYI_API_KEY")
            return
        if args.api == "yige" and not (YIGE_API_KEY and YIGE_SECRET_KEY):
            print("❌ 请设置 YIGE_API_KEY 和 YIGE_SECRET_KEY")
            return
        if args.api == "hunyuan" and not (HUNYUAN_SECRET_ID and HUNYUAN_SECRET_KEY):
            print("❌ 请设置 HUNYUAN_SECRET_ID 和 HUNYUAN_SECRET_KEY")
            return
        if args.api == "huggingface" and not HF_API_TOKEN:
            print("❌ 请设置 HF_API_TOKEN")
            return
        if args.api == "agnes" and not AGNES_API_KEY:
            print("❌ 请设置 AGNES_API_KEY")
            return
        
        print(f"🌐 使用云端 API: {args.api}")
        try:
            api_engine = create_api_engine(args.api, api_config)
        except Exception as e:
            print(f"❌ API 引擎初始化失败: {e}")
            return
    else:
        # 本地 SD 模式
        if not MODEL_PATH or not Path(MODEL_PATH).exists():
            print(f"\n❌ 模型文件不存在: {MODEL_PATH}")
            print("   请检查 config.py 中的 MODEL_PATH 配置")
            print("   或使用 --list-models 查看可用模型")
            return

        # 解析 LoRA
        lora_list = []
        if args.lora:
            lora_list = resolve_loras(args.lora, MODEL_TYPE)
        else:
            saved_lora = get_saved_lora()
            if saved_lora:
                print(f"🔗 使用默认 LoRA: {saved_lora}")
                lora_list = resolve_loras([saved_lora], MODEL_TYPE)

        generator = SDGenerator(MODEL_PATH, device="cpu", loras=lora_list)

    print(f"\n🎨 开始生成 {len(prompts)} 张...")

    if args.image and not use_api:
        print(f"   📷 图生图模式 | 参考图: {args.image} | 强度: {args.strength}")
        if not Path(args.image).exists():
            print(f"   ❌ 参考图不存在: {args.image}")
            return

    # 存储生成的图片路径，用于鉴赏
    generated_paths = []

    for idx, prompt in enumerate(prompts):
        print(f"\n   [{idx+1}/{len(prompts)}]")
        
        # 检测是否为素描风格
        is_sketch = False
        if args.preset:
            is_sketch = any(kw in args.preset.lower() for kw in ["sketch", "lineart"])
        if not is_sketch:
            is_sketch = any(kw in prompt.lower() for kw in ["sketch", "lineart", "pencil", "baimiao"])
        
        if use_api:
            # ⭐ 使用 API 生成
            try:
                image = api_engine.generate_single(
                    prompt=prompt,
                    negative=DEFAULT_NEGATIVE,
                    width=args.width,
                    height=args.height,
                    steps=args.steps,
                    cfg=args.cfg,
                    seed=args.seed + idx if args.seed else None,
                )
                # 保存图片（API 返回 PIL Image）
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(OUTPUT_DIR, f"{timestamp}_{args.seed or 0}.png")
                image.save(output_path)
                print(f"   ✅ 已保存: {output_path}")
                generated_paths.append(output_path)
            except Exception as e:
                print(f"   ❌ API 生成失败: {e}")
                continue
        else:
            # 本地 SD 生成
            if args.image:
                output_path = generator.generate_from_image(
                    prompt=prompt,
                    negative=DEFAULT_NEGATIVE,
                    image_path=args.image,
                    strength=args.strength,
                    width=args.width,
                    height=args.height,
                    steps=args.steps,
                    cfg=args.cfg,
                    seed=args.seed + idx if args.seed else None,
                )
            else:
                output_path = generator.generate(
                    prompt=prompt,
                    negative=DEFAULT_NEGATIVE,
                    width=args.width,
                    height=args.height,
                    steps=args.steps,
                    cfg=args.cfg,
                    seed=args.seed + idx if args.seed else None,
                )
            
            # 每张图生成后立即后处理
            final_path = output_path
            if not args.dry_run and not args.no_postprocess:
                final_path = postprocess_image(output_path, is_sketch=is_sketch)
            
            generated_paths.append(final_path)

    # ==================== AI 图像鉴赏（批量鉴赏） ====================
    if args.appraise and generated_paths:
        print("\n📝 AI 图像鉴赏...")
        appraiser = Appraiser(ollama_model=args.appraise_model or OLLAMA_MODEL)
        
        for idx, img_path in enumerate(generated_paths):
            if not Path(img_path).exists():
                continue
            
            # 获取对应的提示词
            prompt_text = prompts[idx] if idx < len(prompts) else None
            
            print(f"\n   [{idx+1}/{len(generated_paths)}] {Path(img_path).name}")
            caption = appraiser.appraise(img_path, prompt_text)
            
            # 保存鉴赏结果
            txt_file = img_path.replace('.png', '.txt').replace('.jpg', '.txt')
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"【图片】: {Path(img_path).name}\n")
                f.write(f"【提示词】: {prompt_text}\n")
                f.write(f"{'='*50}\n")
                f.write(f"【AI 鉴赏】:\n{caption}\n")
            
            print(f"      💾 已保存: {Path(txt_file).name}")
            print(f"      📝 {caption[:80]}...")

    print(f"\n✅ 全部完成！输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()