from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_accounts: int = 0
    active_accounts: int = 0
    auto_change_enabled: int = 0
    pending_manual: int = 0
    expiring_soon: int = 0
    recent_success: int = 0
    recent_failed: int = 0
