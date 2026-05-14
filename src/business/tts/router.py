"""TTS路由 - 云端API（增强版）"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
import time

from loguru import logger

from src.business.tts.aliyun_client import AliyunTTS, TTSResult, ALIYUN_VOICES, VoiceConfig
from src.business.tts.volcengine_tts import VolcEngineTTS
from src.business.tts.voice_clone import VoiceClone, CloneResult
from src.business.tts.emotion_mapper import EmotionTTSMapper, EmotionType, VoicePreset
from src.business.tts.voice_library import VoiceLibraryManager as VoiceLibrary
from src.business.tts.voicebox import VoiceboxTTSClient, VoiceboxConfig


class TTSMode(Enum):
    """TTS模式"""
    CLOUD = "cloud"
    LOCAL = "local"


class TTSProvider(Enum):
    """TTS提供商"""
    ALIYUN = "aliyun"
    VOLCENGINE = "volcengine"
    VOICEBOX = "voicebox"


@dataclass
class TTSConfig:
    """TTS配置"""
    mode: TTSMode = TTSMode.CLOUD
    provider: str = "aliyun"  # aliyun / volcengine / voicebox

    # 阿里云配置
    aliyun_api_key: str = ""
    aliyun_region: str = "cn-shanghai"

    # 火山引擎配置
    volcengine_api_key: str = ""
    volcengine_secret_key: str = ""

    # Voicebox本地配置
    voicebox_enabled: bool = False
    voicebox_path: str = "./vendors/voicebox/Voicebox/voicebox.exe"
    voicebox_server_path: str = "./vendors/voicebox/Voicebox/voicebox-server.exe"
    voicebox_host: str = "127.0.0.1"
    voicebox_port: int = 7890

    # 通用配置
    default_voice: str = "xiaomo"
    default_speed: float = 1.0
    default_pitch: float = 0.0
    default_volume: float = 1.0
    output_dir: str = "./data/voices"


@dataclass
class TTSRequest:
    """TTS请求"""
    text: str
    voice: str = "xiaomo"  # 音色ID或名称
    speed: float = 1.0  # 语速 0.5-2.0
    pitch: float = 0.0  # 音调
    volume: float = 1.0  # 音量
    emotion: Optional[str] = None  # 情感标签
    output_path: Optional[str] = None


@dataclass
class BatchTTSRequest:
    """批量TTS请求"""
    texts: List[str]
    voice: str = "xiaomo"
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0


@dataclass
class TTSResponse:
    """TTS响应"""
    success: bool
    audio_path: str = ""
    duration: float = 0.0
    error: str = ""
    mode: str = ""
    provider: str = ""
    processing_time: float = 0.0


@dataclass
class BatchTTSResponse:
    """批量TTS响应"""
    success: bool
    results: List[TTSResponse] = field(default_factory=list)
    total_duration: float = 0.0
    total_time: float = 0.0
    error: str = ""


@dataclass
class VoiceInfo:
    """音色信息"""
    voice_id: str
    name: str
    provider: str
    language: str = "zh"
    gender: str = "female"
    category: str = "通用"  # 年龄、风格等分类
    description: str = ""
    emotion_scores: Dict[str, float] = field(default_factory=dict)  # 情感得分


class TTSRouter:
    """
    TTS路由 - 云端API模式（增强版）
    支持阿里云TTS、火山引擎TTS
    支持声音克隆
    支持情感语音映射
    """

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._tts_client = None
        self._clone_client = None
        self._voicebox_client = None
        self._cloned_voices: dict = {}  # voice_name -> voice_id

        # 初始化辅助组件
        self.emotion_mapper = EmotionTTSMapper()
        self.voice_library = VoiceLibrary()

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

    async def _get_voicebox_client(self) -> VoiceboxTTSClient:
        """获取Voicebox客户端"""
        if self._voicebox_client is None:
            voicebox_config = VoiceboxConfig(
                enabled=True,
                exe_path=self.config.voicebox_path,
                server_path=self.config.voicebox_server_path,
                host=self.config.voicebox_host,
                port=self.config.voicebox_port,
                output_dir=self.config.output_dir
            )
            self._voicebox_client = VoiceboxTTSClient(voicebox_config)
        return self._voicebox_client

    async def _get_clone_client(self):
        """获取克隆客户端"""
        if self._clone_client is None:
            if self.config.provider == "aliyun":
                self._clone_client = VoiceClone(
                    api_key=self.config.aliyun_api_key,
                    region=self.config.aliyun_region
                )
            else:
                raise ValueError("Voice clone not supported for provider: {self.config.provider}")
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
        start_time = time.time()

        try:
            # Voicebox本地TTS
            if self.config.provider == "voicebox":
                client = await self._get_voicebox_client()
                result = await client.synthesize(
                    text=request.text,
                    voice=request.voice,
                    speed=request.speed,
                    output_path=request.output_path
                )

                return TTSResponse(
                    success=result.get("success", False),
                    audio_path=result.get("audio_path", ""),
                    duration=result.get("duration", 0.0),
                    error=result.get("error", ""),
                    mode="local",
                    provider="voicebox",
                    processing_time=time.time() - start_time
                )

            # 检查是否是克隆的声音
            voice_id = self._get_voice_id(request.voice)

            # 情感映射
            if request.emotion:
                emotion, voice_params = self.emotion_mapper.map_emotion_to_tts(request.emotion, request.voice)
                # 合并参数（用户参数优先）
                if request.speed == 1.0:  # 默认值，使用情感映射的值
                    request.speed = voice_params.speed
                if request.pitch == 0.0:
                    request.pitch = voice_params.pitch

            client = await self._get_tts_client()

            # 阿里云TTS
            if self.config.provider == "aliyun":
                speech_rate = int((request.speed - 1.0) * 500)
                pitch_rate = int(request.pitch * 50)

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
                    provider="aliyun",
                    processing_time=time.time() - start_time
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
                    provider="volcengine",
                    processing_time=time.time() - start_time
                )

            else:
                return TTSResponse(
                    success=False,
                    error=f"Unknown provider: {self.config.provider}",
                    mode="cloud",
                    provider=self.config.provider,
                    processing_time=time.time() - start_time
                )

        except Exception as e:
            logger.error(f"TTS synthesize failed: {e}")
            return TTSResponse(
                success=False,
                error=str(e),
                mode="cloud",
                provider=self.config.provider,
                processing_time=time.time() - start_time
            )

    async def synthesize_batch(
        self,
        request: BatchTTSRequest,
        progress_callback: Optional[Callable] = None
    ) -> BatchTTSResponse:
        """
        批量合成语音

        Args:
            request: 批量TTS请求
            progress_callback: 进度回调

        Returns:
            批量TTS响应
        """
        start_time = time.time()
        results = []
        total_duration = 0.0

        for idx, text in enumerate(request.texts):
            response = await self.synthesize(TTSRequest(
                text=text,
                voice=request.voice,
                speed=request.speed,
                pitch=request.pitch,
                volume=request.volume
            ))

            results.append(response)

            if response.success:
                total_duration += response.duration

            if progress_callback:
                progress_callback(idx, len(request.texts), response)

        return BatchTTSResponse(
            success=all(r.success for r in results),
            results=results,
            total_duration=total_duration,
            total_time=time.time() - start_time
        )

    async def synthesize_long_text(
        self,
        text: str,
        voice: str = "xiaomo",
        speed: float = 1.0,
        max_segment_length: int = 300,
        output_dir: Optional[str] = None
    ) -> TTSResponse:
        """
        长文本合成（自动分段）

        Args:
            text: 长文本
            voice: 音色
            speed: 语速
            max_segment_length: 每段最大字符数
            output_dir: 输出目录

        Returns:
            TTS响应（合并后的音频路径）
        """
        start_time = time.time()

        # 分段
        segments = self._split_text(text, max_segment_length)

        # 逐段合成
        segment_files = []
        for idx, segment in enumerate(segments):
            output_path = f"{output_dir or self.config.output_dir}/segment_{idx:03d}.mp3"

            response = await self.synthesize(TTSRequest(
                text=segment,
                voice=voice,
                speed=speed,
                output_path=output_path
            ))

            if not response.success:
                return response

            segment_files.append(response.audio_path)

        # 合并音频
        merged_path = f"{output_dir or self.config.output_dir}/merged_{int(time.time())}.mp3"
        merge_success = await self._merge_audio_files(segment_files, merged_path)

        if not merge_success:
            return TTSResponse(
                success=False,
                error="Failed to merge audio files",
                provider=self.config.provider,
                processing_time=time.time() - start_time
            )

        # 清理分段文件
        for f in segment_files:
            try:
                import os
                os.remove(f)
            except Exception:
                pass

        return TTSResponse(
            success=True,
            audio_path=merged_path,
            duration=sum(len(s) for s in segments) / 300 * 3.0,  # 估算
            provider=self.config.provider,
            processing_time=time.time() - start_time
        )

    def _split_text(self, text: str, max_length: int = 300) -> List[str]:
        """按标点和长度分段"""
        import re

        # 按句子分隔
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

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

        return result if result else [text]

    async def _merge_audio_files(self, files: List[str], output_path: str) -> bool:
        """合并音频文件"""
        try:
            from src.services.ffmpeg_service import get_ffmpeg_service
            ffmpeg = get_ffmpeg_service()

            # 创建文件列表
            list_file = output_path + ".txt"
            with open(list_file, "w") as f:
                for file in files:
                    f.write(f"file '{file}'\n")

            # 使用FFmpeg合并
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                output_path
            ]

            import asyncio
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            # 删除临时文件
            try:
                import os
                os.remove(list_file)
            except Exception:
                pass

            return True

        except Exception as e:
            logger.error(f"Merge audio failed: {e}")
            return False

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

    async def list_cloned_voices(self) -> List[Dict]:
        """列出已克隆的声音"""
        try:
            client = await self._get_clone_client()
            return await client.list_cloned_voices()
        except Exception as e:
            logger.error(f"List cloned voices failed: {e}")
            return []

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

        # Voicebox 本地音色
        if self.config.provider == "voicebox":
            voices.append(VoiceConfig(
                voice_id="default",
                name="默认音色",
                description="Voicebox默认音色"
            ))
            # 可以添加更多Voicebox音色

        # 添加克隆的声音
        for name, vid in self._cloned_voices.items():
            voices.append(VoiceConfig(
                voice_id=vid,
                name=f"[克隆] {name}",
                description="克隆音色"
            ))

        return voices

    def get_voice_presets(self, category: Optional[str] = None) -> List[VoicePreset]:
        """获取音色预设"""
        return self.emotion_mapper.get_voice_presets(emotion=EmotionType.CALM if category else None)

    async def close(self):
        """关闭连接"""
        if self._tts_client:
            await self._tts_client.close()
            self._tts_client = None

        if self._clone_client:
            await self._clone_client.close()
            self._clone_client = None

        if self._voicebox_client:
            await self._voicebox_client.close()
            self._voicebox_client = None


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


async def synthesize_long_text(
    text: str,
    voice: str = "xiaomo",
    speed: float = 1.0,
    config: Optional[TTSConfig] = None
) -> TTSResponse:
    """便捷的长文本合成函数"""
    if config is None:
        config = TTSConfig()

    router = TTSRouter(config)

    try:
        return await router.synthesize_long_text(text, voice, speed)
    finally:
        await router.close()