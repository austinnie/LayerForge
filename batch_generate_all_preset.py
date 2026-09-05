#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量生成所有预设（每个 1 张），自动保存提示词文件"""

import os
import time
import subprocess
from pathlib import Path

def main():
    preset_dir = Path("presets")
    
    # 获取所有预设文件（排除 __init__.py 和 index.py）
    preset_files = [f for f in preset_dir.glob("*.py") 
                    if f.stem not in ["__init__", "index"]]
    
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
        
        try:
            # 调用 agnes.py 生成
            result = subprocess.run(
                ['python', 'agnes.py', 'preset', preset_name, '-n', '1'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"   ✅ 成功")
                success_count += 1
            else:
                print(f"   ❌ 失败: {result.stderr[:200] if result.stderr else '未知错误'}")
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
        
        # 等待 2 秒，避免请求过快
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