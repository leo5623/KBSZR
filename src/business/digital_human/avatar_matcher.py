"""形象/背景自动匹配"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

from loguru import logger


class IndustryCategory(Enum):
    """行业分类"""
    BEAUTY = "beauty"           # 美妆
    KNOWLEDGE = "knowledge"      # 知识付费
    ECOMMERCE = "ecommerce"      # 电商带货
    FOOD = "food"                # 美食
    MOTHER_BABY = "mother_baby"  # 母婴
    LIFE = "life"                # 家居生活
    FITNESS = "fitness"          # 健身
    TRAVEL = "travel"            # 旅游


class AvatarTone(Enum):
    """数字人语气风格"""
    FRIENDLY = "friendly"       # 亲切友好
    PROFESSIONAL = "professional"  # 专业严肃
    LIVELY = "lively"           # 活泼开朗
    STEADY = "steady"            # 沉稳稳重


@dataclass
class AvatarMatchRule:
    """形象匹配规则"""
    industry: IndustryCategory
    tone: AvatarTone
    recommended_avatar_ids: List[str]
    recommended_background_ids: List[str]
    description: str = ""


@dataclass
class AvatarMatchResult:
    """匹配结果"""
    avatar_id: str
    avatar_name: str
    background_id: str
    background_name: str
    confidence: float  # 匹配置信度 0-1
    reason: str        # 匹配原因


# 匹配规则配置
AVATAR_MATCH_RULES: List[AvatarMatchRule] = [
    # 美妆行业
    AvatarMatchRule(
        industry=IndustryCategory.BEAUTY,
        tone=AvatarTone.FRIENDLY,
        recommended_avatar_ids=["avatar_001", "avatar_002", "avatar_008"],
        recommended_background_ids=["bg_001", "bg_005"],
        description="美妆类推荐青春活泼或知性优雅女性形象"
    ),
    AvatarMatchRule(
        industry=IndustryCategory.BEAUTY,
        tone=AvatarTone.LIVELY,
        recommended_avatar_ids=["avatar_001", "avatar_008"],
        recommended_background_ids=["bg_005", "bg_003"],
        description="美妆种草推荐活泼开朗风格"
    ),

    # 知识付费
    AvatarMatchRule(
        industry=IndustryCategory.KNOWLEDGE,
        tone=AvatarTone.PROFESSIONAL,
        recommended_avatar_ids=["avatar_004", "avatar_007"],
        recommended_background_ids=["bg_001", "bg_002"],
        description="知识讲解推荐成熟稳重专业人士"
    ),
    AvatarMatchRule(
        industry=IndustryCategory.KNOWLEDGE,
        tone=AvatarTone.FRIENDLY,
        recommended_avatar_ids=["avatar_002", "avatar_003"],
        recommended_background_ids=["bg_001", "bg_003"],
        description="知识分享推荐亲和友好风格"
    ),

    # 电商带货
    AvatarMatchRule(
        industry=IndustryCategory.ECOMMERCE,
        tone=AvatarTone.LIVELY,
        recommended_avatar_ids=["avatar_001", "avatar_008"],
        recommended_background_ids=["bg_005", "bg_006"],
        description="电商带货推荐活力主播形象"
    ),
    AvatarMatchRule(
        industry=IndustryCategory.ECOMMERCE,
        tone=AvatarTone.FRIENDLY,
        recommended_avatar_ids=["avatar_002", "avatar_003"],
        recommended_background_ids=["bg_005", "bg_001"],
        description="带货推荐亲和可信风格"
    ),

    # 美食
    AvatarMatchRule(
        industry=IndustryCategory.FOOD,
        tone=AvatarTone.FRIENDLY,
        recommended_avatar_ids=["avatar_001", "avatar_002"],
        recommended_background_ids=["bg_003", "bg_004"],
        description="美食推荐温馨风格"
    ),

    # 母婴
    AvatarMatchRule(
        industry=IndustryCategory.MOTHER_BABY,
        tone=AvatarTone.WARM,
        recommended_avatar_ids=["avatar_002", "avatar_008"],
        recommended_background_ids=["bg_003", "bg_001"],
        description="母婴类推荐温暖亲切形象"
    ),

    # 家居生活
    AvatarMatchRule(
        industry=IndustryCategory.LIFE,
        tone=AvatarTone.FRIENDLY,
        recommended_avatar_ids=["avatar_001", "avatar_002"],
        recommended_background_ids=["bg_003"],
        description="家居生活推荐舒适自然风格"
    ),

    # 健身
    AvatarMatchRule(
        industry=IndustryCategory.FITNESS,
        tone=AvatarTone.LIVELY,
        recommended_avatar_ids=["avatar_006", "avatar_003"],
        recommended_background_ids=["bg_004", "bg_006"],
        description="健身运动推荐活力专业形象"
    ),

    # 旅游
    AvatarMatchRule(
        industry=IndustryCategory.TRAVEL,
        tone=AvatarTone.FRIENDLY,
        recommended_avatar_ids=["avatar_001", "avatar_005"],
        recommended_background_ids=["bg_004", "bg_006"],
        description="旅游推荐清新自然风格"
    ),
]


# 背景匹配映射
BACKGROUND_MATCH_MAP = {
    IndustryCategory.BEAUTY: ["bg_001", "bg_005", "bg_003"],
    IndustryCategory.KNOWLEDGE: ["bg_001", "bg_002", "bg_006"],
    IndustryCategory.ECOMMERCE: ["bg_005", "bg_001", "bg_006"],
    IndustryCategory.FOOD: ["bg_003", "bg_004"],
    IndustryCategory.MOTHER_BABY: ["bg_003", "bg_001"],
    IndustryCategory.LIFE: ["bg_003", "bg_006"],
    IndustryCategory.FITNESS: ["bg_004", "bg_006"],
    IndustryCategory.TRAVEL: ["bg_004", "bg_006"],
}


@dataclass
class AvatarMatcherConfig:
    """匹配器配置"""
    default_avatar_id: str = "avatar_001"
    default_background_id: str = "bg_001"


class AvatarMatcher:
    """
    形象/背景自动匹配器

    根据行业/场景自动推荐数字人和背景
    """

    def __init__(self, config: Optional[AvatarMatcherConfig] = None):
        self.config = config or AvatarMatcherConfig()
        self._rules = AVATAR_MATCH_RULES
        self._bg_map = BACKGROUND_MATCH_MAP

    def match(
        self,
        industry: str = None,
        tone: str = None,
        content_keywords: List[str] = None
    ) -> AvatarMatchResult:
        """
        智能匹配数字人和背景

        Args:
            industry: 行业分类 (beauty/knowledge/ecommerce/food/mother_baby/life/fitness/travel)
            tone: 语气风格 (friendly/professional/lively/steady)
            content_keywords: 内容关键词（用于辅助判断）

        Returns:
            AvatarMatchResult: 匹配结果
        """
        content_keywords = content_keywords or []

        # 1. 通过行业和语气匹配
        if industry:
            industry_enum = self._str_to_industry(industry)
            tone_enum = self._str_to_tone(tone) if tone else None

            for rule in self._rules:
                if rule.industry == industry_enum:
                    if tone_enum is None or rule.tone == tone_enum:
                        return self._build_match_result(rule, content_keywords)

        # 2. 通过关键词推断行业
        if content_keywords:
            inferred_industry = self._infer_industry(content_keywords)
            inferred_tone = self._infer_tone(content_keywords)

            for rule in self._rules:
                if rule.industry == inferred_industry:
                    if inferred_tone is None or rule.tone == inferred_tone:
                        return self._build_match_result(rule, content_keywords)

        # 3. 默认匹配
        return self._default_match()

    def _build_match_result(
        self,
        rule: AvatarMatchRule,
        keywords: List[str]
    ) -> AvatarMatchResult:
        """构建匹配结果"""
        import random

        avatar_id = random.choice(rule.recommended_avatar_ids)
        background_id = random.choice(rule.recommended_background_ids)

        # 获取名称（简化，实际应查表）
        avatar_name = self._get_avatar_name(avatar_id)
        background_name = self._get_background_name(background_id)

        return AvatarMatchResult(
            avatar_id=avatar_id,
            avatar_name=avatar_name,
            background_id=background_id,
            background_name=background_name,
            confidence=0.85,
            reason=rule.description
        )

    def _default_match(self) -> AvatarMatchResult:
        """默认匹配"""
        return AvatarMatchResult(
            avatar_id=self.config.default_avatar_id,
            avatar_name="小美",
            background_id=self.config.default_background_id,
            background_name="演播室",
            confidence=0.5,
            reason="使用默认配置"
        )

    def _str_to_industry(self, s: str) -> IndustryCategory:
        """字符串转行业枚举"""
        mapping = {
            "beauty": IndustryCategory.BEAUTY,
            "美妆": IndustryCategory.BEAUTY,
            "knowledge": IndustryCategory.KNOWLEDGE,
            "知识": IndustryCategory.KNOWLEDGE,
            "ecommerce": IndustryCategory.ECOMMERCE,
            "电商": IndustryCategory.ECOMMERCE,
            "food": IndustryCategory.FOOD,
            "美食": IndustryCategory.FOOD,
            "mother_baby": IndustryCategory.MOTHER_BABY,
            "母婴": IndustryCategory.MOTHER_BABY,
            "life": IndustryCategory.LIFE,
            "家居": IndustryCategory.LIFE,
            "fitness": IndustryCategory.FITNESS,
            "健身": IndustryCategory.FITNESS,
            "travel": IndustryCategory.TRAVEL,
            "旅游": IndustryCategory.TRAVEL,
        }
        return mapping.get(s.lower(), IndustryCategory.ECOMMERCE)

    def _str_to_tone(self, s: str) -> AvatarTone:
        """字符串转语气枚举"""
        mapping = {
            "friendly": AvatarTone.FRIENDLY,
            "亲切": AvatarTone.FRIENDLY,
            "professional": AvatarTone.PROFESSIONAL,
            "专业": AvatarTone.PROFESSIONAL,
            "lively": AvatarTone.LIVELY,
            "活泼": AvatarTone.LIVELY,
            "steady": AvatarTone.STEADY,
            "沉稳": AvatarTone.STEADY,
        }
        return mapping.get(s.lower(), AvatarTone.FRIENDLY)

    def _infer_industry(self, keywords: List[str]) -> IndustryCategory:
        """通过关键词推断行业"""
        keyword_text = " ".join(keywords).lower()

        industry_signals = {
            IndustryCategory.BEAUTY: ["美妆", "口红", "护肤", "化妆", "粉底", "眼影"],
            IndustryCategory.KNOWLEDGE: ["知识", "教程", "讲解", "揭秘", "分析", "干货"],
            IndustryCategory.ECOMMERCE: ["推荐", "购买", "链接", "上车", "种草", "好物"],
            IndustryCategory.FOOD: ["美食", "食谱", "做饭", "吃播", "探店", "餐厅"],
            IndustryCategory.MOTHER_BABY: ["宝宝", "育儿", "辅食", "带娃", "妈妈"],
            IndustryCategory.LIFE: ["家居", "收纳", "好物", "生活", "卧室", "客厅"],
            IndustryCategory.FITNESS: ["健身", "减脂", "增肌", "运动", "训练", "瑜伽"],
            IndustryCategory.TRAVEL: ["旅游", "旅行", "打卡", "攻略", "目的地", "风景"],
        }

        for industry, signals in industry_signals.items():
            if any(s in keyword_text for s in signals):
                return industry

        return IndustryCategory.ECOMMERCE

    def _infer_tone(self, keywords: List[str]) -> AvatarTone:
        """通过关键词推断语气"""
        keyword_text = " ".join(keywords).lower()

        tone_signals = {
            AvatarTone.LIVELY: ["推荐", "必看", "超", "太", "绝", "冲", "种草"],
            AvatarTone.PROFESSIONAL: ["分析", "揭秘", "原理", "讲解", "专业"],
            AvatarTone.FRIENDLY: ["分享", "喜欢", "觉得", "感觉", "大家"],
            AvatarTone.STEADY: ["注意", "提醒", "千万", "一定", "必须"],
        }

        for tone, signals in tone_signals.items():
            if any(s in keyword_text for s in signals):
                return tone

        return AvatarTone.FRIENDLY

    def _get_avatar_name(self, avatar_id: str) -> str:
        """获取数字人名称"""
        names = {
            "avatar_001": "小美",
            "avatar_002": "小雅",
            "avatar_003": "小帅",
            "avatar_004": "老王",
            "avatar_005": "阿娜",
            "avatar_006": "健身教练",
            "avatar_007": "商务精英",
            "avatar_008": "主播小雪",
        }
        return names.get(avatar_id, "未知")

    def _get_background_name(self, background_id: str) -> str:
        """获取背景名称"""
        names = {
            "bg_001": "演播室",
            "bg_002": "办公室",
            "bg_003": "客厅",
            "bg_004": "户外风景",
            "bg_005": "商品展示",
            "bg_006": "抽象背景",
        }
        return names.get(background_id, "未知")


# 全局实例
_matcher: Optional[AvatarMatcher] = None


def get_avatar_matcher(config: Optional[AvatarMatcherConfig] = None) -> AvatarMatcher:
    """获取匹配器实例"""
    global _matcher
    if _matcher is None or config is not None:
        _matcher = AvatarMatcher(config)
    return _matcher