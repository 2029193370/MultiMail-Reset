from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Account, PasswordHistory
from app.schemas.password_history import PasswordHistoryOut, PasswordHistoryDetail
from app.utils.crypto import decrypt

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[PasswordHistoryOut])
async def list_history(
    account_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PasswordHistory).order_by(PasswordHistory.created_at.desc())

    if account_id:
        stmt = stmt.where(PasswordHistory.account_id == UUID(account_id))
    if status:
        stmt = stmt.where(PasswordHistory.status == status)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    out = []
    for h in items:
        account = await db.get(Account, h.account_id)
        item = PasswordHistoryOut.model_validate(h)
        item.account_email = account.email if account else "已删除"
        out.append(item)
    return out


@router.get("/count")
async def history_count(
    account_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(func.count(PasswordHistory.id))
    if account_id:
        stmt = stmt.where(PasswordHistory.account_id == UUID(account_id))
    if status:
        stmt = stmt.where(PasswordHistory.status == status)
    total = await db.scalar(stmt)
    return {"total": total or 0}


@router.get("/{history_id}", response_model=PasswordHistoryDetail)
async def get_history_detail(history_id: UUID, db: AsyncSession = Depends(get_db)):
    h = await db.get(PasswordHistory, history_id)
    if not h:
        raise HTTPException(404, "记录不存在")

    account = await db.get(Account, h.account_id)
    detail = PasswordHistoryDetail.model_validate(h)
    detail.account_email = account.email if account else "已删除"
    detail.old_password = decrypt(h.encrypted_old_password) if h.encrypted_old_password else None
    detail.new_password = decrypt(h.encrypted_new_password) if h.encrypted_new_password else None
    return detail
