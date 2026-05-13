"""Whisper字幕生成器 - 本地语音识别"""
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from loguru import logger

# Whisper可能不可用，先检查
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not installed. Install with: pip install openai-whisper")


@dataclass
class SubtitleResult:
    """字幕生成结果"""
    success: bool
    srt_path: str = ""
    duration: float = 0.0
    segments: int = 0
    error: str = ""


@dataclass
class SubtitleSegment:
    """字幕片段"""
    index: int
    start: float  # 秒
    end: float    # 秒
    text: str


class SubtitleGenerator:
    """
    Whisper字幕生成器

    使用OpenAI Whisper进行本地语音识别
    支持模型：tiny/base/small/medium/large
    """

    def __init__(
        self,
        model_size: str = "base",
        model_dir: str = "./models/whisper",
        device: str = "cpu"  # cpu 或 cuda
    ):
        self.model_size = model_size
        self.model_dir = model_dir
        self.device = device
        self._model = None

        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available. Please install: pip install openai-whisper")

        logger.info(f"SubtitleGenerator initialized: model={model_size}, device={device}")

    async def load_model(self):
        """加载模型"""
        if self._model is None and WHISPER_AVAILABLE:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = whisper.load_model(
                self.model_size,
                download_root=self.model_dir
            )
            logger.info(f"Whisper model loaded")

    async def health_check(self) -> dict:
        """检查Whisper是否可用"""
        result = {
            "whisper_available": WHISPER_AVAILABLE,
            "model_loaded": self._model is not None,
            "model_size": self.model_size,
            "device": self.device
        }

        if WHISPER_AVAILABLE:
            try:
                # 检查ffmpeg
                import subprocess
                r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
                result["ffmpeg_available"] = r.returncode == 0
            except FileNotFoundError:
                result["ffmpeg_available"] = False
        else:
            result["ffmpeg_available"] = False

        return result

    async def generate_subtitle(
        self,
        audio_path: str,
        output_srt_path: str,
        language: str = "zh",
        max_chars_per_line: int = 40
    ) -> SubtitleResult:
        """
        生成字幕文件

        Args:
            audio_path: 音频文件路径
            output_srt_path: 输出SRT文件路径
            language: 音频语言（如"zh"、"en"）
            max_chars_per_line: 每行最大字符数

        Returns:
            SubtitleResult
        """
        if not WHISPER_AVAILABLE:
            return SubtitleResult(
                success=False,
                error="Whisper not installed. Run: pip install openai-whisper"
            )

        try:
            # 确保模型已加载
            await self.load_model()

            # 转写
            logger.info(f"Transcribing: {audio_path}")

            # 在线程池中运行（Whisper是CPU密集型）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(
                    audio_path,
                    language=language if language != "auto" else None,
                    word_timestamps=False
                )
            )

            # 提取片段
            segments = result.get("segments", [])
            srt_content = self._generate_srt(segments, max_chars_per_line)

            # 保存文件
            Path(output_srt_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

            # 计算总时长
            duration = segments[-1]["end"] if segments else 0.0

            logger.info(f"Subtitle generated: {output_srt_path}, {len(segments)} segments")

            return SubtitleResult(
                success=True,
                srt_path=output_srt_path,
                duration=duration,
                segments=len(segments)
            )

        except Exception as e:
            logger.error(f"Generate subtitle failed: {e}")
            return SubtitleResult(success=False, error=str(e))

    def _generate_srt(
        self,
        segments: List[dict],
        max_chars_per_line: int = 40
    ) -> str:
        """生成SRT格式字幕"""
        srt_lines = []

        for i, segment in enumerate(segments, 1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

            # 断行处理
            if len(text) > max_chars_per_line:
                text = self._wrap_text(text, max_chars_per_line)

            # SRT格式
            srt_lines.append(f"{i}")
            srt_lines.append(f"{self._format_time(start)} --> {self._format_time(end)}")
            srt_lines.append(text)
            srt_lines.append("")  # 空行分隔

        return "\n".join(srt_lines)

    def _format_time(self, seconds: float) -> str:
        """格式化时间码"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _wrap_text(self, text: str, max_chars: int) -> str:
        """文本断行"""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    async def generate_from_video(
        self,
        video_path: str,
        output_srt_path: str,
        language: str = "zh"
    ) -> SubtitleResult:
        """
        从视频提取音频并生成字幕

        Args:
            video_path: 视频文件路径
            output_srt_path: 输出SRT文件路径
            language: 音频语言

        Returns:
            SubtitleResult
        """
        try:
            # 先提取音频
            import subprocess
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio_path = tmp.name

            # 使用ffmpeg提取音频
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vn",  # 不要视频
                "-acodec", "pcm_s16le",
                "-ar", "16000",  # Whisper推荐16kHz
                "-ac", "1",  # 单声道
                audio_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error = stderr.decode() if stderr else "Failed to extract audio"
                return SubtitleResult(success=False, error=error)

            # 生成字幕
            result = await self.generate_subtitle(
                audio_path=audio_path,
                output_srt_path=output_srt_path,
                language=language
            )

            # 清理临时文件
            Path(audio_path).unlink(missing_ok=True)

            return result

        except Exception as e:
            logger.error(f"Generate from video failed: {e}")
            return SubtitleResult(success=False, error=str(e))

    @staticmethod
    def list_available_models() -> List[str]:
        """列出可用模型"""
        return ["tiny", "base", "small", "medium", "large"]

    @staticmethod
    def get_model_info(model_size: str) -> dict:
        """获取模型信息（参数量、推荐配置）"""
        models = {
            "tiny": {"params": "39M", "requires_gpu": False, "speed": "fast", "accuracy": "low"},
            "base": {"params": "74M", "requires_gpu": False, "speed": "medium", "accuracy": "medium"},
            "small": {"params": "244M", "requires_gpu": True, "speed": "slow", "accuracy": "high"},
            "medium": {"params": "769M", "requires_gpu": True, "speed": "very_slow", "accuracy": "very_high"},
            "large": {"params": "1550M", "requires_gpu": True, "speed": "very_slow", "accuracy": "highest"},
        }
        return models.get(model_size, {})


# 全局实例
_subtitle_generator: Optional[SubtitleGenerator] = None


def get_subtitle_generator(model_size: str = "base") -> SubtitleGenerator:
    """获取字幕生成器实例"""
    global _subtitle_generator
    if _subtitle_generator is None:
        _subtitle_generator = SubtitleGenerator(model_size=model_size)
    return _subtitle_generator