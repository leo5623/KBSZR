"""Playwright浏览器自动化服务"""
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from loguru import logger

# 检查Playwright是否可用
try:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Install with: pip install playwright")


@dataclass
class BrowserResult:
    """浏览器操作结果"""
    success: bool
    content: str = ""
    error: str = ""


class PlaywrightService:
    """
    Playwright浏览器自动化服务

    功能：
    - 链接解析（提取文案）
    - 平台登录（Cookie管理）
    - 自动化操作
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium"  # chromium / firefox / webkit
    ):
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run: pip install playwright")

        self.headless = headless
        self.browser_type = browser_type
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context = None
        logger.info(f"PlaywrightService initialized: browser={browser_type}, headless={headless}")

    async def start(self):
        """启动浏览器"""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            if self.browser_type == "chromium":
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--disable-setuid-sandbox",
                        "--disable-web-security",
                        "--disable-blink-features",
                        "--disable-extensions",
                    ]
                )
            elif self.browser_type == "firefox":
                self._browser = await self._playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self._browser = await self._playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unknown browser type: {self.browser_type}")

            self._context = await self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )
            logger.info("Browser started")

    async def close(self):
        """关闭浏览器"""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed")

    async def health_check(self) -> dict:
        """检查Playwright是否可用"""
        return {
            "available": PLAYWRIGHT_AVAILABLE,
            "browser": self.browser_type,
            "running": self._browser is not None
        }

    async def navigate(self, url: str, timeout: int = 60000) -> BrowserResult:
        """
        导航到URL

        Args:
            url: 目标URL
            timeout: 超时时间(毫秒)，默认60秒

        Returns:
            BrowserResult
        """
        try:
            await self.start()
            page = await self._context.new_page()

            # 使用 domcontentloaded 而不是 networkidle，避免重定向时超时
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            # 等待一小段时间让页面稳定
            await page.wait_for_timeout(2000)
            content = await page.content()
            await page.close()

            return BrowserResult(success=True, content=content)

        except Exception as e:
            logger.error(f"Navigate failed: {e}")
            return BrowserResult(success=False, error=str(e))

    async def get_text(self, url: str, selector: str) -> BrowserResult:
        """
        获取页面元素文本

        Args:
            url: 目标URL
            selector: CSS选择器

        Returns:
            BrowserResult
        """
        try:
            await self.start()
            page = await self._context.new_page()
            await page.goto(url, wait_until="networkidle")
            element = await page.query_selector(selector)
            text = await element.inner_text() if element else ""
            await page.close()

            return BrowserResult(success=True, content=text)

        except Exception as e:
            logger.error(f"Get text failed: {e}")
            return BrowserResult(success=False, error=str(e))

    async def execute_script(self, url: str, script: str) -> BrowserResult:
        """
        执行JavaScript

        Args:
            url: 目标URL
            script: JavaScript代码

        Returns:
            BrowserResult
        """
        try:
            await self.start()
            page = await self._context.new_page()
            await page.goto(url, wait_until="networkidle")
            result = await page.evaluate(script)
            await page.close()

            return BrowserResult(success=True, content=str(result))

        except Exception as e:
            logger.error(f"Execute script failed: {e}")
            return BrowserResult(success=False, error=str(e))

    def set_cookies(self, cookies: List[Dict]):
        """设置Cookie"""
        if self._context:
            asyncio.create_task(self._context.add_cookies(cookies))
            logger.info(f"Set {len(cookies)} cookies")

    async def get_cookies(self) -> List[Dict]:
        """获取当前Cookie"""
        if self._context:
            return await self._context.cookies()
        return []

    async def qrcode_login(self, login_url: str, timeout: int = 120) -> Dict[str, Any]:
        """
        二维码登录，获取Cookie

        Args:
            login_url: 登录页面URL
            timeout: 超时时间(秒)

        Returns:
            {"success": bool, "cookies": [], "error": str}
        """
        try:
            await self.start()
            page = await self._context.new_page()

            logger.info(f"Opening QR code login: {login_url}")
            await page.goto(login_url, wait_until="domcontentloaded", timeout=timeout * 1000)

            # 等待二维码出现
            await page.wait_for_timeout(2000)

            # 等待用户扫码登录 - 检查是否跳转到已登录状态
            # 抖音扫码成功后会跳转到主页面
            max_wait = timeout
            check_interval = 3
            for _ in range(max_wait // check_interval):
                await page.wait_for_timeout(check_interval * 1000)

                # 检查当前URL是否还在登录页
                current_url = page.url
                if "login" not in current_url.lower():
                    # 已登录，获取cookies
                    cookies = await self._context.cookies()
                    logger.info(f"QR code login success, got {len(cookies)} cookies")
                    await page.close()
                    return {
                        "success": True,
                        "cookies": cookies,
                        "url": current_url
                    }

            await page.close()
            return {
                "success": False,
                "error": "Login timeout, please scan QR code in time",
                "cookies": []
            }

        except Exception as e:
            logger.error(f"QR code login failed: {e}")
            return {"success": False, "error": str(e), "cookies": []}

    @staticmethod
    async def install_browsers():
        """安装浏览器"""
        import subprocess
        result = subprocess.run(
            ["playwright", "install"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0


# 全局实例
_playwright_service: Optional[PlaywrightService] = None


def get_playwright_service() -> PlaywrightService:
    """获取Playwright服务实例"""
    global _playwright_service
    if _playwright_service is None:
        _playwright_service = PlaywrightService()
    return _playwright_service