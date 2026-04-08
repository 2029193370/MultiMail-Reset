from app.providers.base import BaseProvider
from app.providers.qq_personal import QQPersonalProvider
from app.providers.netease_personal import NeteasePersonalProvider
from app.providers.outlook_personal import OutlookPersonalProvider
from app.providers.gmail_personal import GmailPersonalProvider

PROVIDER_MAP: dict[str, type[BaseProvider]] = {
    "qq": QQPersonalProvider,
    "netease": NeteasePersonalProvider,
    "outlook": OutlookPersonalProvider,
    "gmail": GmailPersonalProvider,
}


def create_provider(provider_type: str) -> BaseProvider:
    cls = PROVIDER_MAP.get(provider_type)
    if not cls:
        raise ValueError(f"不支持的邮箱类型: {provider_type}")
    return cls()


def detect_provider_type(email: str) -> str | None:
    """根据邮箱域名自动识别服务商类型"""
    domain = email.split("@")[-1].lower()
    domain_map = {
        "qq.com": "qq",
        "163.com": "netease",
        "126.com": "netease",
        "yeah.net": "netease",
        "outlook.com": "outlook",
        "hotmail.com": "outlook",
        "live.com": "outlook",
        "live.cn": "outlook",
        "gmail.com": "gmail",
        "googlemail.com": "gmail",
    }
    return domain_map.get(domain)
