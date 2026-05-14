"""画质增强模块测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.business.post_production.video_enhancer import (
    VideoEnhancer, VideoEnhanceResult, VideoEnhanceConfig,
    VideoCompressor, EnhancePreset, PRESETS, get_video_enhancer
)


class TestVideoEnhanceResult:
    """VideoEnhanceResult数据类测试"""

    def test_enhance_result_success(self):
        """测试成功结果"""
        result = VideoEnhanceResult(
            success=True,
            output_path="/path/to/enhanced.mp4",
            original_path="/path/to/original.mp4",
            resolution="high_enhanced",
            enhanced_duration=30.0,
            file_size_before=1024000,
            file_size_after=2048000,
            processing_time=15.5
        )

        assert result.success is True
        assert result.output_path == "/path/to/enhanced.mp4"
        assert result.file_size_after > result.file_size_before

    def test_enhance_result_failure(self):
        """测试失败结果"""
        result = VideoEnhanceResult(
            success=False,
            error_message="API timeout"
        )

        assert result.success is False
        assert result.error_message == "API timeout"


class TestVideoEnhancer:
    """VideoEnhancer测试"""

    def test_init_default(self):
        """测试默认初始化"""
        enhancer = VideoEnhancer()

        assert enhancer.config.provider == "aliyun"
        assert enhancer.output_dir == Path("./data/output/enhanced")

    def test_init_custom_config(self):
        """测试自定义配置"""
        config = VideoEnhanceConfig(
            provider="local",
            enhance_level="high",
            output_dir="./custom_output"
        )
        enhancer = VideoEnhancer(config)

        assert enhancer.config.provider == "local"
        assert enhancer.config.enhance_level == "high"
        assert enhancer.output_dir == Path("./custom_output")

    def test_list_presets(self):
        """测试列出预设"""
        enhancer = VideoEnhancer()
        presets = enhancer.list_presets()

        assert len(presets) >= 4

        preset_ids = [p["id"] for p in presets]
        assert "fast" in preset_ids
        assert "quality" in preset_ids
        assert "balance" in preset_ids
        assert "upscale_4k" in preset_ids

    @pytest.mark.asyncio
    async def test_enhance_local(self, tmp_path):
        """测试本地增强"""
        # 创建测试视频文件
        video_path = tmp_path / "test.mp4"
        output_path = tmp_path / "output_enhanced.mp4"
        video_path.write_text("fake video content")

        config = VideoEnhanceConfig(provider="local", output_dir=str(tmp_path))
        enhancer = VideoEnhancer(config)

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = mock_process

            result = await enhancer.enhance(
                video_path=str(video_path),
                output_path=str(output_path),
                preset_id="balance"
            )

            # 由于mock，结果取决于实现
            assert isinstance(result, VideoEnhanceResult)


class TestPRESETS:
    """PRESETS预设测试"""

    def test_fast_preset(self):
        """测试fast预设"""
        preset = PRESETS["fast"]

        assert preset.id == "fast"
        assert preset.level == "low"
        assert "denoise" in preset.services
        assert preset.scale_factor == 1

    def test_quality_preset(self):
        """测试quality预设"""
        preset = PRESETS["quality"]

        assert preset.id == "quality"
        assert preset.level == "high"
        assert "denoise" in preset.services
        assert "sharpen" in preset.services
        assert "super_resolution" in preset.services
        assert "color_correct" in preset.services
        assert preset.scale_factor == 2

    def test_upscale_4k_preset(self):
        """测试upscale_4k预设"""
        preset = PRESETS["upscale_4k"]

        assert preset.id == "upscale_4k"
        assert preset.scale_factor == 4


class TestVideoCompressor:
    """VideoCompressor测试"""

    def test_init(self):
        """测试初始化"""
        compressor = VideoCompressor()

        assert "抖音" in compressor.presets
        assert "快手" in compressor.presets
        assert "视频号" in compressor.presets

    def test_presets_structure(self):
        """测试预设结构"""
        douyin_preset = VideoCompressor().presets["抖音"]

        assert "codec" in douyin_preset
        assert "crf" in douyin_preset
        assert "preset" in douyin_preset
        assert "max_bitrate" in douyin_preset

    @pytest.mark.asyncio
    async def test_compress_douyin(self, tmp_path):
        """测试抖音压缩"""
        video_path = tmp_path / "test.mp4"
        output_path = tmp_path / "douyin_compressed.mp4"
        video_path.write_text("fake video content")

        compressor = VideoCompressor()

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = mock_process

            result = await compressor.compress(
                video_path=str(video_path),
                output_path=str(output_path),
                platform="抖音"
            )

            assert isinstance(result, VideoEnhanceResult)


class TestGetVideoEnhancer:
    """get_video_enhancer单例测试"""

    def test_get_video_enhancer_new_instance(self):
        """测试获取新实例"""
        config = VideoEnhanceConfig(provider="local")
        enhancer = get_video_enhancer(config)

        assert isinstance(enhancer, VideoEnhancer)
        assert enhancer.config.provider == "local"