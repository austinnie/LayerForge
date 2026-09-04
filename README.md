# LayerForge 🔥

**LayerForge** —— 基于 6 层结构化提示词架构的 Stable Diffusion 文生图工具。

告别随机抽卡，让 AI 绘画变为精准可控的创作流程。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **6 层提示词架构** | 主体 / 场景 / 风格 / 光影 / 视角 / 画质，层层可控 |
| **预设风格库** | 内置 90+ 预设风格（机甲、国风、人像、素描等） |
| **动态提示词 (Ollama)** | 输入中文描述，AI 自动生成高质量 SD 提示词 |
| **AI 图像鉴赏** | 生成图片后自动生成点评文案，适合作品集分享 |
| **云端 API 支持** | 支持 7 种云端 API，无需本地 GPU 即可生成 |
| **模型管理** | 自动检测本地模型，一键切换 SD1.5 / SDXL |
| **LoRA 支持** | 加载 LoRA 增强风格，支持权重控制和默认设置 |
| **图生图 (img2img)** | 基于参考图生成，保持构图换风格 |
| **照片真实化后处理** | 自动清除元数据、添加噪点/暗角、注入 EXIF |
| **Word 文档生成** | 自动生成作品集排版文档 |
| **智能缓存** | 模型和 LoRA 列表缓存，秒级响应 |
| **灵活组合** | 支持索引轮询、完全随机两种组合模式 |
| **轻量无依赖** | 纯 Python 实现，无 WebUI 复杂依赖 |

---

## 🏗️ 六层架构

| 层级 | 文件 | 说明 |
|------|------|------|
| 1 | `layer_01_subject.py` | 核心内容（主体、动作、生物、物件） |
| 2 | `layer_02_scene.py` | 背景设定（场地、时段、气候、周边） |
| 3 | `layer_03_style.py` | 画风风格（流派、名家、动漫名作） |
| 4 | `layer_04_lighting.py` | 色彩/光影（主色调、光照感、配色） |
| 5 | `layer_05_view.py` | 取景视角（角度、距离、构图法） |
| 6 | `layer_06_quality.py` | 画面细节（规格、质感、特效、比例） |

**每层独立配置，增删改查互不影响，组合数自动膨胀。**

---

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置模型
```bash
# 查看本地所有模型
python cli.py --list-models

# 切换默认模型
python cli.py --set-model anytimeRealistic
```

### 生成第一张图
```bash
# 干跑预览提示词（不生成图片）
python cli.py -n 3 --dry-run

# 正式生成
python cli.py -n 3
```

### 📚 预设风格

内置 90+ 预设风格，覆盖 8 大分类：

| 分类 | 示例 |
|------|------|
| 机甲 / 科幻 | `mecha_glow`, `mecha_sketch`, `transformers_optimus_prime` |
| 国风 / 水墨 | `chinese_ink_animals`, `chinese_landscape_master` |
| 人像 / 摄影 | `beach_resort_swimwear`, `nature_outdoor_girl` |
| 动漫 / 二次元 | `anime_figures`, `autumn_anime_portrait` |
| 素描 / 线稿 | `pencil_sketch_01_fashion`, `human_portrait_sketch` |
| 动物 / 生肖 | `tiger_sketch`, `dragon_sketch`, `bird_sketch` |
| 画廊 / 设计 | `jewelry_showcase`, `watch_blueprint`, `calligraphy_art` |
| 特殊 | `nuclear_01_sketch` ~ `nuclear_04_operational` |

### 使用预设
```bash
# 查看所有预设
python cli.py --list-presets

# 使用预设生成
python cli.py -n 3 --preset mecha_glow
python cli.py -n 3 --preset chinese_ink_animals
python cli.py -n 3 --preset tiger_sketch
```

### 🎮 CLI 命令

#### 生成控制

| 命令 | 说明 |
|------|------|
| `-n, --count N` | 生成 N 张图片 |
| `--seed N` | 固定随机种子（后续递增） |
| `--random` | 完全随机组合（否则按索引轮询） |
| `--steps N` | 迭代步数（默认 25） |
| `--cfg N` | CFG 值（默认 7.5） |
| `--width W --height H` | 自定义分辨率（默认 512x768） |
| `--dry-run` | 仅预览提示词，不生成 |


### 动态提示词 (Ollama)

| 命令 | 说明 |
|------|------|
| `--prompt, -p TEXT` | 输入中文描述，AI 自动生成 SD 提示词 |
| `--dynamic, -d` | 交互式模式（逐步引导输入） |
| `--style-hint STYLE` | 风格提示: `general` / `anime` / `realistic` / `sketch` / `mecha` |
| `--ollama-model MODEL` | 指定 Ollama 模型（默认 `qwen2.5:1.5b`） |

**动态提示词示例：**
```bash
# 非交互模式：直接生成
python cli.py --prompt "一个穿着白色连衣裙的女孩在向日葵花田里" -n 1

# 指定风格
python cli.py --prompt "机甲少女在赛博朋克城市" --style-hint mecha -n 1

# 干跑预览（不生成图片）
python cli.py --prompt "夕阳下的武士" --dry-run

# 交互模式
python cli.py --dynamic

# 指定 Ollama 模型
python cli.py --prompt "描述" --ollama-model qwen2.5:7b -n 1
```

### 支持的 Ollama 模型

| 模型 | 大小 | 速度 | 质量 | 推荐度 |
|------|------|------|------|--------|
| `qwen2.5:1.5b` | 986MB | ⚡⚡⚡ 最快 | ⭐⭐⭐ 良好 | **默认推荐** |
| `qwen2.5:3b` | 1.9GB | ⚡⚡ 快 | ⭐⭐⭐⭐ 较好 | 追求更好质量 |
| `qwen2.5:7b` | 4.7GB | ⚡ 较慢 | ⭐⭐⭐⭐⭐ 最好 | 高质量提示词 |


###  修改默认配置
在 config.py 中调整：

```python
# ==================== Ollama 配置 ====================
OLLAMA_HOST = "http://localhost:11434"   # Ollama 服务地址
OLLAMA_MODEL = "qwen2.5:1.5b"            # 默认模型
OLLAMA_TIMEOUT = 120                     # 超时时间（秒）
OLLAMA_TEMPERATURE = 0.7                 # 温度参数
OLLAMA_MAX_TOKENS = 200                  # 最大 token 数
```

### 云端 API

| 命令 | 说明 |
|------|------|
| `--api PROVIDER` | 使用云端 API 生成图片 |
| `--list-apis` | 列出所有可用 API 提供商 |

**支持的 API 提供商：**

| 提供商 | 费用 | 注册 | 说明 |
|--------|------|------|------|
| `pollinations` | 免费 | 不需要 | 完全免费，无需配置，推荐 |
| `freeapi` | 免费 | 不需要 | 社区免费代理 |
| `huggingface` | 免费 | 需要 Token | 需配置 `HF_API_TOKEN` |
| `tongyi` | 付费 | 需要 | 通义万相（阿里云） |
| `yige` | 付费 | 需要 | 文心一格（百度） |
| `hunyuan` | 付费 | 需要 | 腾讯混元 |
| `agnes` | 免费 | 需要注册 | Agnes AI |


### 配置 .env
为 .env 并填入你的 API Key：

```bash
# .env
# ============================================================
# 图像生成模式: "local" 或 "api"
# ============================================================
GENERATION_MODE=api
API_PROVIDER=huggingface

# ============================================================
# HuggingFace (免费，推荐)
# 获取 token: https://huggingface.co/settings/tokens
# ============================================================
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HF_MODEL=sdxl

# ============================================================
# 通义万相 (阿里云)
# ============================================================
TONGYI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TONGYI_MODEL=wanx-v1

# ============================================================
# 文心一格 (百度)
# ============================================================
YIGE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
YIGE_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================================
# 腾讯混元
# ============================================================
HUNYUAN_SECRET_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HUNYUAN_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================================
# Agnes AI (需注册)
# ============================================================
AGNES_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AGNES_MODEL=flux
```

**云端 API 示例：**

```bash
# Pollinations（完全免费，无需注册）
python cli.py -n 1 --preset mecha_glow --api pollinations

# Free API（社区免费代理）
python cli.py -n 1 --preset mecha_glow --api freeapi

# HuggingFace（需配置 HF_API_TOKEN）
python cli.py -n 1 --preset mecha_glow --api huggingface
```

### 配置 API Key：

```bash
# 编辑 .env 填入你的 API Key
```


### AI 图像鉴赏

| 命令 | 说明 |
|------|------|
| `--appraise` | 生成图片后自动鉴赏 |
| `--appraise-only PATH` | 单独鉴赏已有图片 |
| `--appraise-model MODEL` | 指定鉴赏用的 Ollama 模型 |

**AI 图像鉴赏示例：**

```bash
# 生成 + 自动鉴赏
python cli.py -n 1 --preset mecha_glow --appraise

# 动态提示词 + 鉴赏
python cli.py --prompt "一个穿白裙的女孩在向日葵田" -n 1 --appraise

# 单独鉴赏已有图片
python cli.py --appraise-only output/20260904_120000_123456.png

# 指定鉴赏模型（质量更高）
python cli.py -n 1 --preset mecha_glow --appraise --appraise-model qwen2.5:7b
```

#### 模型管理

| 命令 | 说明 |
|------|------|
| `--list-models` | 列出所有本地模型 |
| `--set-model NAME` | 切换默认模型（支持部分匹配） |


#### LoRA 管理

| 命令 | 说明 |
|------|------|
|`--list-loras`	|列出所有可用 LoRA 文件|
|`--set-lora NAME@WEIGHT`	|设置默认 LoRA（如 --set-lora style@0.7）|
|`--lora NAME@WEIGHT`	|临时加载 LoRA（可多次使用）|

#### LoRA 使用示例：

```bash
# 设置默认 LoRA
python cli.py --set-lora MechaGirlFigure_v1@0.7

# 临时加载 LoRA（覆盖默认）
python cli.py -n 1 --preset mecha_glow --lora eula_v2@0.6

# 加载多个 LoRA
python cli.py -n 1 --preset mecha_glow --lora style@0.6 --lora detail@0.4
```


#### 图生图

| 命令 | 说明 |
|------|------|
|`--image, -i PATH`	|指定参考图路径（图生图模式）|
|`--strength N`	|重绘强度 0.0-1.0（默认 0.7）|

#### 图生图示例：

```bash
# 基于参考图 + 预设生成
python cli.py -n 1 --image pose.png --preset mecha_glow

# 控制重绘强度
python cli.py -n 1 --image pose.png --preset mecha_glow --strength 0.5
```

#### 预设管理

| 命令 | 说明 |
|------|------|
| `--list-presets` | 列出所有可用预设 |
| `--preset NAME` | 使用指定预设 |


### 后处理（照片真实化）

| 命令 | 说明 |
|------|------|
| `--no-postprocess` | 关闭后处理（输出原始 PNG） |
| `--postprocess-mode MODE` | 处理模式: `clean` / `realistic` / `full`（默认 `full`） |

**后处理模式说明：**

| 模式 | 清除元数据 | 转 JPG | 噪点/暗角 | EXIF 注入 |
|------|:--------:|:------:|:--------:|:--------:|
| `clean` | ✅ | ✅ | ❌ | ❌ |
| `realistic` | ✅ | ✅ | ✅ | ❌ |
| `full`（默认） | ✅ | ✅ | ✅ | ✅ |

```bash
# 仅清理元数据（不加真实感）
python cli.py -n 1 --preset mecha_glow --postprocess-mode clean

# 关闭所有后处理
python cli.py -n 1 --preset mecha_glow --no-postprocess
```

#### 调试与缓存

| 命令 | 说明 |
|------|------|
| `--list-layers` 		| 查看各层配置和总组合数 |
|`--refresh-cache`		|强制刷新缓存（添加新模型/LoRA 后使用）|
|`--doc`				|生成 Word 文档（作品集排版）|
|`--remove-watermark`	|去除图片中的水印|

📁 目录结构
```text
LayerForge/
├── cli.py                 # 命令行入口
├── config.py              # 全局配置（自动检测模型/LoRA）
├── requirements.txt       # 依赖清单
├── .model_config          # 用户选择的模型路径（自动生成）
├── .lora_config           # 用户选择的默认 LoRA（自动生成）
├── .cache.json            # 模型/LoRA 缓存（自动生成）
├── .env                   # API Key 配置（不提交）
│
├── core/                  # 核心引擎
│   ├── loader.py          # 动态加载 6 层
│   ├── composer.py        # 6 层组合器（含智能 token 截断 + Ollama）
│   ├── generator.py       # SD 生成后端（含 LoRA 加载）
│   ├── postprocessor.py   # 统一后处理入口
│   ├── appraiser.py       # AI 图像鉴赏器（BLIP + Ollama）
│   └── api_engines/       # 云端 API 引擎
│       ├── base.py        # API 引擎基类
│       ├── tongyi.py      # 通义万相
│       ├── yige.py        # 文心一格
│       ├── hunyuan.py     # 腾讯混元
│       ├── huggingface.py # HuggingFace
│       ├── pollinations.py # Pollinations AI（免费）
│       ├── agnes.py       # Agnes AI
│       └── freeapi.py     # 社区免费代理
│
├── utils/                 # 工具模块
│   ├── logger.py          # 日志
│   ├── imagemeta_cleaner.py # 元数据清理
│   ├── exif_injector.py   # EXIF 注入（31种相机预设）
│   ├── photo_realistic.py # 照片真实化
│   ├── doc_generator.py   # Word 文档生成
│   └── watermark.py       # 水印处理
│
├── layers/                # 6 层提示词（可自由增删改）
│   ├── layer_01_subject.py
│   ├── layer_02_scene.py
│   ├── layer_03_style.py
│   ├── layer_04_lighting.py
│   ├── layer_05_view.py
│   └── layer_06_quality.py
│
├── presets/               # 预设风格库（90+ 个）
│   ├── mecha_glow.py
│   ├── tiger_sketch.py
│   └── ...
│
└── output/                # 生成的图片
```

### 🎯 使用场景

| 场景 | 推荐方式 |
|------|----------|
| 批量生成系列作品 | `python cli.py -n 20 --preset mecha_glow` |
| 探索创意灵感 | `python cli.py -n 10 --random` |
| 精准控制构图 | 修改 `layers/layer_05_view.py` 锁定视角 |
| 换模型对比效果 | `--set-model` 快速切换 SD1.5 / SDXL |

| LoRA 风格增强	|`--set-lora style@0.7` + 预设生成|
| 保持姿势换风格	|`--image pose.png --preset chinese_ink` |
| 出图更真实	    | 默认 `--postprocess-mode full`（相机预设可切换）|

### 🔧 自定义提示词

#### 添加新的 6 层选项

直接在 `layers/` 目录下编辑对应的 `layer_*.py` 文件，在 `LAYER` 列表中增删选项即可。

```python
# layers/layer_01_subject.py
LAYER = [
    "a beautiful young woman ...",  # 已有
    "your new subject here",        # 新增
]
```

#### 添加新的预设风格
在 presets/ 目录下创建 风格名.py 文件：

```python
# presets/my_style.py
PRESET = {
    "name": "my_style",
    "description": "我的自定义风格",
    "layers": {
        "subject": ["..."],
        "scene": ["..."],
        "style": ["..."],
        "lighting": ["..."],
        "view": ["..."],
        "quality": ["..."],
    },
}
```


### LoRA 存放位置

将 LoRA 文件（`.safetensors`）放入以下目录之一：

| 模型类型 | LoRA 目录 |
|----------|-----------|
| SD1.5 | `D:/SD_OpenVINO/models/sd15-lora/` |
| SDXL | `D:/SD_OpenVINO/models/sdxl-lora/` |

系统会自动扫描 D:/E:/F:/G: 盘符。


### 动态提示词 (Ollama)

| 命令 | 说明 |
|------|------|
| `--prompt, -p TEXT` | 输入中文描述，AI 自动生成 SD 提示词 |
| `--dynamic, -d` | 交互式模式（逐步引导输入） |
| `--style-hint STYLE` | 风格提示: `general` / `anime` / `realistic` / `sketch` / `mecha` |
| `--ollama-model MODEL` | 指定 Ollama 模型（默认 `qwen2.5:1.5b`） |

**动态提示词示例：**
```bash
# 非交互模式：直接生成
python cli.py --prompt "一个穿着白色连衣裙的女孩在向日葵花田里" -n 1

# 指定风格
python cli.py --prompt "机甲少女在赛博朋克城市" --style-hint mecha -n 1

# 干跑预览（不生成图片）
python cli.py --prompt "夕阳下的武士" --dry-run

# 交互模式
python cli.py --dynamic

# 指定 Ollama 模型
python cli.py --prompt "描述" --ollama-model qwen2.5:7b -n 1
```

### 📷 相机预设

后处理支持 **31 种相机预设**，可在 `config.py` 中切换：

| 品牌 | 型号 |
|------|------|
| **Sony** | α7 IV, α7 III, α1, α7R V, α9 III, α6700 |
| **Canon** | EOS R5, R6, R3, R6 Mark II, R8 |
| **Nikon** | Z 8, Z 9, Z f, Z6 III |
| **Fujifilm** | X100V, X-H2S, X-T5, GFX 100 II |
| **Panasonic** | Lumix S5 II, GH6 |
| **Leica** | M11, Q3 |
| **Hasselblad** | X2D 100C |
| **手机** | iPhone 15/16 Pro Max, Pixel 8/9 Pro, Galaxy S24 Ultra |

```python
# config.py 中切换
REALISTIC_CAMERA = "sony_a1"        # Sony α1
REALISTIC_CAMERA = "leica_m11"      # Leica M11
REALISTIC_CAMERA = "iphone_16"      # iPhone 16 Pro Max
```

#### 📦 依赖
```python
Python >= 3.10

torch >= 2.0.0

diffusers >= 0.26.0

transformers >= 4.40.0

peft >= 0.20.0 #加载LORA时需要

accelerate >= 1.14.0

pillow >= 10.0.0

numpy >= 1.24.0

safetensors >= 0.8.0

opencv-python >= 5.0.0   # 照片真实化需要

requests >= 2.31.0       # Ollama API 调用需要

python-dotenv >= 1.0.0          # .env 配置需要

python-docx >= 1.0.0            # Word 文档生成需要（可选）


```

#### 📄 License
MIT License
