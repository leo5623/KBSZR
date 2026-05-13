"""TTS路由 - 云端API"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

from loguru import logger

from src.business.tts.aliyun_client import AliyunTTS, TTSResult, ALIYUN_VOICES, VoiceConfig
from src.business.tts.volcengine_tts import VolcEngineTTS
from src.business.tts.voice_clone import VoiceClone, CloneResult


class TTSMode(Enum):
    """TTS模式"""
    CLOUD = "cloud"


@dataclass
class TTSConfig:
    """TTS配置"""
    mode: TTSMode = TTSMode.CLOUD
    provider: str = "aliyun"  # aliyun / volcengine

    # 阿里云配置
    aliyun_api_key: str = ""
    aliyun_region: str = "cn-shanghai"

    # 火山引擎配置
    volcengine_api_key: str = ""
    volcengine_secret_key: str = ""


@dataclass
class TTSRequest:
    """TTS请求"""
    text: str
    voice: str = "xiaomo"  # 音色ID或名称
    speed: float = 1.0  # 语速 0.5-2.0
    pitch: float = 0.0  # 音调
    volume: float = 1.0  # 音量
    output_path: Optional[str] = None


@dataclass
class TTSResponse:
    """TTS响应"""
    success: bool
    audio_path: str = ""
    duration: float = 0.0
    error: str = ""
    mode: str = ""
    provider: str = ""


class TTSRouter:
    """
    TTS路由 - 云端API模式
    支持阿里云TTS、火山引擎TTS
    声音克隆仅云端支持
    """

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._tts_client = None
        self._clone_client = None
        self._cloned_voices: dict = {}  # voice_name -> voice_id
        logger.info(f"TTSRouter initialized: provider={self.config.provider}")

    async def _get_tts_client(self):
        """获取TTS客户端"""
        if self._tts_client is None:
            if self.config.provider == "aliyun":
                self._tts_client = AliyunTTS(
                    api_key=self.config.aliyun_api_key,
                    region=self.config.aliyun_region
                )
            elif self.config.provider == "volcengine":
                self._tts_client = VolcEngineTTS(
                    api_key=self.config.volcengine_api_key,
                    secret_key=self.config.volcengine_secret_key
                )
            else:
                raise ValueError(f"Unknown provider: {self.config.provider}")
        return self._tts_client

    async def _get_clone_client(self):
        """获取克隆客户端"""
        if self._clone_client is None:
            if self.config.provider == "aliyun":
                self._clone_client = VoiceClone(
                    api_key=self.config.aliyun_api_key,
                    region=self.config.aliyun_region
                )
            else:
                raise ValueError(f"Voice clone not supported for provider: {self.config.provider}")
        return self._clone_client

    async def health_check(self) -> dict:
        """检查TTS服务健康状态"""
        results = {"tts": {}, "clone": {}}

        try:
            client = await self._get_tts_client()
            tts_ok = await client.health_check()
            results["tts"] = {"available": tts_ok, "provider": self.config.provider}
        except Exception as e:
            results["tts"] = {"available": False, "error": str(e)}

        try:
            clone = await self._get_clone_client()
            clone_ok = await clone.health_check()
            results["clone"] = {"available": clone_ok, "provider": self.config.provider}
        except Exception as e:
            results["clone"] = {"available": False, "error": str(e)}

        return results

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """
        合成语音

        Args:
            request: TTS请求

        Returns:
            TTS响应
        """
        try:
            # 检查是否是克隆的声音
            voice_id = self._get_voice_id(request.voice)

            client = await self._get_tts_client()

            # 阿里云TTS
            if self.config.provider == "aliyun":
                # 转换参数
                speech_rate = int((request.speed - 1.0) * 500)  # 转换到-500~500
                pitch_rate = int(request.pitch * 50)  # 转换

                result = await client.synthesize(
                    text=request.text,
                    voice=voice_id,
                    speech_rate=speech_rate,
                    pitch_rate=pitch_rate,
                    output_path=request.output_path
                )

                return TTSResponse(
                    success=result.success,
                    audio_path=result.audio_path,
                    duration=result.duration,
                    error=result.error,
                    mode="cloud",
                    provider="aliyun"
                )

            # 火山引擎TTS
            elif self.config.provider == "volcengine":
                result = await client.synthesize(
                    text=request.text,
                    voice=voice_id,
                    speed=request.speed,
                    pitch=request.pitch,
                    volume=request.volume,
                    output_path=request.output_path
                )

                return TTSResponse(
                    success=result.success,
                    audio_path=result.audio_path,
                    duration=result.duration,
                    error=result.error,
                    mode="cloud",
                    provider="volcengine"
                )

            else:
                return TTSResponse(
                    success=False,
                    error=f"Unknown provider: {self.config.provider}",
                    mode="cloud",
                    provider=self.config.provider
                )

        except Exception as e:
            logger.error(f"TTS synthesize failed: {e}")
            return TTSResponse(
                success=False,
                error=str(e),
                mode="cloud",
                provider=self.config.provider
            )

    async def clone_voice(
        self,
        audio_samples: List[str],
        voice_name: str
    ) -> CloneResult:
        """
        克隆声音

        Args:
            audio_samples: 音频样本路径列表
            voice_name: 克隆音色的名称

        Returns:
            CloneResult
        """
        try:
            client = await self._get_clone_client()
            result = await client.clone(audio_samples, voice_name)

            if result.success:
                self._cloned_voices[voice_name] = result.voice_id

            return result

        except Exception as e:
            logger.error(f"Voice clone failed: {e}")
            return CloneResult(
                success=False,
                error=str(e),
                provider=self.config.provider
            )

    def _get_voice_id(self, voice_name_or_id: str) -> str:
        """获取voice_id"""
        # 先检查是否是克隆的声音
        if voice_name_or_id in self._cloned_voices:
            return self._cloned_voices[voice_name_or_id]

        # 检查是否是预置音色
        for voice in ALIYUN_VOICES:
            if voice.name == voice_name_or_id or voice.voice_id == voice_name_or_id:
                return voice.voice_id

        # 默认返回
        return voice_name_or_id

    def list_voices(self) -> List[VoiceConfig]:
        """列出所有可用音色"""
        voices = list(ALIYUN_VOICES)

        # 添加克隆的声音
        for name, vid in self._cloned_voices.items():
            voices.append(VoiceConfig(
                voice_id=vid,
                name=f"[克隆] {name}",
                description="克隆音色"
            ))

        return voices

    async def close(self):
        """关闭连接"""
        if self._tts_client:
            await self._tts_client.close()
            self._tts_client = None

        if self._clone_client:
            await self._clone_client.close()
            self._clone_client = None


# 便捷函数
async def synthesize_speech(
    text: str,
    voice: str = "xiaomo",
    speed: float = 1.0,
    config: Optional[TTSConfig] = None
) -> TTSResponse:
    """便捷的语音合成函数"""
    if config is None:
        config = TTSConfig()

    router = TTSRouter(config)
    request = TTSRequest(text=text, voice=voice, speed=speed)

    try:
        return await router.synthesize(request)
    finally:
        await router.close()


async def clone_voice(
    audio_samples: List[str],
    voice_name: str,
    config: Optional[TTSConfig] = None
) -> CloneResult:
    """便捷的声音克隆函数"""
    if config is None:
        config = TTSConfig()

    router = TTSRouter(config)

    try:
        return await router.clone_voice(audio_samples, voice_name)
    finally:
        await router.close()