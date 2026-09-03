# LayerForge 🔥

**LayerForge** —— 基于 6 层结构化提示词架构的 Stable Diffusion 文生图工具。

告别随机抽卡，让 AI 绘画变为精准可控的创作流程。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **6 层提示词架构** | 主体 / 场景 / 风格 / 光影 / 视角 / 画质，层层可控 |
| **预设风格库** | 内置 90+ 预设风格（机甲、国风、人像、素描等） |
| **模型管理** | 自动检测本地模型，一键切换 SD1.5 / SDXL |
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

#### 模型管理

| 命令 | 说明 |
|------|------|
| `--list-models` | 列出所有本地模型 |
| `--set-model NAME` | 切换默认模型（支持部分匹配） |

#### 预设管理

| 命令 | 说明 |
|------|------|
| `--list-presets` | 列出所有可用预设 |
| `--preset NAME` | 使用指定预设 |

#### 调试

| 命令 | 说明 |
|------|------|
| `--list-layers` | 查看各层配置和总组合数 |


📁 目录结构
```text
LayerForge/
├── cli.py                 # 命令行入口
├── config.py              # 全局配置（自动检测模型）
├── requirements.txt       # 依赖清单
├── .model_config          # 用户选择的模型路径（自动生成）
│
├── core/                  # 核心引擎
│   ├── loader.py          # 动态加载 6 层
│   ├── composer.py        # 6 层组合器
│   └── generator.py       # SD 生成后端
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

#### 📦 依赖
```python
Python >= 3.10

torch >= 2.0.0

diffusers >= 0.26.0

transformers >= 4.40.0

accelerate >= 1.14.0

pillow >= 10.0.0

numpy >= 1.24.0

safetensors >= 0.8.0
```

#### 📄 License
MIT License
