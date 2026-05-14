"""分发机器人测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.browser.platform_bots.distributor import (
    DistributorBot, DistributionResult, Platform,
    PublishRequest, PlatformConfig, BaseDistributor
)


class TestDistributionResult:
    """DistributionResult数据类测试"""

    def test_distribution_result_success(self):
        """测试成功结果"""
        result = DistributionResult(
            success=True,
            platform="douyin",
            url="https://www.douyin.com/video/123",
            video_id="123",
            duration=15.5
        )

        assert result.success is True
        assert result.platform == "douyin"
        assert result.url == "https://www.douyin.com/video/123"
        assert result.video_id == "123"

    def test_distribution_result_failure(self):
        """测试失败结果"""
        result = DistributionResult(
            success=False,
            platform="douyin",
            error="Upload timeout"
        )

        assert result.success is False
        assert result.error == "Upload timeout"


class TestPlatform:
    """Platform枚举测试"""

    def test_platform_values(self):
        """测试平台枚举值"""
        assert Platform.DOUYIN.value == "douyin"
        assert Platform.KUAISHOU.value == "kuaishou"
        assert Platform.XIAOHONGSHU.value == "xiaohongshu"
        assert Platform.WEIXIN.value == "weixin"
        assert Platform.BILIBILI.value == "bilibili"


class TestPublishRequest:
    """PublishRequest数据类测试"""

    def test_publish_request_creation(self):
        """测试创建发布请求"""
        request = PublishRequest(
            video_path="/path/to/video.mp4",
            title="测试标题",
            description="测试描述",
            tags=["tag1", "tag2"],
            visibility="public"
        )

        assert request.video_path == "/path/to/video.mp4"
        assert request.title == "测试标题"
        assert request.tags == ["tag1", "tag2"]
        assert request.visibility == "public"

    def test_publish_request_defaults(self):
        """测试发布请求默认值"""
        request = PublishRequest(
            video_path="/path/to/video.mp4",
            title="标题",
            description="描述"
        )

        assert request.tags == []
        assert request.cover_path is None
        assert request.visibility == "public"


class TestDistributorBot:
    """DistributorBot测试"""

    def test_init(self):
        """测试初始化"""
        bot = DistributorBot()

        assert bot._distributors == {}
        assert bot._platform_configs == {}

    def test_configure_platform(self):
        """测试配置平台"""
        bot = DistributorBot()
        cookies = [{"name": "session", "value": "abc123"}]

        bot.configure_platform("douyin", cookies)

        assert "douyin" in bot._platform_configs

    def test_configure_multiple_platforms(self):
        """测试配置多个平台"""
        bot = DistributorBot()

        bot.configure_platform("douyin", [{"name": "dy", "value": "1"}])
        bot.configure_platform("kuaishou", [{"name": "ks", "value": "2"}])
        bot.configure_platform("xiaohongshu", [{"name": "xhs", "value": "3"}])

        assert len(bot._platform_configs) == 3
        assert "douyin" in bot._platform_configs
        assert "kuaishou" in bot._platform_configs
        assert "xiaohongshu" in bot._platform_configs

    @pytest.mark.asyncio
    async def test_distribute_without_config(self):
        """测试未配置平台时的分发"""
        bot = DistributorBot()

        results = await bot.distribute(
            video_path="/path/to/video.mp4",
            title="标题",
            description="描述",
            tags=["tag1"],
            platforms=["douyin"]
        )

        assert "douyin" in results
        assert results["douyin"].success is False
        assert "not configured" in results["douyin"].error.lower()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        bot = DistributorBot()
        bot.configure_platform("douyin", [{"name": "test", "value": "123"}])

        health = await bot.health_check()

        assert "douyin" in health
        assert health["douyin"] is True


class TestBaseDistributorSelectors:
    """BaseDistributor选择器测试"""

    def test_douyin_selectors(self):
        """测试抖音选择器"""
        selectors = BaseDistributor.SELECTORS.get("douyin")

        assert selectors is not None
        assert "upload_input" in selectors
        assert "title_input" in selectors
        assert "publish_button" in selectors

    def test_all_platforms_have_selectors(self):
        """测试所有平台都有选择器"""
        platforms = ["douyin", "kuaishou", "xiaohongshu", "weixin", "bilibili"]

        for platform in platforms:
            selectors = BaseDistributor.SELECTORS.get(platform)
            assert selectors is not None, f"Missing selectors for {platform}"
            assert "upload_input" in selectors
            assert "title_input" in selectors


# 便捷函数测试
class TestDistributeToPlatforms:
    """distribute_to_platforms便捷函数测试"""

    @pytest.mark.asyncio
    async def test_distribute_with_cookies(self):
        """测试带cookies的分发"""
        from src.browser.platform_bots.distributor import distribute_to_platforms

        with patch('src.browser.platform_bots.distributor.DistributorBot') as MockBot:
            mock_bot_instance = MagicMock()
            MockBot.return_value = mock_bot_instance

            mock_bot_instance.distribute = AsyncMock(return_value={
                "douyin": DistributionResult(success=True, platform="douyin", url="")
            })

            results = await distribute_to_platforms(
                video_path="/path/to/video.mp4",
                title="标题",
                description="描述",
                tags=["tag1"],
                platforms=["douyin"],
                cookies={"douyin": [{"name": "test", "value": "123"}]}
            )

            assert "douyin" in results
            mock_bot_instance.configure_platform.assert_called_once()


class TestSaveDistributionResult:
    """save_distribution_result测试"""

    def test_save_result_to_file(self, tmp_path):
        """测试保存结果到文件"""
        from src.browser.platform_bots.distributor import save_distribution_result

        results = {
            "douyin": DistributionResult(
                success=True,
                platform="douyin",
                url="https://douyin.com/video/123"
            ),
            "kuaishou": DistributionResult(
                success=False,
                platform="kuaishou",
                error="Upload failed"
            )
        }

        output_path = tmp_path / "distribution_results.json"
        save_distribution_result(results, str(output_path))

        assert output_path.exists()

        # 验证内容
        import json
        with open(output_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert len(saved_data) == 2

        douyin_result = next(r for r in saved_data if r["platform"] == "douyin")
        assert douyin_result["success"] is True

        kuaishou_result = next(r for r in saved_data if r["platform"] == "kuaishou")
        assert kuaishou_result["success"] is False