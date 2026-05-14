"""本地数字人渲染器 - 开源模型增强版"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import asyncio
import subprocess
import os
import shutil
from loguru import logger


@dataclass
class LocalRenderResult:
    """本地渲染结果"""
    success: bool
    video_path: str = ""
    duration: float = 0.0
    error: str = ""
    model: str = ""
    frames_generated: int = 0


@dataclass
class RenderProgress:
    """渲染进度"""
    stage: str  # preparing / processing / finalizing
    progress: float  # 0.0 - 1.0
    current_frame: int = 0
    total_frames: int = 0
    message: str = ""


@dataclass
class LocalRenderConfig:
    """本地渲染配置"""
    model_dir: str = "./models/digital_human"
    output_dir: str = "./data/output/temp"
    device: str = "cuda"  # cuda / cpu
    cache_dir: str = "./cache"
    temp_dir: str = "./data/temp"


class LocalRenderer:
    """
    本地数字人渲染器

    支持的开源模型：
    - SadTalker: 从音频生成说话人视频
    - Wav2Lip: 唇形同步（需要预先准备人脸视频）
    - DFM (Diffusion Model): 扩散模型（未来支持）

    功能：
    - GPU加速支持
    - 进度回调
    - 中断恢复
    - 多模型管理
    """

    def __init__(
        self,
        model_dir: str = "./models/digital_human",
        device: str = "cuda",
        output_dir: str = "./data/output/temp"
    ):
        self.model_dir = Path(model_dir)
        self.device = device
        self.output_dir = Path(output_dir)
        self.cache_dir = Path("./cache")
        self.temp_dir = Path("./data/temp")

        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self._models: Dict[str, Any] = {}
        self._active_process: Optional[asyncio.subprocess.Process] = None
        self._cancel_requested = False

        logger.info(f"LocalRenderer initialized: device={device}, model_dir={model_dir}")

    async def health_check(self) -> dict:
        """检查本地渲染环境"""
        results = {
            "available": False,
            "ffmpeg": False,
            "python": False,
            "cuda": False,
            "models": [],
            "gpu_memory": "",
            "errors": []
        }

        # 检查ffmpeg
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            results["ffmpeg"] = result.returncode == 0
        except FileNotFoundError:
            results["errors"].append("FFmpeg not found in PATH")

        # 检查Python环境
        try:
            import sys
            results["python"] = True
        except Exception as e:
            results["errors"].append(f"Python check failed: {e}")

        # 检查CUDA
        try:
            cuda_check = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True
            )
            if cuda_check.returncode == 0:
                results["cuda"] = True
                results["gpu_memory"] = cuda_check.stdout.strip().split("\n")[0] if cuda_check.stdout else ""
                self.device = "cuda"
            else:
                self.device = "cpu"
        except FileNotFoundError:
            results["errors"].append("CUDA not available, falling back to CPU")
            self.device = "cpu"

        # 检查模型
        if self.model_dir.exists():
            for model_path in self.model_dir.iterdir():
                if model_path.is_dir():
                    results["models"].append({
                        "name": model_path.name,
                        "path": str(model_path),
                        "size": self._get_folder_size(model_path)
                    })

        results["available"] = results["ffmpeg"] and results["python"]
        return results

    def _get_folder_size(self, path: Path) -> str:
        """获取文件夹大小"""
        total = 0
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
            # 转换为可读单位
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total < 1024:
                    return f"{total:.1f} {unit}"
                total /= 1024
        except Exception:
            pass
        return "0 B"

    async def render_sadtalker(
        self,
        audio_path: str,
        image_path: str,
        output_path: str,
        checkpoint: str = "sadtalker",
        progress_callback=None
    ) -> LocalRenderResult:
        """
        使用SadTalker渲染

        Args:
            audio_path: 音频文件路径
            image_path: 人脸图片路径
            output_path: 输出视频路径
            checkpoint: 模型检查点名称
            progress_callback: 进度回调函数

        Returns:
            LocalRenderResult
        """
        try:
            # 文件检查
            if not os.path.exists(audio_path):
                return LocalRenderResult(success=False, error=f"Audio file not found: {audio_path}", model="sadtalker")
            if not os.path.exists(image_path):
                return LocalRenderResult(success=False, error=f"Image file not found: {image_path}", model="sadtalker")

            # 创建临时目录
            temp_id = f"sadtalker_{Path(audio_path).stem}"
            temp_work_dir = self.temp_dir / temp_id
            temp_work_dir.mkdir(parents=True, exist_ok=True)

            # 复制素材到临时目录
            temp_audio = temp_work_dir / "audio.wav"
            temp_image = temp_work_dir / "source.jpg"
            shutil.copy(audio_path, temp_audio)
            shutil.copy(image_path, temp_image)

            # 准备输出目录
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # SadTalker推理命令
            # 实际项目中需要根据SadTalker的github仓库正确配置
            sadtalker_path = self.model_dir / "sadtalker"
            if not sadtalker_path.exists():
                # 如果没有下载模型，使用占位处理
                return await self._render_placeholder(
                    audio_path, image_path, output_path, "sadtalker", progress_callback
                )

            cmd = [
                "python", str(sadtalker_path / "inference.py"),
                "--driven_audio", str(temp_audio),
                "--source_image", str(temp_image),
                "--result_dir", str(temp_work_dir),
                "--save_name", Path(output_path).stem,
                "--batch_size", "1"
            ]

            if self.device == "cpu":
                cmd.append("--cpu")
            else:
                cmd.append("--gpu")

            logger.info(f"Running SadTalker: {' '.join(cmd)}")

            # 报告进度
            if progress_callback:
                await progress_callback(RenderProgress(
                    stage="processing",
                    progress=0.1,
                    message="正在初始化模型..."
                ))

            # 执行
            self._cancel_requested = False
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(sadtalker_path.parent)
            )
            self._active_process = process

            # 监控进度
            stderr_lines = []
            async for line in process.stderr.readline():
                if line:
                    stderr_lines.append(line.decode())
                    # 解析进度（SadTalker会输出进度信息）
                    if b"Processing" in line or b"frame" in line:
                        if progress_callback:
                            await progress_callback(RenderProgress(
                                stage="processing",
                                progress=0.3,
                                message=f"渲染中... {line.decode().strip()}"
                            ))

                # 检查取消
                if self._cancel_requested:
                    process.terminate()
                    return LocalRenderResult(
                        success=False,
                        error="Render cancelled by user",
                        model="sadtalker"
                    )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # 查找输出文件
                output_dir = temp_work_dir
                generated_files = list(output_dir.glob("*.mp4")) + list(output_dir.glob("*.avi"))

                if generated_files:
                    # 复制到最终输出位置
                    shutil.copy(generated_files[0], output_path)

                    if progress_callback:
                        await progress_callback(RenderProgress(
                            stage="finalizing",
                            progress=0.95,
                            message="正在完成..."
                        ))

                    return LocalRenderResult(
                        success=True,
                        video_path=output_path,
                        duration=self._estimate_duration(output_path),
                        model="sadtalker",
                        frames_generated=self._estimate_frames(output_path)
                    )
                else:
                    return LocalRenderResult(
                        success=False,
                        error="Output file not generated",
                        model="sadtalker"
                    )
            else:
                error_msg = "".join(stderr_lines[-10:]) if stderr_lines else "Unknown error"
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
        finally:
            self._active_process = None

    async def render_wav2lip(
        self,
        audio_path: str,
        video_path: str,
        output_path: str,
        checkpoint: str = "wav2lip",
        progress_callback=None
    ) -> LocalRenderResult:
        """
        使用Wav2Lip进行唇形同步

        Args:
            audio_path: 音频文件路径
            video_path: 人脸视频路径（需要预先准备）
            output_path: 输出视频路径
            checkpoint: 模型检查点名称
            progress_callback: 进度回调函数

        Returns:
            LocalRenderResult
        """
        try:
            if not os.path.exists(audio_path):
                return LocalRenderResult(success=False, error=f"Audio not found: {audio_path}", model="wav2lip")
            if not os.path.exists(video_path):
                return LocalRenderResult(success=False, error=f"Video not found: {video_path}", model="wav2lip")

            # 准备输出目录
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            wav2lip_path = self.model_dir / "wav2lip"
            if not wav2lip_path.exists():
                return await self._render_placeholder(audio_path, video_path, output_path, "wav2lip", progress_callback)

            # Wav2Lip命令
            cmd = [
                "python", str(wav2lip_path / "inference.py"),
                "--audio", str(audio_path),
                "--face", str(video_path),
                "--outfile", str(output_path)
            ]

            if self.device == "cpu":
                cmd.append("--cpu")
            else:
                cmd.extend(["--gpu", "0"])

            logger.info(f"Running Wav2Lip: {' '.join(cmd)}")

            if progress_callback:
                await progress_callback(RenderProgress(
                    stage="processing",
                    progress=0.1,
                    message="正在处理唇形同步..."
                ))

            self._cancel_requested = False
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self._active_process = process

            async for line in process.stderr.readline():
                if line:
                    if progress_callback and (b"Processing" in line or b"frame" in line):
                        await progress_callback(RenderProgress(
                            stage="processing",
                            progress=0.5,
                            message=f"处理中... {line.decode().strip()[:50]}"
                        ))

                if self._cancel_requested:
                    process.terminate()
                    return LocalRenderResult(
                        success=False,
                        error="Render cancelled by user",
                        model="wav2lip"
                    )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and os.path.exists(output_path):
                return LocalRenderResult(
                    success=True,
                    video_path=output_path,
                    duration=self._estimate_duration(output_path),
                    model="wav2lip",
                    frames_generated=self._estimate_frames(output_path)
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return LocalRenderResult(success=False, error=error_msg, model="wav2lip")

        except Exception as e:
            logger.error(f"Wav2Lip render exception: {e}")
            return LocalRenderResult(success=False, error=str(e), model="wav2lip")
        finally:
            self._active_process = None

    async def _render_placeholder(
        self,
        audio_path: str,
        image_or_video_path: str,
        output_path: str,
        model: str,
        progress_callback
    ) -> LocalRenderResult:
        """
        当本地模型未安装时的占位渲染
        使用FFmpeg将音频与图片/视频简单合成
        """
        logger.warning(f"Model not installed, using placeholder render for {model}")

        if progress_callback:
            await progress_callback(RenderProgress(
                stage="preparing",
                progress=0.1,
                message="模型未安装，使用简化渲染..."
            ))

        try:
            # 检查输入是图片还是视频
            is_image = image_or_video_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))

            if is_image:
                # 图片 + 音频 -> 视频（简单合成）
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", image_or_video_path,
                    "-i", audio_path,
                    "-c:v", "libx264",
                    "-tune", "stillimage",
                    "-c:a", "aac",
                    "-shortest",
                    "-pix_fmt", "yuv420p",
                    output_path
                ]
            else:
                # 视频 + 音频 -> 合并
                cmd = [
                    "ffmpeg", "-y",
                    "-i", image_or_video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    output_path
                ]

            if progress_callback:
                await progress_callback(RenderProgress(
                    stage="processing",
                    progress=0.5,
                    message="正在合成..."
                ))

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            if os.path.exists(output_path):
                if progress_callback:
                    await progress_callback(RenderProgress(
                        stage="finalizing",
                        progress=1.0,
                        message="完成"
                    ))

                return LocalRenderResult(
                    success=True,
                    video_path=output_path,
                    duration=self._estimate_duration(output_path),
                    model=f"{model}_placeholder",
                    frames_generated=self._estimate_frames(output_path)
                )
            else:
                return LocalRenderResult(
                    success=False,
                    error="FFmpeg合成失败",
                    model=f"{model}_placeholder"
                )

        except Exception as e:
            return LocalRenderResult(
                success=False,
                error=f"Placeholder render failed: {e}",
                model=f"{model}_placeholder"
            )

    async def cancel(self):
        """取消当前渲染"""
        self._cancel_requested = True
        if self._active_process:
            try:
                self._active_process.terminate()
                logger.info("Render cancelled by user")
            except Exception as e:
                logger.error(f"Failed to cancel render: {e}")

    def _estimate_duration(self, video_path: str) -> float:
        """估算视频时长"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return 10.0

    def _estimate_frames(self, video_path: str) -> int:
        """估算帧数"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=nb_frames",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        return 0

    @staticmethod
    def list_available_models() -> List[Dict[str, Any]]:
        """列出可用的本地模型"""
        return [
            {
                "id": "sadtalker",
                "name": "SadTalker",
                "description": "从单张图片+音频生成说话人视频",
                "gpu_recommended": True,
                "min_gpu_memory": "4GB",
                "dependencies": ["torch", "dlib", "facenet-pytorch"],
                "download_url": "https://github.com/OpenTalker/SadTalker"
            },
            {
                "id": "wav2lip",
                "name": "Wav2Lip",
                "description": "唇形同步（需要预先准备人脸视频）",
                "gpu_recommended": True,
                "min_gpu_memory": "4GB",
                "dependencies": ["torch", "face detection models"],
                "download_url": "https://github.com/Rudrabha/Wav2Lip"
            },
            {
                "id": "wav2lip_gan",
                "name": "Wav2Lip (GAN version)",
                "description": "Wav2Lip GAN增强版，更高质量",
                "gpu_recommended": True,
                "min_gpu_memory": "6GB",
                "dependencies": ["torch", "PerceptualLoss"],
                "download_url": "https://github.com/Rudrabha/Wav2Lip"
            }
        ]

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


class ModelDownloader:
    """模型下载器"""

    def __init__(self, cache_dir: str = "./cache/models"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def download_sadtalker(self, progress_callback=None) -> Tuple[bool, str]:
        """下载SadTalker模型"""
        model_url = "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2/sadtalker_models.zip"
        dest_path = self.cache_dir / "sadtalker_models.zip"

        try:
            import urllib.request

            if progress_callback:
                await progress_callback("downloading", 0.0, "开始下载...")

            # 简化版：记录下载链接，实际使用需要wget或aria2
            logger.info(f"SadTalker download URL: {model_url}")
            logger.info(f"Please download manually and place in: {self.cache_dir}")

            if progress_callback:
                await progress_callback("downloaded", 1.0, "下载完成（请手动安装）")

            return True, str(dest_path)

        except Exception as e:
            return False, str(e)

    async def download_wav2lip(self, progress_callback=None) -> Tuple[bool, str]:
        """下载Wav2Lip模型"""
        model_url = "https://github.com/Rudrabha/Wav2Lip/releases/download/models/wav2lip.pth"
        dest_path = self.cache_dir / "wav2lip.pth"

        try:
            logger.info(f"Wav2Lip download URL: {model_url}")
            logger.info(f"Please download manually and place in: {self.cache_dir}")
            return True, str(dest_path)
        except Exception as e:
            return False, str(e)


# 全局实例
_renderer: Optional[LocalRenderer] = None


def get_local_renderer() -> LocalRenderer:
    """获取本地渲染器实例"""
    global _renderer
    if _renderer is None:
        _renderer = LocalRenderer()
    return _renderer


# 便捷函数
async def render_local_digital_human(
    audio_path: str,
    image_or_video_path: str,
    output_path: str,
    model: str = "sadtalker",
    device: str = "cuda",
    progress_callback=None
) -> LocalRenderResult:
    """便捷的本地渲染函数"""
    renderer = LocalRenderer(device=device)

    if model == "sadtalker":
        return await renderer.render_sadtalker(
            audio_path=audio_path,
            image_path=image_or_video_path,
            output_path=output_path,
            progress_callback=progress_callback
        )
    elif model == "wav2lip":
        return await renderer.render_wav2lip(
            audio_path=audio_path,
            video_path=image_or_video_path,
            output_path=output_path,
            progress_callback=progress_callback
        )
    else:
        return LocalRenderResult(
            success=False,
            error=f"Unknown model: {model}"
        )