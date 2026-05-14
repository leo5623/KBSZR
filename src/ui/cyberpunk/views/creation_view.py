"""创作视图 - 链接解析+文案改写工作流"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QFrame,
    QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from ..theme import COLORS, get_card_qss, get_input_qss, get_neon_glow
from ..widgets import CyberCard, NeonButton


class ParseWorker(QThread):
    """链接解析工作线程"""
    finished = pyqtSignal(dict)  # 解析结果
    error = pyqtSignal(str)      # 错误信息

    def __init__(self, link: str, cookies: dict = None):
        super().__init__()
        self._link = link
        self._cookies = cookies or {}

    def run(self):
        try:
            from src.browser.video_extractor import VideoExtractor
            import asyncio

            async def parse():
                extractor = VideoExtractor(whisper_model="base")
                extractor.cookies = self._cookies
                result = await extractor.extract(self._link)
                return result

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(parse())
            loop.close()

            self.finished.emit({
                "success": result.success,
                "text": result.transcript,
                "title": result.metadata.title if result.metadata else '',
                "platform": result.metadata.platform if result.metadata else 'unknown',
                "error": result.error
            })
        except Exception as e:
            self.error.emit(str(e))


class QrLoginWorker(QThread):
    """扫码登录工作线程"""
    finished = pyqtSignal(dict)  # 登录结果
    error = pyqtSignal(str)      # 错误信息

    def __init__(self, platform: str):
        super().__init__()
        self._platform = platform

    def run(self):
        try:
            from src.browser.cookie_manager import get_cookie_manager
            import asyncio

            async def login():
                manager = get_cookie_manager()
                result = await manager.qr_login(self._platform)
                return result

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(login())
            loop.close()

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class RewriteWorker(QThread):
    """文案改写工作线程"""
    finished = pyqtSignal(dict)  # 改写结果
    error = pyqtSignal(str)      # 错误信息

    def __init__(self, text: str, industry: str, scenario: str, style: str):
        super().__init__()
        self._text = text
        self._industry = industry
        self._scenario = scenario
        self._style = style

    def run(self):
        try:
            from src.business.rewriter.router import RewriterRouter
            from src.business.rewriter.router import RewriteRequest
            import asyncio

            async def rewrite():
                router = RewriterRouter()
                await router.initialize()
                result = await router.rewrite(RewriteRequest(
                    text=self._text,
                    industry=self._industry,
                    scenario=self._scenario,
                    style=self._style
                ))
                await router.close()
                return result

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(rewrite())
            loop.close()

            self.finished.emit({
                "success": result.success,
                "original_text": result.original_text,
                "rewritten_text": result.rewritten_text,
                "error": result.error
            })
        except Exception as e:
            self.error.emit(str(e))


class CreationView(QWidget):
    """
    创作视图
    水平步骤指示器: [1.链接] → [2.解析] → [3.改写] → [4.配音] → [5.预览]
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parse_worker = None
        self._rewrite_worker = None
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 步骤指示器
        steps_frame = self._create_steps_indicator()
        main_layout.addWidget(steps_frame)

        # 登录区域
        login_frame = self._create_login_panel()
        main_layout.addWidget(login_frame)

        # 主体内容区
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 左侧：输入区
        input_panel = self._create_input_panel()
        content_layout.addWidget(input_panel, 1)

        # 中间：操作按钮
        action_panel = self._create_action_panel()
        content_layout.addWidget(action_panel)

        # 右侧：输出区
        output_panel = self._create_output_panel()
        content_layout.addWidget(output_panel, 1)

        main_layout.addLayout(content_layout)

        # 状态栏
        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")
        main_layout.addWidget(self._status_label)

    def _create_steps_indicator(self) -> QFrame:
        """创建步骤指示器"""
        frame = QFrame()
        frame.setFixedHeight(60)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 0, 20, 0)

        steps = [
            {"num": "1", "text": "链接"},
            {"num": "2", "text": "解析"},
            {"num": "3", "text": "改写"},
            {"num": "4", "text": "配音"},
            {"num": "5", "text": "预览"},
        ]

        self._step_labels = []

        for i, step in enumerate(steps):
            # 步骤圆圈
            step_widget = QWidget()
            step_layout = QVBoxLayout(step_widget)
            step_layout.setSpacing(4)

            num_label = QLabel(step["num"])
            num_label.setFixedSize(28, 28)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet(f"""
                background: {COLORS['CARD']};
                color: {COLORS['TEXT_SECONDARY']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 14px;
                font-size: 13px;
                font-weight: 600;
            """)

            text_label = QLabel(step["text"])
            text_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")

            step_layout.addWidget(num_label, 0, Qt.AlignmentFlag.AlignCenter)
            step_layout.addWidget(text_label, 0, Qt.AlignmentFlag.AlignCenter)

            self._step_labels.append(num_label)

            layout.addWidget(step_widget)

            # 箭头（除了最后一个）
            if i < len(steps) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet(f"color: {COLORS['BORDER']}; font-size: 18px;")
                layout.addWidget(arrow)

            layout.addStretch()

        return frame

    def _create_login_panel(self) -> QFrame:
        """创建登录面板"""
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 8px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # 说明
        info_label = QLabel("账号登录 - 扫码登录后可提取会员专属内容")
        info_label.setStyleSheet(f"color: {COLORS['TEXT_PRIMARY']}; font-size: 13px;")
        layout.addWidget(info_label)

        layout.addStretch()

        # 平台选择
        self._login_platform = QComboBox()
        self._login_platform.addItems(["抖音", "快手", "小红书"])
        self._login_platform.setFixedWidth(100)
        self._login_platform.setStyleSheet(get_input_qss())
        layout.addWidget(self._login_platform)

        # 扫码登录按钮
        self._qr_login_btn = NeonButton("📱 扫码登录", variant="primary")
        self._qr_login_btn.clicked.connect(self._on_qr_login_clicked)
        layout.addWidget(self._qr_login_btn)

        # 登录状态
        self._login_status = QLabel("")
        self._login_status.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")
        layout.addWidget(self._login_status)

        return frame

    def _create_input_panel(self) -> CyberCard:
        """创建输入面板"""
        card = CyberCard(title="📥 输入文案", neon_color="cyan")
        card.setStyleSheet(get_card_qss(False, "cyan"))

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # 链接输入
        link_label = QLabel("视频链接")
        link_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")

        self._link_input = QLineEdit()
        self._link_input.setPlaceholderText("粘贴抖音/快手/小红书链接...")
        self._link_input.setStyleSheet(get_input_qss())

        # 解析按钮
        parse_btn = NeonButton("🔍 解析链接", variant="secondary")
        parse_btn.clicked.connect(self._on_parse_clicked)

        # 文案输入区
        text_label = QLabel("或直接输入文案")
        text_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")

        self._text_input = QTextEdit()
        self._text_input.setPlaceholderText("在此输入需要改写的文案...")
        self._text_input.setStyleSheet(get_input_qss())
        self._text_input.setMinimumHeight(150)

        layout.addWidget(link_label)
        layout.addWidget(self._link_input)
        layout.addWidget(parse_btn)
        layout.addWidget(text_label)
        layout.addWidget(self._text_input, 1)

        # 添加到卡片的布局
        card.layout().addLayout(layout)

        return card

    def _create_action_panel(self) -> QWidget:
        """创建操作面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 100, 0, 0)

        # 参数设置
        param_label = QLabel("参数设置")
        param_label.setStyleSheet(f"color: {COLORS['TEXT_PRIMARY']}; font-size: 13px; font-weight: 600;")
        layout.addWidget(param_label)

        # 行业选择
        industry_label = QLabel("行业")
        industry_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")

        self._industry_combo = QComboBox()
        self._industry_combo.addItems(["不指定", "beauty", "knowledge", "ecommerce", "food", "education"])
        self._industry_combo.setStyleSheet(get_input_qss())

        # 场景选择
        scenario_label = QLabel("场景")
        scenario_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")

        self._scenario_combo = QComboBox()
        self._scenario_combo.addItems(["不指定", "种草安利", "干货分享", "教程分享", "产品介绍"])
        self._scenario_combo.setStyleSheet(get_input_qss())

        # 风格选择
        style_label = QLabel("风格")
        style_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 12px;")

        self._style_combo = QComboBox()
        self._style_combo.addItems(["不指定", "亲切", "专业", "活泼", "沉稳"])
        self._style_combo.setStyleSheet(get_input_qss())

        layout.addWidget(industry_label)
        layout.addWidget(self._industry_combo)
        layout.addWidget(scenario_label)
        layout.addWidget(self._scenario_combo)
        layout.addWidget(style_label)
        layout.addWidget(self._style_combo)

        # 改写按钮
        rewrite_btn = NeonButton("✍️ 一键改写", variant="primary")
        rewrite_btn.clicked.connect(self._on_rewrite_clicked)

        # TTS按钮
        tts_btn = NeonButton("🎙️ 生成配音", variant="secondary")
        tts_btn.clicked.connect(self._on_tts_clicked)

        layout.addStretch()
        layout.addWidget(rewrite_btn)
        layout.addWidget(tts_btn)

        return panel

    def _create_output_panel(self) -> CyberCard:
        """创建输出面板"""
        card = CyberCard(title="📤 输出结果", neon_color="magenta")
        card.setStyleSheet(get_card_qss(False, "magenta"))

        layout = QVBoxLayout()

        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setPlaceholderText("改写后的文案将显示在这里...")
        self._output_text.setStyleSheet(get_input_qss())
        self._output_text.setMinimumHeight(200)

        # 保存按钮
        save_btn = NeonButton("💾 保存文案", variant="ghost")
        save_btn.clicked.connect(self._on_save_clicked)

        layout.addWidget(self._output_text)
        layout.addWidget(save_btn)

        card.layout().addLayout(layout)

        return card

    def _update_step(self, step: int):
        """更新步骤指示器"""
        for i, label in enumerate(self._step_labels):
            if i < step:
                label.setStyleSheet(f"""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['PRIMARY_NEON']}, stop:1 {COLORS['ACCENT']});
                    color: {COLORS['BACKGROUND']};
                    border: none;
                    border-radius: 14px;
                    font-size: 13px;
                    font-weight: 600;
                """)
            elif i == step:
                label.setStyleSheet(f"""
                    background: {COLORS['SECONDARY_NEON']};
                    color: {COLORS['BACKGROUND']};
                    border: none;
                    border-radius: 14px;
                    font-size: 13px;
                    font-weight: 600;
                """)
            else:
                label.setStyleSheet(f"""
                    background: {COLORS['CARD']};
                    color: {COLORS['TEXT_SECONDARY']};
                    border: 1px solid {COLORS['BORDER']};
                    border-radius: 14px;
                    font-size: 13px;
                    font-weight: 600;
                """)

    def _on_qr_login_clicked(self):
        """扫码登录按钮点击"""
        platform_map = {"抖音": "douyin", "快手": "kuaishou", "小红书": "xiaohongshu"}
        platform = platform_map.get(self._login_platform.currentText(), "douyin")

        self._login_status.setText("正在打开登录页面...")
        self._qr_login_btn.setEnabled(False)

        self._qr_login_worker = QrLoginWorker(platform)
        self._qr_login_worker.finished.connect(self._on_qr_login_finished)
        self._qr_login_worker.error.connect(self._on_qr_login_error)
        self._qr_login_worker.start()

    def _on_qr_login_finished(self, result: dict):
        """扫码登录完成"""
        self._qr_login_btn.setEnabled(True)

        if result["success"]:
            self._login_status.setText(f"登录成功 ({len(result['cookies'])} cookies)")
            self._login_status.setStyleSheet(f"color: {COLORS['SUCCESS']}; font-size: 12px;")
        else:
            self._login_status.setText(f"登录失败: {result.get('error', '未知错误')}")
            self._login_status.setStyleSheet(f"color: {COLORS['ERROR']}; font-size: 12px;")

    def _on_qr_login_error(self, error: str):
        """扫码登录错误"""
        self._qr_login_btn.setEnabled(True)
        self._login_status.setText(f"登录异常: {error}")
        self._login_status.setStyleSheet(f"color: {COLORS['ERROR']}; font-size: 12px;")

    def _on_parse_clicked(self):
        """解析链接按钮点击"""
        link = self._link_input.text().strip()
        if not link:
            self._status_label.setText("请输入链接")
            return

        self._status_label.setText("正在解析链接...")
        self._update_step(1)

        # 加载保存的Cookie
        from src.browser.cookie_manager import get_cookie_manager
        platform_map = {"抖音": "douyin", "快手": "kuaishou", "小红书": "xiaohongshu"}
        platform = platform_map.get(self._login_platform.currentText(), "douyin")

        cookies = {}
        manager = get_cookie_manager()
        saved_cookies = manager.load_cookies(platform)
        if saved_cookies:
            for c in saved_cookies:
                if 'name' in c and 'value' in c:
                    cookies[c['name']] = c['value']

        self._parse_worker = ParseWorker(link, cookies)
        self._parse_worker.finished.connect(self._on_parse_finished)
        self._parse_worker.error.connect(self._on_parse_error)
        self._parse_worker.start()

    def _on_parse_finished(self, result: dict):
        """解析完成"""
        if result["success"]:
            self._text_input.setPlainText(result["text"])
            self._status_label.setText(f"解析成功 ({result['platform']})")
            self._update_step(1)
        else:
            self._status_label.setText(f"解析失败: {result['error']}")

    def _on_parse_error(self, error: str):
        """解析错误"""
        self._status_label.setText(f"解析错误: {error}")

    def _on_rewrite_clicked(self):
        """改写按钮点击"""
        text = self._text_input.toPlainText().strip()
        if not text:
            self._status_label.setText("请输入需要改写的文案")
            return

        industry = self._industry_combo.currentText()
        scenario = self._scenario_combo.currentText()
        style = self._style_combo.currentText()

        industry = None if industry == "不指定" else industry
        scenario = None if scenario == "不指定" else scenario
        style = None if style == "不指定" else style

        self._status_label.setText("正在改写文案...")
        self._update_step(2)

        self._rewrite_worker = RewriteWorker(text, industry, scenario, style)
        self._rewrite_worker.finished.connect(self._on_rewrite_finished)
        self._rewrite_worker.error.connect(self._on_rewrite_error)
        self._rewrite_worker.start()

    def _on_rewrite_finished(self, result: dict):
        """改写完成"""
        if result["success"]:
            self._output_text.setPlainText(result["rewritten_text"])
            self._status_label.setText("改写完成")
            self._update_step(3)
        else:
            self._status_label.setText(f"改写失败: {result['error']}")

    def _on_rewrite_error(self, error: str):
        """改写错误"""
        self._status_label.setText(f"改写错误: {error}")

    def _on_tts_clicked(self):
        """TTS按钮点击"""
        text = self._output_text.toPlainText().strip()
        if not text:
            self._status_label.setText("请先进行文案改写")
            return

        self._status_label.setText("正在生成配音...")
        self._update_step(3)

        # TODO: 调用TTS
        self._status_label.setText("配音功能开发中...")

    def _on_save_clicked(self):
        """保存按钮点击"""
        text = self._output_text.toPlainText().strip()
        if not text:
            self._status_label.setText("没有内容可保存")
            return

        # TODO: 实现保存功能
        self._status_label.setText("文案已保存")