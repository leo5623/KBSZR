"""链接解析器测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.browser.link_parser import (
    LinkParser, ParsedContent, ParseOptions, Platform,
    parse_link, parse_links_batch, save_parsed_content
)


class TestParsedContent:
    """ParsedContent数据类测试"""

    def test_parsed_content_success(self):
        """测试成功解析结果"""
        content = ParsedContent(
            success=True,
            text="测试文案内容",
            title="测试标题",
            tags=["tag1", "tag2"],
            author="作者名",
            platform="douyin",
            url="https://v.douyin.com/abc"
        )

        assert content.success is True
        assert content.text == "测试文案内容"
        assert content.title == "测试标题"
        assert len(content.tags) == 2

    def test_parsed_content_failure(self):
        """测试失败解析结果"""
        content = ParsedContent(
            success=False,
            error="无法提取文案",
            platform="douyin"
        )

        assert content.success is False
        assert content.error == "无法提取文案"


class TestParseOptions:
    """ParseOptions测试"""

    def test_default_options(self):
        """测试默认选项"""
        options = ParseOptions()

        assert options.timeout == 60
        assert options.retry_count == 2
        assert options.extract_metadata is True
        assert options.cookies == []

    def test_custom_options(self):
        """测试自定义选项"""
        options = ParseOptions(
            timeout=120,
            retry_count=3,
            cookies=[{"name": "test", "value": "123"}]
        )

        assert options.timeout == 120
        assert options.retry_count == 3
        assert len(options.cookies) == 1


class TestPlatform:
    """Platform枚举测试"""

    def test_platform_values(self):
        """测试平台枚举"""
        assert Platform.DOUYIN.value == "douyin"
        assert Platform.KUAISHOU.value == "kuaishou"
        assert Platform.XIAOHONGSHU.value == "xiaohongshu"
        assert Platform.BILIBILI.value == "bilibili"

    def test_all_platforms(self):
        """测试所有平台"""
        platforms = list(Platform)
        assert len(platforms) >= 8


class TestLinkParser:
    """LinkParser测试"""

    def test_init(self):
        """测试初始化"""
        parser = LinkParser()

        assert parser.playwright is not None
        assert len(parser._parsers) >= 8

    def test_extract_url_douyin(self):
        """测试抖音URL提取"""
        parser = LinkParser()

        text = "复制这段内容，打开抖音App查看【视频链接】https://v.douyin.com/abc123 和更多内容"
        url = parser._extract_url(text)

        assert "v.douyin.com" in url
        assert url == "https://v.douyin.com/abc123"

    def test_extract_url_xiaohongshu(self):
        """测试小红书URL提取"""
        parser = LinkParser()

        text = "小红书链接：https://xhslink.com/abc 复制这段内容"
        url = parser._extract_url(text)

        assert "xhslink.com" in url

    def test_extract_url_no_match(self):
        """测试无匹配"""
        parser = LinkParser()

        text = "这是一段普通文本，没有链接"
        url = parser._extract_url(text)

        assert url == text

    def test_detect_platform_douyin(self):
        """测试平台检测-抖音"""
        parser = LinkParser()

        assert parser._detect_platform("https://v.douyin.com/abc") == "douyin"
        assert parser._detect_platform("https://www.douyin.com/video/123") == "douyin"

    def test_detect_platform_kuaishou(self):
        """测试平台检测-快手"""
        parser = LinkParser()

        assert parser._detect_platform("https://www.kuaishou.com/video/123") == "kuaishou"

    def test_detect_platform_xiaohongshu(self):
        """测试平台检测-小红书"""
        parser = LinkParser()

        assert parser._detect_platform("https://xhslink.com/abc") == "xiaohongshu"
        assert parser._detect_platform("https://www.xiaohongshu.com/discovery/item/123") == "xiaohongshu"

    def test_detect_platform_bilibili(self):
        """测试平台检测-B站"""
        parser = LinkParser()

        assert parser._detect_platform("https://b23.tv/abc") == "bilibili"
        assert parser._detect_platform("https://bilibili.com/video/123") == "bilibili"

    def test_detect_platform_unsupported(self):
        """测试不支持的平台"""
        parser = LinkParser()

        assert parser._detect_platform("https://example.com/video") is None

    def test_list_supported_platforms(self):
        """测试列出支持的平台"""
        parser = LinkParser()
        platforms = parser.list_supported_platforms()

        assert len(platforms) >= 8
        platform_ids = [p["id"] for p in platforms]
        assert "douyin" in platform_ids
        assert "xiaohongshu" in platform_ids

    def test_get_platform_name(self):
        """测试获取平台名称"""
        parser = LinkParser()

        assert parser._get_platform_name("douyin") == "抖音"
        assert parser._get_platform_name("xiaohongshu") == "小红书"
        assert parser._get_platform_name("bilibili") == "B站"


class TestParseLink:
    """parse_link便捷函数测试"""

    @pytest.mark.asyncio
    async def test_parse_link_with_mock(self):
        """测试parse_link函数（带mock）"""
        with patch('src.browser.link_parser.LinkParser') as MockParser:
            mock_instance = MagicMock()
            MockParser.return_value = mock_instance

            mock_result = ParsedContent(success=True, text="测试", platform="douyin")
            mock_instance.parse = AsyncMock(return_value=mock_result)
            mock_instance.close = AsyncMock()

            result = await parse_link("https://v.douyin.com/test")

            assert result.success is True
            mock_instance.close.assert_called_once()


class TestSaveParsedContent:
    """save_parsed_content测试"""

    def test_save_to_file(self, tmp_path):
        """测试保存解析结果"""
        results = [
            ParsedContent(success=True, text="文案1", platform="douyin"),
            ParsedContent(success=True, text="文案2", platform="xiaohongshu")
        ]

        output_path = tmp_path / "parsed_content.json"
        save_parsed_content(results, str(output_path))

        assert output_path.exists()

        import json
        with open(output_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert len(saved_data) == 2
        assert saved_data[0]["text"] == "文案1"
        assert saved_data[0]["platform"] == "douyin"