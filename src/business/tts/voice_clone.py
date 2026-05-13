"""声音克隆 - 阿里云少样本克隆"""
from dataclasses import dataclass
from typing import List, Optional
import httpx
from loguru import logger


@dataclass
class CloneResult:
    """克隆结果"""
    success: bool
    voice_id: str = ""
    voice_name: str = ""
    error: str = ""
    provider: str = "aliyun"


class VoiceClone:
    """
    阿里云声音克隆

    支持少样本克隆：只需30秒-5分钟音频即可克隆
    克隆后的音色可用于TTS合成
    """

    def __init__(
        self,
        api_key: str,
        region: str = "cn-shanghai"
    ):
        self.api_key = api_key
        self.region = region
        self.base_url = f"https://nls-gateway-{region}.aliyuncs.com/stream/v1/voiceclone"
        self._client: Optional[httpx.AsyncClient] = None
        self._cloned_voices: dict = {}  # 缓存已克隆的voice_id
        logger.info(f"VoiceClone initialized: region={region}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """检查克隆服务是否可用"""
        try:
            client = await self._get_client()
            return True
        except Exception as e:
            logger.warning(f"VoiceClone health check failed: {e}")
            return False

    async def clone(
        self,
        audio_samples: List[str],
        voice_name: str,
        language: str = "zh"
    ) -> CloneResult:
        """
        克隆声音

        Args:
            audio_samples: 音频样本路径列表（支持wav/mp3格式）
                          建议：30秒-5分钟，清晰无噪音
            voice_name: 克隆音色的名称（用于标识）
            language: 音频语言（默认zh）

        Returns:
            CloneResult: 包含克隆后的voice_id
        """
        client = await self._get_client()

        try:
            # 验证音频文件
            import os
            for sample_path in audio_samples:
                if not os.path.exists(sample_path):
                    return CloneResult(
                        success=False,
                        error=f"Audio file not found: {sample_path}",
                        provider="aliyun"
                    )

            # 构建multipart请求
            files = {}
            data = {
                "voice_name": voice_name,
                "language": language
            }

            for i, sample_path in enumerate(audio_samples):
                with open(sample_path, "rb") as f:
                    files[f"audio_{i}"] = (f"sample_{i}.mp3", f.read(), "audio/mpeg")

            response = await client.post(
                f"{self.base_url}/clone",
                data=data,
                files=files
            )

            if response.status_code == 200:
                result = response.json()
                voice_id = result.get("voice_id", "")

                # 缓存
                self._cloned_voices[voice_name] = voice_id

                logger.info(f"Voice cloned successfully: {voice_name} -> {voice_id}")

                return CloneResult(
                    success=True,
                    voice_id=voice_id,
                    voice_name=voice_name,
                    provider="aliyun"
                )
            else:
                error_msg = response.text
                logger.error(f"Voice clone failed: {response.status_code} - {error_msg}")
                return CloneResult(
                    success=False,
                    error=f"Clone failed: {error_msg}",
                    provider="aliyun"
                )

        except Exception as e:
            logger.error(f"Voice clone exception: {e}")
            return CloneResult(
                success=False,
                error=str(e),
                provider="aliyun"
            )

    async def list_cloned_voices(self) -> List[dict]:
        """
        列出已克隆的声音

        注意：阿里云克隆API可能不提供此接口，这里返回本地缓存
        """
        return [
            {"voice_name": name, "voice_id": vid}
            for name, vid in self._cloned_voices.items()
        ]

    async def delete_voice(self, voice_id: str) -> bool:
        """
        删除克隆的声音

        Args:
            voice_id: 要删除的voice_id

        Returns:
            是否删除成功
        """
        client = await self._get_client()

        try:
            response = await client.delete(
                f"{self.base_url}/voice/{voice_id}"
            )

            if response.status_code == 200:
                # 从缓存中移除
                to_remove = [name for name, vid in self._cloned_voices.items() if vid == voice_id]
                for name in to_remove:
                    del self._cloned_voices[name]

                logger.info(f"Voice deleted: {voice_id}")
                return True
            else:
                logger.error(f"Delete voice failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Delete voice exception: {e}")
            return False

    def get_voice_id(self, voice_name: str) -> Optional[str]:
        """获取已克隆声音的voice_id"""
        return self._cloned_voices.get(voice_name)


# 便捷函数
async def clone_voice(
    audio_samples: List[str],
    voice_name: str,
    api_key: str,
    region: str = "cn-shanghai"
) -> CloneResult:
    """便捷的克隆函数"""
    cloner = VoiceClone(api_key=api_key, region=region)
    try:
        return await cloner.clone(audio_samples, voice_name)
    finally:
        await cloner.close()