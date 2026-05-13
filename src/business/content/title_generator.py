"""标题自动生成 - LLM 生成标题 + 副标题 + 话题标签"""
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

from loguru import logger


class Platform(Enum):
    """目标平台"""
    DOUYIN = "douyin"          # 抖音
    KUAISHOU = "kuaishou"      # 快手
    XIAOHONGSHU = "xiaohongshu" # 小红书
    WEIXIN = "weixin"          # 视频号


@dataclass
class TitleResult:
    """标题生成结果"""
    title: str                          # 主标题
    subtitle: str                       # 副标题/引导语
    hashtags: List[str]                 # 话题标签 (#开头)
    platform_adapted: Dict[Platform, str] = field(default_factory=dict)  # 各平台适配版本
    is_completed: bool = True


@dataclass
class TitleGeneratorConfig:
    """标题生成器配置"""
    api_key: str = ""
    provider: str = "dashscope"  # dashscope / openai / ernie / deepseek / doubao / moonshot
    default_platform: Platform = Platform.DOUYIN

    # 各平台标题规则
    platform_rules: Dict[Platform, dict] = field(default_factory=lambda: {
        Platform.DOUYIN: {"max_title_len": 30, "hashtags_count": 3, "emoji": False},
        Platform.KUAISHOU: {"max_title_len": 20, "hashtags_count": 2, "emoji": False},
        Platform.XIAOHONGSHU: {"max_title_len": 20, "hashtags_count": 0, "emoji": True},
        Platform.WEIXIN: {"max_title_len": 40, "hashtags_count": 0, "emoji": False},
    })


class TitleGenerator:
    """
    标题自动生成器

    功能：
    1. 根据文案内容生成吸引人的标题
    2. 生成副标题/引导语
    3. 提取/生成话题标签
    4. 多平台文案适配
    """

    # 常用话题标签库
    COMMON_HASHTAGS = {
        "美妆": ["#美妆教程", "#口红试色", "#变美技巧", "#化妆技巧", "#护肤心得"],
        "知识": ["#知识分享", "#干货教程", "#学习技巧", "#职场干货", "#认知提升"],
        "电商": ["#好物推荐", "#购物分享", "#开箱测评", "#省钱攻略", "#种草清单"],
        "美食": ["#美食推荐", "#食谱分享", "#做饭教程", "#探店打卡", "#吃货日常"],
        "母婴": ["#育儿分享", "#宝宝辅食", "#带娃日常", "#亲子教育", "#妈妈必看"],
        "家居": ["#家居好物", "#软装搭配", "#收纳技巧", "#home", "#生活美学"],
        "健身": ["#健身打卡", "#减脂日记", "#塑形教程", "#运动日常", "#健康生活"],
        "旅游": ["#旅行攻略", "#打卡拍照", "#目的地推荐", "#旅游日记", "#出行必备"],
    }

    def __init__(self, config: Optional[TitleGeneratorConfig] = None):
        self.config = config or TitleGeneratorConfig()

    async def generate(
        self,
        content: str,
        platform: Platform = None,
        category: str = None
    ) -> TitleResult:
        """
        生成标题

        Args:
            content: 文案内容
            platform: 目标平台
            category: 内容分类（美妆/知识/电商等）

        Returns:
            TitleResult: 生成结果
        """
        if not content:
            return TitleResult(
                title="",
                subtitle="",
                hashtags=[],
                platform_adapted={}
            )

        platform = platform or self.config.default_platform

        # 1. 提取关键词
        keywords = self._extract_keywords(content)

        # 2. 生成标题（调用 LLM 或使用模板）
        if self.config.api_key:
            title = await self._generate_with_llm(content, keywords, platform)
            subtitle = await self._generate_subtitle_with_llm(content, platform)
            hashtags = await self._generate_hashtags_with_llm(content, keywords, platform, category)
        else:
            title = self._generate_template_title(content, keywords, platform)
            subtitle = self._generate_template_subtitle(content, platform)
            hashtags = self._generate_template_hashtags(keywords, category, platform)

        # 3. 多平台适配
        platform_adapted = await self._adapt_for_platforms(content, keywords)

        return TitleResult(
            title=title,
            subtitle=subtitle,
            hashtags=hashtags,
            platform_adapted=platform_adapted
        )

    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 简单实现，实际可用 NLP 或 LLM
        words = []
        for char in content:
            if char.isalnum():
                words.append(char)

        # 取前10个关键词
        return list(set("".join(words).split()))[:10]

    def _generate_template_title(
        self,
        content: str,
        keywords: List[str],
        platform: Platform
    ) -> str:
        """使用模板生成标题"""
        # 取前N个字作为标题
        max_len = self.config.platform_rules[platform]["max_title_len"]

        if len(content) <= max_len:
            return content
        else:
            # 在句子里找断点
            for i in range(min(max_len, len(content)), 0, -1):
                if content[i] in "，。！？、":
                    return content[:i+1]
            return content[:max_len] + "..."

    def _generate_template_subtitle(self, content: str, platform: Platform) -> str:
        """使用模板生成副标题"""
        # 取内容中间部分作为副标题
        if len(content) < 30:
            return ""
        return content[20:50] + "..."

    def _generate_template_hashtags(
        self,
        keywords: List[str],
        category: str,
        platform: Platform
    ) -> List[str]:
        """使用模板生成话题标签"""
        hashtags = []

        # 从分类标签库选择
        if category and category in self.COMMON_HASHTAGS:
            hashtags = self.COMMON_HASHTAGS[category][:2].copy()
        else:
            # 从所有标签中随机选
            for tags in self.COMMON_HASHTAGS.values():
                hashtags.extend(tags[:1])
            hashtags = hashtags[:2]

        # 抖音额外标签
        if platform == Platform.DOUYIN:
            hashtags.append(f"#{keywords[0] if keywords else '推荐'}")
        elif platform == Platform.XIAOHONGSHU and self.config.platform_rules[platform]["emoji"]:
            hashtags.append("💄")

        return hashtags

    async def _generate_with_llm(
        self,
        content: str,
        keywords: List[str],
        platform: Platform
    ) -> str:
        """调用 LLM 生成标题"""
        prompt = f"""请为以下文案生成一个吸引人的短视频标题。

要求：
- 标题{self.config.platform_rules[platform]['max_title_len']}字以内
- 吸引眼球，引发好奇
- 适合{platform.value}平台风格

文案内容：
{content[:200]}...

请直接输出标题，不要其他内容："""

        result = await self._call_llm(prompt)
        return result.strip()

    async def _generate_subtitle_with_llm(self, content: str, platform: Platform) -> str:
        """调用 LLM 生成副标题"""
        prompt = f"""请为以下文案生成一个引导语/副标题。

要求：
- 10-20字
- 引导用户继续观看
- 适合{platform.value}平台风格

文案内容：
{content[:200]}...

请直接输出引导语，不要其他内容："""

        result = await self._call_llm(prompt)
        return result.strip()

    async def _generate_hashtags_with_llm(
        self,
        content: str,
        keywords: List[str],
        platform: Platform,
        category: str
    ) -> List[str]:
        """调用 LLM 生成话题标签"""
        count = self.config.platform_rules[platform]["hashtags_count"]
        if count == 0:
            return []

        prompt = f"""请为以下文案生成{count}个话题标签。

要求：
- 格式：#话题名
- 精准匹配内容主题
- 热门且流量大

文案内容：
{content[:200]}...

请直接输出标签，用空格分隔，不要其他内容："""

        result = await self._call_llm(prompt)
        hashtags = [tag.strip() for tag in result.split("#") if tag.strip()]
        return ["#" + tag for tag in hashtags][:count]

    async def _adapt_for_platforms(
        self,
        content: str,
        keywords: List[str]
    ) -> Dict[Platform, str]:
        """多平台文案适配"""
        adapted = {}

        for platform in Platform:
            rules = self.config.platform_rules[platform]
            max_len = rules["max_title_len"]

            if self.config.api_key:
                prompt = f"""请将以下文案改写为适合{platform.value}平台的标题。

要求：{max_len}字以内
文案：{content[:100]}...

请直接输出标题："""
                adapted[platform] = (await self._call_llm(prompt)).strip()
            else:
                adapted[platform] = content[:max_len]

        return adapted

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if self.config.provider == "dashscope":
            return await self._call_dashscope(prompt)
        elif self.config.provider == "deepseek":
            return await self._call_deepseek(prompt)
        elif self.config.provider == "doubao":
            return await self._call_doubao(prompt)
        elif self.config.provider == "moonshot":
            return await self._call_moonshot(prompt)
        else:
            return await self._call_dashscope(prompt)

    async def _call_dashscope(self, prompt: str) -> str:
        """调用通义千问 API"""
        import aiohttp

        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"DashScope API error: {response.status}")

    async def _call_deepseek(self, prompt: str) -> str:
        """调用 DeepSeek API"""
        import aiohttp

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"DeepSeek API error: {response.status}")

    async def _call_doubao(self, prompt: str) -> str:
        """调用豆包 API"""
        import aiohttp

        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "doubao-pro-32k",
            "messages": [{"role": "user", "content": prompt}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Doubao API error: {response.status}")

    async def _call_moonshot(self, prompt: str) -> str:
        """调用 Kimi / Moonshot API"""
        import aiohttp

        url = "https://api.moonshot.cn/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "moonshot-v1-128k",
            "messages": [{"role": "user", "content": prompt}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Moonshot API error: {response.status}")


# 全局实例
_generator: Optional[TitleGenerator] = None


def get_title_generator(config: Optional[TitleGeneratorConfig] = None) -> TitleGenerator:
    """获取标题生成器实例"""
    global _generator
    if _generator is None or config is not None:
        _generator = TitleGenerator(config)
    return _generator