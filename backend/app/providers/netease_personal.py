from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from app.providers.base import BaseProvider, ChangePasswordResult


class NeteasePersonalProvider(BaseProvider):
    provider_type = "netease"
    display_name = "网易邮箱"
    change_password_url = "https://reg.163.com/naq/safe-index"

    async def change_password(self, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        """网易邮箱 (163/126/yeah) 密码修改，通过网易账号安全中心。"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    return await self._attempt_change(browser, email, old_password, new_password)
                finally:
                    await browser.close()
        except PlaywrightTimeout:
            logger.error(f"[Netease] 页面加载超时: {email}")
            return await self._fallback_manual("页面加载超时，请手动修改")
        except Exception as e:
            logger.error(f"[Netease] 自动化异常: {e}")
            return await self._fallback_manual(f"自动化异常: {str(e)}")

    async def _attempt_change(self, browser, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        await page.goto("https://mail.163.com/", wait_until="domcontentloaded", timeout=15000)

        iframe = page.frame_locator('iframe[id^="x-URS-iframe"]')
        email_prefix = email.split("@")[0]

        try:
            await iframe.locator('input[name="email"]').fill(email_prefix, timeout=5000)
            await iframe.locator('input[name="password"]').fill(old_password, timeout=3000)
            await iframe.locator('#dologin').click(timeout=3000)
            await page.wait_for_timeout(3000)
        except (PlaywrightTimeout, Exception):
            return await self._fallback_manual("登录页面元素变化，无法自动填充")

        if await page.locator('img.yidun').count() > 0:
            return await self._fallback_manual("登录遇到图形验证码，需要手动处理")

        if await page.locator('.ferrorhead').count() > 0:
            return ChangePasswordResult(success=False, error_message="登录失败，请检查邮箱和密码是否正确")

        try:
            await page.goto("https://reg.163.com/naq/safe-index#/pwd", wait_until="networkidle", timeout=10000)
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"][placeholder*="当前"]', old_password, timeout=5000)
            await page.fill('input[type="password"][placeholder*="新"]', new_password, timeout=3000)
            await page.fill('input[type="password"][placeholder*="确认"]', new_password, timeout=3000)
            await page.click('button:has-text("确认修改")', timeout=3000)
            await page.wait_for_timeout(3000)

            if await page.locator('text=修改成功').count() > 0:
                return ChangePasswordResult(success=True, method="auto")

            return await self._fallback_manual("密码修改表单提交后未检测到成功提示")
        except PlaywrightTimeout:
            return await self._fallback_manual("密码修改页面操作超时")
