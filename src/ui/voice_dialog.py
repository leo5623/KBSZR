"""我的声音管理窗口 - 支持录制/播放/克隆/TTS试听"""
import os
import time
import json
import threading
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt, QUrl, QSettings, pyqtSignal, QObject, QThread
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget,
    QMessageBox, QFileDialog, QWidget, QGroupBox,
    QLineEdit, QComboBox, QProgressBar,
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from loguru import logger

# 克隆音色缓存文件
CLONED_VOICES_FILE = Path("./data/cloned_voices.json")


class RecordWorker(QObject):
    """录音工作线程（纯录音，不碰UI）"""
    finished = pyqtSignal(object)  # 传递 numpy 音频数据

    def run(self):
        try:
            import sounddevice as sd
            import numpy as np
            fs = 44100
            logger.info("Recording started...")
            recording = sd.rec(int(fs * 30), samplerate=fs, channels=1, dtype=np.int16)
            sd.wait()
            self.finished.emit(recording)
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            self.finished.emit(None)


class VoiceDialog(QDialog):
    """声音管理窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("我的声音")
        self.setMinimumSize(700, 580)

        # 播放器
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status)

        self._recording = False
        self._cloned_voices = self._load_cloned_voices()

        self._init_ui()
        self._load_voices()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # ======== 声音列表 ========
        list_group = QGroupBox("已有声音")
        list_layout = QVBoxLayout(list_group)
        self.voice_list = QListWidget()
        self.voice_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a; border: 1px solid #3d3d3d;
                border-radius: 5px; padding: 5px; color: #cccccc;
            }
            QListWidget::item { padding: 10px; border-radius: 3px; }
            QListWidget::item:selected { background-color: #4CAF50; color: white; }
            QListWidget::item:hover { background-color: #333; }
        """)
        list_layout.addWidget(self.voice_list)
        layout.addWidget(list_group)

        # ======== 操作按钮 ========
        btn_layout = QHBoxLayout()

        self.record_btn = QPushButton("🎤 录制声音")
        self.record_btn.clicked.connect(self._on_record_toggle)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white;
                border: none; padding: 8px 16px; border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)

        self.import_btn = QPushButton("导入文件")
        self.import_btn.clicked.connect(self._on_import)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._on_play)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #555; }
        """)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #555; }
        """)

        self.clone_btn = QPushButton("🔊 克隆音色")
        self.clone_btn.setEnabled(False)
        self.clone_btn.clicked.connect(self._on_clone)
        self.clone_btn.setStyleSheet("""
            QPushButton {
                background-color: #8BC34A; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #689F38; }
            QPushButton:disabled { background-color: #555; }
        """)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e; color: white;
                border: none; padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #757575; }
            QPushButton:disabled { background-color: #555; }
        """)

        btn_layout.addWidget(self.record_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.clone_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 录制进度/播放进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3d3d3d; border-radius: 3px;
                background-color: #1a1a1a; text-align: center;
                color: #888; font-size: 10px;
            }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
        """)
        layout.addWidget(self.progress_bar)

        # ======== TTS 试听区 ========
        tts_group = QGroupBox("语音合成试听")
        tts_layout = QHBoxLayout(tts_group)

        tts_layout.addWidget(QLabel("文本:"))
        self.tts_text = QLineEdit()
        self.tts_text.setPlaceholderText("输入要试听的文本...")
        self.tts_text.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a; color: #cccccc;
                border: 1px solid #3d3d3d; border-radius: 4px; padding: 6px;
            }
        """)
        tts_layout.addWidget(self.tts_text)

        tts_layout.addWidget(QLabel("音色:"))
        self.voice_select = QComboBox()
        self.voice_select.setMinimumWidth(160)
        self.voice_select.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d; color: white;
                border: none; padding: 6px; border-radius: 4px;
            }
        """)
        tts_layout.addWidget(self.voice_select)

        self.tts_play_btn = QPushButton("▶ 试听")
        self.tts_play_btn.clicked.connect(self._on_tts_preview)
        self.tts_play_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; color: white;
                border: none; padding: 8px 20px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        tts_layout.addWidget(self.tts_play_btn)

        layout.addWidget(tts_group)

        # ======== 关闭按钮 ========
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #555; color: white;
                border: none; padding: 8px 24px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #666; }
        """)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        self.voice_list.currentRowChanged.connect(self._on_selection_changed)

    # ========== 声音文件管理 ==========

    def _get_voice_paths(self) -> list[Path]:
        """获取所有声音文件路径"""
        voices_dir = Path("./data/voices")
        if not voices_dir.exists():
            voices_dir.mkdir(parents=True, exist_ok=True)
        return sorted([
            f for f in voices_dir.iterdir()
            if f.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg")
        ])

    def _load_voices(self):
        """加载声音列表"""
        self.voice_list.clear()
        self.voice_select.clear()

        for f in self._get_voice_paths():
            duration = ""
            self.voice_list.addItem(f"{f.stem}{f.suffix}")
            self.voice_select.addItem(f.stem)

        # 已克隆的音色（优先显示）
        for name, info in self._cloned_voices.items():
            self.voice_select.addItem(f"【克隆】{name} ({info['voice_id']})")

        # 火山引擎默认音色
        default_voices = [
            ("BV700_V2", "亲切女声"),
            ("BV701_V2", "温柔女声"),
            ("BV702_V2", "知性女声"),
            ("BV703_V2", "阳光男声"),
            ("BV704_V2", "沉稳男声"),
        ]
        for vid, name in default_voices:
            self.voice_select.addItem(f"{name} ({vid})")

        if self.voice_list.count() == 0:
            self.voice_list.addItem("（暂无声音，请录制或导入）")

        self._on_selection_changed(-1)

    def _on_selection_changed(self, index):
        """选中变化"""
        has = index >= 0 and self.voice_list.currentItem() is not None
        text = self.voice_list.currentItem().text() if has else ""
        is_real = has and not text.startswith("（")
        self.play_btn.setEnabled(is_real and not self._recording)
        self.clone_btn.setEnabled(is_real and not self._recording)
        self.delete_btn.setEnabled(is_real)

    def _on_import(self):
        """导入声音文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择声音文件", "",
            "音频文件 (*.mp3 *.wav *.m4a *.ogg);;所有文件 (*)"
        )
        if not files:
            return

        voices_dir = Path("./data/voices")
        voices_dir.mkdir(parents=True, exist_ok=True)

        imported = 0
        for src in files:
            src_path = Path(src)
            try:
                import shutil
                shutil.copy2(str(src_path), str(voices_dir / src_path.name))
                imported += 1
            except Exception as e:
                logger.error(f"Import failed: {src} - {e}")

        if imported > 0:
            QMessageBox.information(self, "导入成功", f"成功导入 {imported} 个文件")
            self._load_voices()
        else:
            QMessageBox.warning(self, "失败", "没有成功导入任何文件")

    def _on_delete(self):
        """删除声音"""
        item = self.voice_list.currentItem()
        if not item or item.text().startswith("（"):
            return
        name = item.text()

        reply = QMessageBox.question(
            self, "确认删除", f"删除「{name}」？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for f in Path("./data/voices").iterdir():
            if f.name == name:
                try:
                    f.unlink()
                except Exception as e:
                    logger.error(f"Delete failed: {e}")

        self._load_voices()

    # ========== 声音克隆 ==========

    def _load_cloned_voices(self) -> dict:
        """加载已克隆的音色列表"""
        if CLONED_VOICES_FILE.exists():
            try:
                return json.loads(CLONED_VOICES_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Load cloned voices failed: {e}")
        return {}

    def _save_cloned_voices(self):
        """保存已克隆的音色列表"""
        CLONED_VOICES_FILE.parent.mkdir(parents=True, exist_ok=True)
        CLONED_VOICES_FILE.write_text(
            json.dumps(self._cloned_voices, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _is_cloned_voice(self, voice_id: str) -> bool:
        """判断voice_id是否为克隆音色"""
        for info in self._cloned_voices.values():
            if info.get("voice_id") == voice_id:
                return True
        return False

    def _on_clone(self):
        """克隆选中声音"""
        item = self.voice_list.currentItem()
        if not item or item.text().startswith("（"):
            return
        name = item.text()

        # 找到对应的音频文件
        audio_path = None
        for f in Path("./data/voices").iterdir():
            if f.name == name and f.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg"):
                audio_path = f
                break

        if not audio_path:
            QMessageBox.warning(self, "克隆失败", "找不到对应的音频文件")
            return

        # 检查API Key
        settings = QSettings("KBSZR", "config")
        dh_api_key = settings.value("api/dh_key", "")
        if not dh_api_key:
            QMessageBox.warning(self, "克隆失败",
                "数字人 API Key 未配置\n请在系统设置 → API密钥 → 数字人 API 中填写阿里云 Key")
            return

        self.clone_btn.setEnabled(False)
        self.clone_btn.setText("克隆中...")
        self.progress_bar.setRange(0, 0)

        thread = threading.Thread(
            target=self._clone_worker,
            args=(str(audio_path), name, dh_api_key),
            daemon=True
        )
        thread.start()

    def _clone_worker(self, audio_path: str, voice_name: str, api_key: str):
        """克隆工作线程"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            from src.business.tts.voice_clone import VoiceClone
            cloner = VoiceClone(api_key=api_key)
            result = loop.run_until_complete(cloner.clone(
                audio_samples=[audio_path],
                voice_name=voice_name
            ))
            loop.run_until_complete(cloner.close())
            loop.close()

            if result.success:
                # 保存克隆结果
                self._cloned_voices[voice_name] = {
                    "voice_id": result.voice_id,
                    "source": audio_path,
                    "time": time.time(),
                }
                self._save_cloned_voices()

                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)

                # 刷新UI（在主线程中）
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, "克隆成功",
                    f"音色「{voice_name}」克隆完成！\n"
                    f"voice_id: {result.voice_id}\n\n"
                    f"现在可以在「语音合成试听」中选择该音色进行试听"
                )
                self._load_voices()
            else:
                raise Exception(result.error or "克隆失败")

        except Exception as e:
            logger.error(f"Clone failed: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "克隆失败", str(e))

        finally:
            self.clone_btn.setEnabled(True)
            self.clone_btn.setText("🔊 克隆音色")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    # ========== 录音 ==========

    def _on_record_toggle(self):
        """开始/停止录制"""
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """开始录制（主线程）"""
        try:
            self._recording = True
            self.record_btn.setText("⏹ 停止录制")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9C27B0; color: white;
                    border: none; padding: 8px 16px; border-radius: 4px; font-size: 13px;
                }
                QPushButton:hover { background-color: #7B1FA2; }
            """)
            self.import_btn.setEnabled(False)
            self.play_btn.setEnabled(False)
            self.clone_btn.setEnabled(False)
            self.progress_bar.setRange(0, 0)

            self._record_worker_obj = RecordWorker()
            self._record_thread = QThread()
            self._record_worker_obj.moveToThread(self._record_thread)
            self._record_thread.started.connect(self._record_worker_obj.run)
            self._record_worker_obj.finished.connect(self._on_recording_finished)
            self._record_worker_obj.finished.connect(self._record_thread.quit)
            self._record_worker_obj.finished.connect(self._record_worker_obj.deleteLater)
            self._record_thread.finished.connect(self._record_thread.deleteLater)
            self._record_thread.start()

        except Exception as e:
            self._recording = False
            QMessageBox.warning(self, "录制失败", f"无法启动录音: {e}\n请检查麦克风连接。")

    def _on_recording_finished(self, recording):
        """录音完成回调（主线程安全）"""
        if recording is None or len(recording) == 0:
            self._reset_recording_ui()
            return

        import numpy as np

        # 主线程安全地弹出输入对话框
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, "保存录音", "输入声音名称:",
            text=f"我的声音_{int(time.time())}"
        )
        if not ok or not name.strip():
            self._reset_recording_ui()
            return

        try:
            import scipy.io.wavfile as wav
            output_path = Path(f"./data/voices/{name.strip()}.wav")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            wav.write(str(output_path), 44100, recording)
            logger.info(f"Recording saved: {output_path}")
            self._load_voices()
        except ImportError:
            QMessageBox.warning(self, "保存失败", "缺少 scipy，请执行: pip install scipy")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

        self._reset_recording_ui()

    def _reset_recording_ui(self):
        """重置录制UI状态"""
        self._recording = False
        self.record_btn.setText("🎤 录制声音")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white;
                border: none; padding: 8px 16px; border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        self.import_btn.setEnabled(True)
        self._update_play_button_state()
        self.clone_btn.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    def _stop_recording(self):
        """停止录制"""
        import sounddevice as sd
        sd.stop()
        # sd.stop() 让 sd.wait() 提前返回 → RecordWorker 发 finished 信号
        # → _on_recording_finished 主线程弹出命名对话框

    # ========== 播放 ==========

    def _on_play(self):
        """播放选中声音"""
        item = self.voice_list.currentItem()
        if not item or item.text().startswith("（"):
            return
        name = item.text()

        for f in Path("./data/voices").iterdir():
            if f.name == name:
                self._player.setSource(QUrl.fromLocalFile(str(f.absolute())))
                self._audio_output.setVolume(0.8)
                self._player.play()
                self.stop_btn.setEnabled(True)
                self.play_btn.setEnabled(False)
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(0)
                return

        QMessageBox.warning(self, "播放失败", f"找不到文件: {name}")

    def _on_stop(self):
        """停止播放"""
        self._player.stop()
        self.stop_btn.setEnabled(False)
        self._update_play_button_state()
        self.progress_bar.setValue(0)

    def _on_position_changed(self, position):
        """播放进度更新"""
        duration = self._player.duration()
        if duration > 0:
            self.progress_bar.setValue(int(position / duration * 100))

    def _on_media_status(self, status):
        """播放器状态变化"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.stop_btn.setEnabled(False)
            self._update_play_button_state()
            self.progress_bar.setValue(0)
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            self._player.play()

    def _update_play_button_state(self):
        """更新播放按钮状态"""
        has = self.voice_list.currentItem() is not None
        text = self.voice_list.currentItem().text() if has else ""
        is_real = has and not text.startswith("（")
        self.play_btn.setEnabled(is_real and not self._recording)

    # ========== TTS 试听 ==========

    def _on_tts_preview(self):
        """TTS试听"""
        text = self.tts_text.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入要试听的文本")
            return

        voice_text = self.voice_select.currentText()
        # 提取voice_id
        import re
        match = re.search(r'(BV\d+)', voice_text)
        voice_id = match.group(1) if match else "BV700_V2"

        self.tts_play_btn.setEnabled(False)
        self.tts_play_btn.setText("合成中...")
        self.statusbar_message = QLabel("正在合成语音...")
        self.progress_bar.setRange(0, 0)  # 繁忙

        # 后台线程合成
        thread = threading.Thread(target=self._tts_worker, args=(text, voice_id), daemon=True)
        thread.start()

    def _tts_worker(self, text: str, voice_id: str):
        """TTS合成工作线程"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            settings = QSettings("KBSZR", "config")

            # 判断是否为克隆音色 → 走阿里云
            if self._is_cloned_voice(voice_id):
                from src.business.tts.aliyun_client import AliyunTTS
                api_key = settings.value("api/dh_key", "")
                if not api_key:
                    raise ValueError("数字人 API Key 未配置，克隆音色需要阿里云 Key")
                tts = AliyunTTS(api_key=api_key)
                result = loop.run_until_complete(
                    tts.synthesize(text, voice=voice_id)
                )
                loop.run_until_complete(tts.close())

            else:
                tts_provider = settings.value("tts/provider", "volcengine")
                if tts_provider == "volcengine":
                    from src.business.tts.volcengine_tts import VolcEngineTTS
                    api_key = settings.value("api/tts_key", "")
                    if not api_key:
                        raise ValueError("TTS API Key 未配置，请在系统设置中填写")
                    tts = VolcEngineTTS(api_key=api_key)
                    result = loop.run_until_complete(tts.synthesize(text, voice=voice_id))
                    loop.run_until_complete(tts.close())
                else:
                    from src.business.tts.aliyun_client import AliyunTTS
                    api_key = settings.value("api/tts_key", "")
                    if not api_key:
                        raise ValueError("TTS API Key 未配置，请在系统设置中填写")
                    tts = AliyunTTS(api_key=api_key)
                    result = loop.run_until_complete(tts.synthesize(text))
                    loop.run_until_complete(tts.close())

            if result.success:
                self._player.setSource(QUrl.fromLocalFile(str(Path(result.audio_path).absolute())))
                self._audio_output.setVolume(0.8)
                self._player.play()
                self.stop_btn.setEnabled(True)
                self.progress_bar.setRange(0, 100)

                # 导入到声音列表
                src_path = Path(result.audio_path)
                if src_path.exists():
                    import shutil
                    dest = Path(f"./data/voices/tts_preview{src_path.suffix}")
                    shutil.copy2(str(src_path), str(dest))
                    self._load_voices()
            else:
                raise Exception(result.error)

            loop.close()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            error_msg = str(e)
            logger.error(f"TTS preview failed: {error_msg}")

        finally:
            self.tts_play_btn.setEnabled(True)
            self.tts_play_btn.setText("▶ 试听")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def closeEvent(self, event):
        """关闭时停止播放"""
        self._player.stop()
        super().closeEvent(event)
