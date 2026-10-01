# pwa/run.py
"""
LayerForge PWA 独立启动入口
用法: python pwa/run.py
"""
import sys
import socket
import argparse
from pathlib import Path

# 1. 确保项目根目录在 sys.path 中，这样 api.py 里的 from core... 才能正常生效
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 2. 🔥 核心修复：直接导入 api.py 中的 app 对象，彻底避开 uvicorn 字符串解析的模块查找问题！
from api import app

def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except: 
        return "127.0.0.1"

def main():
    ap = argparse.ArgumentParser(description="LayerForge PWA 服务")
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--reload", action="store_true", help="开发模式自动重载")
    args = ap.parse_args()

    lan_ip = get_lan_ip()
    print(f"\n🎨 LayerForge PWA 已启动!")
    print(f"   🖥️ 本机: http://127.0.0.1:{args.port}")
    print(f"   📱 局域网: http://{lan_ip}:{args.port}\n")

    import uvicorn
    
    # 3. 🔥 核心修复：直接传入 app 对象，而不是字符串 "pwa.api:app"
    uvicorn.run(app, host="0.0.0.0", port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()