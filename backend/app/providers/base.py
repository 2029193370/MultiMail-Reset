from abc import ABC, abstractmethod
from dataclasses import dataclass

from loguru import logger


@dataclass
class ChangePasswordResult:
    success: bool
    method: str = "auto"
    error_message: str = ""
    needs_manual: bool = False
    manual_url: str = ""
    manual_instructions: str = ""


class BaseProvider(ABC):
    """个人邮箱改密码的基类"""

    provider_type: str = ""
    display_name: str = ""
    change_password_url: str = ""

    @abstractmethod
    async def change_password(self, email: str, old_password: str, new_password: str) -> ChangePasswordResult:
        """尝试自动化改密码，返回结果"""
        ...

    async def _fallback_manual(self, reason: str) -> ChangePasswordResult:
        logger.warning(f"[{self.provider_type}] 自动化失败，降级为手动模式: {reason}")
        return ChangePasswordResult(
            success=False,
            method="manual",
            needs_manual=True,
            error_message=reason,
            manual_url=self.change_password_url,
            manual_instructions=f"请手动前往 {self.change_password_url} 修改密码",
        )

    @staticmethod
    def get_provider_info() -> list[dict]:
        return [
            {
                "type": "qq",
                "name": "QQ邮箱",
                "domains": ["qq.com"],
                "change_url": "https://aq.qq.com/cn2/index",
            },
            {
                "type": "netease",
                "name": "网易邮箱",
                "domains": ["163.com", "126.com", "yeah.net"],
                "change_url": "https://reg.163.com/naq/safe-index",
            },
            {
                "type": "outlook",
                "name": "Outlook / Hotmail",
                "domains": ["outlook.com", "hotmail.com", "live.com", "live.cn"],
                "change_url": "https://account.live.com/password/Change",
            },
            {
                "type": "gmail",
                "name": "Gmail",
                "domains": ["gmail.com", "googlemail.com"],
                "change_url": "https://myaccount.google.com/signinoptions/password",
            },
        ]
