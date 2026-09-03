# LayerForge 🔥
**LayerForge** 是一个严格基于「6大维度」理论构建的 AI 生图工具。

## 六层架构
| 层级 | 文件名 | 说明 |
|------|--------|------|
| 1 | layer_01_subject.py | 核心内容（主体、动作、生物、物件） |
| 2 | layer_02_scene.py | 背景设定（场地、时段、气候、周边） |
| 3 | layer_03_style.py | 画风风格（流派、名家、动漫名作） |
| 4 | layer_04_lighting.py | 色彩/光影（主色调、光照感、配色） |
| 5 | layer_05_view.py | 取景视角（角度、距离、构图法） |
| 6 | layer_06_quality.py | 画面细节（规格、质感、特效、比例） |

## 快速开始
1. 修改 `config.py` 中的 `MODEL_PATH`
2. `pip install -r requirements.txt`
3. `python cli.py -n 1 --dry-run`
