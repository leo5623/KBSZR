"""copy 模块 - 多平台文案适配"""
from src.business.copy.platform_adapter import (
    PlatformAdapter,
    PlatformAdapterConfig,
    Platform,
    PlatformConfig,
    AdaptedContent,
    get_platform_adapter
)

__all__ = [
    "PlatformAdapter",
    "PlatformAdapterConfig",
    "Platform",
    "PlatformConfig",
    "AdaptedContent",
    "get_platform_adapter"
]