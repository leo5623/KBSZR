"""成品自动归档"""
import json
import os
import shutil
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from loguru import logger


@dataclass
class VideoMetadata:
    """视频元数据"""
    video_id: str
    video_path: str
    title: str
    category: str              # 内容分类
    account_id: str = ""       # 账号ID
    platform: str = ""         # 发布平台
    tags: List[str] = field(default_factory=list)
    duration: float = 0.0
    resolution: str = ""
    file_size: int = 0
    created_at: str = ""
    published_at: str = ""
    status: str = "draft"      # draft / published
    metadata: Dict = field(default_factory=dict)


@dataclass
class ArchiveEntry:
    """归档条目"""
    archive_id: str
    video_id: str
    archive_path: str
    archive_date: str
    category: str
    account_id: str
    platform: str


@dataclass
class ArchiveResult:
    """归档结果"""
    success: bool
    archive_id: str = ""
    archive_path: str = ""
    error_message: str = ""


@dataclass
class ArchiveManagerConfig:
    """归档管理器配置"""
    archive_base_path: str = "./archive"  # 归档根目录
    organize_by: str = "date"  # date / account / category
    auto_clean_days: int = 0   # 自动清理天数（0=不清理）


class ArchiveManager:
    """
    成品自动归档管理器

    功能：
    1. 按日期/账号/内容类型自动分类存储
    2. 归档记录管理
    3. 归档查询
    """

    def __init__(self, config: Optional[ArchiveManagerConfig] = None):
        self.config = config or ArchiveManagerConfig()
        self._archive_db_path = os.path.join(self.config.archive_base_path, "archive_db.json")
        self._archives: Dict[str, ArchiveEntry] = {}
        self._load_archive_db()

    def _load_archive_db(self):
        """加载归档数据库"""
        if os.path.exists(self._archive_db_path):
            try:
                with open(self._archive_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        entry = ArchiveEntry(**item)
                        self._archives[entry.archive_id] = entry
                logger.info(f"加载归档记录 {len(self._archives)} 条")
            except Exception as e:
                logger.error(f"加载归档数据库失败: {e}")

    def _save_archive_db(self):
        """保存归档数据库"""
        os.makedirs(self.config.archive_base_path, exist_ok=True)
        try:
            with open(self._archive_db_path, "w", encoding="utf-8") as f:
                data = [vars(a) for a in self._archives.values()]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存归档数据库失败: {e}")

    async def archive(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> ArchiveResult:
        """
        归档视频

        Args:
            video_path: 视频文件路径
            metadata: 视频元数据

        Returns:
            ArchiveResult: 归档结果
        """
        try:
            # 1. 生成归档ID
            archive_id = f"arc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{metadata.video_id}"

            # 2. 构建归档路径
            archive_path = self._build_archive_path(metadata)

            # 3. 复制/移动文件到归档目录
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
            shutil.copy2(video_path, archive_path)

            # 4. 创建归档条目
            entry = ArchiveEntry(
                archive_id=archive_id,
                video_id=metadata.video_id,
                archive_path=archive_path,
                archive_date=datetime.now().strftime("%Y-%m-%d"),
                category=metadata.category,
                account_id=metadata.account_id,
                platform=metadata.platform
            )
            self._archives[archive_id] = entry

            # 5. 保存元数据
            metadata_path = archive_path + ".meta.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(vars(metadata), f, ensure_ascii=False, indent=2)

            # 6. 保存归档数据库
            self._save_archive_db()

            logger.info(f"归档成功: {archive_id} -> {archive_path}")

            return ArchiveResult(
                success=True,
                archive_id=archive_id,
                archive_path=archive_path
            )

        except Exception as e:
            logger.error(f"归档失败: {e}")
            return ArchiveResult(success=False, error_message=str(e))

    def _build_archive_path(self, metadata: VideoMetadata) -> str:
        """构建归档路径"""
        if self.config.organize_by == "date":
            date_str = datetime.now().strftime("%Y-%m-%d")
            return os.path.join(
                self.config.archive_base_path,
                date_str,
                metadata.category,
                os.path.basename(metadata.video_path)
            )
        elif self.config.organize_by == "account":
            return os.path.join(
                self.config.archive_base_path,
                metadata.account_id or "unknown",
                metadata.category,
                os.path.basename(metadata.video_path)
            )
        elif self.config.organize_by == "category":
            return os.path.join(
                self.config.archive_base_path,
                metadata.category,
                os.path.basename(metadata.video_path)
            )
        else:
            # 默认按日期
            date_str = datetime.now().strftime("%Y-%m-%d")
            return os.path.join(
                self.config.archive_base_path,
                date_str,
                os.path.basename(metadata.video_path)
            )

    def list_archives(
        self,
        category: str = None,
        account_id: str = None,
        platform: str = None,
        date_from: str = None,
        date_to: str = None
    ) -> List[ArchiveEntry]:
        """
        查询归档记录

        Args:
            category: 分类过滤
            account_id: 账号过滤
            platform: 平台过滤
            date_from: 开始日期
            date_to: 结束日期

        Returns:
            List[ArchiveEntry]: 归档记录列表
        """
        results = list(self._archives.values())

        if category:
            results = [a for a in results if a.category == category]
        if account_id:
            results = [a for a in results if a.account_id == account_id]
        if platform:
            results = [a for a in results if a.platform == platform]
        if date_from:
            results = [a for a in results if a.archive_date >= date_from]
        if date_to:
            results = [a for a in results if a.archive_date <= date_to]

        return results

    def get_archive(self, archive_id: str) -> Optional[ArchiveEntry]:
        """获取归档记录"""
        return self._archives.get(archive_id)

    def delete_archive(self, archive_id: str, delete_file: bool = True) -> bool:
        """
        删除归档记录

        Args:
            archive_id: 归档ID
            delete_file: 是否同时删除文件
        """
        entry = self._archives.get(archive_id)
        if not entry:
            return False

        # 删除文件
        if delete_file and os.path.exists(entry.archive_path):
            os.remove(entry.archive_path)
            meta_path = entry.archive_path + ".meta.json"
            if os.path.exists(meta_path):
                os.remove(meta_path)

        # 删除记录
        del self._archives[archive_id]
        self._save_archive_db()

        logger.info(f"删除归档: {archive_id}")
        return True

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_count = len(self._archives)
        by_category: Dict[str, int] = {}
        by_platform: Dict[str, int] = {}
        by_date: Dict[str, int] = {}

        for entry in self._archives.values():
            by_category[entry.category] = by_category.get(entry.category, 0) + 1
            by_platform[entry.platform] = by_platform.get(entry.platform, 0) + 1
            by_date[entry.archive_date] = by_date.get(entry.archive_date, 0) + 1

        return {
            "total_count": total_count,
            "by_category": by_category,
            "by_platform": by_platform,
            "by_date": by_date
        }


# 全局实例
_archive_manager: Optional[ArchiveManager] = None


def get_archive_manager(config: Optional[ArchiveManagerConfig] = None) -> ArchiveManager:
    """获取归档管理器实例"""
    global _archive_manager
    if _archive_manager is None or config is not None:
        _archive_manager = ArchiveManager(config)
    return _archive_manager