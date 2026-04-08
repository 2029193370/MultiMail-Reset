from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from app.providers.base import BaseProvider, ChangePasswordResult


class GmailPersonalProvider(BaseProvider):
    provider_type = "gmail"
    display_name = "Gmail"
    change_password_url = "https://myaccount.google.com/signinoptions/password"

    async def change_password(self, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        """
        Gmail 密码修改。
        Google 对自动化登录有严格检测（reCAPTCHA、设备验证等），
        大多数情况下需要降级为手动模式。
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    return await self._attempt_change(browser, email, old_password, new_password)
                finally:
                    await browser.close()
        except PlaywrightTimeout:
            logger.error(f"[Gmail] 页面加载超时: {email}")
            return await self._fallback_manual("页面加载超时，请手动修改")
        except Exception as e:
            logger.error(f"[Gmail] 自动化异常: {e}")
            return await self._fallback_manual(f"自动化异常: {str(e)}")

    async def _attempt_change(self, browser, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        await page.goto("https://accounts.google.com/signin/v2/identifier", wait_until="networkidle", timeout=15000)

        try:
            await page.fill('input[type="email"]', email, timeout=5000)
            await page.click('#identifierNext', timeout=3000)
            await page.wait_for_timeout(3000)
        except PlaywrightTimeout:
            return await self._fallback_manual("Google 登录页面操作超时")

        if await page.locator('iframe[title*="reCAPTCHA"]').count() > 0:
            return await self._fallback_manual("Google 登录遇到 reCAPTCHA 验证，需手动完成")

        unusual = (
            await page.locator('text=异常活动').count() > 0
            or await page.locator('text=unusual activity').count() > 0
        )
        if unusual:
            return await self._fallback_manual("Google 检测到异常登录活动，需手动验证")

        try:
            await page.fill('input[type="password"]', old_password, timeout=5000)
            await page.click('#passwordNext', timeout=3000)
            await page.wait_for_timeout(3000)
        except PlaywrightTimeout:
            return await self._fallback_manual("密码输入页面操作超时")

        two_fa = (
            await page.locator('text=两步验证').count() > 0
            or await page.locator('text=2-Step Verification').count() > 0
        )
        if two_fa:
            return await self._fallback_manual("需要两步验证，请手动完成")

        try:
            await page.goto("https://myaccount.google.com/signinoptions/password", wait_until="networkidle", timeout=15000)

            password_inputs = page.locator('input[type="password"]')
            count = await password_inputs.count()
            if count >= 2:
                await password_inputs.nth(0).fill(new_password)
                await password_inputs.nth(1).fill(new_password)
                await page.click('button:has-text("更改密码"), button:has-text("Change password")', timeout=5000)
                await page.wait_for_timeout(3000)

                success = (
                    await page.locator('text=密码已更改').count() > 0
                    or await page.locator('text=Password changed').count() > 0
                )
                if success:
                    return ChangePasswordResult(success=True, method="auto")

            return await self._fallback_manual("密码修改页面结构变化，需手动操作")
        except PlaywrightTimeout:
            return await self._fallback_manual("密码修改页面操作超时")
