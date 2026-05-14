"""一键分发机器人 - 各平台分发（完整版）"""
import asyncio
import time
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
from enum import Enum
from loguru import logger

from src.browser.playwright_service import PlaywrightService


class Platform(Enum):
    """支持的平台"""
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    XIAOHONGSHU = "xiaohongshu"
    WEIXIN = "weixin"  # 视频号
    BILIBILI = "bilibili"


class DistributionStatus(Enum):
    """分发状态"""
    PENDING = "pending"
    UPLOADING = "uploading"
    FILLING_INFO = "filling_info"
    PUBLISHING = "publishing"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class DistributionResult:
    """分发结果"""
    success: bool
    platform: str
    url: str = ""  # 发布后的链接
    video_id: str = ""  # 平台视频ID
    error: str = ""
    status: str = ""
    duration: float = 0.0  # 耗时


@dataclass
class PlatformConfig:
    """平台配置"""
    platform: Platform
    cookies: List[Dict] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    upload_url: str = ""
    publish_url: str = ""


@dataclass
class PublishRequest:
    """发布请求"""
    video_path: str
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    cover_path: Optional[str] = None
    visibility: str = "public"  # public / private / friends


@dataclass
class ProgressCallback:
    """进度回调"""
    on_progress: Callable[[str, float, str], None] = None  # (stage, progress, message)


class BaseDistributor:
    """分发器基类"""

    # 平台特定的页面选择器
    SELECTORS = {
        "douyin": {
            "upload_input": 'input[type="file"]',
            "title_input": 'input[placeholder*="标题"]',
            "description_input": 'textarea[placeholder*="描述"]',
            "publish_button": 'button:has-text("发布")',
            "confirm_button": 'button:has-text("确认")',
            "upload_progress": '.upload-progress',
            "error_toast": '.error-toast'
        },
        "kuaishou": {
            "upload_input": 'input[type="file"]',
            "title_input": 'input[placeholder*="标题"]',
            "description_input": 'textarea[placeholder*="简介"]',
            "publish_button": 'button:has-text("发布")',
            "confirm_button": 'button:has-text("确认发布")'
        },
        "xiaohongshu": {
            "upload_input": 'input[type="file"]',
            "title_input": 'input[placeholder*="标题"]',
            "description_input": '.note-textarea',
            "publish_button": 'button:has-text("发布")',
            "confirm_button": 'button:has-text("确认")'
        },
        "weixin": {
            "upload_input": 'input[type="file"]',
            "title_input": 'input[placeholder*="标题"]',
            "description_input": 'textarea[placeholder*="描述"]',
            "publish_button": 'button:has-text("发表")'
        },
        "bilibili": {
            "upload_input": '.upload-input',
            "title_input": '#video-title-input',
            "description_input": '#video-desc-input',
            "publish_button": '.publish-button',
            "confirm_button": '.confirm-publish'
        }
    }

    def __init__(
        self,
        playwright: PlaywrightService,
        cookies: List[Dict],
        platform: Platform,
        config: Optional[Dict] = None
    ):
        self.playwright = playwright
        self.cookies = cookies
        self.platform = platform
        self.config = config or {}
        self._page = None
        self._browser = None

    async def initialize(self) -> bool:
        """初始化浏览器和登录"""
        try:
            await self.playwright.start()
            self._browser = await self.playwright.get_browser()

            # 设置cookies
            if self.cookies:
                context = await self._browser.new_context()
                await context.add_cookies(self.cookies)
                self._page = await context.new_page()
            else:
                self._page = await self._browser.new_page()

            return True
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False

    async def close(self):
        """关闭资源"""
        try:
            if self._page:
                await self._page.close()
                self._page = None
        except Exception:
            pass

    async def _wait_for_upload_complete(self, timeout: float = 120) -> bool:
        """等待上传完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # 检查上传进度元素是否消失
                progress = await self._page.query_selector('.upload-progress')
                if not progress:
                    return True

                # 检查错误提示
                error = await self._page.query_selector('.error-toast')
                if error:
                    error_text = await error.text_content()
                    logger.error(f"上传错误: {error_text}")
                    return False

                await asyncio.sleep(1)
            except Exception:
                pass
        return False

    async def _fill_form(
        self,
        title: str,
        description: str,
        tags: List[str]
    ) -> bool:
        """填写发布表单"""
        selectors = self.SELECTORS.get(self.platform.value, {})

        try:
            # 填写标题
            title_input = await self._page.query_selector(selectors.get("title_input", "input"))
            if title_input:
                await title_input.fill(title[:100])  # 限制长度

            # 填写描述
            desc_input = await self._page.query_selector(selectors.get("description_input", "textarea"))
            if desc_input:
                tag_text = " ".join([f"#{tag}" for tag in tags])
                full_description = f"{description}\n{tag_text}"
                await desc_input.fill(full_description[:2000])

            return True
        except Exception as e:
            logger.error(f"填写表单失败: {e}")
            return False

    async def _click_publish(self) -> bool:
        """点击发布按钮"""
        selectors = self.SELECTORS.get(self.platform.value, {})

        try:
            # 点击发布
            publish_btn = await self._page.query_selector(selectors.get("publish_button", "button"))
            if publish_btn:
                await publish_btn.click()
                await asyncio.sleep(2)

            # 确认发布
            confirm_btn = await self._page.query_selector(selectors.get("confirm_button"))
            if confirm_btn:
                await confirm_btn.click()

            return True
        except Exception as e:
            logger.error(f"点击发布失败: {e}")
            return False

    async def _get_published_url(self) -> str:
        """获取发布后的链接"""
        try:
            # 等待跳转或获取URL
            await asyncio.sleep(3)

            current_url = self._page.url

            # 尝试提取视频ID
            if "douyin.com" in current_url:
                # 抖音URL格式
                return current_url
            elif "kuaishou.com" in current_url:
                return current_url
            elif "xiaohongshu.com" in current_url:
                return current_url

            return current_url
        except Exception as e:
            logger.error(f"获取URL失败: {e}")
            return ""

    async def publish(self, request: PublishRequest) -> DistributionResult:
        """发布视频（子类实现）"""
        raise NotImplementedError


class DouyinDistributor(BaseDistributor):
    """抖音分发机器人"""

    UPLOAD_URL = "https://creator.douyin.com/creator/microapp/upload"

    def __init__(self, playwright: PlaywrightService, cookies: List[Dict], config: Optional[Dict] = None):
        super().__init__(playwright, cookies, Platform.DOUYIN, config)

    async def publish(self, request: PublishRequest) -> DistributionResult:
        """发布到抖音"""
        start_time = time.time()

        try:
            # 初始化
            if not await self.initialize():
                return DistributionResult(
                    success=False,
                    platform=self.platform.value,
                    error="初始化失败"
                )

            # 导航到上传页面
            await self._page.goto(self.UPLOAD_URL)
            await self._page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # 上传视频
            upload_input = await self._page.query_selector('input[type="file"]')
            if not upload_input:
                return DistributionResult(
                    success=False,
                    platform=self.platform.value,
                    error="找不到上传输入框"
                )

            await upload_input.set_input_files(request.video_path)

            # 等待上传
            if not await self._wait_for_upload_complete():
                return DistributionResult(
                    success=False,
                    platform=self.platform.value,
                    error="上传超时"
                )

            # 填写信息
            await self._fill_form(
                request.title,
                request.description,
                request.tags
            )

            # 发布
            await self._click_publish()

            # 获取结果
            url = await self._get_published_url()

            return DistributionResult(
                success=True,
                platform=self.platform.value,
                url=url,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"抖音发布失败: {e}")
            return DistributionResult(
                success=False,
                platform=self.platform.value,
                error=str(e),
                duration=time.time() - start_time
            )
        finally:
            await self.close()


class KuaishouDistributor(BaseDistributor):
    """快手分发机器人"""

    UPLOAD_URL = "https://cp.kuaishou.com/upload"

    def __init__(self, playwright: PlaywrightService, cookies: List[Dict], config: Optional[Dict] = None):
        super().__init__(playwright, cookies, Platform.KUAISHOU, config)

    async def publish(self, request: PublishRequest) -> DistributionResult:
        """发布到快手"""
        start_time = time.time()

        try:
            if not await self.initialize():
                return DistributionResult(success=False, platform=self.platform.value, error="初始化失败")

            await self._page.goto(self.UPLOAD_URL)
            await self._page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            upload_input = await self._page.query_selector('input[type="file"]')
            if not upload_input:
                return DistributionResult(success=False, platform=self.platform.value, error="找不到上传输入框")

            await upload_input.set_input_files(request.video_path)

            if not await self._wait_for_upload_complete():
                return DistributionResult(success=False, platform=self.platform.value, error="上传超时")

            await self._fill_form(request.title, request.description, request.tags)
            await self._click_publish()

            url = await self._get_published_url()

            return DistributionResult(
                success=True,
                platform=self.platform.value,
                url=url,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"快手发布失败: {e}")
            return DistributionResult(success=False, platform=self.platform.value, error=str(e))
        finally:
            await self.close()


class XiaohongshuDistributor(BaseDistributor):
    """小红书分发机器人"""

    UPLOAD_URL = "https://creator.xiaohongshu.com/creator/post"

    def __init__(self, playwright: PlaywrightService, cookies: List[Dict], config: Optional[Dict] = None):
        super().__init__(playwright, cookies, Platform.XIAOHONGSHU, config)

    async def publish(self, request: PublishRequest) -> DistributionResult:
        """发布到小红书"""
        start_time = time.time()

        try:
            if not await self.initialize():
                return DistributionResult(success=False, platform=self.platform.value, error="初始化失败")

            await self._page.goto(self.UPLOAD_URL)
            await self._page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            upload_input = await self._page.query_selector('input[type="file"]')
            if not upload_input:
                return DistributionResult(success=False, platform=self.platform.value, error="找不到上传输入框")

            await upload_input.set_input_files(request.video_path)

            # 小红书需要更长的时间上传
            if not await self._wait_for_upload_complete(timeout=180):
                return DistributionResult(success=False, platform=self.platform.value, error="上传超时")

            await self._fill_form(request.title, request.description, request.tags)
            await self._click_publish()

            url = await self._get_published_url()

            return DistributionResult(
                success=True,
                platform=self.platform.value,
                url=url,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"小红书发布失败: {e}")
            return DistributionResult(success=False, platform=self.platform.value, error=str(e))
        finally:
            await self.close()


class WeixinDistributor(BaseDistributor):
    """视频号分发机器人"""

    UPLOAD_URL = "https://channels.weixin.qq.com/platform/media/upload"

    def __init__(self, playwright: PlaywrightService, cookies: List[Dict], config: Optional[Dict] = None):
        super().__init__(playwright, cookies, Platform.WEIXIN, config)

    async def publish(self, request: PublishRequest) -> DistributionResult:
        """发布到视频号"""
        start_time = time.time()

        try:
            if not await self.initialize():
                return DistributionResult(success=False, platform=self.platform.value, error="初始化失败")

            await self._page.goto(self.UPLOAD_URL)
            await self._page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            upload_input = await self._page.query_selector('input[type="file"]')
            if not upload_input:
                return DistributionResult(success=False, platform=self.platform.value, error="找不到上传输入框")

            await upload_input.set_input_files(request.video_path)

            if not await self._wait_for_upload_complete():
                return DistributionResult(success=False, platform=self.platform.value, error="上传超时")

            await self._fill_form(request.title, request.description, request.tags)
            await self._click_publish()

            url = await self._get_published_url()

            return DistributionResult(
                success=True,
                platform=self.platform.value,
                url=url,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"视频号发布失败: {e}")
            return DistributionResult(success=False, platform=self.platform.value, error=str(e))
        finally:
            await self.close()


class BilibiliDistributor(BaseDistributor):
    """B站分发机器人"""

    UPLOAD_URL = "https://member.bilibili.com/v/video/upload"

    def __init__(self, playwright: PlaywrightService, cookies: List[Dict], config: Optional[Dict] = None):
        super().__init__(playwright, cookies, Platform.BILIBILI, config)

    async def publish(self, request: PublishRequest) -> DistributionResult:
        """发布到B站"""
        start_time = time.time()

        try:
            if not await self.initialize():
                return DistributionResult(success=False, platform=self.platform.value, error="初始化失败")

            await self._page.goto(self.UPLOAD_URL)
            await self._page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # B站使用特定的class选择器
            upload_input = await self._page.query_selector('.upload-input input[type="file"]')
            if not upload_input:
                upload_input = await self._page.query_selector('input[type="file"]')

            if not upload_input:
                return DistributionResult(success=False, platform=self.platform.value, error="找不到上传输入框")

            await upload_input.set_input_files(request.video_path)

            if not await self._wait_for_upload_complete():
                return DistributionResult(success=False, platform=self.platform.value, error="上传超时")

            await self._fill_form(request.title, request.description, request.tags)
            await self._click_publish()

            url = await self._get_published_url()

            return DistributionResult(
                success=True,
                platform=self.platform.value,
                url=url,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"B站发布失败: {e}")
            return DistributionResult(success=False, platform=self.platform.value, error=str(e))
        finally:
            await self.close()


class DistributorBot:
    """
    分发机器人管理器

    支持多平台分发，自动重试，进度跟踪
    """

    def __init__(self, playwright: Optional[PlaywrightService] = None):
        self.playwright = playwright or PlaywrightService()
        self._distributors: Dict[str, BaseDistributor] = {}
        self._platform_configs: Dict[str, PlatformConfig] = {}
        logger.info("DistributorBot initialized")

    def configure_platform(
        self,
        platform: str,
        cookies: List[Dict],
        config: Optional[Dict] = None
    ):
        """配置平台"""
        self._platform_configs[platform] = PlatformConfig(
            platform=Platform(platform),
            cookies=cookies,
            **(config or {})
        )

        logger.info(f"Platform configured: {platform}")

    def _create_distributor(self, platform: str) -> Optional[BaseDistributor]:
        """创建分发器实例"""
        config = self._platform_configs.get(platform)
        if not config:
            logger.warning(f"Platform not configured: {platform}")
            return None

        if platform == "douyin":
            return DouyinDistributor(self.playwright, config.cookies, config.__dict__)
        elif platform == "kuaishou":
            return KuaishouDistributor(self.playwright, config.cookies, config.__dict__)
        elif platform == "xiaohongshu":
            return XiaohongshuDistributor(self.playwright, config.cookies, config.__dict__)
        elif platform == "weixin":
            return WeixinDistributor(self.playwright, config.cookies, config.__dict__)
        elif platform == "bilibili":
            return BilibiliDistributor(self.playwright, config.cookies, config.__dict__)
        else:
            logger.error(f"Unknown platform: {platform}")
            return None

    async def distribute(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        platforms: List[str],
        max_retries: int = 2
    ) -> Dict[str, DistributionResult]:
        """
        分发到多个平台

        Args:
            video_path: 视频文件路径
            title: 标题
            description: 描述
            tags: 话题标签
            platforms: 目标平台列表
            max_retries: 最大重试次数

        Returns:
            各平台分发结果
        """
        results = {}

        for platform in platforms:
            # 创建分发器
            distributor = self._create_distributor(platform)
            if distributor is None:
                results[platform] = DistributionResult(
                    success=False,
                    platform=platform,
                    error=f"Platform not configured: {platform}"
                )
                continue

            # 构建请求
            request = PublishRequest(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags
            )

            # 尝试发布（带重试）
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Publishing to {platform} (attempt {attempt + 1})")
                    result = await distributor.publish(request)

                    if result.success:
                        results[platform] = result
                        break
                    else:
                        last_error = result.error

                        # 重试前等待
                        if attempt < max_retries:
                            await asyncio.sleep(3)

                except Exception as e:
                    logger.error(f"Publish attempt failed: {e}")
                    last_error = str(e)

                    if attempt < max_retries:
                        await asyncio.sleep(3)

            # 所有重试都失败
            if platform not in results:
                results[platform] = DistributionResult(
                    success=False,
                    platform=platform,
                    error=last_error or "All retries failed"
                )

        return results

    async def distribute_with_progress(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        platforms: List[str],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, DistributionResult]:
        """
        带进度回应的分发

        Args:
            video_path: 视频文件路径
            title: 标题
            description: 描述
            tags: 话题标签
            platforms: 目标平台列表
            progress_callback: 进度回调 (platform, stage, progress, message)

        Returns:
            各平台分发结果
        """
        results = {}
        total_platforms = len(platforms)

        for idx, platform in enumerate(platforms):
            if progress_callback:
                progress_callback(platform, "starting", 0.0, f"准备发布到{platform}...")

            distributor = self._create_distributor(platform)
            if distributor is None:
                results[platform] = DistributionResult(
                    success=False, platform=platform, error=f"Platform not configured: {platform}"
                )
                continue

            request = PublishRequest(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags
            )

            if progress_callback:
                progress_callback(platform, "uploading", 0.3, "上传视频中...")

            try:
                result = await distributor.publish(request)
                results[platform] = result

                if progress_callback:
                    if result.success:
                        progress_callback(platform, "completed", 1.0, f"发布成功: {result.url}")
                    else:
                        progress_callback(platform, "failed", 1.0, f"发布失败: {result.error}")

            except Exception as e:
                logger.error(f"Distribute to {platform} failed: {e}")
                results[platform] = DistributionResult(
                    success=False, platform=platform, error=str(e)
                )

            # 平台间休息
            if idx < total_platforms - 1:
                await asyncio.sleep(2)

        return results

    async def health_check(self) -> Dict[str, bool]:
        """检查各平台配置状态"""
        results = {}
        for platform, config in self._platform_configs.items():
            try:
                # 简单的连通性检查
                results[platform] = len(config.cookies) > 0
            except Exception:
                results[platform] = False
        return results

    async def close(self):
        """关闭所有资源"""
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

    # 配置平台
    for platform, platform_cookies in cookies.items():
        bot.configure_platform(platform, platform_cookies)

    try:
        return await bot.distribute(video_path, title, description, tags, platforms)
    finally:
        await bot.close()


def save_distribution_result(results: Dict[str, DistributionResult], output_path: str):
    """保存分发结果到文件"""
    output_data = []
    for platform, result in results.items():
        output_data.append({
            "platform": platform,
            "success": result.success,
            "url": result.url,
            "video_id": result.video_id,
            "error": result.error,
            "duration": result.duration
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Distribution results saved to: {output_path}")