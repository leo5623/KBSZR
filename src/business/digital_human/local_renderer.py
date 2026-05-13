"""本地数字人渲染器 - 开源模型"""
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
import asyncio
import subprocess
from loguru import logger


@dataclass
class LocalRenderResult:
    """本地渲染结果"""
    success: bool
    video_path: str = ""
    duration: float = 0.0
    error: str = ""
    model: str = ""


class LocalRenderer:
    """
    本地数字人渲染器

    支持的开源模型：
    - SadTalker: 从音频生成说话人视频
    - Wav2Lip: 唇形同步（需要预先准备人脸视频）
    """

    def __init__(
        self,
        model_dir: str = "./models/digital_human",
        device: str = "cuda"  # cuda / cpu
    ):
        self.model_dir = Path(model_dir)
        self.device = device
        self._models = {}
        logger.info(f"LocalRenderer initialized: device={device}")

    async def health_check(self) -> dict:
        """检查本地渲染环境"""
        results = {"ffmpeg": False, "python": False, "models": []}

        # 检查ffmpeg
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            results["ffmpeg"] = result.returncode == 0
        except FileNotFoundError:
            pass

        # 检查Python环境
        try:
            import sys
            results["python"] = True
        except Exception:
            pass

        # 检查模型
        if self.model_dir.exists():
            for model_path in self.model_dir.iterdir():
                if model_path.is_dir():
                    results["models"].append(model_path.name)

        return results

    async def render_sadtalker(
        self,
        audio_path: str,
        image_path: str,
        output_path: str,
        checkpoint: str = "SadTalker"
    ) -> LocalRenderResult:
        """
        使用SadTalker渲染

        Args:
            audio_path: 音频文件路径
            image_path: 人脸图片路径
            output_path: 输出视频路径
            checkpoint: 模型检查点名称

        Returns:
            LocalRenderResult
        """
        try:
            # 检查文件存在
            import os
            if not os.path.exists(audio_path):
                return LocalRenderResult(
                    success=False,
                    error=f"Audio file not found: {audio_path}"
                )
            if not os.path.exists(image_path):
                return LocalRenderResult(
                    success=False,
                    error=f"Image file not found: {image_path}"
                )

            # 构建命令
            # SadTalker用法: python inference.py --driven_audio audio.mp3 --source_image image.jpg --result_dir output
            cmd = [
                "python", "-m", "sadtalker",
                "--driven_audio", audio_path,
                "--source_image", image_path,
                "--result_dir", str(Path(output_path).parent),
                "--save_name", Path(output_path).stem
            ]

            if self.device == "cpu":
                cmd.append("--cpu")

            logger.info(f"Running SadTalker: {' '.join(cmd)}")

            # 执行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # 检查输出文件
                if os.path.exists(output_path):
                    return LocalRenderResult(
                        success=True,
                        video_path=output_path,
                        duration=self._estimate_duration(audio_path),
                        model="sadtalker"
                    )
                else:
                    return LocalRenderResult(
                        success=False,
                        error="Output file not generated",
                        model="sadtalker"
                    )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"SadTalker failed: {error_msg}")
                return LocalRenderResult(
                    success=False,
                    error=error_msg,
                    model="sadtalker"
                )

        except Exception as e:
            logger.error(f"SadTalker render exception: {e}")
            return LocalRenderResult(
                success=False,
                error=str(e),
                model="sadtalker"
            )

    async def render_wav2lip(
        self,
        audio_path: str,
        video_path: str,
        output_path: str,
        checkpoint: str = "wav2lip"
    ) -> LocalRenderResult:
        """
        使用Wav2Lip进行唇形同步

        Args:
            audio_path: 音频文件路径
            video_path: 人脸视频路径（需要预先准备）
            output_path: 输出视频路径
            checkpoint: 模型检查点名称

        Returns:
            LocalRenderResult
        """
        try:
            import os
            if not os.path.exists(audio_path):
                return LocalRenderResult(success=False, error=f"Audio not found: {audio_path}")
            if not os.path.exists(video_path):
                return LocalRenderResult(success=False, error=f"Video not found: {video_path}")

            # Wav2Lip用法
            cmd = [
                "python", "-m", "wav2lip",
                "--audio", audio_path,
                "--face", video_path,
                "--outfile", output_path
            ]

            logger.info(f"Running Wav2Lip: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and os.path.exists(output_path):
                return LocalRenderResult(
                    success=True,
                    video_path=output_path,
                    duration=self._estimate_duration(audio_path),
                    model="wav2lip"
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return LocalRenderResult(success=False, error=error_msg, model="wav2lip")

        except Exception as e:
            logger.error(f"Wav2Lip render exception: {e}")
            return LocalRenderResult(success=False, error=str(e), model="wav2lip")

    def _estimate_duration(self, audio_path: str) -> float:
        """估算音频时长"""
        try:
            # 使用ffprobe获取时长
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return 10.0  # 默认10秒

    @staticmethod
    def list_available_models() -> List[str]:
        """列出可用的本地模型"""
        return ["sadtalker", "wav2lip"]

    @staticmethod
    def get_model_requirements(model: str) -> dict:
        """获取模型要求"""
        requirements = {
            "sadtalker": {
                "name": "SadTalker",
                "description": "从单张图片+音频生成说话人视频",
                "gpu_recommended": True,
                "min_gpu_memory": "4GB",
                "dependencies": ["torch", "dlib", "facenet-pytorch"],
                "download_url": "https://github.com/OpenTalker/SadTalker"
            },
            "wav2lip": {
                "name": "Wav2Lip",
                "description": "唇形同步（需要预先准备人脸视频）",
                "gpu_recommended": True,
                "min_gpu_memory": "4GB",
                "dependencies": ["torch", "face detection models"],
                "download_url": "https://github.com/Rudrabha/Wav2Lip"
            }
        }
        return requirements.get(model, {})


# 便捷函数
async def render_local_digital_human(
    audio_path: str,
    image_or_video_path: str,
    output_path: str,
    model: str = "sadtalker",
    device: str = "cuda"
) -> LocalRenderResult:
    """便捷的本地渲染函数"""
    renderer = LocalRenderer(device=device)

    if model == "sadtalker":
        return await renderer.render_sadtalker(
            audio_path=audio_path,
            image_path=image_or_video_path,
            output_path=output_path
        )
    elif model == "wav2lip":
        return await renderer.render_wav2lip(
            audio_path=audio_path,
            video_path=image_or_video_path,
            output_path=output_path
        )
    else:
        return LocalRenderResult(
            success=False,
            error=f"Unknown model: {model}"
        )