"""FFmpeg服务封装"""
import asyncio
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple
from loguru import logger


@dataclass
class FFmpegResult:
    """FFmpeg操作结果"""
    success: bool
    output_path: str = ""
    duration: float = 0.0
    error: str = ""


class FFmpegService:
    """
    FFmpeg服务封装

    提供音视频处理功能：
    - 音视频合并
    - 音频降噪
    - 语速调整
    - BGM混音
    - 音量压制
    - 横竖屏转换
    - 视频拼接
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        logger.info(f"FFmpegService initialized: {ffmpeg_path}")

    async def health_check(self) -> dict:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True
            )
            return {"available": result.returncode == 0, "version": result.stdout.split("\n")[0]}
        except FileNotFoundError:
            return {"available": False, "error": "FFmpeg not found in PATH"}

    async def get_duration(self, file_path: str) -> float:
        """获取音视频时长（秒）"""
        try:
            cmd = [
                self.ffprobe_path, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Get duration failed: {e}")
        return 0.0

    async def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        mute_original: bool = True
    ) -> FFmpegResult:
        """
        合并音视频

        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 输出文件路径
            mute_original: 是否静音原视频

        Returns:
            FFmpegResult
        """
        try:
            # 构建命令
            if mute_original:
                # 静音原视频，使用新音频
                cmd = [
                    self.ffmpeg_path, "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    output_path
                ]
            else:
                # 混合原音频和新音频
                cmd = [
                    self.ffmpeg_path, "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first",
                    "-c:a", "aac",
                    "-shortest",
                    output_path
                ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                logger.info(f"Merge success: {output_path}, duration={duration}s")
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Merge failed: {error}")
                return FFmpegResult(success=False, error=error)

        except Exception as e:
            logger.error(f"Merge exception: {e}")
            return FFmpegResult(success=False, error=str(e))

    async def add_subtitle(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        style: str = "default"
    ) -> FFmpegResult:
        """
        添加字幕（烧录到视频）

        Args:
            video_path: 视频文件路径
            subtitle_path: 字幕文件路径（SRT格式）
            output_path: 输出文件路径
            style: 字幕样式

        Returns:
            FFmpegResult
        """
        try:
            # 使用ffmpeg的libass滤镜烧录字幕
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", video_path,
                "-vf", f"ass={subtitle_path}",
                "-c:a", "copy",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                logger.info(f"Add subtitle success: {output_path}")
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                # 尝试使用srt格式
                return await self._add_srt_subtitle(video_path, subtitle_path, output_path)

        except Exception as e:
            logger.error(f"Add subtitle exception: {e}")
            return FFmpegResult(success=False, error=str(e))

    async def _add_srt_subtitle(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str
    ) -> FFmpegResult:
        """使用SRT格式添加字幕"""
        try:
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", video_path,
                "-vf", f"subtitles='{subtitle_path}'",
                "-c:a", "copy",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                return FFmpegResult(success=False, error=error)

        except Exception as e:
            return FFmpegResult(success=False, error=str(e))

    async def convert_ratio(
        self,
        video_path: str,
        output_path: str,
        target_ratio: str = "9:16"
    ) -> FFmpegResult:
        """
        转换视频比例

        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径
            target_ratio: 目标比例 ("9:16" 或 "16:9")

        Returns:
            FFmpegResult
        """
        try:
            if target_ratio == "9:16":
                # 横屏转竖屏
                # 方法：裁剪中间部分，然后放大
                vf = "crop=in_w:in_h*0.5625:0:(in_h-in_h*0.5625)/2,scale=1080:1920"
            elif target_ratio == "16:9":
                # 竖屏转横屏
                # 方法：两侧加黑边
                vf = "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
            else:
                return FFmpegResult(success=False, error=f"Unsupported ratio: {target_ratio}")

            cmd = [
                self.ffmpeg_path, "-y",
                "-i", video_path,
                "-vf", vf,
                "-c:a", "copy",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                logger.info(f"Convert ratio success: {target_ratio}")
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                return FFmpegResult(success=False, error=error)

        except Exception as e:
            logger.error(f"Convert ratio exception: {e}")
            return FFmpegResult(success=False, error=str(e))

    async def adjust_volume(
        self,
        audio_path: str,
        output_path: str,
        volume_db: float = 0.0
    ) -> FFmpegResult:
        """
        调整音量

        Args:
            audio_path: 输入音频路径
            output_path: 输出音频路径
            volume_db: 音量调整（分贝），负数降低，正数增加

        Returns:
            FFmpegResult
        """
        try:
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", audio_path,
                "-af", f"volume={volume_db}dB",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                logger.info(f"Adjust volume success: {volume_db}dB")
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                return FFmpegResult(success=False, error=error)

        except Exception as e:
            logger.error(f"Adjust volume exception: {e}")
            return FFmpegResult(success=False, error=str(e))

    async def mix_bgm(
        self,
        audio_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: float = 0.3,
        duck_threshold: float = -20.0
    ) -> FFmpegResult:
        """
        混音BGM（人声优先，自动降低BGM音量）

        Args:
            audio_path: 人声音频路径
            bgm_path: BGM音频路径
            output_path: 输出音频路径
            bgm_volume: BGM相对音量 (0.0-1.0)
            duck_threshold: 音量阈值（低于此值时BGM音量恢复）

        Returns:
            FFmpegResult
        """
        try:
            # 使用amix混合，BG音量降低
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", audio_path,
                "-i", bgm_path,
                "-filter_complex",
                f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first:weights=1 {bgm_volume}",
                "-c:a", "aac",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                logger.info(f"Mix BGM success: bgm_volume={bgm_volume}")
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                return FFmpegResult(success=False, error=error)

        except Exception as e:
            logger.error(f"Mix BGM exception: {e}")
            return FFmpegResult(success=False, error=str(e))

    async def adjust_speed(
        self,
        audio_path: str,
        output_path: str,
        speed: float = 1.0
    ) -> FFmpegResult:
        """
        调整语速

        Args:
            audio_path: 输入音频路径
            output_path: 输出音频路径
            speed: 语速 (0.5-2.0, 1.0为正常)

        Returns:
            FFmpegResult
        """
        try:
            # atempo滤镜可以调整速度不影响音调
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", audio_path,
                "-af", f"atempo={speed}",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                logger.info(f"Adjust speed success: speed={speed}")
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                return FFmpegResult(success=False, error=error)

        except Exception as e:
            logger.error(f"Adjust speed exception: {e}")
            return FFmpegResult(success=False, error=str(e))

    async def denoise(
        self,
        audio_path: str,
        output_path: str,
        level: str = "low"
    ) -> FFmpegResult:
        """
        音频降噪

        Args:
            audio_path: 输入音频路径
            output_path: 输出音频路径
            level: 降噪级别 (low/medium/high)

        Returns:
            FFmpegResult
        """
        try:
            # 使用afade和hdem filters进行基础降噪
            # 实际生产环境建议使用DeepNoise等专门降噪模型
            noise_reduction = {"low": 0.5, "medium": 1.0, "high": 2.0}.get(level, 0.5)

            cmd = [
                self.ffmpeg_path, "-y",
                "-i", audio_path,
                "-af", f"afftdn=nf={noise_reduction}",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and Path(output_path).exists():
                duration = await self.get_duration(output_path)
                logger.info(f"Denoise success: level={level}")
                return FFmpegResult(success=True, output_path=output_path, duration=duration)
            else:
                error = stderr.decode() if stderr else "Unknown error"
                return FFmpegResult(success=False, error=error)

        except Exception as e:
            logger.error(f"Denoise exception: {e}")
            return FFmpegResult(success=False, error=str(e))


# 全局实例
_ffmpeg_service: Optional[FFmpegService] = None


def get_ffmpeg_service() -> FFmpegService:
    """获取FFmpeg服务实例"""
    global _ffmpeg_service
    if _ffmpeg_service is None:
        _ffmpeg_service = FFmpegService()
    return _ffmpeg_service