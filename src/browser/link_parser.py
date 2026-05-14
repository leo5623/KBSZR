"""链接解析器 - 从各平台链接提取文案（增强版）"""
import asyncio
import re
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Pattern, Callable
from pathlib import Path
from enum import Enum
from loguru import logger

from src.browser.playwright_service import PlaywrightService, BrowserResult


# 编译后的正则表达式模式（提升性能）
_URL_PATTERNS: List[Pattern] = [
    re.compile(r'https?://v\.douyin\.com/[^\s一-龥]+', re.IGNORECASE),  # 抖音
    re.compile(r'https?://www\.kuaishou\.com/[^\s一-龥]+', re.IGNORECASE),  # 快手
    re.compile(r'https?://xhslink\.com/[^\s一-龥]+', re.IGNORECASE),  # 小红书
    re.compile(r'https?://b23\.tv/[^\s一-龥]+', re.IGNORECASE),  # B站短链接
    re.compile(r'https?://[^\s一-龥]+\.(?:douyin|kuaishou|xhslink|bilibili)\.com[^\s一-龥]*', re.IGNORECASE),  # 其他
    re.compile(r'https?://channels\.weixin\.qq\.com[^\s一-龥]+', re.IGNORECASE),  # 视频号
    re.compile(r'https?://weibo\.com/[^\s一-龥]+', re.IGNORECASE),  # 微博
    re.compile(r'https?://www\.zhihu\.com/[^\s一-龥]+', re.IGNORECASE),  # 知乎
    re.compile(r'https?://[^\s]+\.(?:ixigua\.com)\.com[^\s一-龥]*', re.IGNORECASE),  # 西瓜视频
]


class Platform(Enum):
    """支持的平台"""
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    XIAOHONGSHU = "xiaohongshu"
    WEIXIN = "weixin"
    BILIBILI = "bilibili"
    WEIBO = "weibo"
    ZHIHU = "zhihu"
    XIGUA = "xigua"


@dataclass
class ParsedContent:
    """解析结果"""
    success: bool
    text: str = ""  # 文案文本
    title: str = ""  # 标题
    tags: list = field(default_factory=list)  # 话题标签
    author: str = ""  # 作者
    error: str = ""
    platform: str = ""
    url: str = ""  # 原始URL
    timestamp: str = ""  # 发布时间
    likes: int = 0  # 点赞数
    favorites: int = 0  # 收藏数
    shares: int = 0  # 分享数
    metadata: Dict[str, Any] = field(default_factory=dict)  # 其他元数据


@dataclass
class ParseOptions:
    """解析选项"""
    timeout: int = 60  # 超时时间（秒）
    retry_count: int = 2  # 重试次数
    retry_delay: float = 3.0  # 重试间隔（秒）
    extract_metadata: bool = True  # 是否提取元数据
    cookies: List[Dict] = field(default_factory=list)  # 登录cookies
    headers: Dict[str, str] = field(default_factory=dict)  # 自定义headers


class LinkParser:
    """
    链接解析器（增强版）

    支持平台：
    - 抖音/抖音极速版
    - 快手
    - 小红书
    - 视频号
    - B站
    - 微博
    - 知乎
    - 西瓜视频
    """

    # 各平台的内容提取模式
    CONTENT_PATTERNS = {
        "douyin": {
            "text": [
                r'"text":"([^"]+)"',
                r'"description":"([^"]+)"',
                r'data-render="true"[^>]*>([^<]+)</p>',
            ],
            "title": [
                r'"title":"([^"]+)"',
            ],
            "author": [
                r'"nickname":"([^"]+)"',
                r'"author":"([^"]+)"',
            ],
            "tags": r'#([^#\s]+)',
        },
        "kuaishou": {
            "text": r'"caption":"([^"]+)"',
            "title": r'"videoCaption":"([^"]+)"',
            "author": r'"authorName":"([^"]+)"',
            "tags": r'#([^#\s]+)',
        },
        "xiaohongshu": {
            "text": r'"desc":"([^"]+)"',
            "title": r'"title":"([^"]+)"',
            "author": r'"nickname":"([^"]+)"',
            "tags": r'#"([^"]+)"',
        },
        "wechat": {
            "text": r'"description":"([^"]+)"',
            "title": r'"title":"([^"]+)"',
            "author": r'"author":"([^"]+)"',
        },
        "bilibili": {
            "text": r'"description":"([^"]+)"',
            "title": r'"title":"([^"]+)"',
            "author": r'"author":"([^"]+)"',
            "tags": r'"tag_name":"([^"]+)"',
        },
        "weibo": {
            "text": r'"text":"([^"]+)"',
            "title": r'"page_title":"([^"]+)"',
            "author": r'"screen_name":"([^"]+)"',
            "tags": r'#([^#\s]+)',
        },
        "zhihu": {
            "text": r'"content":"([^"]+)"',
            "title": r'"title":"([^"]+)"',
            "author": r'"author":"([^"]+)"',
        },
        "xigua": {
            "text": r'"video_description":"([^"]+)"',
            "title": r'"video_title":"([^"]+)"',
            "author": r'"author_name":"([^"]+)"',
            "tags": r'#([^#\s]+)',
        }
    }

    def __init__(
        self,
        playwright_service: Optional[PlaywrightService] = None,
        options: Optional[ParseOptions] = None
    ):
        self.playwright = playwright_service or PlaywrightService()
        self.options = options or ParseOptions()
        self._parsers = {
            Platform.DOUYIN.value: self._parse_douyin,
            Platform.KUAISHOU.value: self._parse_kuaishou,
            Platform.XIAOHONGSHU.value: self._parse_xiaohongshu,
            Platform.WEIXIN.value: self._parse_wechat,
            Platform.BILIBILI.value: self._parse_bilibili,
            Platform.WEIBO.value: self._parse_weibo,
            Platform.ZHIHU.value: self._parse_zhihu,
            Platform.XIGUA.value: self._parse_xigua,
        }
        logger.info("LinkParser initialized with enhanced features")

    async def parse(self, url: str, options: Optional[ParseOptions] = None) -> ParsedContent:
        """
        解析链接

        Args:
            url: 平台链接（支持纯URL或分享文本格式）
            options: 解析选项（覆盖默认选项）

        Returns:
            ParsedContent
        """
        opts = options or self.options

        # 从分享文本中提取URL
        url = self._extract_url(url)

        # 解析短链接
        url = await self.resolve_short_url(url, timeout=opts.timeout)

        # 检测平台
        platform = self._detect_platform(url)

        if platform is None:
            return ParsedContent(
                success=False,
                error=f"Unsupported platform or invalid URL: {url}",
                url=url
            )

        # 调用对应解析器（带重试）
        parser = self._parsers.get(platform)
        if parser is None:
            return ParsedContent(
                success=False,
                error=f"Parser not implemented for: {platform}",
                platform=platform,
                url=url
            )

        # 重试机制
        last_error = None
        for attempt in range(opts.retry_count + 1):
            try:
                result = await parser(url, opts)
                result.url = url
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Parse attempt {attempt + 1} failed: {e}")
                if attempt < opts.retry_count:
                    await asyncio.sleep(opts.retry_delay)

        return ParsedContent(
            success=False,
            error=str(last_error) if last_error else "Parse failed",
            platform=platform,
            url=url
        )

    async def parse_batch(
        self,
        urls: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[ParsedContent]:
        """
        批量解析链接

        Args:
            urls: URL列表
            progress_callback: 进度回调 (index, total, result)

        Returns:
            解析结果列表
        """
        results = []
        total = len(urls)

        for idx, url in enumerate(urls):
            result = await self.parse(url)
            results.append(result)

            if progress_callback:
                progress_callback(idx, total, result)

            # 避免请求过快
            if idx < total - 1:
                await asyncio.sleep(1)

        return results

    def _extract_url(self, text: str) -> str:
        """从分享文本中提取URL（使用编译后的正则）"""
        for pattern in _URL_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return text

    async def resolve_short_url(self, url: str, timeout: int = 30) -> str:
        """
        解析短链接，获取最终URL

        Args:
            url: 短链接
            timeout: 超时时间（秒）

        Returns:
            解析后的完整URL
        """
        import httpx

        # 短链接域名列表
        short_domains = [
            "v.douyin.com",    # 抖音短链
            "b23.tv",          # B站短链
            "xhslink.com",     # 小红书短链
            "weibo.cn",        # 微博短链
        ]

        # 检查是否是短链接
        url_lower = url.lower()
        is_short = any(domain in url_lower for domain in short_domains)

        if not is_short:
            return url

        try:
            async with httpx.AsyncClient(follow_redirects=False, timeout=timeout) as client:
                response = await client.get(url)
                if response.status_code in (301, 302, 303, 307, 308):
                    final_url = response.headers.get("location", url)
                    logger.info(f"Resolved short URL: {url} -> {final_url}")
                    return final_url
                return url
        except Exception as e:
            logger.warning(f"Failed to resolve short URL {url}: {e}")
            return url

    def _detect_platform(self, url: str) -> Optional[str]:
        """检测平台"""
        url_lower = url.lower()

        if "douyin.com" in url_lower:
            return Platform.DOUYIN.value
        elif "kuaishou.com" in url_lower:
            return Platform.KUAISHOU.value
        elif "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
            return Platform.XIAOHONGSHU.value
        elif "channels.weixin.qq.com" in url_lower:
            return Platform.WEIXIN.value
        elif "bilibili.com" in url_lower or "b23.tv" in url_lower:
            return Platform.BILIBILI.value
        elif "weibo.com" in url_lower:
            return Platform.WEIBO.value
        elif "zhihu.com" in url_lower:
            return Platform.ZHIHU.value
        elif "ixigua.com" in url_lower:
            return Platform.XIGUA.value

        return None

    def _extract_by_pattern(self, content: str, pattern, default: str = "") -> str:
        """使用正则提取内容"""
        if isinstance(pattern, list):
            for p in pattern:
                match = re.search(p, content, re.DOTALL)
                if match:
                    return match.group(1)
            return default
        else:
            match = re.search(pattern, content, re.DOTALL)
            return match.group(1) if match else default

    def _extract_tags(self, content: str, pattern: str) -> List[str]:
        """提取标签"""
        if not pattern:
            return []
        tags = re.findall(pattern, content)
        return [t.strip() for t in tags if t.strip()][:20]  # 限制最多20个

    async def _parse_douyin(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析抖音链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="douyin")

            content = result.content
            patterns = self.CONTENT_PATTERNS["douyin"]

            # 提取文案
            text = self._extract_by_pattern(content, patterns["text"])

            # 提取标题（有时标题和文案相同）
            title = self._extract_by_pattern(content, patterns["title"], text[:50])

            # 提取作者
            author = self._extract_by_pattern(content, patterns["author"])

            # 提取标签
            tags = self._extract_tags(content, patterns["tags"])

            # 清理文本
            text = text.replace("\\n", "\n").replace("\\", "").strip()

            # 尝试提取元数据
            metadata = {}
            if opts.extract_metadata:
                # 点赞数、收藏数等
                likes_match = re.search(r'"dig_count":(\d+)', content)
                if likes_match:
                    metadata["likes"] = int(likes_match.group(1))

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，抖音需要登录态才能获取内容",
                    platform="douyin"
                )

            return ParsedContent(
                success=True,
                text=text,
                title=title[:100] if title else "",
                tags=tags,
                author=author,
                platform="douyin",
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Parse douyin failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="douyin")

    async def _parse_kuaishou(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析快手链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="kuaishou")

            content = result.content
            patterns = self.CONTENT_PATTERNS["kuaishou"]

            text = self._extract_by_pattern(content, patterns["text"])
            tags = self._extract_tags(content, patterns["tags"])

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="kuaishou"
                )

            return ParsedContent(
                success=True,
                text=text,
                tags=tags,
                platform="kuaishou"
            )

        except Exception as e:
            logger.error(f"Parse kuaishou failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="kuaishou")

    async def _parse_xiaohongshu(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析小红书链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="xiaohongshu")

            content = result.content
            patterns = self.CONTENT_PATTERNS["xiaohongshu"]

            text = self._extract_by_pattern(content, patterns["text"])
            author = self._extract_by_pattern(content, patterns["author"])
            tags = self._extract_tags(content, patterns["tags"])

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="xiaohongshu"
                )

            return ParsedContent(
                success=True,
                text=text,
                tags=tags,
                author=author,
                platform="xiaohongshu"
            )

        except Exception as e:
            logger.error(f"Parse xiaohongshu failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="xiaohongshu")

    async def _parse_wechat(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析视频号链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="wechat")

            content = result.content
            patterns = self.CONTENT_PATTERNS["wechat"]

            text = self._extract_by_pattern(content, patterns["text"])
            title = self._extract_by_pattern(content, patterns["title"])
            author = self._extract_by_pattern(content, patterns["author"])

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="wechat"
                )

            return ParsedContent(
                success=True,
                text=text,
                title=title,
                author=author,
                platform="wechat"
            )

        except Exception as e:
            logger.error(f"Parse wechat failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="wechat")

    async def _parse_bilibili(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析B站链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="bilibili")

            content = result.content
            patterns = self.CONTENT_PATTERNS["bilibili"]

            title = self._extract_by_pattern(content, patterns["title"])
            text = self._extract_by_pattern(content, patterns["text"])
            author = self._extract_by_pattern(content, patterns["author"])
            tags = self._extract_tags(content, patterns["tags"])

            if not text and not title:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="bilibili"
                )

            return ParsedContent(
                success=True,
                text=f"{title}\n{text}".strip(),
                title=title,
                tags=tags,
                author=author,
                platform="bilibili"
            )

        except Exception as e:
            logger.error(f"Parse bilibili failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="bilibili")

    async def _parse_weibo(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析微博链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="weibo")

            content = result.content
            patterns = self.CONTENT_PATTERNS["weibo"]

            text = self._extract_by_pattern(content, patterns["text"])
            author = self._extract_by_pattern(content, patterns["author"])
            tags = self._extract_tags(content, patterns["tags"])

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="weibo"
                )

            return ParsedContent(
                success=True,
                text=text,
                tags=tags,
                author=author,
                platform="weibo"
            )

        except Exception as e:
            logger.error(f"Parse weibo failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="weibo")

    async def _parse_zhihu(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析知乎链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="zhihu")

            content = result.content
            patterns = self.CONTENT_PATTERNS["zhihu"]

            text = self._extract_by_pattern(content, patterns["text"])
            title = self._extract_by_pattern(content, patterns["title"])
            author = self._extract_by_pattern(content, patterns["author"])

            if not text:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="zhihu"
                )

            return ParsedContent(
                success=True,
                text=text,
                title=title,
                author=author,
                platform="zhihu"
            )

        except Exception as e:
            logger.error(f"Parse zhihu failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="zhihu")

    async def _parse_xigua(self, url: str, opts: ParseOptions) -> ParsedContent:
        """解析西瓜视频链接"""
        try:
            result = await self.playwright.navigate(url, timeout=opts.timeout * 1000)

            if not result.success:
                return ParsedContent(success=False, error=result.error, platform="xigua")

            content = result.content
            patterns = self.CONTENT_PATTERNS["xigua"]

            title = self._extract_by_pattern(content, patterns["title"])
            text = self._extract_by_pattern(content, patterns["text"])
            author = self._extract_by_pattern(content, patterns["author"])
            tags = self._extract_tags(content, patterns["tags"])

            if not text and not title:
                return ParsedContent(
                    success=False,
                    error="未能提取到文案，可能需要登录后查看",
                    platform="xigua"
                )

            return ParsedContent(
                success=True,
                text=text or title,
                title=title,
                tags=tags,
                author=author,
                platform="xigua"
            )

        except Exception as e:
            logger.error(f"Parse xigua failed: {e}")
            return ParsedContent(success=False, error=str(e), platform="xigua")

    async def close(self):
        """关闭"""
        await self.playwright.close()

    def list_supported_platforms(self) -> List[Dict[str, str]]:
        """列出支持的平台"""
        return [
            {"id": p.value, "name": self._get_platform_name(p.value)}
            for p in Platform
        ]

    def _get_platform_name(self, platform_id: str) -> str:
        """获取平台名称"""
        names = {
            "douyin": "抖音",
            "kuaishou": "快手",
            "xiaohongshu": "小红书",
            "weixin": "视频号",
            "bilibili": "B站",
            "weibo": "微博",
            "zhihu": "知乎",
            "xigua": "西瓜视频"
        }
        return names.get(platform_id, platform_id)


# 便捷函数
async def parse_link(url: str, options: Optional[ParseOptions] = None) -> ParsedContent:
    """解析链接"""
    parser = LinkParser()
    try:
        return await parser.parse(url, options)
    finally:
        await parser.close()


async def parse_links_batch(
    urls: List[str],
    progress_callback: Optional[Callable] = None
) -> List[ParsedContent]:
    """批量解析链接"""
    parser = LinkParser()
    try:
        return await parser.parse_batch(urls, progress_callback)
    finally:
        await parser.close()


def save_parsed_content(results: List[ParsedContent], output_path: str):
    """保存解析结果到JSON文件"""
    output_data = [
        {
            "success": r.success,
            "text": r.text,
            "title": r.title,
            "tags": r.tags,
            "author": r.author,
            "platform": r.platform,
            "url": r.url,
            "error": r.error
        }
        for r in results
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(results)} parsed content to {output_path}")