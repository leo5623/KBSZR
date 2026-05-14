"""TTS路由测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.business.tts.router import (
    TTSRouter, TTSConfig, TTSRequest, TTSResponse,
    BatchTTSRequest, BatchTTSResponse, AudioFormat, TTSMode
)
from src.business.tts.aliyun_client import AliyunTTS


class TestTTSConfig:
    """TTSConfig测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = TTSConfig()

        assert config.mode == TTSMode.CLOUD
        assert config.provider == "aliyun"
        assert config.default_voice == "xiaomo"
        assert config.default_speed == 1.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = TTSConfig(
            provider="volcengine",
            aliyun_api_key="test-key",
            default_voice="xiaogang"
        )

        assert config.provider == "volcengine"
        assert config.aliyun_api_key == "test-key"
        assert config.default_voice == "xiaogang"


class TestTTSRequest:
    """TTSRequest测试"""

    def test_tts_request_defaults(self):
        """测试TTS请求默认值"""
        request = TTSRequest(text="测试文本")

        assert request.text == "测试文本"
        assert request.voice == "xiaomo"
        assert request.speed == 1.0
        assert request.pitch == 0.0
        assert request.emotion is None

    def test_tts_request_with_emotion(self):
        """测试带情感的TTS请求"""
        request = TTSRequest(
            text="测试文本",
            voice="xiaoyun",
            speed=1.2,
            emotion="excited"
        )

        assert request.emotion == "excited"
        assert request.speed == 1.2


class TestTTSResponse:
    """TTSResponse测试"""

    def test_tts_response_success(self):
        """测试成功响应"""
        response = TTSResponse(
            success=True,
            audio_path="/path/to/audio.mp3",
            duration=10.5,
            provider="aliyun",
            processing_time=1.2
        )

        assert response.success is True
        assert response.audio_path == "/path/to/audio.mp3"
        assert response.duration == 10.5

    def test_tts_response_failure(self):
        """测试失败响应"""
        response = TTSResponse(
            success=False,
            error="合成失败",
            provider="aliyun"
        )

        assert response.success is False
        assert response.error == "合成失败"


class TestBatchTTSResponse:
    """BatchTTSResponse测试"""

    def test_batch_tts_response(self):
        """测试批量TTS响应"""
        responses = [
            TTSResponse(success=True, duration=5.0),
            TTSResponse(success=True, duration=6.0),
            TTSResponse(success=True, duration=7.0)
        ]

        batch = BatchTTSResponse(
            success=True,
            results=responses,
            total_duration=18.0,
            total_time=3.5
        )

        assert batch.success is True
        assert len(batch.results) == 3
        assert batch.total_duration == 18.0


class TestTTSRouter:
    """TTSRouter测试"""

    def test_init(self):
        """测试初始化"""
        config = TTSConfig(provider="aliyun", aliyun_api_key="test-key")
        router = TTSRouter(config)

        assert router.config.provider == "aliyun"
        assert router.emotion_mapper is not None
        assert router.voice_library is not None

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        config = TTSConfig(provider="aliyun", aliyun_api_key="test-key")
        router = TTSRouter(config)

        with patch.object(router, '_get_tts_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.health_check = AsyncMock(return_value=True)
            mock_get_client.return_value = mock_client

            result = await router.health_check()

            assert "tts" in result
            assert "clone" in result

    def test_get_voice_id_cloned(self):
        """测试获取克隆音色的voice_id"""
        config = TTSConfig(provider="aliyun")
        router = TTSRouter(config)
        router._cloned_voices["我的声音"] = "cloned_voice_123"

        voice_id = router._get_voice_id("我的声音")
        assert voice_id == "cloned_voice_123"

    def test_get_voice_id_preset(self):
        """测试获取预置音色的voice_id"""
        config = TTSConfig(provider="aliyun")
        router = TTSRouter(config)

        voice_id = router._get_voice_id("小mo亲")
        assert voice_id == "xiaomo"

    def test_split_text(self):
        """测试文本分段"""
        config = TTSConfig(provider="aliyun")
        router = TTSRouter(config)

        text = "第一句。第二句。第三句。"
        segments = router._split_text(text, max_length=10)

        assert len(segments) > 1


class TestAudioFormat:
    """AudioFormat测试"""

    def test_audio_format_values(self):
        """测试音频格式枚举"""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.OGG.value == "ogg"
        assert AudioFormat.PCM.value == "pcm"


class TestTTSRouterClone:
    """TTSRouter克隆功能测试"""

    @pytest.mark.asyncio
    async def test_clone_voice(self):
        """测试克隆声音"""
        config = TTSConfig(provider="aliyun", aliyun_api_key="test-key")
        router = TTSRouter(config)

        with patch.object(router, '_get_clone_client') as mock_get_client:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.voice_id = "cloned_123"
            mock_result.voice_name = "测试音色"
            mock_client.clone = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_client

            result = await router.clone_voice(
                audio_samples=["/path/to/sample.mp3"],
                voice_name="测试音色"
            )

            assert result.success is True
            assert "测试音色" in router._cloned_voices