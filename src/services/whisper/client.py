"""Whisper语音识别客户端"""
import os
import asyncio
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, AsyncIterator
from pathlib import Path

from loguru import logger


@dataclass
class WhisperConfig:
    """Whisper配置"""
    model_size: str = "base"  # tiny/base/small/medium/large
    language: str = "zh"  # 语言代码
    model_path: Optional[str] = None  # 本地模型路径
    device: str = "auto"  # auto/cpu/cuda


# 模型大小和推荐用途
WHISPER_MODELS = {
    "tiny": {"size": "39MB", "vram": "1GB", "desc": "最快，最低精度"},
    "base": {"size": "140MB", "vram": "1GB", "desc": "快速，中等精度（推荐）"},
    "small": {"size": "488MB", "vram": "2GB", "desc": "较慢，高精度"},
    "medium": {"size": "1.5GB", "vram": "5GB", "desc": "慢，高精度"},
    "large": {"size": "2.9GB", "vram": "10GB", "desc": "最慢，最高精度"},
}


class WhisperClient:
    """
    Whisper语音识别客户端

    功能：
    - 音频文件转文字
    - 支持多种音频格式 (mp3, wav, m4a, etc.)
    - 支持中文普通话
    - 模型下载管理
    """

    def __init__(self, config: Optional[WhisperConfig] = None):
        self.config = config or WhisperConfig()
        self._model = None
        self._model_loaded = False

    async def _load_model(self):
        """加载Whisper模型"""
        if self._model_loaded:
            return

        try:
            import whisper

            if self.config.model_path and os.path.exists(self.config.model_path):
                logger.info(f"Loading Whisper model from: {self.config.model_path}")
                self._model = await asyncio.to_thread(
                    whisper.load_model,
                    self.config.model_path,
                    device=self.config.device
                )
            else:
                logger.info(f"Loading Whisper model: {self.config.model_size}")
                self._model = await asyncio.to_thread(
                    whisper.load_model,
                    self.config.model_size,
                    device=self.config.device
                )

            self._model_loaded = True
            logger.info("Whisper model loaded successfully")

        except ImportError:
            logger.error("Whisper not installed. Run: pip install openai-whisper")
            raise RuntimeError("Whisper not installed. Run: pip install openai-whisper")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    async def download_model(self, model_size: str = "base") -> AsyncIterator[str]:
        """
        下载Whisper模型

        Args:
            model_size: 模型大小 (tiny/base/small/medium/large)

        Yields:
            下载进度信息
        """
        if model_size not in WHISPER_MODELS:
            yield f"无效的模型大小: {model_size}"
            return

        model_info = WHISPER_MODELS[model_size]
        yield f"开始下载 Whisper {model_size} 模型 ({model_info['size']})..."

        try:
            import whisper

            # 使用 whisper.download 下载模型
            def download():
                whisper.download(model_size)
                return True

            result = await asyncio.to_thread(download)
            if result:
                yield f"Whisper {model_size} 模型下载完成！"
            else:
                yield "模型下载失败"

        except Exception as e:
            yield f"下载错误: {str(e)}"

    async def list_downloaded_models(self) -> List[str]:
        """列出已下载的模型"""
        try:
            import whisper
            # whisper不会直接提供已下载列表，这里检查本地缓存目录
            cache_dir = os.path.expanduser("~/.cache/whisper")
            if os.path.exists(cache_dir):
                return [d for d in os.listdir(cache_dir) if os.path.isdir(os.path.join(cache_dir, d))]
            return []
        except Exception:
            return []

    async def get_model_info(self, model_size: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_size in WHISPER_MODELS:
            info = WHISPER_MODELS[model_size].copy()
            info["downloaded"] = model_size in await self.list_downloaded_models()
            return info
        return {}

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        将音频转换为文字

        Args:
            audio_path: 音频文件路径
            language: 语言代码（覆盖配置）
            task: transcribe 或 translate
            verbose: 是否输出详细信息

        Returns:
            包含text, segments等信息的字典
        """
        if not os.path.exists(audio_path):
            return {
                "success": False,
                "error": f"Audio file not found: {audio_path}",
                "text": "",
                "segments": []
            }

        await self._load_model()

        try:
            lang = language or self.config.language

            logger.info(f"Transcribing audio: {audio_path}, language: {lang}")

            # 在线程中执行转录（避免阻塞）
            result = await asyncio.to_thread(
                self._model.transcribe,
                audio_path,
                language=lang,
                task=task,
                verbose=verbose
            )

            # 提取纯文本
            full_text = result.get("text", "").strip()

            # 提取段落
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "id": seg.get("id"),
                    "start": seg.get("start"),
                    "end": seg.get("end"),
                    "text": seg.get("text", "").strip()
                })

            return {
                "success": True,
                "text": full_text,
                "segments": segments,
                "language": result.get("language", lang),
                "duration": self._get_audio_duration(audio_path)
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "segments": []
            }

    async def transcribe_srt(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        将音频转换为SRT字幕文件

        Args:
            audio_path: 音频文件路径
            output_path: 输出SRT文件路径
            language: 语言代码

        Returns:
            SRT文件内容或路径
        """
        result = await self.transcribe(audio_path, language=language)

        if not result["success"]:
            raise RuntimeError(f"Transcription failed: {result.get('error')}")

        # 生成SRT格式
        srt_content = self._generate_srt(result["segments"])

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            return output_path

        return srt_content

    def _generate_srt(self, segments: List[Dict]) -> str:
        """生成SRT格式字幕"""
        srt_lines = []

        for i, seg in enumerate(segments, 1):
            start_time = self._format_timestamp(seg["start"])
            end_time = self._format_timestamp(seg["end"])
            text = seg["text"]

            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")

        return "\n".join(srt_lines)

    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为SRT格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            import librosa
            duration = librosa.get_duration(path=audio_path)
            return duration
        except Exception:
            return 0.0

    async def close(self):
        """关闭客户端"""
        self._model = None
        self._model_loaded = False

    async def health_check(self) -> Dict[str, Any]:
        """检查服务健康状态"""
        try:
            await self._load_model()
            return {
                "available": True,
                "model_loaded": self._model_loaded,
                "model_size": self.config.model_size
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }


# 便捷函数
async def transcribe_audio(
    audio_path: str,
    language: str = "zh",
    model_size: str = "base"
) -> Dict[str, Any]:
    """便捷的音频转文字函数"""
    config = WhisperConfig(model_size=model_size, language=language)
    client = WhisperClient(config)

    try:
        return await client.transcribe(audio_path, language=language)
    finally:
        await client.close()


async def audio_to_srt(
    audio_path: str,
    output_path: str,
    language: str = "zh"
) -> str:
    """便捷的音频转SRT函数"""
    config = WhisperConfig(model_size="base", language=language)
    client = WhisperClient(config)

    try:
        return await client.transcribe_srt(audio_path, output_path, language)
    finally:
        await client.close()