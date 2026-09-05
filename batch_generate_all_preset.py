#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量生成所有预设（每个 1 张），自动保存提示词文件"""

import os
import time
import subprocess
from pathlib import Path

def main():
    preset_dir = Path("presets")
    preset_files = [f for f in preset_dir.glob("*.py") if f.stem not in ["__init__", "index"]]
    total = len(preset_files)
    print("=" * 60)
    print(f"📊 找到 {total} 个预设")
    print("=" * 60)

    success_count = 0
    fail_count = 0
    failed_presets = []

    for idx, preset_path in enumerate(preset_files, 1):
        preset_name = preset_path.stem
        print(f"\n[{idx}/{total}] 🎨 生成: {preset_name}")
        print("-" * 40)

        # 设置环境变量强制子进程使用 UTF-8
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            result = subprocess.run(
                ['python', 'agnes.py', 'preset', preset_name, '-n', '1'],
                capture_output=True,
                text=True,
                encoding='utf-8',      # 指定解码编码
                errors='replace',      # 遇非法字符替换为 �，不抛异常
                timeout=120,
                env=env                # 传入环境变量
            )
            if result.returncode == 0:
                print(f"   ✅ 成功")
                success_count += 1
            else:
                print(f"   ❌ 失败: {result.stderr}")
                fail_count += 1
                failed_presets.append(preset_name)
        except subprocess.TimeoutExpired:
            print(f"   ⏰ 超时（120秒）")
            fail_count += 1
            failed_presets.append(preset_name)
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            fail_count += 1
            failed_presets.append(preset_name)

        if idx < total:
            time.sleep(2)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 生成总结")
    print("=" * 60)
    print(f"   ✅ 成功: {success_count} 个")
    print(f"   ❌ 失败: {fail_count} 个")
    if failed_presets:
        print(f"\n   失败预设:")
        for name in failed_presets:
            print(f"      - {name}")
    print(f"\n📁 图片和提示词文件保存在: output/")
    print("   (每个图片都有对应的 .txt 提示词文件)")
    print("=" * 60)

if __name__ == "__main__":
    main()