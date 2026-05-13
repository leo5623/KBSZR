"""视频处理路由 - 本地/云端双选"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger

from src.services.ffmpeg_service import FFmpegService, FFmpegResult, get_ffmpeg_service
from src.business.post_production.subtitle.local_subtitle import (
    SubtitleGenerator,
    SubtitleResult,
    get_subtitle_generator
)
from src.business.post_production.video_composer.local_composer import (
    VideoComposer,
    VideoComposeResult,
    get_video_composer
)


class VideoProcessingMode(Enum):
    """视频处理模式"""
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class VideoProcessingConfig:
    """视频处理配置"""
    mode: VideoProcessingMode = VideoProcessingMode.LOCAL

    # FFmpeg配置
    ffmpeg_path: str = "ffmpeg"

    # Whisper配置
    whisper_model: str = "base"

    # 云端配置（待实现）
    cloud_provider: str = "tencent"
    cloud_api_key: str = ""


@dataclass
class SubtitleRequest:
    """字幕生成请求"""
    audio_path: str
    output_srt_path: str
    language: str = "zh"


@dataclass
class ComposeRequest:
    """视频合成请求"""
    video_path: str
    audio_path: str
    output_path: str
    subtitle_path: Optional[str] = None
    bgm_path: Optional[str] = None
    bgm_volume: float = 0.3
    target_ratio: str = "9:16"


class VideoProcessingRouter:
    """
    视频处理路由

    本地处理：FFmpeg + Whisper
    云端处理：腾讯云/阿里云（待实现）
    """

    def __init__(self, config: Optional[VideoProcessingConfig] = None):
        self.config = config or VideoProcessingConfig()

        # 初始化服务
        self.ffmpeg = get_ffmpeg_service()
        self.subtitle_generator = get_subtitle_generator(self.config.whisper_model)
        self.video_composer = get_video_composer()

        logger.info(f"VideoProcessingRouter initialized: mode={self.config.mode.value}")

    async def close(self):
        """关闭路由"""
        pass  # 当前无需要关闭的连接

    async def health_check(self) -> dict:
        """检查服务健康状态"""
        results = {"mode": self.config.mode.value}

        # FFmpeg检查
        ffmpeg_health = await self.ffmpeg.health_check()
        results["ffmpeg"] = ffmpeg_health

        # Whisper检查
        whisper_health = await self.subtitle_generator.health_check()
        results["whisper"] = whisper_health

        return results

    async def generate_subtitle(self, request: SubtitleRequest) -> SubtitleResult:
        """
        生成字幕

        Args:
            request: 字幕请求

        Returns:
            SubtitleResult
        """
        if self.config.mode == VideoProcessingMode.LOCAL:
            return await self.subtitle_generator.generate_subtitle(
                audio_path=request.audio_path,
                output_srt_path=request.output_srt_path,
                language=request.language
            )
        else:
            # 云端处理（待实现）
            raise NotImplementedError("Cloud subtitle not implemented")

    async def generate_subtitle_from_video(
        self,
        video_path: str,
        output_srt_path: str,
        language: str = "zh"
    ) -> SubtitleResult:
        """
        从视频生成字幕

        Args:
            video_path: 视频文件路径
            output_srt_path: 输出字幕文件路径
            language: 音频语言

        Returns:
            SubtitleResult
        """
        return await self.subtitle_generator.generate_from_video(
            video_path=video_path,
            output_srt_path=output_srt_path,
            language=language
        )

    async def compose_video(self, request: ComposeRequest) -> VideoComposeResult:
        """
        合成视频

        Args:
            request: 合成请求

        Returns:
            VideoComposeResult
        """
        return await self.video_composer.compose(
            video_path=request.video_path,
            audio_path=request.audio_path,
            output_path=request.output_path,
            subtitle_path=request.subtitle_path,
            bgm_path=request.bgm_path,
            bgm_volume=request.bgm_volume,
            target_ratio=request.target_ratio
        )

    async def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ) -> FFmpegResult:
        """合并音视频"""
        return await self.ffmpeg.merge_audio_video(
            video_path=video_path,
            audio_path=audio_path,
            output_path=output_path
        )

    async def convert_ratio(
        self,
        video_path: str,
        output_path: str,
        target_ratio: str = "9:16"
    ) -> FFmpegResult:
        """转换视频比例"""
        return await self.ffmpeg.convert_ratio(
            video_path=video_path,
            output_path=output_path,
            target_ratio=target_ratio
        )

    async def adjust_audio(
        self,
        audio_path: str,
        output_path: str,
        volume_db: float = -12.0,
        speed: float = 1.0
    ) -> FFmpegResult:
        """
        调整音频

        Args:
            audio_path: 输入音频路径
            output_path: 输出音频路径
            volume_db: 音量调整（分贝）
            speed: 语速

        Returns:
            FFmpegResult
        """
        # 先调整音量
        if volume_db != 0.0:
            result = await self.ffmpeg.adjust_volume(
                audio_path=audio_path,
                output_path=output_path,
                volume_db=volume_db
            )
            if not result.success:
                return result

        # 再调整语速
        if speed != 1.0:
            result = await self.ffmpeg.adjust_speed(
                audio_path=audio_path,
                output_path=output_path,
                speed=speed
            )

        return result


# 便捷函数
async def generate_subtitle(
    audio_path: str,
    output_srt_path: str,
    language: str = "zh"
) -> SubtitleResult:
    """便捷的字幕生成函数"""
    generator = get_subtitle_generator()
    return await generator.generate_subtitle(audio_path, output_srt_path, language)


async def compose_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    subtitle_path: str = None,
    bgm_path: str = None,
    target_ratio: str = "9:16"
) -> VideoComposeResult:
    """便捷的视频合成函数"""
    composer = get_video_composer()
    return await composer.compose(
        video_path=video_path,
        audio_path=audio_path,
        output_path=output_path,
        subtitle_path=subtitle_path,
        bgm_path=bgm_path,
        target_ratio=target_ratio
    )