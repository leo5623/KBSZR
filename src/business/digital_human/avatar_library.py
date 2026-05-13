"""数字人库管理 - 公版 + 自定义创建"""
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

from loguru import logger

from src.business.digital_human.aliyun_client import (
    AvatarInfo,
    ALIYUN_PUBLIC_AVATARS
)


class AvatarSource(Enum):
    """数字人来源"""
    PUBLIC = "public"           # 公版
    CUSTOM = "custom"          # 自定义创建
    CLONED = "cloned"          # 克隆（未来）


@dataclass
class AvatarLibraryItem:
    """数字人库项"""
    avatar_id: str
    name: str
    source: AvatarSource
    category: str
    gender: str = ""
    preview_url: str = ""
    thumbnail_url: str = ""
    description: str = ""
    is_favorite: bool = False
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0       # 使用次数
    created_at: str = ""       # 创建时间
    metadata: Dict = field(default_factory=dict)  # 其他元数据


@dataclass
class AvatarLibraryConfig:
    """数字人库配置"""
    library_path: str = "./data/avatars"  # 数字人库存储路径
    enable_custom: bool = True           # 允许自定义
    max_custom_count: int = 50          # 最大自定义数量


class AvatarLibraryManager:
    """
    数字人库管理器

    功能：
    1. 管理公版数字人
    2. 管理自定义数字人
    3. 数字人收藏
    4. 使用统计
    """

    # 分类映射
    CATEGORY_MAP = {
        "女生": "女性形象",
        "男生": "男性形象",
        "综合": "通用形象",
        "民族风": "民族风格",
        "健身": "健身运动",
        "商务": "商务正装",
    }

    def __init__(self, config: Optional[AvatarLibraryConfig] = None):
        self.config = config or AvatarLibraryConfig()
        self._public_avatars: Dict[str, AvatarLibraryItem] = {}
        self._custom_avatars: Dict[str, AvatarLibraryItem] = {}
        self._favorites: set = set()
        self._load_library()

    def _load_library(self):
        """加载数字人库"""
        # 加载公版
        for avatar in ALIYUN_PUBLIC_AVATARS:
            item = AvatarLibraryItem(
                avatar_id=avatar.avatar_id,
                name=avatar.name,
                source=AvatarSource.PUBLIC,
                category=avatar.category,
                gender=avatar.gender,
                preview_url=avatar.preview_url,
                description=avatar.description
            )
            self._public_avatars[avatar.avatar_id] = item

        # 加载自定义
        self._load_custom_avatars()

        logger.info(f"数字人库加载完成: 公版 {len(self._public_avatars)} 个, 自定义 {len(self._custom_avatars)} 个")

    def _load_custom_avatars(self):
        """加载自定义数字人"""
        library_file = os.path.join(self.config.library_path, "custom_avatars.json")
        if os.path.exists(library_file):
            try:
                with open(library_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item_data in data:
                        item = AvatarLibraryItem(**item_data)
                        self._custom_avatars[item.avatar_id] = item
            except Exception as e:
                logger.error(f"加载自定义数字人失败: {e}")

    def _save_custom_avatars(self):
        """保存自定义数字人"""
        os.makedirs(self.config.library_path, exist_ok=True)
        library_file = os.path.join(self.config.library_path, "custom_avatars.json")

        try:
            with open(library_file, "w", encoding="utf-8") as f:
                data = [
                    {
                        **vars(item),
                        "tags": item.tags,
                        "metadata": item.metadata
                    }
                    for item in self._custom_avatars.values()
                ]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存自定义数字人失败: {e}")

    def list_avatars(
        self,
        source: AvatarSource = None,
        category: str = None,
        search_keyword: str = None,
        only_favorites: bool = False
    ) -> List[AvatarLibraryItem]:
        """
        获取数字人列表

        Args:
            source: 来源过滤
            category: 分类过滤
            search_keyword: 搜索关键词
            only_favorites: 只显示收藏

        Returns:
            List[AvatarLibraryItem]
        """
        all_avatars = []

        # 根据来源选择
        if source == AvatarSource.PUBLIC or source is None:
            all_avatars.extend(self._public_avatars.values())
        if source == AvatarSource.CUSTOM or source is None:
            all_avatars.extend(self._custom_avatars.values())

        # 收藏过滤
        if only_favorites:
            all_avatars = [a for a in all_avatars if a.avatar_id in self._favorites]

        # 分类过滤
        if category:
            all_avatars = [a for a in all_avatars if a.category == category]

        # 关键词搜索
        if search_keyword:
            keyword = search_keyword.lower()
            all_avatars = [
                a for a in all_avatars
                if (keyword in a.name.lower() or
                    keyword in a.description.lower() or
                    any(keyword in tag.lower() for tag in a.tags))
            ]

        return all_avatars

    def get_avatar(self, avatar_id: str) -> Optional[AvatarLibraryItem]:
        """获取数字人信息"""
        if avatar_id in self._public_avatars:
            return self._public_avatars[avatar_id]
        if avatar_id in self._custom_avatars:
            return self._custom_avatars[avatar_id]
        return None

    def add_custom_avatar(self, avatar: AvatarLibraryItem) -> bool:
        """
        添加自定义数字人

        未来支持：上传照片/视频训练自定义数字人
        """
        if len(self._custom_avatars) >= self.config.max_custom_count:
            logger.warning(f"自定义数字人数量已达上限: {self.config.max_custom_count}")
            return False

        avatar.source = AvatarSource.CUSTOM
        self._custom_avatars[avatar.avatar_id] = avatar
        self._save_custom_avatars()

        logger.info(f"添加自定义数字人: {avatar.name} ({avatar.avatar_id})")
        return True

    def remove_custom_avatar(self, avatar_id: str) -> bool:
        """移除自定义数字人"""
        if avatar_id not in self._custom_avatars:
            return False

        del self._custom_avatars[avatar_id]
        self._favorites.discard(avatar_id)
        self._save_custom_avatars()

        logger.info(f"移除自定义数字人: {avatar_id}")
        return True

    def toggle_favorite(self, avatar_id: str) -> bool:
        """切换收藏状态"""
        if avatar_id in self._favorites:
            self._favorites.discard(avatar_id)
            favorite = False
        else:
            self._favorites.add(avatar_id)
            favorite = True

        # 更新数字人的收藏状态
        if avatar_id in self._public_avatars:
            self._public_avatars[avatar_id].is_favorite = favorite
        if avatar_id in self._custom_avatars:
            self._custom_avatars[avatar_id].is_favorite = favorite

        return favorite

    def record_usage(self, avatar_id: str):
        """记录使用"""
        if avatar_id in self._public_avatars:
            self._public_avatars[avatar_id].usage_count += 1
        if avatar_id in self._custom_avatars:
            self._custom_avatars[avatar_id].usage_count += 1

    def get_categories(self) -> List[Dict]:
        """获取所有分类"""
        categories = set()

        for avatar in self._public_avatars.values():
            categories.add(avatar.category)
        for avatar in self._custom_avatars.values():
            categories.add(avatar.category)

        return [
            {"id": cat, "name": self.CATEGORY_MAP.get(cat, cat)}
            for cat in sorted(categories)
        ]

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        public_count = len(self._public_avatars)
        custom_count = len(self._custom_avatars)
        favorite_count = len(self._favorites)

        # 使用最多的数字人
        all_avatars = list(self._public_avatars.values()) + list(self._custom_avatars.values())
        if all_avatars:
            most_used = max(all_avatars, key=lambda a: a.usage_count)
            most_used_info = {"id": most_used.avatar_id, "name": most_used.name, "count": most_used.usage_count}
        else:
            most_used_info = None

        return {
            "public_count": public_count,
            "custom_count": custom_count,
            "total_count": public_count + custom_count,
            "favorite_count": favorite_count,
            "most_used": most_used_info
        }


# 全局实例
_avatar_library: Optional[AvatarLibraryManager] = None


def get_avatar_library(config: Optional[AvatarLibraryConfig] = None) -> AvatarLibraryManager:
    """获取数字人库管理器"""
    global _avatar_library
    if _avatar_library is None or config is not None:
        _avatar_library = AvatarLibraryManager(config)
    return _avatar_library