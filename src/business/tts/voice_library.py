"""音色库管理 - 公版 + 克隆"""
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

from loguru import logger


class VoiceSource(Enum):
    """音色来源"""
    PUBLIC = "public"       # 公版
    CLONED = "cloned"       # 克隆音色


@dataclass
class VoiceLibraryItem:
    """音色库项"""
    voice_id: str
    name: str
    source: VoiceSource
    provider: str              # aliyun / volcengine / spark / minimax
    language: str = "zh"
    gender: str = ""           # male / female
    suitable_scenes: List[str] = field(default_factory=list)  # 适用场景
    suitable_emotions: List[str] = field(default_factory=list)  # 适用情绪
    preview_audio: str = ""    # 预览音频 URL
    description: str = ""
    is_favorite: bool = False
    usage_count: int = 0
    created_at: str = ""


@dataclass
class VoiceLibraryConfig:
    """音色库配置"""
    library_path: str = "./data/voices"  # 音色库存储路径
    enable_clone: bool = True           # 允许克隆
    max_clone_count: int = 20          # 最大克隆数量


# 公版音色预设
PUBLIC_VOICES = [
    # 阿里云 TTS
    VoiceLibraryItem(
        voice_id="xiaoyun",
        name="亲和女声",
        source=VoiceSource.PUBLIC,
        provider="aliyun",
        gender="female",
        suitable_scenes=["日常", "种草", "知识"],
        suitable_emotions=["calm", "warm"],
        description="温柔亲切，适合日常内容"
    ),
    VoiceLibraryItem(
        voice_id="xiaogang",
        name="成熟男声",
        source=VoiceSource.PUBLIC,
        provider="aliyun",
        gender="male",
        suitable_scenes=["知识", "商务", "新闻"],
        suitable_emotions=["serious", "calm"],
        description="低沉稳重，适合知识讲解"
    ),
    VoiceLibraryItem(
        voice_id="aiqi",
        name="活泼女声",
        source=VoiceSource.PUBLIC,
        provider="aliyun",
        gender="female",
        suitable_scenes=["种草", "好物", "娱乐"],
        suitable_emotions=["excited", "warm"],
        description="活泼开朗，适合种草推荐"
    ),
    VoiceLibraryItem(
        voice_id="aiya",
        name="甜美女声",
        source=VoiceSource.PUBLIC,
        provider="aliyun",
        gender="female",
        suitable_scenes=["美妆", "母婴", "生活"],
        suitable_emotions=["warm", "calm"],
        description="甜美柔和，适合母婴美妆"
    ),
    VoiceLibraryItem(
        voice_id="zhuli",
        name="知性女声",
        source=VoiceSource.PUBLIC,
        provider="aliyun",
        gender="female",
        suitable_scenes=["知识", "教程", "职场"],
        suitable_emotions=["calm", "serious"],
        description="知性大方，适合知识教程"
    ),

    # 火山引擎 TTS
    VoiceLibraryItem(
        voice_id="BV001_streaming",
        name="新闻主播",
        source=VoiceSource.PUBLIC,
        provider="volcengine",
        gender="male",
        suitable_scenes=["新闻", "资讯", "报道"],
        suitable_emotions=["serious"],
        description="字正腔圆，适合新闻资讯"
    ),
    VoiceLibraryItem(
        voice_id="BV002_streaming",
        name="情感女声",
        source=VoiceSource.PUBLIC,
        provider="volcengine",
        gender="female",
        suitable_scenes=["故事", "情感", "倾诉"],
        suitable_emotions=["warm", "calm"],
        description="情感丰富，适合故事讲述"
    ),
    VoiceLibraryItem(
        voice_id="BV003_streaming",
        name="活力男声",
        source=VoiceSource.PUBLIC,
        provider="volcengine",
        gender="male",
        suitable_scenes=["营销", "推广", "活动"],
        suitable_emotions=["excited"],
        description="充满活力，适合营销推广"
    ),

    # MiniMax TTS
    VoiceLibraryItem(
        voice_id="speech-01",
        name="海螺女声",
        source=VoiceSource.PUBLIC,
        provider="minimax",
        gender="female",
        suitable_scenes=["日常", "知识", "情感"],
        suitable_emotions=["calm", "warm", "serious"],
        description="自然流畅，情感真实"
    ),
    VoiceLibraryItem(
        voice_id="speech-02",
        name="海螺男声",
        source=VoiceSource.PUBLIC,
        provider="minimax",
        gender="male",
        suitable_scenes=["知识", "商务", "评论"],
        suitable_emotions=["serious", "calm"],
        description="成熟稳重，专业感强"
    ),

    # 讯飞 TTS
    VoiceLibraryItem(
        voice_id="xunfei_female",
        name="讯飞女声",
        source=VoiceSource.PUBLIC,
        provider="spark",
        gender="female",
        suitable_scenes=["助手", "导航", "客服"],
        suitable_emotions=["calm", "warm"],
        description="清晰自然，适合语音助手"
    ),
    VoiceLibraryItem(
        voice_id="xunfei_male",
        name="讯飞男声",
        source=VoiceSource.PUBLIC,
        provider="spark",
        gender="male",
        suitable_scenes=["播报", "讲解", "介绍"],
        suitable_emotions=["serious", "calm"],
        description="专业播报，适合内容讲解"
    ),
]


class VoiceLibraryManager:
    """
    音色库管理器

    功能：
    1. 管理公版音色
    2. 管理克隆音色
    3. 音色收藏
    4. 使用统计
    """

    def __init__(self, config: Optional[VoiceLibraryConfig] = None):
        self.config = config or VoiceLibraryConfig()
        self._public_voices: Dict[str, VoiceLibraryItem] = {}
        self._cloned_voices: Dict[str, VoiceLibraryItem] = {}
        self._favorites: set = set()
        self._load_library()

    def _load_library(self):
        """加载音色库"""
        # 加载公版
        for voice in PUBLIC_VOICES:
            self._public_voices[voice.voice_id] = voice

        # 加载克隆音色
        self._load_cloned_voices()

        logger.info(f"音色库加载完成: 公版 {len(self._public_voices)} 个, 克隆 {len(self._cloned_voices)} 个")

    def _load_cloned_voices(self):
        """加载克隆音色"""
        library_file = os.path.join(self.config.library_path, "cloned_voices.json")
        if os.path.exists(library_file):
            try:
                with open(library_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item_data in data:
                        item = VoiceLibraryItem(**item_data)
                        self._cloned_voices[item.voice_id] = item
            except Exception as e:
                logger.error(f"加载克隆音色失败: {e}")

    def _save_cloned_voices(self):
        """保存克隆音色"""
        os.makedirs(self.config.library_path, exist_ok=True)
        library_file = os.path.join(self.config.library_path, "cloned_voices.json")

        try:
            with open(library_file, "w", encoding="utf-8") as f:
                data = [
                    {
                        **vars(item),
                        "suitable_scenes": item.suitable_scenes,
                        "suitable_emotions": item.suitable_emotions
                    }
                    for item in self._cloned_voices.values()
                ]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存克隆音色失败: {e}")

    def list_voices(
        self,
        source: VoiceSource = None,
        provider: str = None,
        gender: str = None,
        emotion: str = None,
        search_keyword: str = None,
        only_favorites: bool = False
    ) -> List[VoiceLibraryItem]:
        """
        获取音色列表

        Args:
            source: 来源过滤
            provider: 提供商过滤
            gender: 性别过滤
            emotion: 情绪过滤
            search_keyword: 搜索关键词
            only_favorites: 只显示收藏

        Returns:
            List[VoiceLibraryItem]
        """
        all_voices = []

        if source == VoiceSource.PUBLIC or source is None:
            all_voices.extend(self._public_voices.values())
        if source == VoiceSource.CLONED or source is None:
            all_voices.extend(self._cloned_voices.values())

        # 收藏过滤
        if only_favorites:
            all_voices = [v for v in all_voices if v.voice_id in self._favorites]

        # 提供商过滤
        if provider:
            all_voices = [v for v in all_voices if v.provider == provider]

        # 性别过滤
        if gender:
            all_voices = [v for v in all_voices if v.gender == gender]

        # 情绪过滤
        if emotion:
            all_voices = [v for v in all_voices if emotion in v.suitable_emotions]

        # 关键词搜索
        if search_keyword:
            keyword = search_keyword.lower()
            all_voices = [
                v for v in all_voices
                if (keyword in v.name.lower() or
                    keyword in v.description.lower())
            ]

        return all_voices

    def get_voice(self, voice_id: str) -> Optional[VoiceLibraryItem]:
        """获取音色信息"""
        if voice_id in self._public_voices:
            return self._public_voices[voice_id]
        if voice_id in self._cloned_voices:
            return self._cloned_voices[voice_id]
        return None

    def add_cloned_voice(self, voice: VoiceLibraryItem) -> bool:
        """
        添加克隆音色

        Args:
            voice: 音色项（应包含 voice_id, name, provider 等）
        """
        if len(self._cloned_voices) >= self.config.max_clone_count:
            logger.warning(f"克隆音色数量已达上限: {self.config.max_clone_count}")
            return False

        voice.source = VoiceSource.CLONED
        self._cloned_voices[voice.voice_id] = voice
        self._save_cloned_voices()

        logger.info(f"添加克隆音色: {voice.name} ({voice.voice_id})")
        return True

    def remove_cloned_voice(self, voice_id: str) -> bool:
        """移除克隆音色"""
        if voice_id not in self._cloned_voices:
            return False

        del self._cloned_voices[voice_id]
        self._favorites.discard(voice_id)
        self._save_cloned_voices()

        logger.info(f"移除克隆音色: {voice_id}")
        return True

    def toggle_favorite(self, voice_id: str) -> bool:
        """切换收藏状态"""
        if voice_id in self._favorites:
            self._favorites.discard(voice_id)
            favorite = False
        else:
            self._favorites.add(voice_id)
            favorite = True

        # 更新音色的收藏状态
        if voice_id in self._public_voices:
            self._public_voices[voice_id].is_favorite = favorite
        if voice_id in self._cloned_voices:
            self._cloned_voices[voice_id].is_favorite = favorite

        return favorite

    def record_usage(self, voice_id: str):
        """记录使用"""
        if voice_id in self._public_voices:
            self._public_voices[voice_id].usage_count += 1
        if voice_id in self._cloned_voices:
            self._cloned_voices[voice_id].usage_count += 1

    def get_providers(self) -> List[Dict]:
        """获取所有提供商"""
        providers = set()

        for voice in self._public_voices.values():
            providers.add(voice.provider)
        for voice in self._cloned_voices.values():
            providers.add(voice.provider)

        provider_names = {
            "aliyun": "阿里云 TTS",
            "volcengine": "火山引擎 TTS",
            "minimax": "MiniMax TTS",
            "spark": "讯飞 TTS"
        }

        return [
            {"id": p, "name": provider_names.get(p, p)}
            for p in sorted(providers)
        ]

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        public_count = len(self._public_voices)
        cloned_count = len(self._cloned_voices)
        favorite_count = len(self._favorites)

        # 使用最多的音色
        all_voices = list(self._public_voices.values()) + list(self._cloned_voices.values())
        if all_voices:
            most_used = max(all_voices, key=lambda v: v.usage_count)
            most_used_info = {"id": most_used.voice_id, "name": most_used.name, "count": most_used.usage_count}
        else:
            most_used_info = None

        return {
            "public_count": public_count,
            "cloned_count": cloned_count,
            "total_count": public_count + cloned_count,
            "favorite_count": favorite_count,
            "most_used": most_used_info,
            "providers": self.get_providers()
        }


# 全局实例
_voice_library: Optional[VoiceLibraryManager] = None


def get_voice_library(config: Optional[VoiceLibraryConfig] = None) -> VoiceLibraryManager:
    """获取音色库管理器"""
    global _voice_library
    if _voice_library is None or config is not None:
        _voice_library = VoiceLibraryManager(config)
    return _voice_library