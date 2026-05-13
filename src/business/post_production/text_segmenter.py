"""文本自动分段 - 标点切分 + LLM 语义优化"""
import re
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

from loguru import logger


class TextEmotion(Enum):
    """文本情绪分类"""
    EXCITED = "excited"      # 兴奋
    CALM = "calm"            # 平静
    SERIOUS = "serious"      # 严肃
    WARM = "warm"            # 温暖


@dataclass
class TextSegment:
    """文本段落"""
    index: int              # 段落索引
    text: str              # 段落文本
    start_pos: int         # 在原文中的起始位置
    end_pos: int           # 在原文中的结束位置
    estimated_duration: float  # 预估时长（秒）
    emotion: TextEmotion   # 段落情绪

    @property
    def duration(self) -> float:
        return self.estimated_duration


@dataclass
class SegmentResult:
    """分段结果"""
    segments: List[TextSegment]       # 段落列表
    total_duration: float             # 总时长
    original_text: str                # 原始文本
    is_completed: bool                # 是否完成


@dataclass
class TextSegmenterConfig:
    """分段器配置"""
    max_duration: float = 60.0        # 单段最大时长（秒）
    min_duration: float = 5.0         # 单段最小时长（秒）
    avg_read_speed: float = 5.0       # 平均语速（字/秒）

    # LLM API 配置（可选，用于语义优化）
    llm_api_key: str = ""
    llm_provider: str = "dashscope"   # dashscope / openai / ernie / deepseek


class TextSegmenter:
    """
    文本自动分段器

    功能：
    1. 标点符号切分短句
    2. 语义完整性检查
    3. 时长约束（默认单段落 < 60秒）
    4. 情绪连贯性（同一情绪的句子尽量合并）
    """

    # 标点符号列表
    PUNCTUATIONS = ["。", "！", "？", "；", "\n"]

    def __init__(self, config: Optional[TextSegmenterConfig] = None):
        self.config = config or TextSegmenterConfig()

    def segment(self, text: str) -> SegmentResult:
        """
        基础分段（纯规则）

        Args:
            text: 输入文本

        Returns:
            SegmentResult: 分段结果
        """
        if not text:
            return SegmentResult(
                segments=[],
                total_duration=0.0,
                original_text="",
                is_completed=True
            )

        # 1. 按标点初步切分
        raw_segments = self._split_by_punctuation(text)

        # 2. 合并过短的段落
        merged_segments = self._merge_short_segments(raw_segments)

        # 3. 分割过长的段落
        final_segments = self._split_long_segments(merged_segments)

        # 4. 构建结果
        result_segments = []
        total_duration = 0.0
        text_len = len(text)

        for i, seg_text in enumerate(final_segments):
            duration = len(seg_text) / self.config.avg_read_speed
            total_duration += duration

            result_segments.append(TextSegment(
                index=i,
                text=seg_text.strip(),
                start_pos=text.find(seg_text),
                end_pos=text.find(seg_text) + len(seg_text),
                estimated_duration=duration,
                emotion=TextEmotion.CALM  # 默认平静
            ))

        return SegmentResult(
            segments=result_segments,
            total_duration=total_duration,
            original_text=text,
            is_completed=True
        )

    def _split_by_punctuation(self, text: str) -> List[str]:
        """按标点符号初步切分"""
        # 替换换行符为空格
        text = re.sub(r'\n+', ' ', text)

        # 按句末标点分割
        pattern = r'([。！？？；])'
        parts = re.split(pattern, text)

        # 合并句子和标点
        segments = []
        current = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:
                current += part
            else:
                current += part
                if current.strip():
                    segments.append(current)
                current = ""

        # 处理最后一段
        if current.strip():
            segments.append(current)

        return [s.strip() for s in segments if s.strip()]

    def _merge_short_segments(self, segments: List[str]) -> List[str]:
        """合并过短的段落"""
        if not segments:
            return []

        merged = [segments[0]]

        for seg in segments[1:]:
            # 如果当前段落太短，合并到上一个
            if len(merged[-1]) < self.config.min_duration * self.config.avg_read_speed:
                merged[-1] += seg
            else:
                merged.append(seg)

        return merged

    def _split_long_segments(self, segments: List[str]) -> List[str]:
        """分割过长的段落"""
        max_chars = self.config.max_duration * self.config.avg_read_speed
        result = []

        for seg in segments:
            if len(seg) <= max_chars:
                result.append(seg)
            else:
                # 在中间位置找分割点
                sub_parts = self._find_split_point(seg, max_chars)
                result.extend(sub_parts)

        return result

    def _find_split_point(self, text: str, max_chars: int) -> List[str]:
        """在长文本中找合适的分割点"""
        parts = []
        while len(text) > max_chars:
            # 找到中点附近的最大分割点
            split_pos = max_chars
            for punct in ["，", "、", "；", "。", "！", "？"]:
                pos = text.rfind(punct, 0, max_chars)
                if pos > max_chars * 0.6:  # 至少在60%位置之后
                    split_pos = pos + 1
                    break

            parts.append(text[:split_pos])
            text = text[split_pos:]

        if text:
            parts.append(text)

        return parts

    async def segment_with_llm_optimize(self, text: str) -> SegmentResult:
        """
        LLM 语义优化分段（可选）

        使用 LLM 对分段进行语义优化，确保每段语义完整

        Args:
            text: 输入文本

        Returns:
            SegmentResult: 分段结果
        """
        # 先做基础分段
        result = self.segment(text)

        # 如果没有配置 LLM，直接返回基础结果
        if not self.config.llm_api_key:
            return result

        try:
            # 调用 LLM 优化分段
            optimized = await self._call_llm_optimize(text, result.segments)
            return optimized
        except Exception as e:
            logger.warning(f"LLM 优化分段失败: {e}")
            return result

    async def _call_llm_optimize(self, text: str, segments: List[str]) -> SegmentResult:
        """调用 LLM 优化分段"""
        # 构建提示词
        prompt = f"""请将以下文案合理分段，每段时长控制在{self.config.max_duration}秒左右。

原文：
{text}

当前分段：
{chr(10).join([f'{i+1}. {s}' for i, s in enumerate(segments)])}

请输出最优分段，用|分隔各段：
"""

        # 调用 LLM（简化实现，实际需根据不同 provider 实现）
        if self.config.llm_provider == "dashscope":
            result_text = await self._call_dashscope(prompt)
        elif self.config.llm_provider == "deepseek":
            result_text = await self._call_deepseek(prompt)
        else:
            result_text = await self._call_dashscope(prompt)

        # 解析 LLM 返回结果
        optimized = result_text.split("|")
        optimized = [s.strip() for s in optimized if s.strip()]

        # 重新构建结果
        result_segments = []
        total_duration = 0.0

        for i, seg_text in enumerate(optimized):
            duration = len(seg_text) / self.config.avg_read_speed
            total_duration += duration

            result_segments.append(TextSegment(
                index=i,
                text=seg_text,
                start_pos=text.find(seg_text) if seg_text in text else 0,
                end_pos=text.find(seg_text) + len(seg_text) if seg_text in text else len(seg_text),
                estimated_duration=duration,
                emotion=TextEmotion.CALM
            ))

        return SegmentResult(
            segments=result_segments,
            total_duration=total_duration,
            original_text=text,
            is_completed=True
        )

    async def _call_dashscope(self, prompt: str) -> str:
        """调用通义千问 API"""
        import aiohttp

        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.llm_api_key}",
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
                    raise Exception(f"API error: {response.status}")

    async def _call_deepseek(self, prompt: str) -> str:
        """调用 DeepSeek API"""
        import aiohttp

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.llm_api_key}",
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
                    raise Exception(f"API error: {response.status}")


# 全局实例
_segmenter: Optional[TextSegmenter] = None


def get_text_segmenter(config: Optional[TextSegmenterConfig] = None) -> TextSegmenter:
    """获取文本分段器实例"""
    global _segmenter
    if _segmenter is None or config is not None:
        _segmenter = TextSegmenter(config)
    return _segmenter