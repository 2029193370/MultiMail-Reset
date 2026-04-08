from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from app.providers.base import BaseProvider, ChangePasswordResult


class QQPersonalProvider(BaseProvider):
    provider_type = "qq"
    display_name = "QQ邮箱"
    change_password_url = "https://aq.qq.com/cn2/index"

    async def change_password(self, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        """
        QQ邮箱密码 = QQ密码，需要通过 QQ安全中心 修改。
        由于 QQ 登录有滑块验证、设备锁等保护，自动化成功率极低，
        直接降级为手动模式，提供链接和说明。
        """
        qq_number = email.split("@")[0]
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    )
                    page = await context.new_page()
                    await page.goto("https://aq.qq.com/cn2/index", wait_until="networkidle", timeout=15000)
                finally:
                    await browser.close()

            return await self._fallback_manual(
                f"QQ密码修改需要通过QQ安全中心进行安全验证（QQ号: {qq_number}）"
            )

        except PlaywrightTimeout:
            logger.error(f"[QQ] 页面加载超时: {email}")
            return await self._fallback_manual("页面加载超时，请手动修改")
        except Exception as e:
            logger.error(f"[QQ] 自动化异常: {e}")
            return await self._fallback_manual(f"自动化异常: {str(e)}")
