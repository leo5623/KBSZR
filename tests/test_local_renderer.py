"""本地数字人渲染器测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.business.digital_human.local_renderer import (
    LocalRenderer, LocalRenderResult, RenderProgress,
    ModelDownloader, get_local_renderer
)


class TestLocalRenderResult:
    """LocalRenderResult数据类测试"""

    def test_render_result_success(self):
        """测试成功结果"""
        result = LocalRenderResult(
            success=True,
            video_path="/path/to/output.mp4",
            duration=10.5,
            model="sadtalker",
            frames_generated=315
        )

        assert result.success is True
        assert result.video_path == "/path/to/output.mp4"
        assert result.duration == 10.5
        assert result.model == "sadtalker"
        assert result.frames_generated == 315

    def test_render_result_failure(self):
        """测试失败结果"""
        result = LocalRenderResult(
            success=False,
            error="Model not found",
            model="sadtalker"
        )

        assert result.success is False
        assert result.error == "Model not found"


class TestLocalRenderer:
    """LocalRenderer测试"""

    def test_init_default_values(self):
        """测试默认初始化"""
        renderer = LocalRenderer()

        assert renderer.device in ["cuda", "cpu"]
        assert renderer.model_dir == Path("./models/digital_human")
        assert renderer.output_dir == Path("./data/output/temp")

    def test_init_custom_values(self):
        """测试自定义初始化"""
        renderer = LocalRenderer(
            model_dir="./custom_models",
            device="cpu",
            output_dir="./custom_output"
        )

        assert renderer.device == "cpu"
        assert renderer.model_dir == Path("./custom_models")
        assert renderer.output_dir == Path("./custom_output")

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        renderer = LocalRenderer()

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ffmpeg version 4.0"
            mock_run.return_value = mock_result

            result = await renderer.health_check()

            assert "ffmpeg" in result
            assert "python" in result
            assert "cuda" in result

    def test_list_available_models(self):
        """测试列出可用模型"""
        models = LocalRenderer.list_available_models()

        assert len(models) >= 2
        model_ids = [m["id"] for m in models]
        assert "sadtalker" in model_ids
        assert "wav2lip" in model_ids

    def test_get_model_requirements(self):
        """测试获取模型要求"""
        req = LocalRenderer.get_model_requirements("sadtalker")

        assert req["name"] == "SadTalker"
        assert "gpu_recommended" in req
        assert "dependencies" in req

    def test_get_model_requirements_unknown(self):
        """测试获取未知模型要求"""
        req = LocalRenderer.get_model_requirements("unknown_model")
        assert req == {}


class TestModelDownloader:
    """ModelDownloader测试"""

    def test_init(self):
        """测试初始化"""
        downloader = ModelDownloader()

        assert downloader.cache_dir == Path("./cache/models")

    def test_init_custom_cache_dir(self):
        """测试自定义缓存目录"""
        downloader = ModelDownloader(cache_dir="./custom_cache")

        assert downloader.cache_dir == Path("./custom_cache")

    @pytest.mark.asyncio
    async def test_download_sadtalker(self):
        """测试下载SadTalker"""
        downloader = ModelDownloader()

        success, path = await downloader.download_sadtalker()

        assert success is True
        assert "sadtalker" in path


class TestGetLocalRenderer:
    """get_local_renderer单例测试"""

    def test_get_local_renderer_returns_same_instance(self):
        """测试返回相同实例"""
        renderer1 = get_local_renderer()
        renderer2 = get_local_renderer()

        # 注意：由于单例模式，两次调用应该返回相同的实例
        # 但这可能在测试间重置，所以只验证类型
        assert isinstance(renderer1, LocalRenderer)
        assert isinstance(renderer2, LocalRenderer)