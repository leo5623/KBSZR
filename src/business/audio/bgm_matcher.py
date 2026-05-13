"""BGM 自动匹配"""
import os
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from loguru import logger


@dataclass
class BGMTrack:
    """BGM 音轨"""
    id: str
    name: str
    file_path: str
    emotion: str  # excited / calm / serious / warm
    genre: str     # 风格分类
    duration: float  # 时长（秒）
    bpm: int = 0      # 节拍
    description: str = ""


@dataclass
class BGMMatchResult:
    """BGM 匹配结果"""
    bgm: Optional[BGMTrack]
    is_found: bool
    fallback_bgm: Optional[BGMTrack] = None


@dataclass
class BGMMatcherConfig:
    """BGM 匹配器配置"""
    bgm_library_path: str = "./assets/bgm"  # BGM 库路径
    default_volume: float = 0.3  # 默认音量 30%


class BGMMatcher:
    """
    BGM 自动匹配器

    根据情绪/场景自动匹配背景音乐
    """

    # 情绪到 BGM 风格的映射
    EMOTION_BGM_MAP = {
        "excited": ["energetic", "upbeat", "positive", "激励", "欢快"],
        "calm": ["ambient", "peaceful", "relaxing", "轻音乐", "舒缓"],
        "serious": ["cinematic", "dramatic", "corporate", "庄重", "纪录片"],
        "warm": ["heartwarming", "romantic", "acoustic", "温馨", "柔情"],
    }

    # 各平台适合的 BGM 风格
    PLATFORM_BGM_MAP = {
        "douyin": {"style": "short_form", "preferred_length": "15-60s"},
        "kuaishou": {"style": "short_form", "preferred_length": "15-60s"},
        "xiaohongshu": {"style": "aesthetic", "preferred_length": "30-120s"},
        "weixin": {"style": "formal", "preferred_length": "60-180s"},
    }

    def __init__(self, config: Optional[BGMMatcherConfig] = None):
        self.config = config or BGMMatcherConfig()
        self._bgm_library: Dict[str, List[BGMTrack]] = {}
        self._load_bgm_library()

    def _load_bgm_library(self):
        """加载 BGM 库"""
        # 如果路径存在，扫描加载
        if os.path.exists(self.config.bgm_library_path):
            for root, dirs, files in os.walk(self.config.bgm_library_path):
                for file in files:
                    if file.endswith((".mp3", ".wav", ".ogg", ".m4a")):
                        emotion = self._detect_bgm_emotion(file)
                        genre = self._detect_bgm_genre(file)

                        track = BGMTrack(
                            id=file,
                            name=os.path.splitext(file)[0],
                            file_path=os.path.join(root, file),
                            emotion=emotion,
                            genre=genre,
                            duration=0.0  # 实际应读取文件获取
                        )

                        if emotion not in self._bgm_library:
                            self._bgm_library[emotion] = []
                        self._bgm_library[emotion].append(track)
        else:
            # 使用内置示例 BGM（实际项目中应放在 assets 目录）
            self._init_builtin_bgm()

    def _init_builtin_bgm(self):
        """初始化内置 BGM（示例数据）"""
        builtin_bgm = [
            BGMTrack("bgm_excited_01", "活力满满", "", "excited", "energetic", 60,
                     120, "充满活力的背景音乐"),
            BGMTrack("bgm_excited_02", "激情澎湃", "", "excited", "upbeat", 45,
                     128, "激动人心的背景音乐"),
            BGMTrack("bgm_calm_01", "宁静时光", "", "calm", "ambient", 90,
                     70, "平静舒缓的背景音乐"),
            BGMTrack("bgm_calm_02", "轻风细雨", "", "calm", "relaxing", 120,
                     65, "轻柔放松的背景音乐"),
            BGMTrack("bgm_serious_01", "纪录片", "", "serious", "cinematic", 180,
                     80, "庄重正式的背景音乐"),
            BGMTrack("bgm_serious_02", "新闻配乐", "", "serious", "corporate", 120,
                     75, "新闻播报背景音乐"),
            BGMTrack("bgm_warm_01", "温暖时光", "", "warm", "heartwarming", 90,
                     85, "温馨感人的背景音乐"),
            BGMTrack("bgm_warm_02", "浪漫时刻", "", "warm", "romantic", 75,
                     90, "浪漫温馨的背景音乐"),
        ]

        for bgm in builtin_bgm:
            if bgm.emotion not in self._bgm_library:
                self._bgm_library[bgm.emotion] = []
            self._bgm_library[bgm.emotion].append(bgm)

        logger.info(f"初始化内置 BGM 库，共 {len(builtin_bgm)} 首")

    def _detect_bgm_emotion(self, filename: str) -> str:
        """根据文件名检测 BGM 情绪"""
        filename_lower = filename.lower()

        if any(k in filename_lower for k in ["excited", "energetic", "upbeat", "激励", "欢快"]):
            return "excited"
        elif any(k in filename_lower for k in ["calm", "relaxing", "peaceful", "舒缓", "轻"]):
            return "calm"
        elif any(k in filename_lower for k in ["serious", "cinematic", "dramatic", "庄重"]):
            return "serious"
        elif any(k in filename_lower for k in ["warm", "romantic", "温馨", "柔情"]):
            return "warm"

        return "calm"  # 默认平静

    def _detect_bgm_genre(self, filename: str) -> str:
        """根据文件名检测 BGM 风格"""
        filename_lower = filename.lower()

        if "energetic" in filename_lower or "upbeat" in filename_lower:
            return "energetic"
        elif "ambient" in filename_lower or "relaxing" in filename_lower:
            return "ambient"
        elif "cinematic" in filename_lower or "dramatic" in filename_lower:
            return "cinematic"
        elif "corporate" in filename_lower:
            return "corporate"
        elif "heartwarming" in filename_lower or "romantic" in filename_lower:
            return "heartwarming"

        return "general"

    def match(
        self,
        emotion: str,
        duration: float = None,
        platform: str = None,
        genre: str = None
    ) -> BGMMatchResult:
        """
        匹配 BGM

        Args:
            emotion: 情绪类型 (excited / calm / serious / warm)
            duration: 目标时长（秒）
            platform: 目标平台
            genre: 风格偏好

        Returns:
            BGMMatchResult: 匹配结果
        """
        # 获取该情绪的 BGM 列表
        bgm_list = self._bgm_library.get(emotion, [])

        if not bgm_list:
            # 降级到 calm
            bgm_list = self._bgm_library.get("calm", [])

        if not bgm_list:
            return BGMMatchResult(bgm=None, is_found=False)

        # 根据时长筛选
        if duration:
            bgm_list = [b for b in bgm_list if b.duration >= duration * 0.8]

        # 根据风格筛选
        if genre:
            bgm_list = [b for b in bgm_list if b.genre == genre]

        # 随机选择一首
        if bgm_list:
            selected = random.choice(bgm_list)
            return BGMMatchResult(bgm=selected, is_found=True)
        else:
            return BGMMatchResult(bgm=None, is_found=False)

    def get_bgm_by_emotion(self, emotion: str) -> List[BGMTrack]:
        """获取指定情绪的所有 BGM"""
        return self._bgm_library.get(emotion, [])

    def get_all_bgm(self) -> List[BGMTrack]:
        """获取所有 BGM"""
        all_bgm = []
        for bgm_list in self._bgm_library.values():
            all_bgm.extend(bgm_list)
        return all_bgm

    def search_bgm(self, keyword: str) -> List[BGMTrack]:
        """搜索 BGM"""
        results = []
        keyword_lower = keyword.lower()

        for bgm_list in self._bgm_library.values():
            for bgm in bgm_list:
                if (keyword_lower in bgm.name.lower() or
                    keyword_lower in bgm.description.lower() or
                    keyword_lower in bgm.genre.lower()):
                    results.append(bgm)

        return results


# 全局实例
_matcher: Optional[BGMMatcher] = None


def get_bgm_matcher(config: Optional[BGMMatcherConfig] = None) -> BGMMatcher:
    """获取 BGM 匹配器实例"""
    global _matcher
    if _matcher is None or config is not None:
        _matcher = BGMMatcher(config)
    return _matcher