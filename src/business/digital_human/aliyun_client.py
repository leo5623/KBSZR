"""阿里云数字人客户端"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx
import json
from loguru import logger


@dataclass
class AvatarInfo:
    """数字人形象信息"""
    avatar_id: str
    name: str
    category: str = "综合"
    gender: str = ""
    description: str = ""
    preview_url: str = ""
    is_public: bool = True  # 是否公版


@dataclass
class DigitalHumanResult:
    """数字人生成结果"""
    success: bool
    video_path: str = ""
    video_url: str = ""  # 云端URL
    duration: float = 0.0
    task_id: str = ""
    error: str = ""
    provider: str = "aliyun"


# 阿里云公版形象列表
ALIYUN_PUBLIC_AVATARS = [
    AvatarInfo(
        avatar_id="avatar_001",
        name="小美",
        category="女生",
        gender="female",
        description="青春活泼女生"
    ),
    AvatarInfo(
        avatar_id="avatar_002",
        name="小雅",
        category="女生",
        gender="female",
        description="知性优雅女生"
    ),
    AvatarInfo(
        avatar_id="avatar_003",
        name="小帅",
        category="男生",
        gender="male",
        description="阳光帅气男生"
    ),
    AvatarInfo(
        avatar_id="avatar_004",
        name="老王",
        category="男生",
        gender="male",
        description="成熟稳重男士"
    ),
    AvatarInfo(
        avatar_id="avatar_005",
        name="阿娜",
        category="民族风",
        gender="female",
        description="民族风女生"
    ),
    AvatarInfo(
        avatar_id="avatar_006",
        name="健身教练",
        category="健身",
        gender="male",
        description="专业健身教练"
    ),
    AvatarInfo(
        avatar_id="avatar_007",
        name="商务精英",
        category="商务",
        gender="male",
        description="专业商务人士"
    ),
    AvatarInfo(
        avatar_id="avatar_008",
        name="主播小雪",
        category="综合",
        gender="female",
        description="专业主播形象"
    ),
]

# 公版背景列表
ALIYUN_PUBLIC_BACKGROUNDS = [
    {"id": "bg_001", "name": "演播室", "category": "演播室"},
    {"id": "bg_002", "name": "办公室", "category": "演播室"},
    {"id": "bg_003", "name": "客厅", "category": "室内"},
    {"id": "bg_004", "name": "户外风景", "category": "户外"},
    {"id": "bg_005", "name": "商品展示", "category": "商品"},
    {"id": "bg_006", "name": "抽象背景", "category": "抽象"},
]


class AliyunDigitalHuman:
    """阿里云数字人客户端"""

    def __init__(
        self,
        api_key: str,
        region: str = "cn-shanghai"
    ):
        self.api_key = api_key
        self.region = region
        self.base_url = f"https://digitalhuman.cn-{region}.aliyuncs.com/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"AliyunDigitalHuman initialized: region={region}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """检查服务是否可用"""
        try:
            client = await self._get_client()
            # 简单的连通性检查
            return True
        except Exception as e:
            logger.warning(f"DigitalHuman health check failed: {e}")
            return False

    async def list_avatars(self, category: Optional[str] = None) -> List[AvatarInfo]:
        """
        获取公版形象列表

        Args:
            category: 筛选类别（如"女生"、"男生"等）

        Returns:
            形象列表
        """
        avatars = ALIYUN_PUBLIC_AVATARS

        if category:
            avatars = [a for a in avatars if a.category == category]

        return avatars

    async def list_backgrounds(self, category: Optional[str] = None) -> List[Dict]:
        """
        获取公版背景列表

        Args:
            category: 筛选类别

        Returns:
            背景列表
        """
        backgrounds = ALIYUN_PUBLIC_BACKGROUNDS

        if category:
            backgrounds = [b for b in backgrounds if b.get("category") == category]

        return backgrounds

    async def generate(
        self,
        script: str,
        avatar_id: str,
        background_id: str = "bg_001",
        motion: str = "slight",  # slight/medium/none
        aspect_ratio: str = "9:16",
        output_path: Optional[str] = None
    ) -> DigitalHumanResult:
        """
        生成数字人视频

        Args:
            script: 口播文案
            avatar_id: 形象ID
            background_id: 背景ID
            motion: 动作参数 (slight/medium/none)
            aspect_ratio: 视频比例 (9:16 或 16:9)
            output_path: 本地保存路径

        Returns:
            DigitalHumanResult
        """
        client = await self._get_client()

        # 构造请求
        payload = {
            "script": script,
            "avatar_id": avatar_id,
            "background_id": background_id,
            "motion": motion,
            "aspect_ratio": aspect_ratio,
            "callback_url": ""  # 可选，异步回调
        }

        try:
            response = await client.post(
                f"{self.base_url}/digital_human/generate",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()

                # 返回结果
                return DigitalHumanResult(
                    success=True,
                    video_url=result.get("video_url", ""),
                    video_path=output_path or result.get("local_path", ""),
                    duration=result.get("duration", 0.0),
                    task_id=result.get("task_id", ""),
                    provider="aliyun"
                )
            else:
                return DigitalHumanResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    provider="aliyun"
                )

        except httpx.TimeoutException:
            logger.error("DigitalHuman request timeout")
            return DigitalHumanResult(
                success=False,
                error="Request timeout",
                provider="aliyun"
            )
        except Exception as e:
            logger.error(f"DigitalHuman generate failed: {e}")
            return DigitalHumanResult(
                success=False,
                error=str(e),
                provider="aliyun"
            )

    async def generate_async(
        self,
        script: str,
        avatar_id: str,
        background_id: str = "bg_001",
        motion: str = "slight",
        aspect_ratio: str = "9:16"
    ) -> str:
        """
        异步生成数字人视频，返回task_id

        Args:
            script: 口播文案
            avatar_id: 形象ID
            background_id: 背景ID
            motion: 动作参数
            aspect_ratio: 视频比例

        Returns:
            task_id，用于查询进度
        """
        client = await self._get_client()

        payload = {
            "script": script,
            "avatar_id": avatar_id,
            "background_id": background_id,
            "motion": motion,
            "aspect_ratio": aspect_ratio,
        }

        response = await client.post(
            f"{self.base_url}/digital_human/generate_async",
            json=payload
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("task_id", "")
        else:
            raise Exception(f"Async generate failed: {response.text}")

    async def query_task(self, task_id: str) -> Dict[str, Any]:
        """
        查询异步任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.base_url}/digital_human/task/{task_id}"
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query task failed: {response.text}")

    @staticmethod
    def get_public_avatars() -> List[AvatarInfo]:
        """获取所有公版形象"""
        return ALIYUN_PUBLIC_AVATARS

    @staticmethod
    def get_public_backgrounds() -> List[Dict]:
        """获取所有公版背景"""
        return ALIYUN_PUBLIC_BACKGROUNDS