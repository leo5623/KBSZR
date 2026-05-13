"""视频合成器 - 本地FFmpeg合成"""
import asyncio
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from loguru import logger

from src.services.ffmpeg_service import FFmpegService, FFmpegResult


@dataclass
class VideoComposeResult:
    """视频合成结果"""
    success: bool
    output_path: str = ""
    duration: float = 0.0
    error: str = ""


class VideoComposer:
    """
    视频合成器

    将数字人视频、音频、字幕等合成为最终成品
    """

    def __init__(self, ffmpeg_service: Optional[FFmpegService] = None):
        self.ffmpeg = ffmpeg_service or FFmpegService()
        logger.info("VideoComposer initialized")

    async def compose(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        subtitle_path: Optional[str] = None,
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.3,
        target_ratio: str = "9:16",
        add_subtitle: bool = True
    ) -> VideoComposeResult:
        """
        合成最终视频

        Args:
            video_path: 数字人视频路径
            audio_path: TTS音频路径
            output_path: 输出视频路径
            subtitle_path: 字幕文件路径（可选）
            bgm_path: BGM音频路径（可选）
            bgm_volume: BGM音量 (0.0-1.0)
            target_ratio: 目标比例 (9:16 或 16:9)
            add_subtitle: 是否添加字幕

        Returns:
            VideoComposeResult
        """
        try:
            temp_files = []  # 跟踪临时文件

            # Step 1: 合并视频和音频
            merged_video_path = output_path.replace(".mp4", "_merged.mp4")
            result = await self.ffmpeg.merge_audio_video(
                video_path=video_path,
                audio_path=audio_path,
                output_path=merged_video_path,
                mute_original=True
            )

            if not result.success:
                return VideoComposeResult(success=False, error=f"Merge audio/video failed: {result.error}")

            temp_files.append(merged_video_path)

            # Step 2: 添加BGM（如果提供）
            if bgm_path and Path(bgm_path).exists():
                bgm_mixed_path = output_path.replace(".mp4", "_bgm.mp3")
                result = await self.ffmpeg.mix_bgm(
                    audio_path=audio_path,
                    bgm_path=bgm_path,
                    output_path=bgm_mixed_path,
                    bgm_volume=bgm_volume
                )

                if result.success:
                    temp_files.append(bgm_mixed_path)
                    # 重新合并视频和混音后的音频
                    result = await self.ffmpeg.merge_audio_video(
                        video_path=merged_video_path,
                        audio_path=bgm_mixed_path,
                        output_path=merged_video_path,
                        mute_original=False
                    )

                    if not result.success:
                        return VideoComposeResult(success=False, error=f"Mix BGM failed: {result.error}")

            current_video = merged_video_path

            # Step 3: 添加字幕
            if add_subtitle and subtitle_path and Path(subtitle_path).exists():
                subtitle_video_path = output_path.replace(".mp4", "_subtitle.mp4")
                result = await self.ffmpeg.add_subtitle(
                    video_path=current_video,
                    subtitle_path=subtitle_path,
                    output_path=subtitle_video_path
                )

                if result.success:
                    current_video = subtitle_video_path
                    temp_files.append(subtitle_video_path)
                else:
                    logger.warning(f"Add subtitle failed: {result.error}, continuing without subtitle")

            # Step 4: 转换比例
            if target_ratio != "auto":
                ratio_video_path = output_path.replace(".mp4", "_ratio.mp4")
                result = await self.ffmpeg.convert_ratio(
                    video_path=current_video,
                    output_path=ratio_video_path,
                    target_ratio=target_ratio
                )

                if result.success:
                    current_video = ratio_video_path
                    temp_files.append(ratio_video_path)
                else:
                    logger.warning(f"Convert ratio failed: {result.error}, keeping original ratio")

            # Step 5: 复制最终结果
            import shutil
            shutil.copy(current_video, output_path)

            # 清理临时文件
            for temp_file in temp_files:
                Path(temp_file).unlink(missing_ok=True)

            # 获取最终时长
            duration = await self.ffmpeg.get_duration(output_path)

            logger.info(f"Video composed successfully: {output_path}, duration={duration}s")

            return VideoComposeResult(
                success=True,
                output_path=output_path,
                duration=duration
            )

        except Exception as e:
            logger.error(f"Video compose exception: {e}")
            return VideoComposeResult(success=False, error=str(e))

    async def quick_compose(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ) -> VideoComposeResult:
        """
        快速合成（仅合并视频和音频）

        用于预览或快速生成
        """
        result = await self.ffmpeg.merge_audio_video(
            video_path=video_path,
            audio_path=audio_path,
            output_path=output_path
        )

        return VideoComposeResult(
            success=result.success,
            output_path=output_path if result.success else "",
            duration=result.duration,
            error=result.error
        )


# 全局实例
_video_composer: Optional[VideoComposer] = None


def get_video_composer() -> VideoComposer:
    """获取视频合成器实例"""
    global _video_composer
    if _video_composer is None:
        _video_composer = VideoComposer()
    return _video_composer