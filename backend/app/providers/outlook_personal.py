from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from app.providers.base import BaseProvider, ChangePasswordResult


class OutlookPersonalProvider(BaseProvider):
    provider_type = "outlook"
    display_name = "Outlook / Hotmail"
    change_password_url = "https://account.live.com/password/Change"

    async def change_password(self, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        """Microsoft 个人账户 (Outlook/Hotmail/Live) 密码修改。"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    return await self._attempt_change(browser, email, old_password, new_password)
                finally:
                    await browser.close()
        except PlaywrightTimeout:
            logger.error(f"[Outlook] 页面加载超时: {email}")
            return await self._fallback_manual("页面加载超时，请手动修改")
        except Exception as e:
            logger.error(f"[Outlook] 自动化异常: {e}")
            return await self._fallback_manual(f"自动化异常: {str(e)}")

    async def _attempt_change(self, browser, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        await page.goto("https://login.live.com/", wait_until="networkidle", timeout=15000)

        try:
            await page.fill('input[type="email"]', email, timeout=5000)
            await page.click('input[type="submit"]', timeout=3000)
            await page.wait_for_timeout(2000)
            await page.fill('input[type="password"]', old_password, timeout=5000)
            await page.click('input[type="submit"]', timeout=3000)
            await page.wait_for_timeout(3000)
        except PlaywrightTimeout:
            return await self._fallback_manual("登录页面操作超时")

        if await page.locator('#idTd_Tile_ErrorMsg_Login').count() > 0:
            return ChangePasswordResult(success=False, error_message="登录失败，请检查邮箱和密码是否正确")

        two_fa = (
            await page.locator('text=验证你的身份').count() > 0
            or await page.locator('text=Verify your identity').count() > 0
        )
        if two_fa:
            return await self._fallback_manual("需要双因素验证，请手动完成")

        try:
            await page.goto("https://account.live.com/password/Change", wait_until="networkidle", timeout=15000)

            await page.fill('input[id="iOldPwd"], input[name="oldPassword"]', old_password, timeout=5000)
            await page.fill('input[id="iNewPwd"], input[name="newPassword"]', new_password, timeout=3000)
            await page.fill('input[id="iRetypeNewPwd"], input[name="reNewPassword"]', new_password, timeout=3000)
            await page.click('button[type="submit"], input[type="submit"]', timeout=3000)
            await page.wait_for_timeout(3000)

            current_url = page.url.lower()
            if "changed" in current_url or "security" in current_url:
                return ChangePasswordResult(success=True, method="auto")

            if "password/change" not in current_url:
                return ChangePasswordResult(success=True, method="auto")

            return await self._fallback_manual("密码修改提交后未确认成功")
        except PlaywrightTimeout:
            return await self._fallback_manual("密码修改页面操作超时")
