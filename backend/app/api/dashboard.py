from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Account, PasswordHistory
from app.schemas.dashboard import DashboardStats
from app.schemas.password_history import PasswordHistoryOut
from app.schemas.account import AccountOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(Account.id)))
    active = await db.scalar(select(func.count(Account.id)).where(Account.status == "active"))
    auto_enabled = await db.scalar(select(func.count(Account.id)).where(Account.auto_change_enabled == True))
    pending = await db.scalar(select(func.count(Account.id)).where(Account.status == "pending_manual"))

    week_ago = datetime.utcnow() - timedelta(days=7)
    expiring = await db.scalar(
        select(func.count(Account.id)).where(
            Account.next_password_change != None,
            Account.next_password_change <= datetime.utcnow() + timedelta(days=3),
            Account.status == "active",
        )
    )

    recent_success = await db.scalar(
        select(func.count(PasswordHistory.id)).where(
            PasswordHistory.status == "success",
            PasswordHistory.created_at >= week_ago,
        )
    )
    recent_failed = await db.scalar(
        select(func.count(PasswordHistory.id)).where(
            PasswordHistory.status == "failed",
            PasswordHistory.created_at >= week_ago,
        )
    )

    stats = DashboardStats(
        total_accounts=total or 0,
        active_accounts=active or 0,
        auto_change_enabled=auto_enabled or 0,
        pending_manual=pending or 0,
        expiring_soon=expiring or 0,
        recent_success=recent_success or 0,
        recent_failed=recent_failed or 0,
    )

    expiring_stmt = (
        select(Account)
        .where(
            Account.next_password_change != None,
            Account.next_password_change <= datetime.utcnow() + timedelta(days=7),
            Account.status == "active",
        )
        .order_by(Account.next_password_change.asc())
        .limit(10)
    )
    expiring_accounts = (await db.execute(expiring_stmt)).scalars().all()

    pending_stmt = (
        select(Account)
        .where(Account.status == "pending_manual")
        .order_by(Account.updated_at.desc())
        .limit(10)
    )
    pending_accounts = (await db.execute(pending_stmt)).scalars().all()

    recent_history_stmt = (
        select(PasswordHistory)
        .order_by(PasswordHistory.created_at.desc())
        .limit(10)
    )
    recent_history = (await db.execute(recent_history_stmt)).scalars().all()

    history_out = []
    for h in recent_history:
        account = await db.get(Account, h.account_id)
        item = PasswordHistoryOut.model_validate(h)
        item.account_email = account.email if account else "已删除"
        history_out.append(item)

    return {
        "stats": stats,
        "expiring_accounts": [AccountOut.model_validate(a) for a in expiring_accounts],
        "pending_accounts": [AccountOut.model_validate(a) for a in pending_accounts],
        "recent_history": history_out,
    }
