"""平台分发机器人"""
from src.browser.platform_bots.distributor import (
    DouyinDistributor,
    KuaishouDistributor,
    XiaohongshuDistributor,
    DistributorBot,
    DistributionResult,
    distribute_to_platforms
)

__all__ = [
    "DouyinDistributor",
    "KuaishouDistributor",
    "XiaohongshuDistributor",
    "DistributorBot",
    "DistributionResult",
    "distribute_to_platforms"
]