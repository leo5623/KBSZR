"""设置视图"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QLineEdit, QComboBox,
    QFormLayout, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt, QSettings
from ..theme import COLORS, get_input_qss, get_neon_glow
from ..widgets import NeonButton


class SettingsView(QWidget):
    """
    设置视图 - 赛博朋克风格的设置界面
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("KBSZR", "config")
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 标题
        title = QLabel("⚙️ 系统设置")
        title.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 20px;
            font-weight: 600;
        """)
        main_layout.addWidget(title)

        # 可滚动设置区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.Box)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)

        # API设置区域
        api_section = self._create_api_section()
        container_layout.addWidget(api_section)

        # 本地服务设置
        local_section = self._create_local_section()
        container_layout.addWidget(local_section)

        # 输出设置
        output_section = self._create_output_section()
        container_layout.addWidget(output_section)

        container_layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # 保存按钮
        save_bar = self._create_save_bar()
        main_layout.addWidget(save_bar)

    def _create_api_section(self) -> QFrame:
        """创建API设置区域"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("🔑 API 密钥")
        title.setStyleSheet(f"""
            color: {COLORS['PRIMARY_NEON']};
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(title)

        # 文案改写API
        rewriter_group = QGroupBox("文案改写")
        rewriter_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['TEXT_PRIMARY']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 8px;
                padding: 16px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        rewriter_layout = QFormLayout()
        rewriter_layout.setSpacing(12)

        self._provider_combo = QComboBox()
        self._provider_combo.addItems([
            "tongyi", "qwen-turbo", "openai", "claude", "deepseek",
            "doubao", "wenxin", "hunyuan", "spark", "minimax"
        ])
        self._provider_combo.setStyleSheet(get_input_qss())

        self._rewriter_key_input = QLineEdit()
        self._rewriter_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._rewriter_key_input.setPlaceholderText("输入 API Key")
        self._rewriter_key_input.setStyleSheet(get_input_qss())

        rewriter_layout.addRow("默认供应商:", self._provider_combo)
        rewriter_layout.addRow("API Key:", self._rewriter_key_input)

        rewriter_group.setLayout(rewriter_layout)
        layout.addWidget(rewriter_group)

        # TTS API
        tts_group = QGroupBox("语音合成 TTS")
        tts_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['TEXT_PRIMARY']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 8px;
                padding: 16px;
                margin-top: 10px;
            }}
        """)

        tts_layout = QFormLayout()
        tts_layout.setSpacing(12)

        self._tts_provider_combo = QComboBox()
        self._tts_provider_combo.addItems(["aliyun", "volcengine"])
        self._tts_provider_combo.setStyleSheet(get_input_qss())

        self._tts_key_input = QLineEdit()
        self._tts_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._tts_key_input.setPlaceholderText("输入 TTS API Key")
        self._tts_key_input.setStyleSheet(get_input_qss())

        tts_layout.addRow("供应商:", self._tts_provider_combo)
        tts_layout.addRow("API Key:", self._tts_key_input)

        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)

        # 数字人API
        dh_group = QGroupBox("数字人")
        dh_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['TEXT_PRIMARY']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 8px;
                padding: 16px;
                margin-top: 10px;
            }}
        """)

        dh_layout = QFormLayout()
        dh_layout.setSpacing(12)

        self._dh_key_input = QLineEdit()
        self._dh_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._dh_key_input.setPlaceholderText("输入数字人 API Key")
        self._dh_key_input.setStyleSheet(get_input_qss())

        dh_layout.addRow("API Key:", self._dh_key_input)

        dh_group.setLayout(dh_layout)
        layout.addWidget(dh_group)

        return frame

    def _create_local_section(self) -> QFrame:
        """创建本地服务设置"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🖥️ 本地服务")
        title.setStyleSheet(f"""
            color: {COLORS['SECONDARY_NEON']};
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self._ffmpeg_path = QLineEdit("ffmpeg")
        self._ffmpeg_path.setStyleSheet(get_input_qss())

        self._whisper_model = QComboBox()
        self._whisper_model.addItems(["tiny", "base", "small", "medium", "large"])
        self._whisper_model.setStyleSheet(get_input_qss())

        self._ollama_url = QLineEdit("http://localhost:11434")
        self._ollama_url.setStyleSheet(get_input_qss())

        form_layout.addRow("FFmpeg 路径:", self._ffmpeg_path)
        form_layout.addRow("Whisper 模型:", self._whisper_model)
        form_layout.addRow("Ollama 地址:", self._ollama_url)

        layout.addLayout(form_layout)

        return frame

    def _create_output_section(self) -> QFrame:
        """创建输出设置"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📁 输出设置")
        title.setStyleSheet(f"""
            color: {COLORS['ACCENT']};
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self._output_dir = QLineEdit("./data/output")
        self._output_dir.setStyleSheet(get_input_qss())

        self._voice_dir = QLineEdit("./data/voices")
        self._voice_dir.setStyleSheet(get_input_qss())

        form_layout.addRow("视频输出:", self._output_dir)
        form_layout.addRow("语音输出:", self._voice_dir)

        layout.addLayout(form_layout)

        return frame

    def _create_save_bar(self) -> QFrame:
        """创建保存栏"""
        frame = QFrame()
        frame.setFixedHeight(60)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)

        layout.addStretch()

        save_btn = NeonButton("💾 保存设置", variant="primary")
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        reset_btn = NeonButton("🔄 重置", variant="ghost")
        reset_btn.clicked.connect(self._load_settings)
        layout.addWidget(reset_btn)

        return frame

    def _load_settings(self):
        """加载设置"""
        self._provider_combo.setCurrentText(
            self._settings.value("rewriter/provider", "tongyi"))
        self._rewriter_key_input.setText(
            self._settings.value("api/rewriter_key", ""))
        self._tts_provider_combo.setCurrentText(
            self._settings.value("tts/provider", "aliyun"))
        self._tts_key_input.setText(
            self._settings.value("api/tts_key", ""))
        self._dh_key_input.setText(
            self._settings.value("api/dh_key", ""))
        self._ffmpeg_path.setText(
            self._settings.value("local/ffmpeg_path", "ffmpeg"))
        self._whisper_model.setCurrentText(
            self._settings.value("local/whisper_model", "base"))
        self._ollama_url.setText(
            self._settings.value("local/ollama_url", "http://localhost:11434"))
        self._output_dir.setText(
            self._settings.value("output/video_dir", "./data/output"))
        self._voice_dir.setText(
            self._settings.value("output/voice_dir", "./data/voices"))

    def _on_save(self):
        """保存设置"""
        self._settings.setValue("rewriter/provider", self._provider_combo.currentText())
        self._settings.setValue("api/rewriter_key", self._rewriter_key_input.text())
        self._settings.setValue("tts/provider", self._tts_provider_combo.currentText())
        self._settings.setValue("api/tts_key", self._tts_key_input.text())
        self._settings.setValue("api/dh_key", self._dh_key_input.text())
        self._settings.setValue("local/ffmpeg_path", self._ffmpeg_path.text())
        self._settings.setValue("local/whisper_model", self._whisper_model.currentText())
        self._settings.setValue("local/ollama_url", self._ollama_url.text())
        self._settings.setValue("output/video_dir", self._output_dir.text())
        self._settings.setValue("output/voice_dir", self._voice_dir.text())
        self._settings.sync()

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "成功", "设置已保存")