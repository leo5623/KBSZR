"""Voicebox本地TTS客户端"""
import os
import subprocess
import json
import time
import uuid
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

from loguru import logger


@dataclass
class VoiceboxConfig:
    """Voicebox配置"""
    enabled: bool = True
    exe_path: str = "./vendors/voicebox/Voicebox/voicebox.exe"
    server_path: str = "./vendors/voicebox/Voicebox/voicebox-server.exe"
    host: str = "127.0.0.1"
    port: int = 7890
    voice: str = "default"
    speed: float = 1.0
    output_dir: str = "./data/voices"


class VoiceboxTTSClient:
    """
    Voicebox本地TTS客户端
    通过HTTP API调用Voicebox进行语音合成
    """

    def __init__(self, config: Optional[VoiceboxConfig] = None):
        self.config = config or VoiceboxConfig()
        self._server_process: Optional[subprocess.Popen] = None
        self._base_url = f"http://{self.config.host}:{self.config.port}"

    async def health_check(self) -> bool:
        """检查Voicebox服务是否可用"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Voicebox health check failed: {e}")
            return False

    def is_server_running(self) -> bool:
        """检查服务器进程是否运行"""
        if self._server_process is None:
            return False
        return self._server_process.poll() is None

    async def start_server(self) -> bool:
        """启动Voicebox服务器"""
        if self.is_server_running():
            logger.info("Voicebox server already running")
            return True

        try:
            # 检查exe文件是否存在
            if not os.path.exists(self.config.server_path):
                logger.error(f"Voicebox server not found: {self.config.server_path}")
                return False

            # 启动服务器
            logger.info(f"Starting Voicebox server: {self.config.server_path}")
            self._server_process = subprocess.Popen(
                [self.config.server_path, "--port", str(self.config.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 等待服务器启动
            for _ in range(10):
                await asyncio.sleep(1)
                if await self.health_check():
                    logger.info("Voicebox server started successfully")
                    return True

            logger.error("Voicebox server failed to start")
            return False

        except Exception as e:
            logger.error(f"Failed to start Voicebox server: {e}")
            return False

    async def stop_server(self):
        """停止Voicebox服务器"""
        if self._server_process:
            self._server_process.terminate()
            try:
                self._server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._server_process.kill()
            self._server_process = None
            logger.info("Voicebox server stopped")

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        合成语音

        Args:
            text: 要合成的文本
            voice: 音色名称
            speed: 语速
            output_path: 输出文件路径

        Returns:
            包含audio_path, duration等信息的字典
        """
        # 确保服务器运行
        if not self.is_server_running():
            started = await self.start_server()
            if not started:
                return {"success": False, "error": "Failed to start Voicebox server"}

        # 生成输出路径
        if not output_path:
            os.makedirs(self.config.output_dir, exist_ok=True)
            output_path = os.path.join(
                self.config.output_dir,
                f"voicebox_{int(time.time())}_{uuid.uuid4().hex[:8]}.wav"
            )

        voice = voice or self.config.voice

        try:
            import httpx

            # 构建请求
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed,
                "output": output_path
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._base_url}/tts",
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "audio_path": result.get("audio_path", output_path),
                        "duration": result.get("duration", 0.0)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            logger.error(f"Voicebox TTS failed: {e}")
            return {"success": False, "error": str(e)}

    async def list_voices(self) -> list:
        """获取可用音色列表"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/voices")
                if response.status_code == 200:
                    return response.json().get("voices", [])
                return []
        except Exception as e:
            logger.warning(f"List voices failed: {e}")
            return ["default"]  # 默认音色

    def set_voice(self, voice: str):
        """设置默认音色"""
        self.config.voice = voice

    def set_speed(self, speed: float):
        """设置默认语速"""
        self.config.speed = speed

    async def close(self):
        """关闭客户端"""
        await self.stop_server()