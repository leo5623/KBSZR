"""一键分发机器人 - 各平台分发"""
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path
from loguru import logger

from src.browser.playwright_service import PlaywrightService


@dataclass
class DistributionResult:
    """分发结果"""
    success: bool
    platform: str
    url: str = ""  # 发布后的链接
    error: str = ""


class BaseDistributor:
    """分发器基类"""

    def __init__(self, playwright: PlaywrightService, cookies: List[Dict]):
        self.playwright = playwright
        self.cookies = cookies
        self._page = None

    async def login(self) -> bool:
        """登录（使用预存的cookies）"""
        await self.playwright.start()
        self.playwright.set_cookies(self.cookies)
        return True

    async def logout(self):
        """登出"""
        if self._page:
            await self._page.close()
            self._page = None

    async def publish(self, video_path: str, title: str, description: str, tags: List[str]) -> DistributionResult:
        """发布视频（子类实现）"""
        raise NotImplementedError


class DouyinDistributor(BaseDistributor):
    """抖音分发机器人"""

    async def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> DistributionResult:
        """
        发布到抖音

        Args:
            video_path: 视频文件路径
            title: 标题
            description: 描述
            tags: 话题标签

        Returns:
            DistributionResult
        """
        try:
            await self.login()

            # 导航到创作者服务中心
            await self._page.goto("https://creator.douyin.com/creator/microapp/upload")
            await self._page.wait_for_load_state("networkidle")

            # 上传视频
            # 注意：实际实现需要适配抖音的页面结构
            upload_input = await self._page.query_selector('input[type="file"]')
            if upload_input:
                await upload_input.set_input_files(video_path)

            # 填写标题
            title_input = await self._page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)

            # 添加描述
            desc_input = await self._page.query_selector('textarea')
            if desc_input:
                await desc_input.fill(description + "\n" + "\n".join([f"#{tag}" for tag in tags]))

            # 发布
            publish_btn = await self._page.query_selector('button:has-text("发布")')
            if publish_btn:
                await publish_btn.click()
                await self._page.wait_for_timeout(3000)

            return DistributionResult(
                success=True,
                platform="douyin",
                url="",  # 获取实际发布后的链接
                error=""
            )

        except Exception as e:
            logger.error(f"Douyin publish failed: {e}")
            return DistributionResult(
                success=False,
                platform="douyin",
                error=str(e)
            )
        finally:
            await self.logout()


class KuaishouDistributor(BaseDistributor):
    """快手分发机器人"""

    async def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> DistributionResult:
        """发布到快手"""
        try:
            await self.login()

            await self._page.goto("https://cp.kuaishou.com/upload")
            await self._page.wait_for_load_state("networkidle")

            upload_input = await self._page.query_selector('input[type="file"]')
            if upload_input:
                await upload_input.set_input_files(video_path)

            # 填写标题
            title_input = await self._page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)

            # 发布
            publish_btn = await self._page.query_selector('button:has-text("发布")')
            if publish_btn:
                await publish_btn.click()

            return DistributionResult(
                success=True,
                platform="kuaishou",
                url="",
                error=""
            )

        except Exception as e:
            logger.error(f"Kuaishou publish failed: {e}")
            return DistributionResult(
                success=False,
                platform="kuaishou",
                error=str(e)
            )
        finally:
            await self.logout()


class XiaohongshuDistributor(BaseDistributor):
    """小红书分发机器人"""

    async def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> DistributionResult:
        """发布到小红书"""
        try:
            await self.login()

            await self._page.goto("https://creator.xiaohongshu.com/creator/post")
            await self._page.wait_for_load_state("networkidle")

            upload_input = await self._page.query_selector('input[type="file"]')
            if upload_input:
                await upload_input.set_input_files(video_path)

            # 填写标题
            title_input = await self._page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)

            # 填写正文
            content_input = await self._page.query_selector('textarea')
            if content_input:
                await content_input.fill(description + "\n" + "\n".join([f"#{tag}" for tag in tags]))

            # 发布
            publish_btn = await self._page.query_selector('button:has-text("发布")')
            if publish_btn:
                await publish_btn.click()

            return DistributionResult(
                success=True,
                platform="xiaohongshu",
                url="",
                error=""
            )

        except Exception as e:
            logger.error(f"Xiaohongshu publish failed: {e}")
            return DistributionResult(
                success=False,
                platform="xiaohongshu",
                error=str(e)
            )
        finally:
            await self.logout()


class DistributorBot:
    """
    分发机器人管理器

    支持多平台分发
    """

    def __init__(self, playwright: Optional[PlaywrightService] = None):
        self.playwright = playwright or PlaywrightService()
        self._distributors: Dict[str, BaseDistributor] = {}
        logger.info("DistributorBot initialized")

    def register_distributor(self, platform: str, distributor: BaseDistributor):
        """注册分发器"""
        self._distributors[platform] = distributor
        logger.info(f"Registered distributor for: {platform}")

    async def distribute(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        platforms: List[str]
    ) -> Dict[str, DistributionResult]:
        """
        分发到多个平台

        Args:
            video_path: 视频文件路径
            title: 标题
            description: 描述
            tags: 话题标签
            platforms: 目标平台列表

        Returns:
            各平台分发结果
        """
        results = {}

        for platform in platforms:
            distributor = self._distributors.get(platform)

            if distributor is None:
                results[platform] = DistributionResult(
                    success=False,
                    platform=platform,
                    error=f"Distributor not registered for: {platform}"
                )
                continue

            logger.info(f"Distributing to {platform}...")
            result = await distributor.publish(video_path, title, description, tags)
            results[platform] = result

        return results

    async def close(self):
        """关闭"""
        await self.playwright.close()


# 便捷函数
async def distribute_to_platforms(
    video_path: str,
    title: str,
    description: str,
    tags: List[str],
    platforms: List[str],
    cookies: Dict[str, List[Dict]]
) -> Dict[str, DistributionResult]:
    """
    便捷分发函数

    Args:
        video_path: 视频路径
        title: 标题
        description: 描述
        tags: 话题标签
        platforms: 目标平台
        cookies: 各平台Cookie {"douyin": [...], "kuaishou": [...]}

    Returns:
        分发结果
    """
    bot = DistributorBot()

    # 注册分发器
    if "douyin" in platforms and "douyin" in cookies:
        bot.register_distributor("douyin", DouyinDistributor(bot.playwright, cookies["douyin"]))
    if "kuaishou" in platforms and "kuaishou" in cookies:
        bot.register_distributor("kuaishou", KuaishouDistributor(bot.playwright, cookies["kuaishou"]))
    if "xiaohongshu" in platforms and "xiaohongshu" in cookies:
        bot.register_distributor("xiaohongshu", XiaohongshuDistributor(bot.playwright, cookies["xiaohongshu"]))

    try:
        return await bot.distribute(video_path, title, description, tags, platforms)
    finally:
        await bot.close()