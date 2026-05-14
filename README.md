# KBSZR - 极享AI口播智能体

一站式**数字人口播视频**创作平台。输入视频链接 → AI改写文案 → 生成配音 → 数字人渲染 → 一键多平台分发。

## 核心能力

| 环节 | 功能 | 技术方案 |
|------|------|----------|
| **文案提取** | 多平台视频链接解析 + 语音转文字 | yt-dlp + Whisper AI |
| **AI改写** | 文案智能改写，支持多种LLM | Ollama / DeepSeek / 通义千问 / OpenAI / Claude |
| **配音生成** | 多音色TTS，支持情感映射 | 阿里云TTS / 火山引擎 / Voicebox本地 |
| **数字人渲染** | AI数字人口播视频 | 阿里云数字人 / HeyGem本地 |
| **多平台分发** | 抖音/快手/小红书/视频号/B站 | Playwright自动化 |

## 支持平台

- **视频链接**: 抖音、快手、小红书、B站、YouTube、微博、知乎等
- **短链接**: v.douyin.com、b23.tv、xhslink.com、youtu.be
- **分发平台**: 抖音、快手、小红书、视频号、B站

## 技术栈

- **UI**: Gradio 4.0 + PyQt6 赛博朋克主题
- **异步**: asyncio / aiohttp / httpx
- **浏览器**: Playwright + yt-dlp
- **LLM**: Ollama (本地) / DeepSeek / 通义千问 / OpenAI / Claude
- **语音**: faster-whisper / 阿里云TTS / 火山引擎TTS / Voicebox
- **视频处理**: FFmpeg

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 配置

```bash
cp config/config.yaml config/config.yaml.local
# 编辑 config.yaml.local 填入你的 API Key
```

### 3. 启动

```bash
# Gradio Web UI (默认)
python start.py

# 赛博朋克 PyQt6 UI
KBSZR_UI=cyberpunk python start.py
```

### 4. 本地模型 (可选)

```bash
# 安装 Ollama
# https://ollama.ai/

# 下载 Whisper 模型
# https://github.com/openai/whisper

# 下载 Voicebox (本地TTS)
# https://github.com...
```

## 目录结构

```
KBSZR/
├── config/                  # 配置文件
├── data/                    # 数据目录 (audios, cookies, voices)
├── scripts/                 # 测试脚本
├── src/
│   ├── browser/             # 浏览器自动化
│   │   ├── cookie_manager.py    # Cookie管理 (扫码登录)
│   │   ├── link_parser.py       # 链接解析
│   │   └── video_extractor/     # 多平台视频文案提取
│   ├── business/             # 业务逻辑
│   │   ├── rewriter/         # AI文案改写
│   │   ├── tts/              # 语音合成
│   │   ├── digital_human/    # 数字人渲染
│   │   ├── audio/            # 音频处理
│   │   └── post_production/  # 后期处理
│   ├── services/             # 服务层
│   │   ├── ollama/           # Ollama LLM客户端
│   │   └── whisper/          # Whisper客户端
│   ├── ui/                   # 用户界面
│   │   └── cyberpunk/        # 赛博朋克主题
│   └── web/                  # Gradio Web应用
├── vendors/                  # 第三方组件
├── tests/                   # 测试
└── start.py                 # 启动入口
```

## 工作流

```
视频链接 → 文案提取 → AI改写 → 配音生成 → 数字人渲染 → 视频合成 → 多平台分发
   │           │          │          │            │           │
   ▼           ▼          ▼          ▼            ▼           ▼
短链解析   Whisper AI   多Provider   多引擎     阿里云/HeyGem   矩阵分发
平台检测   语音转文字    场景风格      情感映射     FFmpeg合成     账号隔离
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `KBSZR_UI` | UI模式 (web/cyberpunk) | cyberpunk |
| `ALIYUN_DH_API_KEY` | 阿里云数字人API Key | - |
| `ALIYUN_TTS_API_KEY` | 阿里云TTS API Key | - |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `CLAUDE_API_KEY` | Claude API Key | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `TONGYI_API_KEY` | 通义千问API Key | - |

## License

MIT