"""多平台文案适配"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

from loguru import logger


class Platform(Enum):
    """目标平台"""
    DOUYIN = "douyin"              # 抖音
    KUAISHOU = "kuaishou"          # 快手
    XIAOHONGSHU = "xiaohongshu"    # 小红书
    WEIXIN = "weixin"              # 视频号
    WEIBO = "weibo"                # 微博
    BILIBILI = "bilibili"          # B站


@dataclass
class PlatformConfig:
    """平台配置"""
    max_title_len: int = 30          # 标题最大长度
    max_content_len: int = 2000     # 内容最大长度
    hashtags_required: bool = True   # 是否需要话题标签
    hashtags_count: int = 3          # 话题标签数量
    emoji_allowed: bool = True       # 是否允许emoji
    emoji_ratio: float = 0.1         # emoji 密度
    mention_allowed: bool = True     # 是否允许@提及
    link_allowed: bool = True         # 是否允许链接
    newline_limit: int = 3           # 最多换行数
    call_to_action: bool = True      # 是否需要行动号召


# 各平台配置
PLATFORM_CONFIGS: Dict[Platform, PlatformConfig] = {
    Platform.DOUYIN: PlatformConfig(
        max_title_len=30,
        max_content_len=2000,
        hashtags_required=True,
        hashtags_count=3,
        emoji_allowed=True,
        emoji_ratio=0.05,
        newline_limit=5
    ),
    Platform.KUAISHOU: PlatformConfig(
        max_title_len=20,
        max_content_len=1500,
        hashtags_required=True,
        hashtags_count=2,
        emoji_allowed=False,
        newline_limit=3
    ),
    Platform.XIAOHONGSHU: PlatformConfig(
        max_title_len=20,
        max_content_len=1000,
        hashtags_required=False,
        hashtags_count=0,
        emoji_allowed=True,
        emoji_ratio=0.15,
        newline_limit=10,
        call_to_action=False
    ),
    Platform.WEIXIN: PlatformConfig(
        max_title_len=40,
        max_content_len=50000,
        hashtags_required=False,
        hashtags_count=0,
        emoji_allowed=False,
        newline_limit=0,
        call_to_action=True
    ),
    Platform.WEIBO: PlatformConfig(
        max_title_len=30,
        max_content_len=2000,
        hashtags_required=True,
        hashtags_count=5,
        emoji_allowed=True,
        emoji_ratio=0.08,
        mention_allowed=True,
        link_allowed=True
    ),
    Platform.BILIBILI: PlatformConfig(
        max_title_len=50,
        max_content_len=5000,
        hashtags_required=True,
        hashtags_count=3,
        emoji_allowed=True,
        emoji_ratio=0.05,
        call_to_action=True
    ),
}


@dataclass
class AdaptedContent:
    """适配后的内容"""
    platform: Platform
    title: str
    content: str
    hashtags: List[str]
    warning: List[str] = None  # 适配警告（如被截断的内容）

    def __post_init__(self):
        if self.warning is None:
            self.warning = []


@dataclass
class PlatformAdapterConfig:
    """适配器配置"""
    default_platform: Platform = Platform.DOUYIN
    preserve_keywords: bool = True  # 保留关键词


class PlatformAdapter:
    """
    多平台文案适配器

    根据各平台规则自动改写文案
    """

    def __init__(self, config: Optional[PlatformAdapterConfig] = None):
        self.config = config or PlatformAdapterConfig()
        self._platform_configs = PLATFORM_CONFIGS

    def adapt(
        self,
        content: str,
        platform: Platform,
        title: str = None
    ) -> AdaptedContent:
        """
        适配内容到指定平台

        Args:
            content: 原始文案
            platform: 目标平台
            title: 原始标题（可选）

        Returns:
            AdaptedContent: 适配后的内容
        """
        config = self._platform_configs.get(platform, PLATFORM_CONFIGS[Platform.DOUYIN])
        warnings = []

        # 1. 标题适配
        adapted_title = title
        if title:
            adapted_title = self._adapt_title(title, config)

        # 2. 内容适配
        adapted_content = self._adapt_content(content, config, warnings)

        # 3. 话题标签适配
        hashtags = self._adapt_hashtags(content, config)

        return AdaptedContent(
            platform=platform,
            title=adapted_title or "",
            content=adapted_content,
            hashtags=hashtags,
            warning=warnings
        )

    def adapt_all(
        self,
        content: str,
        title: str = None
    ) -> Dict[Platform, AdaptedContent]:
        """
        适配内容到所有平台

        Returns:
            Dict[Platform, AdaptedContent]: 各平台适配结果
        """
        results = {}
        for platform in Platform:
            results[platform] = self.adapt(content, platform, title)
        return results

    def _adapt_title(self, title: str, config: PlatformConfig) -> str:
        """适配标题"""
        if len(title) <= config.max_title_len:
            return title

        # 截断并添加省略号
        truncated = title[:config.max_title_len - 1].strip()
        return truncated + "…"

    def _adapt_content(
        self,
        content: str,
        config: PlatformConfig,
        warnings: List[str]
    ) -> str:
        """适配内容主体"""
        result = content

        # 1. 长度限制
        if len(result) > config.max_content_len:
            warnings.append(f"内容被截断至 {config.max_content_len} 字")
            result = result[:config.max_content_len - 3] + "..."

        # 2. 换行符限制
        if config.newline_limit > 0:
            lines = result.split("\n")
            if len(lines) > config.newline_limit:
                warnings.append(f"换行被限制为最多 {config.newline_limit} 行")
                result = "\n".join(lines[:config.newline_limit])

        # 3. emoji 处理
        if not config.emoji_allowed:
            result = self._remove_emoji(result)
        else:
            # 限制 emoji 密度
            result = self._limit_emoji(result, config.emoji_ratio)

        # 4. 添加行动号召（如果需要）
        if config.call_to_action:
            result = self._add_cta(result, config)

        return result

    def _adapt_hashtags(self, content: str, config: PlatformConfig) -> List[str]:
        """适配话题标签"""
        if not config.hashtags_required or config.hashtags_count == 0:
            return []

        # 从内容中提取或生成话题标签
        hashtags = self._extract_hashtags(content)

        # 返回指定数量
        return hashtags[:config.hashtags_count]

    def _extract_hashtags(self, content: str) -> List[str]:
        """从内容中提取话题标签"""
        import re
        found = re.findall(r'#\w+', content)
        return found if found else ["#推荐", "#种草", "#好物"]

    def _remove_emoji(self, text: str) -> str:
        """移除 emoji"""
        import re
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)

    def _limit_emoji(self, text: str, ratio: float) -> str:
        """限制 emoji 密度"""
        import re
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        emojis = emoji_pattern.findall(text)

        # 计算目标 emoji 数量
        max_emojis = int(len(text) * ratio)
        if len(emojis) <= max_emojis:
            return text

        # 保留部分 emoji
        keep_count = max(1, max_emojis)
        return emojis[0] * keep_count + text[len("".join(emojis)):]

    def _add_cta(self, content: str, config: PlatformConfig) -> str:
        """添加行动号召"""
        cta_templates = [
            "\n\n👍 觉得有用点个赞吧",
            "\n\n❤️ 喜欢的话关注我",
            "\n\n➡️ 点击链接查看更多",
            "\n\n💬 评论区见",
        ]

        # 随机选一个
        import random
        cta = random.choice(cta_templates)

        return content + cta

    def get_platform_config(self, platform: Platform) -> PlatformConfig:
        """获取平台配置"""
        return self._platform_configs.get(platform, PLATFORM_CONFIGS[Platform.DOUYIN])

    def list_platforms(self) -> List[Dict]:
        """列出所有平台"""
        return [
            {
                "id": p.value,
                "name": self._get_platform_name(p),
                "max_title_len": cfg.max_title_len,
                "max_content_len": cfg.max_content_len
            }
            for p, cfg in self._platform_configs.items()
        ]

    def _get_platform_name(self, platform: Platform) -> str:
        """获取平台显示名称"""
        names = {
            Platform.DOUYIN: "抖音",
            Platform.KUAISHOU: "快手",
            Platform.XIAOHONGSHU: "小红书",
            Platform.WEIXIN: "视频号",
            Platform.WEIBO: "微博",
            Platform.BILIBILI: "B站",
        }
        return names.get(platform, platform.value)


# 全局实例
_adapter: Optional[PlatformAdapter] = None


def get_platform_adapter(config: Optional[PlatformAdapterConfig] = None) -> PlatformAdapter:
    """获取适配器实例"""
    global _adapter
    if _adapter is None or config is not None:
        _adapter = PlatformAdapter(config)
    return _adapter