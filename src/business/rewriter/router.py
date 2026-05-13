"""文案改写路由 - 云端API"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from loguru import logger

from src.business.rewriter.api_rewriter import (
    create_rewriter,
    BaseRewriter,
    RewriteResult,
    REWRITER_PROVIDERS
)
from src.business.rewriter.scenario_manager import ScenarioManager, get_scenario_manager


class RewriteMode(Enum):
    """改写模式"""
    CLOUD = "cloud"      # 云端


@dataclass
class RewriteConfig:
    """改写配置"""
    mode: RewriteMode = RewriteMode.CLOUD
    provider: str = "tongyi"  # 云端供应商


@dataclass
class RewriteRequest:
    """改写请求"""
    text: str
    industry: Optional[str] = None
    scenario: Optional[str] = None
    style: Optional[str] = None


@dataclass
class RewriteResponse:
    """改写响应"""
    success: bool
    original_text: str = ""
    rewritten_text: str = ""
    mode: str = ""  # local/cloud
    provider: str = ""
    error: str = ""


class RewriterRouter:
    """
    文案改写路由 - 云端API模式
    """

    def __init__(
        self,
        config: Optional[RewriteConfig] = None,
        scenario_manager: Optional[ScenarioManager] = None
    ):
        self.config = config or RewriteConfig()
        self.scenario_manager = scenario_manager or get_scenario_manager()

        # 云端改写器（延迟初始化）
        self._cloud_rewriter: Optional[BaseRewriter] = None
        self._cloud_config: Optional[dict] = None

        logger.info(f"RewriterRouter initialized: provider={self.config.provider}")

    async def initialize(self, cloud_config: dict):
        """
        初始化云端改写器

        Args:
            cloud_config: 云端配置，格式：
                {
                    "provider": "tongyi",
                    "tongyi": {"api_key": "...", "model": "qwen-max"},
                    ...
                }
        """
        self._cloud_config = cloud_config
        provider = cloud_config.get("provider", "tongyi")

        if provider in REWRITER_PROVIDERS:
            provider_config = cloud_config.get(provider, {})
            self._cloud_rewriter = create_rewriter(provider, **provider_config)
            logger.info(f"Cloud rewriter initialized: {provider}")
        else:
            logger.warning(f"Unknown provider: {provider}, cloud rewrite disabled")

    async def _get_cloud_rewriter(self) -> Optional[BaseRewriter]:
        """获取云端改写器"""
        if self._cloud_rewriter is None and self._cloud_config:
            await self.initialize(self._cloud_config)
        return self._cloud_rewriter

    async def health_check(self) -> dict:
        """检查云端provider的健康状态"""
        results = {}

        if self._cloud_rewriter:
            try:
                cloud_ok = await self._cloud_rewriter.health_check()
                results["cloud"] = {
                    "available": cloud_ok,
                    "provider": self.config.provider
                }
            except Exception as e:
                results["cloud"] = {"available": False, "error": str(e)}
        else:
            results["cloud"] = {"available": False, "error": "not configured"}

        return results

    async def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        """
        改写文案

        Args:
            request: 改写请求

        Returns:
            改写响应
        """
        try:
            # 使用云端改写
            cloud = await self._get_cloud_rewriter()
            if cloud is None:
                return RewriteResponse(
                    success=False,
                    original_text=request.text,
                    error="Cloud rewriter not configured",
                    mode="cloud",
                    provider=self.config.provider
                )

            result = await cloud.rewrite(
                text=request.text,
                scenario=request.scenario,
                industry=request.industry,
                style=request.style
            )

            return RewriteResponse(
                success=result.success,
                original_text=request.text,
                rewritten_text=result.text if result.success else "",
                mode="cloud",
                provider=result.provider,
                error=result.error if not result.success else ""
            )

        except Exception as e:
            logger.error(f"Rewrite failed: {e}")
            return RewriteResponse(
                success=False,
                original_text=request.text,
                error=str(e),
                mode="cloud",
                provider=self.config.provider
            )

    async def close(self):
        """关闭所有连接"""
        if self._cloud_rewriter:
            await self._cloud_rewriter.close()
            self._cloud_rewriter = None


# 便捷函数
async def rewrite_text(
    text: str,
    industry: Optional[str] = None,
    scenario: Optional[str] = None,
    style: Optional[str] = None,
    provider: str = "tongyi",
    cloud_config: Optional[dict] = None
) -> str:
    """
    便捷的文案改写函数

    Args:
        text: 原始文案
        industry: 行业
        scenario: 场景
        style: 风格
        provider: 云端供应商
        cloud_config: 云端配置

    Returns:
        改写后的文案
    """
    config = RewriteConfig(provider=provider)

    router = RewriterRouter(config=config)

    if cloud_config:
        await router.initialize(cloud_config)

    request = RewriteRequest(
        text=text,
        industry=industry,
        scenario=scenario,
        style=style
    )

    try:
        response = await router.rewrite(request)
        return response.rewritten_text if response.success else text
    finally:
        await router.close()