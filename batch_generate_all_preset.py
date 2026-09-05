#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量生成所有预设（每个 1 张）"""

import os
import time
from pathlib import Path

def main():
    preset_dir = Path("presets")
    
    # 获取所有预设文件（排除 __init__.py 和 index.py）
    preset_files = [f for f in preset_dir.glob("*.py") 
                    if f.stem not in ["__init__", "index"]]
    
    total = len(preset_files)
    print(f"📊 找到 {total} 个预设")
    print("=" * 50)
    
    for idx, preset_path in enumerate(preset_files, 1):
        preset_name = preset_path.stem
        print(f"\n[{idx}/{total}] 🎨 生成: {preset_name}")
        
        cmd = f'python agnes.py preset {preset_name} -n 1'
        os.system(cmd)
        
        # 等待 2 秒，避免请求过快
        if idx < total:
            time.sleep(2)
    
    print("\n" + "=" * 50)
    print(f"✅ 全部完成！共生成 {total} 张图片")
    print(f"📁 输出目录: output/")

if __name__ == "__main__":
    main()