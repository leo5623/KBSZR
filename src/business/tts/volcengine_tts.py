"""火山引擎TTS客户端"""
from dataclasses import dataclass
from typing import Optional
import httpx
import base64
from loguru import logger


@dataclass
class TTSResult:
    """TTS结果"""
    success: bool
    audio_path: str = ""
    audio_data: bytes = None
    duration: float = 0.0
    error: str = ""
    provider: str = "volcengine"


class VolcEngineTTS:
    """火山引擎TTS客户端"""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        app_id: str = "",
        cluster: str = "volc_megatts"
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.app_id = app_id
        self.cluster = cluster
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"VolcEngineTTS initialized: cluster={cluster}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            return True
        except Exception as e:
            logger.warning(f"VolcEngine TTS health check failed: {e}")
            return False

    async def synthesize(
        self,
        text: str,
        voice: str = "BV700_V2",
        speed: float = 1.0,
        pitch: float = 0.0,
        volume: float = 1.0,
        output_path: Optional[str] = None
    ) -> TTSResult:
        """
        合成语音

        Args:
            text: 待合成文本
            voice: 音色ID
            speed: 语速 (0.5-2.0)
            pitch: 音调 (-24~24)
            volume: 音量 (0~1.0)
            output_path: 输出文件路径
        """
        client = await self._get_client()

        # 构造请求体
        payload = {
            "appid": self.app_id,
            "cluster": self.cluster,
            "text": text,
            "voice": voice,
            "speed": speed,
            "pitch": pitch,
            "volume": volume,
            "encoding": "mp3"
        }

        try:
            response = await client.post(
                "https://openspeech.bytedance.com/api/v3/mego/tts",
                json=payload,
                headers={
                    "Authorization": f"Bearer; {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 200:
                audio_data = response.content

                # 保存文件
                if output_path is None:
                    import tempfile
                    import os
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir="./data/voices").name
                    output_path = temp_file

                with open(output_path, "wb") as f:
                    f.write(audio_data)

                logger.info(f"VolcEngine TTS synthesized: {len(audio_data)} bytes")

                return TTSResult(
                    success=True,
                    audio_path=output_path,
                    audio_data=audio_data,
                    duration=len(audio_data) / (16000 * 2),
                    provider="volcengine"
                )
            else:
                return TTSResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    provider="volcengine"
                )

        except Exception as e:
            logger.error(f"VolcEngine TTS failed: {e}")
            return TTSResult(
                success=False,
                error=str(e),
                provider="volcengine"
            )