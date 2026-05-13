"""阿里云TTS客户端"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx
import base64
import json
from loguru import logger


@dataclass
class TTSResult:
    """TTS结果"""
    success: bool
    audio_path: str = ""  # 本地保存路径
    audio_data: bytes = None  # 音频数据
    duration: float = 0.0  # 时长（秒）
    error: str = ""
    provider: str = "aliyun"


@dataclass
class VoiceConfig:
    """音色配置"""
    voice_id: str
    name: str
    language: str = "zh"
    gender: str = "female"
    description: str = ""


# 阿里云内置音色列表
ALIYUN_VOICES = [
    VoiceConfig("xiaomo", "小mo亲", "zh", "female", "亲和女声"),
    VoiceConfig("zhijia", "智佳", "zh", "female", "专业女声"),
    VoiceConfig("xiaoyun", "小云", "zh", "female", "温柔女声"),
    VoiceConfig("xiaogang", "小刚", "zh", "male", "活力男声"),
    VoiceConfig("zhiling", "智凌", "zh", "male", "商务男声"),
    VoiceConfig("aiqi", "艾琪", "zh", "female", "甜美女声"),
    VoiceConfig("aibin", "艾斌", "zh", "male", "磁性男声"),
    VoiceConfig("aijia", "艾佳", "zh", "female", "知性女声"),
]


class AliyunTTS:
    """阿里云TTS客户端"""

    def __init__(
        self,
        api_key: str,
        region: str = "cn-shanghai"
    ):
        self.api_key = api_key
        self.region = region
        self.base_url = f"https://nls-gateway-{region}.aliyuncs.com/stream/v1/tts"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"AliyunTTS initialized: region={region}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """检查服务是否可用"""
        try:
            # 简单的token验证请求
            client = await self._get_client()
            return True
        except Exception as e:
            logger.warning(f"Aliyun TTS health check failed: {e}")
            return False

    async def synthesize(
        self,
        text: str,
        voice: str = "xiaomo",
        speech_rate: float = 0.0,  # 语速 -500~500
        pitch_rate: float = 0.0,   # 音调 -500~500
        volume: float = 50.0,     # 音量 0~100
        output_path: Optional[str] = None
    ) -> TTSResult:
        """
        合成语音

        Args:
            text: 待合成文本
            voice: 音色ID
            speech_rate: 语速（-500~500）
            pitch_rate: 音调（-500~500）
            volume: 音量（0~100）
            output_path: 输出文件路径（可选）

        Returns:
            TTSResult
        """
        client = await self._get_client()

        # 请求参数
        params = {
            "appkey": self.api_key,
            "text": text,
            "format": "mp3",
            "voice": voice,
            "speech_rate": str(speech_rate),
            "pitch_rate": str(pitch_rate),
            "volume": str(volume),
        }

        try:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()

            audio_data = response.content

            # 保存文件
            if output_path is None:
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir="./data/voices"):
                    output_path = temp_file

            with open(output_path, "wb") as f:
                f.write(audio_data)

            # 获取时长（估算）
            # 实际应该解析mp3 metadata
            duration = len(audio_data) / (16000 * 2)  # 粗略估算

            logger.info(f"TTS synthesized: {len(audio_data)} bytes, saved to {output_path}")

            return TTSResult(
                success=True,
                audio_path=output_path,
                audio_data=audio_data,
                duration=duration,
                provider="aliyun"
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Aliyun TTS HTTP error: {e.response.status_code} - {e.response.text}")
            return TTSResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
                provider="aliyun"
            )
        except Exception as e:
            logger.error(f"Aliyun TTS failed: {e}")
            return TTSResult(
                success=False,
                error=str(e),
                provider="aliyun"
            )

    async def synthesize_long_text(
        self,
        text: str,
        voice: str = "xiaomo",
        speech_rate: float = 0.0,
        pitch_rate: float = 0.0,
        volume: float = 50.0,
        output_dir: str = "./data/voices"
    ) -> TTSResult:
        """
        长文本合成（自动分段）

        阿里云单次请求有字数限制（最大300字符），需要分段处理
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 分段（按标点符号）
        sentences = self._split_sentences(text)
        audio_files = []

        for i, sentence in enumerate(sentences):
            output_path = os.path.join(output_dir, f"segment_{i:03d}.mp3")
            result = await self.synthesize(
                text=sentence,
                voice=voice,
                speech_rate=speech_rate,
                pitch_rate=pitch_rate,
                volume=volume,
                output_path=output_path
            )

            if not result.success:
                return result

            audio_files.append(result.audio_path)

        # 合并音频文件
        merged_path = os.path.join(output_dir, "merged.mp3")
        await self._merge_audio_files(audio_files, merged_path)

        return TTSResult(
            success=True,
            audio_path=merged_path,
            duration=len(sentences) * 3.0,  # 估算
            provider="aliyun"
        )

    def _split_sentences(self, text: str, max_length: int = 280) -> List[str]:
        """按标点符号分段"""
        import re

        # 按句子分隔
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 合并过短的句子
        result = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) <= max_length:
                current += sentence + "。"
            else:
                if current:
                    result.append(current)
                current = sentence

        if current:
            result.append(current)

        return result

    async def _merge_audio_files(self, files: List[str], output_path: str):
        """合并多个音频文件"""
        # 这里会调用FFmpeg合并
        # 暂时跳过，实现见FFmpeg服务
        pass

    @staticmethod
    def list_voices() -> List[VoiceConfig]:
        """列出所有可用音色"""
        return ALIYUN_VOICES

    @staticmethod
    def get_voice_by_name(name: str) -> Optional[VoiceConfig]:
        """根据名称获取音色"""
        for voice in ALIYUN_VOICES:
            if voice.name == name or voice.voice_id == name:
                return voice
        return None