"""设置对话框"""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QFormLayout,
    QWidget, QMessageBox, QComboBox, QGroupBox, QSpinBox,
)
from PyQt6.QtCore import QSettings
from loguru import logger


class SettingsDialog(QDialog):
    """系统设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.setMinimumSize(600, 500)
        self._settings = QSettings("KBSZR", "config")
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_api_tab(), "API 密钥")
        self.tabs.addTab(self._create_local_tab(), "本地服务")
        self.tabs.addTab(self._create_output_tab(), "输出设置")
        layout.addWidget(self.tabs)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white;
                border: none; padding: 8px 24px; border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555; color: white;
                border: none; padding: 8px 24px; border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #666; }
        """)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _create_api_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setSpacing(10)

        # API密钥分组
        api_group = QGroupBox("文案改写 API")
        api_group_layout = QFormLayout(api_group)

        self.provider_select = QComboBox()
        self.provider_select.addItems(["tongyi", "openai", "claude", "deepseek", "doubao"])
        api_group_layout.addRow("默认供应商:", self.provider_select)

        self.tongyi_key = QLineEdit()
        self.tongyi_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.tongyi_key.setPlaceholderText("通义千问 API Key")
        api_group_layout.addRow("Tongyi Key:", self.tongyi_key)

        self.tongyi_model = QLineEdit("qwen-max")
        api_group_layout.addRow("Tongyi 模型:", self.tongyi_model)

        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setPlaceholderText("OpenAI API Key")
        api_group_layout.addRow("OpenAI Key:", self.openai_key)

        self.openai_model = QLineEdit("gpt-4o")
        api_group_layout.addRow("OpenAI 模型:", self.openai_model)

        self.claude_key = QLineEdit()
        self.claude_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.claude_key.setPlaceholderText("Claude API Key")
        api_group_layout.addRow("Claude Key:", self.claude_key)

        self.claude_model = QLineEdit("claude-3-5-sonnet")
        api_group_layout.addRow("Claude 模型:", self.claude_model)

        self.deepseek_key = QLineEdit()
        self.deepseek_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.deepseek_key.setPlaceholderText("DeepSeek API Key")
        api_group_layout.addRow("DeepSeek Key:", self.deepseek_key)

        self.deepseek_model = QLineEdit("deepseek-chat")
        api_group_layout.addRow("DeepSeek 模型:", self.deepseek_model)

        self.doubao_key = QLineEdit()
        self.doubao_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.doubao_key.setPlaceholderText("豆包 API Key")
        api_group_layout.addRow("Doubao Key:", self.doubao_key)

        self.doubao_model = QLineEdit("doubao-pro")
        api_group_layout.addRow("Doubao 模型:", self.doubao_model)

        form.addRow(api_group)

        # TTS API
        tts_group = QGroupBox("语音合成 API")
        tts_group_layout = QFormLayout(tts_group)

        self.tts_provider = QComboBox()
        self.tts_provider.addItems(["volcengine", "aliyun"])
        tts_group_layout.addRow("TTS 供应商:", self.tts_provider)

        self.tts_key = QLineEdit()
        self.tts_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.tts_key.setPlaceholderText("TTS API Key")
        tts_group_layout.addRow("API Key:", self.tts_key)

        form.addRow(tts_group)

        # 数字人 API
        dh_group = QGroupBox("数字人 API")
        dh_group_layout = QFormLayout(dh_group)

        self.dh_provider = QComboBox()
        self.dh_provider.addItems(["aliyun", "tencent"])
        dh_group_layout.addRow("数字人供应商:", self.dh_provider)

        self.dh_key = QLineEdit()
        self.dh_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.dh_key.setPlaceholderText("数字人 API Key")
        dh_group_layout.addRow("API Key:", self.dh_key)

        form.addRow(dh_group)

        return widget

    def _create_local_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setSpacing(10)

        # Ollama
        ollama_group = QGroupBox("Ollama 本地模型")
        ollama_group_layout = QFormLayout(ollama_group)

        self.ollama_url = QLineEdit("http://localhost:11434")
        ollama_group_layout.addRow("服务地址:", self.ollama_url)

        self.ollama_model = QLineEdit("qwen2.5:7b")
        ollama_group_layout.addRow("生成模型:", self.ollama_model)

        self.embedding_model = QLineEdit("nomic-embed-text")
        ollama_group_layout.addRow("嵌入模型:", self.embedding_model)

        form.addRow(ollama_group)

        # Whisper
        whisper_group = QGroupBox("Whisper 语音识别")
        whisper_group_layout = QFormLayout(whisper_group)

        self.whisper_model = QComboBox()
        self.whisper_model.addItems(["tiny", "base", "small", "medium", "large"])
        whisper_group_layout.addRow("模型大小:", self.whisper_model)

        form.addRow(whisper_group)

        # 改写模式
        rewrite_group = QGroupBox("改写策略")
        rewrite_group_layout = QFormLayout(rewrite_group)

        self.rewrite_mode = QComboBox()
        self.rewrite_mode.addItems(["auto", "local", "cloud"])
        rewrite_group_layout.addRow("改写模式:", self.rewrite_mode)

        self.auto_local_threshold = QSpinBox()
        self.auto_local_threshold.setRange(10, 1000)
        self.auto_local_threshold.setValue(100)
        self.auto_local_threshold.setSuffix(" 字")
        rewrite_group_layout.addRow("本地改写阈值:", self.auto_local_threshold)

        form.addRow(rewrite_group)

        # FFmpeg
        ffmpeg_group = QGroupBox("FFmpeg")
        ffmpeg_group_layout = QFormLayout(ffmpeg_group)

        self.ffmpeg_path = QLineEdit("ffmpeg")
        ffmpeg_group_layout.addRow("路径:", self.ffmpeg_path)

        form.addRow(ffmpeg_group)

        return widget

    def _create_output_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setSpacing(10)

        output_group = QGroupBox("输出目录")
        output_group_layout = QFormLayout(output_group)

        self.output_dir = QLineEdit("./data/output")
        output_group_layout.addRow("视频输出:", self.output_dir)

        self.voice_dir = QLineEdit("./data/voices")
        output_group_layout.addRow("语音输出:", self.voice_dir)

        form.addRow(output_group)

        queue_group = QGroupBox("任务队列")
        queue_group_layout = QFormLayout(queue_group)

        self.max_concurrency = QSpinBox()
        self.max_concurrency.setRange(1, 20)
        self.max_concurrency.setValue(5)
        queue_group_layout.addRow("最大并发:", self.max_concurrency)

        self.min_interval = QSpinBox()
        self.min_interval.setRange(1, 120)
        self.min_interval.setValue(10)
        self.min_interval.setSuffix(" 秒")
        queue_group_layout.addRow("最小间隔:", self.min_interval)

        form.addRow(queue_group)

        return widget

    def _load_settings(self):
        """加载已保存的设置"""
        # API
        self.provider_select.setCurrentText(
            self._settings.value("rewriter/provider", "tongyi"))
        self.tongyi_key.setText(self._settings.value("api/tongyi_key", ""))
        self.tongyi_model.setText(self._settings.value("api/tongyi_model", "qwen-max"))
        self.openai_key.setText(self._settings.value("api/openai_key", ""))
        self.openai_model.setText(self._settings.value("api/openai_model", "gpt-4o"))
        self.claude_key.setText(self._settings.value("api/claude_key", ""))
        self.claude_model.setText(self._settings.value("api/claude_model", "claude-3-5-sonnet"))
        self.deepseek_key.setText(self._settings.value("api/deepseek_key", ""))
        self.deepseek_model.setText(self._settings.value("api/deepseek_model", "deepseek-chat"))
        self.doubao_key.setText(self._settings.value("api/doubao_key", ""))
        self.doubao_model.setText(self._settings.value("api/doubao_model", "doubao-pro"))
        self.tts_provider.setCurrentText(self._settings.value("tts/provider", "volcengine"))
        self.tts_key.setText(self._settings.value("api/tts_key", ""))
        self.dh_provider.setCurrentText(self._settings.value("dh/provider", "aliyun"))
        self.dh_key.setText(self._settings.value("api/dh_key", ""))

        # 本地服务
        self.ollama_url.setText(self._settings.value("local/ollama_url", "http://localhost:11434"))
        self.ollama_model.setText(self._settings.value("local/ollama_model", "qwen2.5:7b"))
        self.embedding_model.setText(self._settings.value("local/embedding_model", "nomic-embed-text"))
        self.whisper_model.setCurrentText(
            self._settings.value("local/whisper_model", "base"))
        self.rewrite_mode.setCurrentText(
            self._settings.value("rewriter/mode", "auto"))
        self.auto_local_threshold.setValue(
            int(self._settings.value("rewriter/local_threshold", 100)))
        self.ffmpeg_path.setText(self._settings.value("local/ffmpeg_path", "ffmpeg"))

        # 输出
        self.output_dir.setText(self._settings.value("output/video_dir", "./data/output"))
        self.voice_dir.setText(self._settings.value("output/voice_dir", "./data/voices"))
        self.max_concurrency.setValue(int(self._settings.value("queue/max_concurrency", 5)))
        self.min_interval.setValue(int(self._settings.value("queue/min_interval", 10)))

    def _on_save(self):
        """保存设置"""
        try:
            # API
            self._settings.setValue("rewriter/provider", self.provider_select.currentText())
            self._settings.setValue("api/tongyi_key", self.tongyi_key.text())
            self._settings.setValue("api/tongyi_model", self.tongyi_model.text())
            self._settings.setValue("api/openai_key", self.openai_key.text())
            self._settings.setValue("api/openai_model", self.openai_model.text())
            self._settings.setValue("api/claude_key", self.claude_key.text())
            self._settings.setValue("api/claude_model", self.claude_model.text())
            self._settings.setValue("api/deepseek_key", self.deepseek_key.text())
            self._settings.setValue("api/deepseek_model", self.deepseek_model.text())
            self._settings.setValue("api/doubao_key", self.doubao_key.text())
            self._settings.setValue("api/doubao_model", self.doubao_model.text())
            self._settings.setValue("tts/provider", self.tts_provider.currentText())
            self._settings.setValue("api/tts_key", self.tts_key.text())
            self._settings.setValue("dh/provider", self.dh_provider.currentText())
            self._settings.setValue("api/dh_key", self.dh_key.text())

            # 本地服务
            self._settings.setValue("local/ollama_url", self.ollama_url.text())
            self._settings.setValue("local/ollama_model", self.ollama_model.text())
            self._settings.setValue("local/embedding_model", self.embedding_model.text())
            self._settings.setValue("local/whisper_model", self.whisper_model.currentText())
            self._settings.setValue("rewriter/mode", self.rewrite_mode.currentText())
            self._settings.setValue("rewriter/local_threshold", self.auto_local_threshold.value())
            self._settings.setValue("local/ffmpeg_path", self.ffmpeg_path.text())

            # 输出
            self._settings.setValue("output/video_dir", self.output_dir.text())
            self._settings.setValue("output/voice_dir", self.voice_dir.text())
            self._settings.setValue("queue/max_concurrency", self.max_concurrency.value())
            self._settings.setValue("queue/min_interval", self.min_interval.value())

            self._settings.sync()
            logger.info("Settings saved")
            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(self, "错误", f"保存设置失败: {e}")
