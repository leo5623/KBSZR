"""敏感词过滤 - 基于阿里云内容安全 API"""
import asyncio
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

from loguru import logger


class ContentCategory(Enum):
    """内容类别"""
    POLITICAL = "political"           # 敏感政治内容
    AD = "ad"                         # 广告
    PORN = "porn"                    # 色情
    VIOLENCE = "violence"            # 暴恐
    DISASTER = "disaster"            # 违禁物品/灾难
    CUSTOM = "custom"                # 自定义敏感词


@dataclass
class SensitiveWordResult:
    """敏感词检测结果"""
    is_passed: bool                  # 是否通过检测
    filtered_text: str               # 过滤后的文本
    detected_words: List[str]        # 检测到的敏感词
    categories: List[ContentCategory] # 触发的类别
    suggestion: str                  # 处理建议


@dataclass
class SensitiveFilterConfig:
    """敏感词过滤配置"""
    api_key: str = ""
    api_region: str = "cn-beijing"  # 默认北京区域
    enable_custom_dict: bool = True  # 启用自定义词库
    custom_words: List[str] = []      # 自定义敏感词列表


class SensitiveWordFilter:
    """
    敏感词过滤器

    使用阿里云内容安全 API 进行实时敏感词检测和过滤
    """

    def __init__(self, config: Optional[SensitiveFilterConfig] = None):
        self.config = config or SensitiveFilterConfig()
        self._custom_word_set = set(self.config.custom_words) if self.config.custom_words else set()

    async def filter(self, text: str) -> SensitiveWordResult:
        """
        过滤敏感词

        Args:
            text: 输入文本

        Returns:
            SensitiveWordResult: 过滤结果
        """
        if not text:
            return SensitiveWordResult(
                is_passed=True,
                filtered_text="",
                detected_words=[],
                categories=[],
                suggestion="文本为空"
            )

        detected_words = []
        categories = []

        # 1. 自定义敏感词检测（本地快速过滤）
        for word in self._custom_word_set:
            if word in text:
                detected_words.append(word)
                categories.append(ContentCategory.CUSTOM)

        # 2. 阿里云内容安全 API 检测
        if self.config.api_key:
            try:
                api_result = await self._call_aliyun_api(text)
                detected_words.extend(api_result.get("detected_words", []))
                categories.extend(api_result.get("categories", []))
            except Exception as e:
                logger.warning(f"阿里云内容安全 API 调用失败: {e}")

        # 3. 本地简单敏感词库（兜底）
        local_result = self._local_filter(text)
        detected_words.extend(local_result.get("detected_words", []))

        # 去重
        detected_words = list(set(detected_words))

        # 过滤敏感词
        filtered_text = text
        for word in detected_words:
            # 用 * 替换敏感词
            filtered_text = filtered_text.replace(word, "*" * len(word))

        is_passed = len(detected_words) == 0

        return SensitiveWordResult(
            is_passed=is_passed,
            filtered_text=filtered_text,
            detected_words=detected_words,
            categories=categories,
            suggestion="请修改后重试" if not is_passed else "通过"
        )

    def _local_filter(self, text: str) -> dict:
        """
        本地简单敏感词过滤（兜底方案）

        常见敏感词类型：
        - 政治相关
        - 色情低俗
        - 暴恐相关
        - 违禁药物
        """
        # 简化示例，实际应使用更完整的词库
        local_sensitive_words = {
            "政治": ["敏感词1", "敏感词2"],  # 示例占位
            "色情": ["敏感词3", "敏感词4"],
        }

        detected = []
        for category, words in local_sensitive_words.items():
            for word in words:
                if word in text:
                    detected.append(word)

        return {"detected_words": detected}

    async def _call_aliyun_api(self, text: str) -> dict:
        """
        调用阿里云内容安全 API

        文档: https://help.aliyun.com/document_detail/28417.html
        """
        import aiohttp

        url = f"https://green.aliyuncs.com/text/scan"

        headers = {
            "Authorization": f"APPCODE {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "labels": [
                "politics",
                "ad",
                "porn",
                "violence",
                "disaster",
                "custom"
            ],
            "scenes": ["default"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._parse_aliyun_result(result)
                else:
                    logger.error(f"阿里云内容安全 API 错误: {response.status}")
                    return {"detected_words": [], "categories": []}

    def _parse_aliyun_result(self, result: dict) -> dict:
        """解析阿里云 API 返回结果"""
        detected_words = []
        categories = []

        try:
            if result.get("success"):
                for item in result.get("data", []):
                    if item.get("label") in ["politics", "ad", "porn", "violence", "disaster", "custom"]:
                        for detail in item.get("details", []):
                            if "words" in detail:
                                detected_words.extend(detail["words"])
        except Exception as e:
            logger.warning(f"解析阿里云结果失败: {e}")

        return {"detected_words": detected_words, "categories": categories}

    def add_custom_words(self, words: List[str]):
        """添加自定义敏感词"""
        self._custom_word_set.update(words)

    def remove_custom_words(self, words: List[str]):
        """移除自定义敏感词"""
        self._custom_word_set.difference_update(words)


# 全局实例
_filter: Optional[SensitiveWordFilter] = None


def get_sensitive_filter(config: Optional[SensitiveFilterConfig] = None) -> SensitiveWordFilter:
    """获取敏感词过滤器实例"""
    global _filter
    if _filter is None or config is not None:
        _filter = SensitiveWordFilter(config)
    return _filter