"""画质增强 - 完整API封装"""
import asyncio
import base64
import hashlib
import time
import shutil
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from loguru import logger


@dataclass
class VideoEnhanceResult:
    """画质增强结果"""
    success: bool
    output_path: str = ""
    original_path: str = ""
    resolution: str = ""
    enhanced_duration: float = 0.0
    error_message: str = ""
    file_size_before: int = 0
    file_size_after: int = 0
    processing_time: float = 0.0


@dataclass
class VideoEnhanceConfig:
    """画质增强配置"""
    api_key: str = ""
    provider: str = "aliyun"  # aliyun / volcengine / local
    enhance_level: str = "medium"  # low / medium / high
    output_dir: str = "./data/output/enhanced"


@dataclass
class EnhancePreset:
    """增强预设"""
    id: str
    name: str
    description: str
    level: str
    services: List[str]
    scale_factor: int = 1


# 增强预设
PRESETS = {
    "fast": EnhancePreset(
        id="fast",
        name="快速增强",
        description="轻度增强，处理速度快",
        level="low",
        services=["denoise"],
        scale_factor=1
    ),
    "quality": EnhancePreset(
        id="quality",
        name="质量优先",
        description="全面增强，最佳质量",
        level="high",
        services=["denoise", "sharpen", "super_resolution", "color_correct"],
        scale_factor=2
    ),
    "balance": EnhancePreset(
        id="balance",
        name="均衡模式",
        description="平衡速度和质量",
        level="medium",
        services=["denoise", "sharpen"],
        scale_factor=1
    ),
    "upscale_4k": EnhancePreset(
        id="upscale_4k",
        name="4K超分",
        description="将视频放大到4K分辨率",
        level="high",
        services=["super_resolution", "sharpen"],
        scale_factor=4
    )
}


class VideoEnhancer:
    """
    画质增强处理器

    支持多种 API 提供商进行视频画质增强：
    - 阿里云：denoise, sharpen, super_resolution, color_correct
    - 火山引擎：denoise, sharpen, color_correct
    - 本地：FFmpeg-based 基础增强
    """

    def __init__(self, config: Optional[VideoEnhanceConfig] = None):
        self.config = config or VideoEnhanceConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def enhance(
        self,
        video_path: str,
        output_path: str = None,
        preset_id: str = "balance",
        level: str = None
    ) -> VideoEnhanceResult:
        """
        画质增强处理

        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径（None则自动生成）
            preset_id: 预设ID (fast/quality/balance/upscale_4k)
            level: 增强级别 (low/medium/high)，会覆盖preset

        Returns:
            VideoEnhanceResult: 处理结果
        """
        start_time = time.time()

        # 获取预设
        preset = PRESETS.get(preset_id, PRESETS["balance"])
        level = level or preset.level

        # 生成输出路径
        if output_path is None:
            input_name = Path(video_path).stem
            output_path = self.output_dir / f"{input_name}_enhanced.mp4"

        # 检查文件
        if not Path(video_path).exists():
            return VideoEnhanceResult(
                success=False,
                error_message=f"Video file not found: {video_path}"
            )

        # 记录原始大小
        original_size = Path(video_path).stat().st_size

        # 选择provider
        if self.config.provider == "aliyun":
            return await self._enhance_aliyun(video_path, str(output_path), level, preset)
        elif self.config.provider == "volcengine":
            return await self._enhance_volcengine(video_path, str(output_path), level, preset)
        else:
            return await self._enhance_local(video_path, str(output_path), level, preset)

    async def _enhance_aliyun(
        self,
        video_path: str,
        output_path: str,
        level: str,
        preset: EnhancePreset
    ) -> VideoEnhanceResult:
        """
        阿里云视频增强

        使用阿里云视频增强 API 进行超分辨率/降噪
        """
        import aiohttp
        start_time = time.time()

        try:
            # 读取视频文件并转为base64
            with open(video_path, "rb") as f:
                video_data = base64.b64encode(f.read()).decode()

            url = "https://ivision-api.aliyuncs.com/api/video/enhance"

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "video_data": video_data,
                "enhance_level": level,
                "scenes": preset.services,
                "scale_factor": preset.scale_factor
            }

            logger.info(f"Calling Aliyun video enhance API with level={level}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=300
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        enhanced_data = result.get("enhanced_video")

                        if enhanced_data:
                            # 保存增强后的视频
                            enhanced_bytes = base64.b64decode(enhanced_data)
                            with open(output_path, "wb") as f:
                                f.write(enhanced_bytes)

                            enhanced_size = Path(output_path).stat().st_size

                            return VideoEnhanceResult(
                                success=True,
                                output_path=output_path,
                                original_path=video_path,
                                resolution=f"{level}_enhanced",
                                enhanced_duration=result.get("duration", 0.0),
                                file_size_before=len(base64.b64decode(video_data)) if video_path else 0,
                                file_size_after=enhanced_size,
                                processing_time=time.time() - start_time
                            )
                        else:
                            return VideoEnhanceResult(
                                success=False,
                                error_message="No enhanced video data returned"
                            )
                    else:
                        error_text = await response.text()
                        logger.error(f"Aliyun API error: {response.status} - {error_text}")
                        return VideoEnhanceResult(
                            success=False,
                            error_message=f"API error: {response.status} - {error_text}"
                        )

        except aiohttp.ClientError as e:
            logger.error(f"Aliyun network error: {e}")
            return VideoEnhanceResult(success=False, error_message=f"Network error: {e}")
        except Exception as e:
            logger.error(f"阿里云画质增强失败: {e}")
            return VideoEnhanceResult(success=False, error_message=str(e))

    async def _enhance_volcengine(
        self,
        video_path: str,
        output_path: str,
        level: str,
        preset: EnhancePreset
    ) -> VideoEnhanceResult:
        """火山引擎视频增强"""
        import aiohttp
        start_time = time.time()

        try:
            url = "https://visual.volcengineapi.com/api/video/enhance"

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }

            # 火山引擎支持URL方式上传
            payload = {
                "video_url": f"file://{video_path}",
                "enhance_level": level,
                "services": preset.services,
                "scale_factor": preset.scale_factor
            }

            logger.info(f"Calling VolcEngine video enhance API with level={level}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=300
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        if result.get("video_url"):
                            # 下载增强后的视频
                            video_url = result["video_url"]
                            await self._download_video(video_url, output_path)

                            enhanced_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0

                            return VideoEnhanceResult(
                                success=True,
                                output_path=output_path,
                                original_path=video_path,
                                resolution=f"{level}_enhanced",
                                file_size_before=Path(video_path).stat().st_size,
                                file_size_after=enhanced_size,
                                processing_time=time.time() - start_time
                            )
                        else:
                            return VideoEnhanceResult(
                                success=False,
                                error_message="No video URL in response"
                            )
                    else:
                        error_text = await response.text()
                        return VideoEnhanceResult(
                            success=False,
                            error_message=f"VolcEngine API error: {response.status}"
                        )

        except Exception as e:
            logger.error(f"火山引擎画质增强失败: {e}")
            return VideoEnhanceResult(success=False, error_message=str(e))

    async def _enhance_local(
        self,
        video_path: str,
        output_path: str,
        level: str,
        preset: EnhancePreset
    ) -> VideoEnhanceResult:
        """
        本地画质增强（FFmpeg滤镜）

        使用FFmpeg内置滤镜进行基础增强：
        - denoise: nf降噪
        - sharpen: unsharp锐化
        - scale: 超分辨率（实际上是将低分辨率放大）
        """
        start_time = time.time()

        try:
            # 构建FFmpeg滤镜链
            filters = []

            # 降噪
            if "denoise" in preset.services:
                noise_level = {"low": 0.5, "medium": 1.0, "high": 2.0}.get(level, 1.0)
                filters.append(f"afftdn=nf={noise_level}")

            # 锐化
            if "sharpen" in preset.services:
                filters.append("unsharp=5:5:1.0:5:5:0.0")

            # 超分辨率（放大）
            if "super_resolution" in preset.services:
                scale = preset.scale_factor
                filters.append(f"scale=iw*{scale}:ih*{scale}")

            # 色彩校正
            if "color_correct" in preset.services:
                filters.append("eq=brightness=0.02:saturation=1.1")

            # 构建命令
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path
            ]

            if filters:
                cmd.extend(["-vf", ",".join(filters)])

            cmd.extend([
                "-c:a", "copy",
                output_path
            ])

            logger.info(f"Running local enhance: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            if Path(output_path).exists():
                enhanced_size = Path(output_path).stat().st_size

                # 获取时长
                duration = await self._get_duration(output_path)

                return VideoEnhanceResult(
                    success=True,
                    output_path=output_path,
                    original_path=video_path,
                    resolution=f"local_{level}",
                    enhanced_duration=duration,
                    file_size_before=Path(video_path).stat().st_size,
                    file_size_after=enhanced_size,
                    processing_time=time.time() - start_time
                )
            else:
                return VideoEnhanceResult(
                    success=False,
                    error_message="Output file not created"
                )

        except Exception as e:
            logger.error(f"Local enhance failed: {e}")
            return VideoEnhanceResult(success=False, error_message=str(e))

    async def _download_video(self, url: str, output_path: str) -> bool:
        """下载视频"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(output_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        return True
            return False
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    async def _get_duration(self, video_path: str) -> float:
        """获取视频时长"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            return float(stdout.decode().strip())
        except Exception:
            return 0.0

    def list_presets(self) -> List[Dict[str, Any]]:
        """列出所有预设"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "level": p.level,
                "services": p.services,
                "scale_factor": p.scale_factor
            }
            for p in PRESETS.values()
        ]


class VideoCompressor:
    """视频压缩器"""

    def __init__(self):
        self.presets = {
            "抖音": {
                "codec": "libx264",
                "crf": 23,
                "preset": "medium",
                "max_bitrate": "8M"
            },
            "快手": {
                "codec": "libx264",
                "crf": 22,
                "preset": "slow",
                "max_bitrate": "10M"
            },
            "视频号": {
                "codec": "libx264",
                "crf": 20,
                "preset": "medium",
                "max_bitrate": "15M"
            },
            "微博": {
                "codec": "libx264",
                "crf": 21,
                "preset": "medium",
                "max_bitrate": "20M"
            }
        }

    async def compress(
        self,
        video_path: str,
        output_path: str,
        platform: str = "抖音"
    ) -> VideoEnhanceResult:
        """
        根据平台优化压缩视频

        Args:
            video_path: 输入视频
            output_path: 输出视频
            platform: 目标平台

        Returns:
            VideoEnhanceResult
        """
        start_time = time.time()
        preset = self.presets.get(platform, self.presets["抖音"])

        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-c:v", preset["codec"],
                "-crf", str(preset["crf"]),
                "-preset", preset["preset"],
                "-maxrate", preset["max_bitrate"],
                "-bufsize", f"{int(preset['max_bitrate'].rstrip('M'))}M",
                "-c:a", "aac",
                "-b:a", "128k",
                output_path
            ]

            logger.info(f"Compressing for {platform}: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            if Path(output_path).exists():
                original_size = Path(video_path).stat().st_size
                compressed_size = Path(output_path).stat().st_size

                return VideoEnhanceResult(
                    success=True,
                    output_path=output_path,
                    original_path=video_path,
                    processing_time=time.time() - start_time,
                    file_size_before=original_size,
                    file_size_after=compressed_size
                )
            else:
                return VideoEnhanceResult(success=False, error_message="Compression failed")

        except Exception as e:
            return VideoEnhanceResult(success=False, error_message=str(e))


# 全局实例
_enhancer: Optional[VideoEnhancer] = None
_compressor: Optional[VideoCompressor] = None


def get_video_enhancer(config: Optional[VideoEnhanceConfig] = None) -> VideoEnhancer:
    """获取增强器实例"""
    global _enhancer
    if _enhancer is None or config is not None:
        _enhancer = VideoEnhancer(config)
    return _enhancer


def get_video_compressor() -> VideoCompressor:
    """获取压缩器实例"""
    global _compressor
    if _compressor is None:
        _compressor = VideoCompressor()
    return _compressor