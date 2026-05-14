"""FFmpeg服务模块测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.services.ffmpeg_service import FFmpegService, FFmpegResult


class TestFFmpegResult:
    """FFmpegResult数据类测试"""

    def test_ffmpeg_result_success(self):
        """测试成功结果"""
        result = FFmpegResult(
            success=True,
            output_path="/path/to/output.mp4",
            duration=10.5
        )

        assert result.success is True
        assert result.output_path == "/path/to/output.mp4"
        assert result.duration == 10.5
        assert result.error == ""

    def test_ffmpeg_result_failure(self):
        """测试失败结果"""
        result = FFmpegResult(
            success=False,
            error="FFmpeg error"
        )

        assert result.success is False
        assert result.error == "FFmpeg error"


class TestFFmpegService:
    """FFmpegService测试"""

    def test_init_default_paths(self):
        """测试默认路径初始化"""
        service = FFmpegService()

        assert service.ffmpeg_path == "ffmpeg"
        assert service.ffprobe_path == "ffprobe"

    def test_init_custom_paths(self):
        """测试自定义路径"""
        service = FFmpegService(
            ffmpeg_path="/usr/local/bin/ffmpeg",
            ffprobe_path="/usr/local/bin/ffprobe"
        )

        assert service.ffmpeg_path == "/usr/local/bin/ffmpeg"
        assert service.ffprobe_path == "/usr/local/bin/ffprobe"

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """测试健康检查成功"""
        service = FFmpegService()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ffmpeg version 4.0"

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.return_value = mock_result

            result = await service.health_check()
            assert result["available"] is True
            assert "version" in result

    @pytest.mark.asyncio
    async def test_health_check_not_found(self):
        """测试健康检查失败（FFmpeg未找到）"""
        service = FFmpegService()

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.side_effect = FileNotFoundError()

            result = await service.health_check()
            assert result["available"] is False

    @pytest.mark.asyncio
    async def test_get_duration_success(self):
        """测试获取时长成功"""
        service = FFmpegService()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "10.5\n"

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = mock_result

            duration = await service.get_duration("/path/to/video.mp4")
            assert duration == 10.5

    @pytest.mark.asyncio
    async def test_merge_audio_video_success(self, tmp_path):
        """测试音视频合并成功"""
        service = FFmpegService()

        video_path = tmp_path / "video.mp4"
        audio_path = tmp_path / "audio.aac"
        output_path = tmp_path / "output.mp4"

        video_path.write_text("video content")
        audio_path.write_text("audio content")
        output_path.write_text("output content")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.communicate = AsyncMock(return_value=(b"", b""))

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.return_value = mock_result

            with patch.object(service, 'get_duration', return_value=10.0):
                result = await service.merge_audio_video(
                    str(video_path),
                    str(audio_path),
                    str(output_path)
                )

                assert result.success is True
                assert result.duration == 10.0

    @pytest.mark.asyncio
    async def test_convert_ratio_9_16(self, tmp_path):
        """测试9:16竖屏转换"""
        service = FFmpegService()

        input_path = tmp_path / "input.mp4"
        output_path = tmp_path / "output.mp4"

        input_path.write_text("video content")
        output_path.write_text("output content")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.communicate = AsyncMock(return_value=(b"", b""))

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.return_value = mock_result

            with patch.object(service, 'get_duration', return_value=15.0):
                result = await service.convert_ratio(
                    str(input_path),
                    str(output_path),
                    "9:16"
                )

                assert result.success is True

    @pytest.mark.asyncio
    async def test_adjust_volume_success(self, tmp_path):
        """测试音量调整"""
        service = FFmpegService()

        input_path = tmp_path / "audio.mp3"
        output_path = tmp_path / "output.mp3"

        input_path.write_text("audio content")
        output_path.write_text("output content")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.communicate = AsyncMock(return_value=(b"", b""))

        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.return_value = mock_result

            result = await service.adjust_volume(
                str(input_path),
                str(output_path),
                volume_db=-3.0
            )

            assert result.success is True