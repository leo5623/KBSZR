"""数字人路由 - 云端API"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

from loguru import logger

from src.business.digital_human.aliyun_client import (
    AliyunDigitalHuman,
    DigitalHumanResult,
    AvatarInfo,
    ALIYUN_PUBLIC_AVATARS
)


class DigitalHumanMode(Enum):
    """数字人模式"""
    CLOUD = "cloud"


@dataclass
class DigitalHumanConfig:
    """数字人配置"""
    mode: DigitalHumanMode = DigitalHumanMode.CLOUD
    provider: str = "aliyun"  # aliyun / tencent / volcengine

    # 阿里云配置
    aliyun_api_key: str = ""
    aliyun_region: str = "cn-shanghai"

    # 腾讯云配置
    tencent_api_key: str = ""
    tencent_region: str = "ap-guangzhou"

    # 火山引擎配置
    volcengine_api_key: str = ""
    volcengine_secret_key: str = ""


@dataclass
class DigitalHumanRequest:
    """数字人请求"""
    script: str
    avatar_id: str
    background_id: str = "bg_001"
    motion: str = "slight"
    aspect_ratio: str = "9:16"
    output_path: Optional[str] = None


@dataclass
class DigitalHumanResponse:
    """数字人响应"""
    success: bool
    video_path: str = ""
    video_url: str = ""
    duration: float = 0.0
    task_id: str = ""
    error: str = ""
    mode: str = ""
    provider: str = ""


@dataclass
class AvatarCategory:
    """形象分类"""
    id: str
    name: str
    avatars: List[AvatarInfo]


class AvatarManager:
    """数字人形象管理器"""

    def __init__(self):
        self._custom_avatars: Dict[str, AvatarInfo] = {}  # 自定义形象
        self._categories = self._build_default_categories()
        logger.info("AvatarManager initialized")

    def _build_default_categories(self) -> List[AvatarCategory]:
        """构建默认分类"""
        categories = {}

        for avatar in ALIYUN_PUBLIC_AVATARS:
            cat_id = avatar.category
            if cat_id not in categories:
                categories[cat_id] = AvatarCategory(
                    id=cat_id,
                    name=self._get_category_name(cat_id),
                    avatars=[]
                )
            categories[cat_id].avatars.append(avatar)

        return list(categories.values())

    def _get_category_name(self, cat_id: str) -> str:
        """获取分类名称"""
        names = {
            "综合": "综合",
            "女生": "女生",
            "男生": "男生",
            "民族风": "民族风",
            "健身": "健身",
            "商务": "商务"
        }
        return names.get(cat_id, cat_id)

    def list_categories(self) -> List[Dict[str, Any]]:
        """列出所有分类"""
        return [
            {"id": cat.id, "name": cat.name, "count": len(cat.avatars)}
            for cat in self._categories
        ]

    def list_avatars(self, category: Optional[str] = None) -> List[AvatarInfo]:
        """列出形象"""
        if category:
            for cat in self._categories:
                if cat.id == category:
                    return list(cat.avatars) + self._get_custom_by_category(category)
            return []
        else:
            avatars = list(ALIYUN_PUBLIC_AVATARS)
            avatars.extend(self._custom_avatars.values())
            return avatars

    def _get_custom_by_category(self, category: str) -> List[AvatarInfo]:
        """获取某个分类的自定义形象"""
        return [
            avatar for avatar in self._custom_avatars.values()
            if avatar.category == category
        ]

    def get_avatar(self, avatar_id: str) -> Optional[AvatarInfo]:
        """获取形象信息"""
        # 公版
        for avatar in ALIYUN_PUBLIC_AVATARS:
            if avatar.avatar_id == avatar_id:
                return avatar
        # 自定义
        if avatar_id in self._custom_avatars:
            return self._custom_avatars[avatar_id]
        return None

    def add_custom_avatar(self, avatar: AvatarInfo) -> bool:
        """
        添加自定义形象

        未来支持：用户上传视频训练自定义形象
        """
        self._custom_avatars[avatar.avatar_id] = avatar
        logger.info(f"Custom avatar added: {avatar.avatar_id} - {avatar.name}")
        return True

    def remove_custom_avatar(self, avatar_id: str) -> bool:
        """移除自定义形象"""
        if avatar_id in self._custom_avatars:
            del self._custom_avatars[avatar_id]
            logger.info(f"Custom avatar removed: {avatar_id}")
            return True
        return False


class BackgroundManager:
    """背景管理器"""

    def __init__(self):
        from src.business.digital_human.aliyun_client import ALIYUN_PUBLIC_BACKGROUNDS
        self._backgrounds = {bg["id"]: bg for bg in ALIYUN_PUBLIC_BACKGROUNDS}
        self._custom_backgrounds: Dict[str, Dict] = {}
        logger.info("BackgroundManager initialized")

    def list_categories(self) -> List[str]:
        """列出背景分类"""
        categories = set(bg.get("category", "") for bg in self._backgrounds.values())
        categories.update(set(bg.get("category", "") for bg in self._custom_backgrounds.values()))
        return list(categories)

    def list_backgrounds(self, category: Optional[str] = None) -> List[Dict]:
        """列出背景"""
        if category:
            bgs = [
                bg for bg in list(self._backgrounds.values()) + list(self._custom_backgrounds.values())
                if bg.get("category") == category
            ]
            return bgs
        return list(self._backgrounds.values()) + list(self._custom_backgrounds.values())

    def get_background(self, background_id: str) -> Optional[Dict]:
        """获取背景信息"""
        if background_id in self._backgrounds:
            return self._backgrounds[background_id]
        if background_id in self._custom_backgrounds:
            return self._custom_backgrounds[background_id]
        return None

    def add_custom_background(self, background: Dict) -> bool:
        """添加自定义背景"""
        bg_id = background.get("id", f"custom_{len(self._custom_backgrounds)}")
        self._custom_backgrounds[bg_id] = background
        logger.info(f"Custom background added: {bg_id}")
        return True


class DigitalHumanRouter:
    """
    数字人路由 - 云端API模式
    支持阿里云数字人、腾讯云数字人、火山引擎数字人
    """

    def __init__(self, config: Optional[DigitalHumanConfig] = None):
        self.config = config or DigitalHumanConfig()
        self._cloud_client = None

        # 形象和背景管理器
        self.avatar_manager = AvatarManager()
        self.background_manager = BackgroundManager()

        logger.info(f"DigitalHumanRouter initialized: provider={self.config.provider}")

    async def _get_cloud_client(self):
        """获取云端数字人客户端"""
        if self._cloud_client is None:
            if self.config.provider == "aliyun":
                self._cloud_client = AliyunDigitalHuman(
                    api_key=self.config.aliyun_api_key,
                    region=self.config.aliyun_region
                )
            elif self.config.provider == "tencent":
                raise NotImplementedError("Tencent digital human not implemented")
            elif self.config.provider == "volcengine":
                raise NotImplementedError("VolcEngine digital human not implemented")
            else:
                raise ValueError(f"Unknown provider: {self.config.provider}")
        return self._cloud_client

    async def health_check(self) -> dict:
        """检查服务健康状态"""
        results = {"cloud": None}

        try:
            client = await self._get_cloud_client()
            ok = await client.health_check()
            results["cloud"] = {"available": ok, "provider": self.config.provider}
        except Exception as e:
            results["cloud"] = {"available": False, "error": str(e)}

        return results

    async def generate(self, request: DigitalHumanRequest) -> DigitalHumanResponse:
        """
        生成数字人视频

        Args:
            request: 数字人请求

        Returns:
            DigitalHumanResponse
        """
        try:
            client = await self._get_cloud_client()

            result = await client.generate(
                script=request.script,
                avatar_id=request.avatar_id,
                background_id=request.background_id,
                motion=request.motion,
                aspect_ratio=request.aspect_ratio,
                output_path=request.output_path
            )

            return DigitalHumanResponse(
                success=result.success,
                video_path=result.video_path,
                video_url=result.video_url,
                duration=result.duration,
                task_id=result.task_id,
                error=result.error,
                mode="cloud",
                provider=self.config.provider
            )

        except Exception as e:
            logger.error(f"Digital human generate failed: {e}")
            return DigitalHumanResponse(
                success=False,
                error=str(e),
                mode="cloud",
                provider=self.config.provider
            )

    async def close(self):
        """关闭连接"""
        if self._cloud_client:
            await self._cloud_client.close()
            self._cloud_client = None


# 全局管理器实例
_avatar_manager: Optional[AvatarManager] = None
_background_manager: Optional[BackgroundManager] = None


def get_avatar_manager() -> AvatarManager:
    """获取形象管理器"""
    global _avatar_manager
    if _avatar_manager is None:
        _avatar_manager = AvatarManager()
    return _avatar_manager


def get_background_manager() -> BackgroundManager:
    """获取背景管理器"""
    global _background_manager
    if _background_manager is None:
        _background_manager = BackgroundManager()
    return _background_manager


# 便捷函数
async def generate_digital_human(
    script: str,
    avatar_id: str,
    background_id: str = "bg_001",
    config: Optional[DigitalHumanConfig] = None
) -> DigitalHumanResponse:
    """便捷的数字人生成函数"""
    if config is None:
        config = DigitalHumanConfig()

    router = DigitalHumanRouter(config)
    request = DigitalHumanRequest(
        script=script,
        avatar_id=avatar_id,
        background_id=background_id
    )

    try:
        return await router.generate(request)
    finally:
        await router.close()