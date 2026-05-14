"""极享AI口播智能体 - Gradio Web应用"""
import os
import gradio as gr
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# 设置无缓冲输出
sys.stdout.reconfigure(line_buffering=True)


def load_config():
    """加载配置"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def save_config(config: dict):
    """保存配置"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def get_rewrite_providers():
    """获取可用的改写提供商"""
    return ["ollama", "tongyi", "qwen-turbo", "openai", "claude", "deepseek", "doubao", "wenxin", "hunyuan", "spark", "minimax"]


def get_tts_providers():
    """获取可用的TTS提供商"""
    return ["aliyun", "volcengine", "voicebox"]


def create_ui():
    """创建UI界面"""
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

    # 加载现有配置
    config = load_config()

    with gr.Blocks(title="极享AI口播智能体", analytics_enabled=False) as demo:
        gr.Markdown("# 极享AI口播智能体\n### 一站式数字人口播视频创作平台")

        # ==================== 设置选项卡 ====================
        with gr.Tab("⚙️ API设置"):
            gr.Markdown("## API配置")

            with gr.Row():
                # 左侧：Rewriter API
                with gr.Column():
                    gr.Markdown("### 📝 文案改写 API")
                    rewriter_provider = gr.Dropdown(
                        label="改写提供商",
                        choices=get_rewrite_providers(),
                        value=config.get("cloud", {}).get("rewriter", {}).get("provider", "deepseek")
                    )

                    deepseek_key = gr.Textbox(
                        label="Deepseek API Key",
                        value=config.get("cloud", {}).get("rewriter", {}).get("deepseek", {}).get("api_key", ""),
                        type="password",
                        placeholder="sk-..."
                    )

                    tongyi_key = gr.Textbox(
                        label="通义千问 API Key",
                        value=config.get("cloud", {}).get("rewriter", {}).get("tongyi", {}).get("api_key", ""),
                        type="password",
                        placeholder="..."
                    )

                    openai_key = gr.Textbox(
                        label="OpenAI API Key",
                        value=config.get("cloud", {}).get("rewriter", {}).get("openai", {}).get("api_key", ""),
                        type="password",
                        placeholder="sk-..."
                    )

                    claude_key = gr.Textbox(
                        label="Claude API Key",
                        value=config.get("cloud", {}).get("rewriter", {}).get("claude", {}).get("api_key", ""),
                        type="password",
                        placeholder="sk-ant-..."
                    )

                # 中间：TTS API
                with gr.Column():
                    gr.Markdown("### 🎤 语音合成 API")
                    tts_provider = gr.Dropdown(
                        label="TTS提供商",
                        choices=get_tts_providers(),
                        value=config.get("cloud", {}).get("tts", {}).get("provider", "aliyun")
                    )

                    aliyun_tts_key = gr.Textbox(
                        label="阿里云 TTS API Key",
                        value=config.get("cloud", {}).get("tts", {}).get("aliyun", {}).get("api_key", ""),
                        type="password",
                        placeholder="..."
                    )

                    volcengine_key = gr.Textbox(
                        label="火山引擎 API Key",
                        value=config.get("cloud", {}).get("tts", {}).get("volcengine", {}).get("api_key", ""),
                        type="password",
                        placeholder="..."
                    )

                    gr.Markdown("**Voicebox**: 本地TTS，无需API Key")

                # 右侧：数字人 API
                with gr.Column():
                    gr.Markdown("### 👤 数字人 API")
                    dh_provider = gr.Dropdown(
                        label="数字人提供商",
                        choices=["aliyun", "tencent", "heygem"],
                        value=config.get("cloud", {}).get("digital_human", {}).get("provider", "aliyun")
                    )

                    aliyun_dh_key = gr.Textbox(
                        label="阿里云 数字人 API Key",
                        value=config.get("cloud", {}).get("digital_human", {}).get("aliyun", {}).get("api_key", ""),
                        type="password",
                        placeholder="..."
                    )

                    heygem_path = gr.Textbox(
                        label="HeyGem 路径",
                        value=config.get("local", {}).get("heygem", {}).get("path", ""),
                        placeholder="C:\\HeyGem\\HeyGem.exe"
                    )

            save_config_btn = gr.Button("💾 保存配置", variant="primary")

            def save_all_config(rewriter_prov, deepseek_k, tongyi_k, openai_k, claude_k,
                               tts_prov, aliyun_tts_k, volcengine_k,
                               dh_prov, aliyun_dh_k, heygem_p):
                """保存所有配置"""
                new_config = {
                    "cloud": {
                        "rewriter": {
                            "provider": rewriter_prov,
                            "deepseek": {"api_key": deepseek_k},
                            "tongyi": {"api_key": tongyi_k},
                            "openai": {"api_key": openai_k},
                            "claude": {"api_key": claude_k},
                        },
                        "tts": {
                            "provider": tts_prov,
                            "aliyun": {"api_key": aliyun_tts_k},
                            "volcengine": {"api_key": volcengine_k},
                        },
                        "digital_human": {
                            "provider": dh_prov,
                            "aliyun": {"api_key": aliyun_dh_k},
                        }
                    },
                    "local": {
                        "heygem": {"path": heygem_p}
                    }
                }
                save_config(new_config)
                return "配置已保存!"

            save_config_btn.click(
                fn=save_all_config,
                inputs=[rewriter_provider, deepseek_key, tongyi_key, openai_key, claude_key,
                       tts_provider, aliyun_tts_key, volcengine_key,
                       dh_provider, aliyun_dh_key, heygem_path],
                outputs=[]
            )

        # ==================== 本地模型设置 ====================
        with gr.Tab("🤖 本地模型"):
            gr.Markdown("## 本地开源模型配置")
            gr.Markdown("无需API Key，使用本地部署的开源模型")

            with gr.Row():
                # Ollama 设置
                with gr.Column():
                    gr.Markdown("### 🧠 Ollama 大语言模型")
                    ollama_url = gr.Textbox(
                        label="Ollama 服务地址",
                        value=config.get("local", {}).get("ollama", {}).get("base_url", "http://localhost:11434"),
                        placeholder="http://localhost:11434"
                    )

                    ollama_model = gr.Dropdown(
                        label="选择模型",
                        choices=[
                            "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b",
                            "llama3.1:8b", "llama3.2:3b",
                            "deepseek-r1:7b", "deepseek-r1:14b",
                            "mistral:7b", "mixtral:8x7b",
                            "phi3:14b", "gemma2:9b"
                        ],
                        value=config.get("local", {}).get("ollama", {}).get("model", "qwen2.5:7b")
                    )

                    check_ollama_btn = gr.Button("🔍 检查服务状态", variant="secondary")
                    ollama_status = gr.Textbox(label="服务状态", lines=3, interactive=False)

                    gr.Markdown("**安装命令**: `ollama pull qwen2.5:7b`")

                # Whisper 设置
                with gr.Column():
                    gr.Markdown("### 🎤 Whisper 语音识别")
                    whisper_model = gr.Dropdown(
                        label="选择模型",
                        choices=["tiny", "base", "small", "medium", "large"],
                        value=config.get("local", {}).get("whisper", {}).get("model_size", "base"),
                        info="base推荐（140MB），large精度最高"
                    )

                    whisper_info = gr.Markdown("""
                    | 模型 | 大小 | 内存 | 推荐用途 |
                    |------|------|------|----------|
                    | tiny | 39MB | 1GB | 快速测试 |
                    | base | 140MB | 1GB | 日常使用（推荐） |
                    | small | 488MB | 2GB | 高精度 |
                    | medium | 1.5GB | 5GB | 很高精度 |
                    | large | 2.9GB | 10GB | 最高精度 |
                    """)

                    check_whisper_btn = gr.Button("🔍 检查模型状态", variant="secondary")
                    whisper_status = gr.Textbox(label="模型状态", lines=3, interactive=False)

                    download_whisper_btn = gr.Button("⬇️ 下载模型", variant="primary")
                    download_whisper_status = gr.Textbox(label="下载进度", lines=3, interactive=False)

            # 事件绑定
            check_ollama_btn.click(
                fn=_check_ollama,
                inputs=[ollama_url],
                outputs=[ollama_status]
            )

            check_whisper_btn.click(
                fn=_check_whisper,
                inputs=[whisper_model],
                outputs=[whisper_status]
            )

            download_whisper_btn.click(
                fn=_download_whisper,
                inputs=[whisper_model],
                outputs=[download_whisper_status]
            )

        # ==================== 主工作流 ====================
        with gr.Tab("🎬 创作中心"):
            gr.Markdown("## 账号登录 - 扫码登录后可提取会员专属内容")
            with gr.Row():
                platform_login = gr.Dropdown(
                    label="选择平台",
                    choices=["抖音", "快手", "小红书"],
                    value="抖音"
                )
                qr_login_btn = gr.Button("📱 扫码登录", variant="primary")
                login_status = gr.Textbox(label="登录状态", lines=1, interactive=False)

            login_msg = gr.Markdown("")

            def do_qr_login(platform: str):
                """执行扫码登录"""
                import asyncio
                from src.browser.cookie_manager import get_cookie_manager

                platform_map = {"抖音": "douyin", "快手": "kuaishou", "小红书": "xiaohongshu"}

                async def login():
                    manager = get_cookie_manager()
                    result = await manager.qr_login(platform_map.get(platform, "douyin"))
                    return result

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(login())
                    loop.close()

                    if result["success"]:
                        return (
                            f"✅ 登录成功！已获取 {len(result['cookies'])} 个Cookie",
                            ""
                        )
                    else:
                        return f"❌ 登录失败: {result.get('error', '未知错误')}", ""
                except Exception as e:
                    return f"❌ 登录异常: {str(e)}", ""

            qr_login_btn.click(
                fn=do_qr_login,
                inputs=[platform_login],
                outputs=[login_status, login_msg]
            )

            gr.Markdown("---")
            with gr.Row():
                # 左侧：输入和处理
                with gr.Column(scale=1):
                    gr.Markdown("### 1️⃣ 链接输入")
                    link_input = gr.Textbox(
                        label="视频链接",
                        lines=3,
                        placeholder="粘贴抖音/快手/小红书/视频号/B站链接..."
                    )
                    extract_btn = gr.Button("🔍 提取文案", variant="primary")

                    gr.Markdown("### 2️⃣ 文案编辑")
                    text_input = gr.Textbox(
                        label="文案内容（可手动修改）",
                        lines=10,
                        placeholder="提取或输入文案..."
                    )

                    gr.Markdown("### 3️⃣ AI改写")
                    rewrite_provider = gr.Dropdown(
                        label="选择改写模型",
                        choices=get_rewrite_providers(),
                        value="deepseek",
                        info="选择用于改写的AI模型"
                    )

                    ai_mode = gr.Radio(
                        choices=["AI自动仿写", "根据指令仿写"],
                        label="仿写模式",
                        value="AI自动仿写"
                    )

                    ai_prompt = gr.Textbox(
                        label="改写指令",
                        lines=2,
                        placeholder="例如：请用幽默的口吻改写这段文案",
                        visible=False
                    )

                    rewrite_btn = gr.Button("✍️ 执行改写", variant="primary")

                    gr.Markdown("### 4️⃣ 配音设置")
                    with gr.Row():
                        voice_dropdown = gr.Dropdown(
                            label="选择音色",
                            choices=["xiaomo", "xiaoyu", "xiaoming"],
                            value="xiaomo"
                        )
                        refresh_voice_btn = gr.Button("🔄", size="small")

                    speed_slider = gr.Slider(
                        minimum=0.5, maximum=2.0, value=1.0, step=0.1,
                        label="语速"
                    )

                    with gr.Row():
                        create_audio_btn = gr.Button("🎙️ 生成配音", variant="primary")
                        download_audio_btn = gr.Button("⬇️ 下载")

                    audio_output = gr.Audio(label="生成的配音")

                    gr.Markdown("### 5️⃣ 字幕")
                    subtitle_btn = gr.Button("📝 生成字幕", variant="secondary")
                    srt_text_output = gr.Textbox(
                        label="字幕内容",
                        lines=5
                    )

                # 右侧：预览和发布
                with gr.Column(scale=1):
                    gr.Markdown("### 6️⃣ 数字人配置")
                    with gr.Row():
                        avatar_dropdown = gr.Dropdown(
                            label="选择数字人",
                            choices=["小美", "小雅", "小帅", "老王"],
                            value="小美"
                        )
                        refresh_avatar_btn = gr.Button("🔄", size="small")

                    with gr.Row():
                        background_dropdown = gr.Dropdown(
                            label="背景",
                            choices=["演播室", "办公室", "客厅", "户外", "商品展示"]
                        )
                        motion_dropdown = gr.Dropdown(
                            label="运动",
                            choices=["无", "轻微", "中等"],
                            value="轻微"
                        )

                    aspect_ratio = gr.Dropdown(
                        label="视频比例",
                        choices=["9:16 竖屏", "16:9 横屏"],
                        value="9:16 竖屏"
                    )

                    gr.Markdown("### 7️⃣ 视频预览")
                    video_output = gr.Video(label="生成的视频", interactive=False)

                    generate_video_btn = gr.Button("🎬 生成视频", variant="primary", size="large")

                    gr.Markdown("### 8️⃣ 后期处理")
                    with gr.Accordion("BGM设置", open=False):
                        bgm_slider = gr.Slider(
                            minimum=0, maximum=1, value=0.5, step=0.1,
                            label="BGM音量"
                        )
                        add_bgm_btn = gr.Button("🎵 添加BGM", variant="secondary")
                        random_bgm_btn = gr.Button("🎲 随机BGM")

                    with gr.Accordion("封面设置", open=False):
                        cover_text = gr.Textbox(
                            label="封面文案",
                            lines=2,
                            placeholder="输入封面文案"
                        )
                        with gr.Row():
                            font_size = gr.Number(value=60, label="字体大小")
                            font_color = gr.ColorPicker(value="#FFFFFF", label="字体颜色")
                        generate_cover_btn = gr.Button("🖼️ 生成封面", variant="secondary")
                        cover_preview = gr.Image(label="封面预览")

                    gr.Markdown("### 9️⃣ 一键发布")
                    with gr.Row():
                        publish_douyin_btn = gr.Button("📱 抖音", variant="primary")
                        publish_xhs_btn = gr.Button("📕 小红书", variant="primary")
                        publish_sph_btn = gr.Button("💬 视频号", variant="primary")

                    publish_all_btn = gr.Button("🚀 一键发布全部", variant="primary", size="large")

                    gr.Markdown("### 📊 状态")
                    status_output = gr.Textbox(
                        label="状态信息",
                        lines=5,
                        interactive=False
                    )

        # ==================== 事件绑定 ====================
        # 提取文案
        extract_btn.click(
            fn=_extract_text,
            inputs=[link_input],
            outputs=[text_input, status_output]
        )

        # 切换仿写模式
        ai_mode.change(
            fn=lambda mode: gr.update(visible=(mode == "根据指令仿写")),
            inputs=[ai_mode],
            outputs=[ai_prompt]
        )

        # 执行改写
        rewrite_btn.click(
            fn=_execute_rewrite,
            inputs=[text_input, ai_mode, ai_prompt, rewrite_provider],
            outputs=[text_input, status_output]
        )

        # 刷新音色
        refresh_voice_btn.click(
            fn=_refresh_voice_list,
            outputs=[voice_dropdown]
        )

        # 生成配音
        create_audio_btn.click(
            fn=_create_audio,
            inputs=[text_input, voice_dropdown, speed_slider, tts_provider],
            outputs=[audio_output, status_output]
        )

        # 生成字幕
        subtitle_btn.click(
            fn=_create_subtitle,
            inputs=[audio_output, text_input],
            outputs=[srt_text_output, status_output]
        )

        # 刷新数字人
        refresh_avatar_btn.click(
            fn=_refresh_avatar_list,
            outputs=[avatar_dropdown]
        )

        # 生成视频
        generate_video_btn.click(
            fn=_generate_video,
            inputs=[text_input, audio_output, avatar_dropdown, background_dropdown, motion_dropdown, aspect_ratio],
            outputs=[video_output, status_output]
        )

        # 添加BGM
        add_bgm_btn.click(
            fn=_add_bgm,
            inputs=[video_output, bgm_slider],
            outputs=[video_output, status_output]
        )

        # 生成封面
        generate_cover_btn.click(
            fn=_generate_cover,
            inputs=[cover_text, font_size, font_color],
            outputs=[cover_preview, status_output]
        )

        # 发布按钮
        publish_douyin_btn.click(
            fn=lambda v, t: _publish("douyin", v, t),
            inputs=[video_output, text_input],
            outputs=[status_output]
        )

        publish_xhs_btn.click(
            fn=lambda v, t: _publish("xiaohongshu", v, t),
            inputs=[video_output, text_input],
            outputs=[status_output]
        )

        publish_sph_btn.click(
            fn=lambda v, t: _publish("video_number", v, t),
            inputs=[video_output, text_input],
            outputs=[status_output]
        )

        publish_all_btn.click(
            fn=lambda v, t: _publish_all(v, t),
            inputs=[video_output, text_input],
            outputs=[status_output]
        )

    return demo


def _check_ollama(url: str) -> str:
    """检查Ollama服务状态"""
    import asyncio

    async def check():
        from src.services.ollama import OllamaClient, OllamaConfig
        config = OllamaConfig(base_url=url)
        client = OllamaClient(config)
        result = await client.health_check()
        await client.close()
        return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(check())
        loop.close()

        if result.get("available"):
            models = result.get("models", [])
            if models:
                return f"✅ Ollama 服务正常\n已安装模型: {', '.join(models)}"
            else:
                return "✅ Ollama 服务正常\n请先安装模型: ollama pull qwen2.5:7b"
        else:
            hint = result.get("hint", "")
            return f"❌ Ollama 服务不可用\n{result.get('error', 'Unknown error')}\n\n提示: {hint}"
    except Exception as e:
        return f"❌ 检查失败: {str(e)}\n\n请确保已启动 Ollama: `ollama serve`"


def _check_whisper(model: str) -> str:
    """检查Whisper模型状态"""
    import asyncio

    async def check():
        from src.services.whisper import WhisperClient, WhisperConfig, WHISPER_MODELS
        config = WhisperConfig(model_size=model)
        client = WhisperClient(config)
        downloaded = await client.list_downloaded_models()
        await client.close()
        return downloaded

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        downloaded = loop.run_until_complete(check())
        loop.close()

        info = WHISPER_MODELS.get(model, {})
        size = info.get("size", "")

        if model in downloaded or model in ["tiny", "base"]:
            return f"✅ Whisper {model} 模型可用 ({size})"
        else:
            return f"⚠️ Whisper {model} 模型未下载 ({size})\n点击下方「下载模型」按钮下载"
    except Exception as e:
        return f"❌ 检查失败: {str(e)}"


def _download_whisper(model: str) -> str:
    """下载Whisper模型"""
    import asyncio

    async def download():
        from src.services.whisper import WhisperClient, WhisperConfig
        config = WhisperConfig(model_size=model)
        client = WhisperClient(config)

        progress = []
        async for status in client.download_model(model):
            progress.append(status)

        await client.close()
        return progress

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(download())
        loop.close()

        return "\n".join(result) if result else "下载完成"
    except Exception as e:
        return f"❌ 下载失败: {str(e)}"


def _refresh_voice_list():
    """刷新音色列表"""
    return gr.update(choices=["xiaomo", "xiaoyu", "xiaoming"])


def _refresh_avatar_list():
    """刷新数字人列表"""
    return gr.update(choices=["小美", "小雅", "小帅", "老王"])


def _extract_text(link: str) -> tuple:
    """提取视频文案"""
    if not link or not link.strip():
        return "", "请输入视频链接"

    import asyncio

    async def extract():
        from src.browser.video_extractor import VideoExtractor
        from src.browser.cookie_manager import get_cookie_manager

        # 检测平台并加载对应Cookie
        extractor = VideoExtractor(whisper_model="base")
        platform = extractor.detect_platform(link.strip())

        cookies = {}
        # 加载已保存的Cookie
        if platform in ["douyin", "kuaishou", "xiaohongshu"]:
            manager = get_cookie_manager()
            saved_cookies = manager.load_cookies(platform)
            if saved_cookies:
                for c in saved_cookies:
                    if 'name' in c and 'value' in c:
                        cookies[c['name']] = c['value']
                extractor.cookies = cookies

        result = await extractor.extract(link.strip())
        if result.success:
            return result.transcript, result.metadata.platform, result.metadata.title
        return None, None, None

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        transcript, platform, title = loop.run_until_complete(extract())
        loop.close()

        if transcript:
            preview = f"{title}\n{'-'*20}\n{transcript[:200]}..." if title else transcript[:200]
            return transcript, f"提取成功 ({platform})\n{'-'*20}\n{preview}"
        else:
            # Fallback: 使用原来的LinkParser
            async def extract_fallback():
                from src.browser.link_parser import LinkParser
                parser = LinkParser()
                result = await parser.parse(link.strip())
                await parser.close()
                return result

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(extract_fallback())
            loop.close()

            if result.success:
                return result.text, f"提取成功 ({result.platform})\n{'-'*20}\n{result.text[:200]}..."
            else:
                return "", f"提取失败: {result.error}\n\n提示: 抖音/快手等内容平台可能需要登录后才能提取文案。\n建议先扫码登录。"
    except Exception as e:
        return "", f"提取错误: {str(e)}\n\n请确保已安装Playwright并配置好浏览器。"


def _execute_rewrite(text: str, mode: str, prompt: str, provider: str) -> tuple:
    """执行AI改写"""
    if not text or not text.strip():
        return "", "请输入需要改写的文案"

    # 如果选择 Ollama，使用本地模型
    if provider == "ollama":
        return _rewrite_with_ollama(text, mode, prompt)

    # 否则使用云端API
    from src.business.rewriter.router import RewriterRouter, RewriteRequest
    import asyncio

    async def rewrite():
        router = RewriterRouter()
        await router.initialize()
        result = await router.rewrite(RewriteRequest(
            text=text,
            style="亲切" if mode == "AI自动仿写" else None
        ))
        await router.close()
        return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(rewrite())
        loop.close()

        if result.success:
            return result.rewritten_text, "改写完成"
        else:
            return text, f"改写失败: {result.error}"
    except Exception as e:
        return text, f"改写错误: {str(e)}"


def _rewrite_with_ollama(text: str, mode: str, prompt: str) -> tuple:
    """使用本地Ollama模型改写"""
    import asyncio

    style_prompt = "亲切自然、口语化，适合短视频口播" if mode == "AI自动仿写" else prompt

    system_prompt = f"""你是一个专业的文案改写专家。请将下面的文案改写成"{style_prompt}"的风格。

要求：
1. 保持原意不变
2. 语言通顺流畅，适合短视频口播
3. 突出重点信息
4. 如果是指令模式，严格按照指令改写"""

    async def rewrite():
        from src.services.ollama import OllamaClient, OllamaConfig
        config = OllamaConfig(model="qwen2.5:7b")
        client = OllamaClient(config)
        result = await client.generate(
            prompt=f"原文：\n{text}\n\n请根据上述要求改写文案：",
            system=system_prompt
        )
        await client.close()
        return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(rewrite())
        loop.close()

        if "error" in result:
            return text, f"Ollama改写失败: {result['error']}"

        rewritten = result.get("response", "").strip()
        if rewritten:
            return rewritten, "改写完成 (Ollama本地模型)"
        else:
            return text, "改写结果为空，请检查Ollama服务是否正常"
    except Exception as e:
        return text, f"Ollama错误: {str(e)}\n\n请确保已启动 Ollama: ollama serve"


def _create_audio(text: str, voice: str, speed: float, provider: str) -> tuple:
    """生成配音"""
    if not text or not text.strip():
        return None, "请输入需要转换的文案"

    from src.business.tts.router import TTSRouter, TTSRequest, TTSConfig, TTSMode
    import asyncio

    async def tts():
        config = TTSConfig(
            mode=TTSMode.LOCAL if provider == "voicebox" else TTSMode.CLOUD,
            provider=provider
        )
        router = TTSRouter(config)
        await router.initialize()
        result = await router.synthesize(TTSRequest(
            text=text,
            voice=voice,
            speed=speed
        ))
        await router.close()
        return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(tts())
        loop.close()

        if result.success:
            return result.audio_path, f"配音生成成功 ({provider})"
        else:
            return None, f"配音生成失败: {result.error}"
    except Exception as e:
        return None, f"配音生成错误: {str(e)}"


def _create_subtitle(audio_path: str, text: str) -> tuple:
    """使用Whisper生成字幕"""
    if not audio_path:
        return "", "请先生成配音"

    import asyncio

    async def transcribe():
        from src.services.whisper import WhisperClient, WhisperConfig
        config = WhisperConfig(model_size="base", language="zh")
        client = WhisperClient(config)
        result = await client.transcribe(audio_path, language="zh")
        await client.close()
        return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(transcribe())
        loop.close()

        if result["success"]:
            srt_content = _generate_srt(result["segments"])
            return srt_content, f"字幕生成成功 ({len(result['segments'])} 段)"
        else:
            return "", f"字幕生成失败: {result.get('error')}"
    except Exception as e:
        return "", f"字幕生成错误: {str(e)}"


def _generate_srt(segments: list) -> str:
    """生成SRT格式字幕"""
    srt_lines = []

    for i, seg in enumerate(segments, 1):
        start = _format_timestamp(seg["start"])
        end = _format_timestamp(seg["end"])
        text = seg["text"]

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")

    return "\n".join(srt_lines)


def _format_timestamp(seconds: float) -> str:
    """格式化时间戳为SRT格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _generate_video(
    script: str, audio_path: str, avatar: str,
    background: str, motion: str, aspect_ratio: str
) -> tuple:
    """生成数字人视频"""
    from src.business.digital_human.router import DigitalHumanRouter, DigitalHumanRequest
    import asyncio

    async def generate():
        router = DigitalHumanRouter()
        await router.initialize()
        result = await router.generate(DigitalHumanRequest(
            script=script or "默认文案",
            avatar_id=avatar,
            background_id=background,
            motion=motion,
            aspect_ratio=aspect_ratio.replace(" ", "").replace("竖屏", ":16").replace("横屏", ":9")
        ))
        await router.close()
        return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate())
        loop.close()

        if result.success:
            return result.video_path, "视频生成成功"
        else:
            return None, f"视频生成失败: {result.error}"
    except Exception as e:
        return None, f"视频生成错误: {str(e)}"


def _add_bgm(video_path: str, volume: float) -> tuple:
    """添加BGM"""
    if not video_path:
        return None, "请先生成视频"
    return video_path, f"BGM设置已保存（音量: {volume}）"


def _generate_cover(text: str, font_size: float, font_color: str) -> tuple:
    """生成封面"""
    if not text:
        return None, "请输入封面文案"
    # TODO: 实现封面生成
    return None, "封面生成功能开发中..."


def _publish(platform: str, video_path: str, title: str) -> str:
    """发布到单个平台"""
    if not video_path:
        return "请先生成视频"
    return f"发布到{platform}功能开发中..."


def _publish_all(video_path: str, title: str) -> str:
    """一键发布"""
    if not video_path:
        return "请先生成视频"
    return "一键发布功能开发中..."


def main():
    """主函数"""
    import os
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))

    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()