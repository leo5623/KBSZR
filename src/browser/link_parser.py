"""链接解析器 - 从各平台链接提取文案"""
import asyncio
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from loguru import logger

from src.browser.playwright_service import PlaywrightService, BrowserResult


@dataclass
class ParsedContent:
    """解析结果"""
    success: bool
    text: str = ""  # 文案文本
    title: str = ""  # 标题
    tags: list = None  # 话题标签
    author: str = ""  # 作者
    error: str = ""
    platform: str = ""


class LinkParser:
    """
    链接解析器

    支持平台：
    - 抖音/抖音极速版
    - 快手
    - 小红书
    - 视频号
    - B站
    """

    def __init__(self, playwright_service: Optional[PlaywrightService] = None):
        self.playwright = playwright_service or PlaywrightService()
        self._parsers = {
            "douyin": self._parse_douyin,
            "kuaishou": self._parse_kuaishou,
            "xiaohongshu": self._parse_xiaohongshu,
            "wechat": self._parse_wechat,
            "bilibili": self._parse_bilibili,
        }
        logger.info("LinkParser initialized")

    async def parse(self, url: str) -> ParsedContent:
        """
        解析链接

        Args:
            url: 平台链接（支持纯URL或分享文本格式）

        Returns:
            ParsedContent
        """
        # 从分享文本中提取URL
        url = self._extract_url(url)

        # 检测平台
        platform = self._detect_platform(url)

        if platform is None:
            return ParsedContent(
                success=False,
                error=f"Unsupported platform or invalid URL: {url}"
            )

        # 调用对应解析器
        parser = self._parsers.get(platform)
        if parser:
            return await parser(url)
        else:
            return ParsedContent(
                success=False,
                error=f"Parser not implemented for: {platform}"
            )

    def _extract_url(self, text: str) -> str:
        """从分享文本中提取URL"""
        # 匹配各种平台的URL模式
        patterns = [
            r'https?://v\.douyin\.com/[^\s一-龥]+',  # 抖音
            r'https?://www\.kuaishou\.com/[^\s一-龥]+',  # 快手
            r'https?://xhslink\.com/[^\s一-龥]+',  # 小红书
            r'https?://b23\.tv/[^\s一-龥]+',  # B站短链接
            r'https?://[^\s一-龥]+\.(?:douyin|kuaishou|xhslink|bilibili)\.com[^\s一-龥]*',  # 其他
            r'https?://channels\.weixin\.qq\.com[^\s一-龥]+',  # 视频号
        ]

        for pattern in patterns:
            import re
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        # 如果没有找到URL模式，返回原文本
        return text

    def _detect_platform(self, url: str) -> Optional[str]:
        """检测平台"""
        url_lower = url.lower()

        if "douyin.com" in url_lower or "v.douyin.com" in url_lower:
            return "douyin"
        elif "kuaishou.com" in url_lower:
            return "kuaishou"
        elif "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
            return "xiaohongshu"
        elif "channels.weixin.qq.com" in url_lower:
            return "wechat"
        elif "bilibili.com" in url_lower or "b23.tv" in url_lower:
            return "bilibili"

        return None

    async def _parse_douyin(self, url: str) -> ParsedContent:
        """解析抖音链接"""
        try:
            result = await self.playwright.navigate(url, timeout=60000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="douyin")

            content = result.content

            # 尝试多种正则提取文案
            patterns = [
                r'"text":"([^"]+)"',
                r'"description":"([^"]+)"',
                r'<div[^>]*class="[^"]*desc[^"]*"[^>]*>([^<]+)</div>',
                r'<p[^>]*class="[^"]*text[^"]*"[^>]*>([^<]+)</p>',
            ]

            text = ""
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    text = match.group(1)
                    break

            tags = re.findall(r'#([^#\s]+)', content)
            text = text.replace("\\n", "\n").replace("\\", "") if text else ""

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，抖音需要登录态才能获取内容",
                    platform="douyin"
                )

            return ParsedContent(
                success=True,
                text=text,
                tags=tags[:10],
                platform="douyin"
            )

        except Exception as e:
            logger.error(f"Parse douyin failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="douyin")

    async def _parse_kuaishou(self, url: str) -> ParsedContent:
        """解析快手链接"""
        try:
            result = await self.playwright.navigate(url, timeout=60000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="kuaishou")

            content = result.content

            # 快手文案提取
            text_match = re.search(r'"caption":"([^"]+)"', content)
            text = text_match.group(1) if text_match else ""

            tags = re.findall(r'#([^#\s]+)', content)

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="kuaishou"
                )

            return ParsedContent(
                success=True,
                text=text,
                tags=tags[:10],
                platform="kuaishou"
            )

        except Exception as e:
            logger.error(f"Parse kuaishou failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="kuaishou")

    async def _parse_xiaohongshu(self, url: str) -> ParsedContent:
        """解析小红书链接"""
        try:
            result = await self.playwright.navigate(url, timeout=60000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="xiaohongshu")

            content = result.content

            # 小红书文案提取
            text_match = re.search(r'"desc":"([^"]+)"', content)
            text = text_match.group(1) if text_match else ""

            tags = re.findall(r'#"([^"]+)"', content)

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="xiaohongshu"
                )

            return ParsedContent(
                success=True,
                text=text,
                tags=tags[:10],
                platform="xiaohongshu"
            )

        except Exception as e:
            logger.error(f"Parse xiaohongshu failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="xiaohongshu")

    async def _parse_wechat(self, url: str) -> ParsedContent:
        """解析视频号链接"""
        try:
            result = await self.playwright.navigate(url, timeout=60000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="wechat")

            content = result.content

            # 视频号文案提取
            text_match = re.search(r'"description":"([^"]+)"', content)
            text = text_match.group(1) if text_match else ""

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="wechat"
                )

            return ParsedContent(
                success=True,
                text=text,
                platform="wechat"
            )

        except Exception as e:
            logger.error(f"Parse wechat failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="wechat")

    async def _parse_bilibili(self, url: str) -> ParsedContent:
        """解析B站链接"""
        try:
            result = await self.playwright.navigate(url, timeout=60000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="bilibili")

            content = result.content

            # B站标题和描述提取
            title_match = re.search(r'"title":"([^"]+)"', content)
            title = title_match.group(1) if title_match else ""

            desc_match = re.search(r'"description":"([^"]+)"', content)
            text = desc_match.group(1) if desc_match else ""

            # B站标签
            tags = re.findall(r'"tag_name":"([^"]+)"', content)

            if not text and not title:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="bilibili"
                )

            return ParsedContent(
                success=True,
                text=f"{title}\n{text}",
                title=title,
                tags=tags[:10],
                platform="bilibili"
            )

        except Exception as e:
            logger.error(f"Parse bilibili failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="bilibili")

    async def close(self):
        """关闭"""
        await self.playwright.close()


# 便捷函数
async def parse_link(url: str) -> ParsedContent:
    """解析链接"""
    parser = LinkParser()
    try:
        return await parser.parse(url)
    finally:
        await parser.close()