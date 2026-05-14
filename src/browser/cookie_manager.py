"""Cookie管理器 - 支持抖音等平台扫码登录"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed")


class CookieManager:
    """
    Cookie管理器

    支持：
    - 抖音扫码登录获取Cookie
    - Cookie持久化存储
    - 多平台Cookie管理
    """

    COOKIE_DIR = Path("./data/cookies")
    PLATFORM_COOKIE_FILES = {
        "douyin": "douyin_cookies.json",
        "kuaishou": "kuaishou_cookies.json",
        "xiaohongshu": "xiaohongshu_cookies.json",
    }

    QR_LOGIN_URLS = {
        "douyin": "https://www.douyin.com/login/",
        "kuaishou": "https://www.kuaishou.com/new-pc",
        "xiaohongshu": "https://www.xiaohongshu.com/login",
    }

    def __init__(self):
        self.COOKIE_DIR.mkdir(parents=True, exist_ok=True)

    def get_cookie_path(self, platform: str) -> Path:
        """获取平台Cookie文件路径"""
        filename = self.PLATFORM_COOKIE_FILES.get(platform, f"{platform}_cookies.json")
        return self.COOKIE_DIR / filename

    def save_cookies(self, platform: str, cookies: List[Dict]) -> bool:
        """保存Cookie到文件"""
        try:
            path = self.get_cookie_path(platform)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(cookies)} cookies for {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False

    def load_cookies(self, platform: str) -> List[Dict]:
        """从文件加载Cookie"""
        try:
            path = self.get_cookie_path(platform)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                logger.info(f"Loaded {len(cookies)} cookies for {platform}")
                return cookies
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
        return []

    def has_cookies(self, platform: str) -> bool:
        """检查是否有保存的Cookie"""
        return self.get_cookie_path(platform).exists()

    def clear_cookies(self, platform: str) -> bool:
        """清除保存的Cookie"""
        try:
            path = self.get_cookie_path(platform)
            if path.exists():
                path.unlink()
                logger.info(f"Cleared cookies for {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
            return False

    async def qr_login(self, platform: str, timeout: int = 120) -> Dict[str, Any]:
        """
        扫码登录获取Cookie

        Args:
            platform: 平台名称 (douyin/kuaishou/xiaohongshu)
            timeout: 超时时间(秒)

        Returns:
            {"success": bool, "cookies": [], "qr_image": base64, "error": str}
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {"success": False, "error": "Playwright not installed", "cookies": []}

        login_url = self.QR_LOGIN_URLS.get(platform)
        if not login_url:
            return {"success": False, "error": f"Unknown platform: {platform}", "cookies": []}

        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless=False,  # 需要显示二维码
                    args=["--no-sandbox"]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                logger.info(f"Opening QR login: {login_url}")
                await page.goto(login_url, wait_until="domcontentloaded")

                # 等待二维码加载
                await page.wait_for_timeout(3000)

                # 尝试找到二维码图片并截图
                qr_screenshot = None
                try:
                    # 查找二维码相关的元素
                    qr_selectors = [
                        "img[src*='qr']",
                        ".qrcode img",
                        ".login-qrcode img",
                        "[class*='qr'] img",
                    ]
                    for selector in qr_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                qr_screenshot = await element.screenshot()
                                logger.info("QR code found and captured")
                                break
                        except:
                            continue

                    # 如果没找到特定元素，截图整个页面
                    if not qr_screenshot:
                        qr_screenshot = await page.screenshot()

                except Exception as e:
                    logger.warning(f"Failed to capture QR: {e}")
                    qr_screenshot = await page.screenshot()

                # 等待登录完成
                max_wait = timeout
                check_interval = 3
                for i in range(max_wait // check_interval):
                    await page.wait_for_timeout(check_interval * 1000)

                    current_url = page.url
                    if "login" not in current_url.lower():
                        # 已登录
                        cookies = await context.cookies()
                        await browser.close()

                        # 保存Cookie
                        self.save_cookies(platform, cookies)

                        return {
                            "success": True,
                            "cookies": cookies,
                            "url": current_url
                        }

                    logger.info(f"Waiting for QR scan... ({i * check_interval}s)")

                await browser.close()
                return {
                    "success": False,
                    "error": "Login timeout, please scan QR code in time",
                    "cookies": []
                }

        except Exception as e:
            logger.error(f"QR login failed: {e}")
            return {"success": False, "error": str(e), "cookies": []}

    def get_cookies_for_ydl(self, platform: str) -> Dict[str, Any]:
        """
        获取用于yt-dlp的Cookie配置

        Returns:
            {"cookie_file": str} 或 {"http_headers": {"Cookie": "..."}}
        """
        cookies = self.load_cookies(platform)
        if not cookies:
            return {}

        # 转换为字符串格式
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        return {
            "http_headers": {
                "Cookie": cookie_str
            }
        }


# 全局实例
_cookie_manager: Optional[CookieManager] = None


def get_cookie_manager() -> CookieManager:
    """获取Cookie管理器实例"""
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    return _cookie_manager