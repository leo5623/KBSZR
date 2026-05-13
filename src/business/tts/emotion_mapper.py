"""情绪分级 TTS - 情绪→TTS参数映射"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from loguru import logger


class TextEmotion(Enum):
    """文本情绪分类"""
    EXCITED = "excited"      # 兴奋 - 语速快、音调高
    CALM = "calm"            # 平静 - 语速中等、音调平稳
    SERIOUS = "serious"      # 严肃 - 语速慢、音调低
    WARM = "warm"            # 温暖 - 语速中等、音调柔和


@dataclass
class TTSParams:
    """TTS 参数"""
    speed: float = 1.0       # 语速 0.5-2.0
    pitch: float = 1.0      # 音调 0.5-2.0
    volume: float = 1.0      # 音量 0.5-2.0
    voice_id: str = ""      # 音色 ID


# 情绪到 TTS 参数的映射
EMOTION_TTS_PARAMS: Dict[TextEmotion, TTSParams] = {
    TextEmotion.EXCITED: TTSParams(speed=1.2, pitch=1.1, volume=1.0),    # 兴奋
    TextEmotion.CALM: TTSParams(speed=1.0, pitch=1.0, volume=0.9),       # 平静
    TextEmotion.SERIOUS: TTSParams(speed=0.85, pitch=0.95, volume=1.1),   # 严肃
    TextEmotion.WARM: TTSParams(speed=1.0, pitch=1.05, volume=0.95),     # 温暖
}


@dataclass
class VoicePreset:
    """音色预设"""
    voice_id: str
    name: str
    provider: str  # aliyun / volcengine / spark / minimax
    language: str = "zh"
    suitable_emotions: List[TextEmotion] = field(default_factory=list)
    description: str = ""


# 公版音色预设
PUBLIC_VOICE_PRESETS: List[VoicePreset] = [
    # 阿里云 TTS
    VoicePreset("xiaoyun", "亲和女声", "aliyun", "zh",
                [TextEmotion.CALM, TextEmotion.WARM], "温柔亲切，适合日常内容"),
    VoicePreset("xiaogang", "成熟男声", "aliyun", "zh",
                [TextEmotion.SERIOUS], "低沉稳重，适合知识讲解"),
    VoicePreset("aiqi", "活泼女声", "aliyun", "zh",
                [TextEmotion.EXCITED], "活泼开朗，适合种草推荐"),
    VoicePreset("aiya", "甜美女声", "aliyun", "zh",
                [TextEmotion.WARM], "甜美柔和，适合母婴美妆"),

    # 火山引擎 TTS
    VoicePreset("BV001_streaming", "新闻主播", "volcengine", "zh",
                [TextEmotion.SERIOUS], "字正腔圆，适合新闻资讯"),
    VoicePreset("BV002_streaming", "情感女声", "volcengine", "zh",
                [TextEmotion.WARM, TextEmotion.CALM], "情感丰富，适合故事讲述"),
    VoicePreset("BV003_streaming", "活力男声", "volcengine", "zh",
                [TextEmotion.EXCITED], "充满活力，适合营销推广"),

    # MiniMax TTS (海螺AI)
    VoicePreset("speech-01", "海螺女声", "minimax", "zh",
                [TextEmotion.CALM, TextEmotion.WARM], "自然流畅，情感真实"),
    VoicePreset("speech-02", "海螺男声", "minimax", "zh",
                [TextEmotion.SERIOUS, TextEmotion.CALM], "成熟稳重，专业感强"),
]


@dataclass
class EmotionMapperConfig:
    """情绪映射器配置"""
    default_emotion: TextEmotion = TextEmotion.CALM
    custom_emotion_params: Dict[TextEmotion, TTSParams] = field(default_factory=dict)


class EmotionTTSMapper:
    """
    情绪分级 TTS 映射器

    功能：
    1. 根据文本情绪自动映射 TTS 参数（语速、音调、音量）
    2. 管理公版音色预设
    3. 支持自定义音色
    """

    def __init__(self, config: Optional[EmotionMapperConfig] = None):
        self.config = config or EmotionMapperConfig()
        self._voice_presets: Dict[str, VoicePreset] = {
            v.voice_id: v for v in PUBLIC_VOICE_PRESETS
        }
        self._custom_voices: Dict[str, VoicePreset] = {}

    def get_tts_params(self, emotion: TextEmotion, voice_id: str = None) -> TTSParams:
        """
        获取 TTS 参数

        Args:
            emotion: 文本情绪
            voice_id: 可选的音色 ID

        Returns:
            TTSParams: TTS 参数
        """
        # 优先使用自定义配置
        if emotion in self.config.custom_emotion_params:
            params = self.config.custom_emotion_params[emotion]
        else:
            params = EMOTION_TTS_PARAMS.get(emotion, EMOTION_TTS_PARAMS[TextEmotion.CALM])

        # 设置音色
        if voice_id and voice_id in self._voice_presets:
            params.voice_id = voice_id
        elif voice_id and voice_id in self._custom_voices:
            params.voice_id = voice_id

        return params

    def map_emotion_to_tts(
        self,
        text: str,
        voice_id: str = None
    ) -> tuple[TextEmotion, TTSParams]:
        """
        分析文本情绪并映射 TTS 参数

        Args:
            text: 文本内容
            voice_id: 可选的音色 ID

        Returns:
            (TextEmotion, TTSParams): 情绪和 TTS 参数
        """
        emotion = self._analyze_emotion(text)
        params = self.get_tts_params(emotion, voice_id)
        return emotion, params

    def _analyze_emotion(self, text: str) -> TextEmotion:
        """
        分析文本情绪

        简单规则匹配，实际可用 LLM 更准确
        """
        # 感叹号密度
        exclaim_count = text.count("！") + text.count("!")

        # 问号密度
        question_count = text.count("？") + text.count("?")

        # 表情符号
        has_emoji = any(c in text for c in ["😊", "😍", "🤩", "🎉", "💖"])

        # 积极词汇
        positive_words = ["推荐", "喜欢", "太棒了", "绝绝子", "冲", "种草", "安利"]
        positive_count = sum(1 for w in positive_words if w in text)

        # 消极词汇
        negative_words = ["注意", "警告", "千万别", "踩雷", "避坑"]
        negative_count = sum(1 for w in negative_words if w in text)

        # 专业词汇
        professional_words = ["分析", "讲解", "揭秘", "真相", "原理"]
        professional_count = sum(1 for w in professional_words if w in text)

        # 情感分析规则
        if exclaim_count >= 2 or positive_count >= 2 or has_emoji:
            return TextEmotion.EXCITED
        elif professional_count >= 2:
            return TextEmotion.SERIOUS
        elif question_count >= 2:
            return TextEmotion.SERIOUS
        elif negative_count >= 1:
            return TextEmotion.SERIOUS
        elif positive_count >= 1:
            return TextEmotion.WARM
        else:
            return TextEmotion.CALM

    def get_voice_presets(
        self,
        provider: str = None,
        emotion: TextEmotion = None
    ) -> List[VoicePreset]:
        """
        获取音色预设列表

        Args:
            provider: 可选的提供商过滤
            emotion: 可选的情绪过滤

        Returns:
            List[VoicePreset]: 音色预设列表
        """
        all_voices = list(self._voice_presets.values()) + list(self._custom_voices.values())

        if provider:
            all_voices = [v for v in all_voices if v.provider == provider]

        if emotion:
            all_voices = [v for v in all_voices if emotion in v.suitable_emotions]

        return all_voices

    def add_custom_voice(self, voice: VoicePreset):
        """添加自定义音色"""
        self._custom_voices[voice.voice_id] = voice
        logger.info(f"添加自定义音色: {voice.name} ({voice.voice_id})")

    def remove_custom_voice(self, voice_id: str):
        """移除自定义音色"""
        if voice_id in self._custom_voices:
            del self._custom_voices[voice_id]
            logger.info(f"移除自定义音色: {voice_id}")

    def set_custom_emotion_params(
        self,
        emotion: TextEmotion,
        params: TTSParams
    ):
        """设置自定义情绪参数"""
        self.config.custom_emotion_params[emotion] = params
        logger.info(f"设置自定义情绪参数: {emotion.value} -> speed={params.speed}")


# 全局实例
_mapper: Optional[EmotionTTSMapper] = None


def get_emotion_mapper(config: Optional[EmotionMapperConfig] = None) -> EmotionTTSMapper:
    """获取情绪映射器实例"""
    global _mapper
    if _mapper is None or config is not None:
        _mapper = EmotionTTSMapper(config)
    return _mapper