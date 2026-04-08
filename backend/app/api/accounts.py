from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountOut, AccountWithPassword
from app.utils.crypto import encrypt, decrypt
from app.providers.factory import detect_provider_type
from app.services.scheduler import schedule_account, unschedule_account
from app.services.password_changer import execute_password_change

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/providers/supported")
async def get_supported_providers():
    from app.providers.base import BaseProvider
    return BaseProvider.get_provider_info()


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    search: str = "",
    provider_type: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Account).order_by(Account.created_at.desc())
    if search:
        stmt = stmt.where(Account.email.ilike(f"%{search}%"))
    if provider_type:
        stmt = stmt.where(Account.provider_type == provider_type)
    if status:
        stmt = stmt.where(Account.status == status)

    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return [AccountOut.model_validate(a) for a in accounts]


@router.post("", response_model=AccountOut, status_code=201)
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Account).where(Account.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "该邮箱已存在")

    provider_type = data.provider_type
    if not provider_type:
        detected = detect_provider_type(data.email)
        if not detected:
            raise HTTPException(400, "无法识别邮箱类型，请手动指定 provider_type")
        provider_type = detected

    now = datetime.utcnow()
    account = Account(
        email=data.email,
        provider_type=provider_type,
        encrypted_password=encrypt(data.password),
        display_name=data.display_name,
        auto_change_enabled=data.auto_change_enabled,
        change_interval_days=data.change_interval_days,
        password_rule=data.password_rule.model_dump_json() if data.password_rule else None,
        notes=data.notes,
        last_password_change=now,
        next_password_change=now + timedelta(days=data.change_interval_days) if data.auto_change_enabled else None,
        status="active",
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)

    if account.auto_change_enabled:
        schedule_account(account)

    return AccountOut.model_validate(account)


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "账号不存在")
    return AccountOut.model_validate(account)


@router.get("/{account_id}/password", response_model=AccountWithPassword)
async def get_account_password(account_id: UUID, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "账号不存在")

    out = AccountWithPassword.model_validate(account)
    out.current_password = decrypt(account.encrypted_password)
    return out


@router.put("/{account_id}", response_model=AccountOut)
async def update_account(account_id: UUID, data: AccountUpdate, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "账号不存在")

    if data.display_name is not None:
        account.display_name = data.display_name
    if data.password is not None:
        account.encrypted_password = encrypt(data.password)
        account.last_password_change = datetime.utcnow()
    if data.auto_change_enabled is not None:
        account.auto_change_enabled = data.auto_change_enabled
    if data.change_interval_days is not None:
        account.change_interval_days = data.change_interval_days
    if data.password_rule is not None:
        account.password_rule = data.password_rule.model_dump_json()
    if data.notes is not None:
        account.notes = data.notes
    if data.status is not None:
        account.status = data.status

    if account.auto_change_enabled and account.status == "active":
        account.next_password_change = datetime.utcnow() + timedelta(days=account.change_interval_days)
        schedule_account(account)
    else:
        unschedule_account(account.id)

    await db.flush()
    await db.refresh(account)
    return AccountOut.model_validate(account)


@router.delete("/{account_id}")
async def delete_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "账号不存在")

    unschedule_account(account.id)
    await db.delete(account)
    return {"message": "已删除"}


@router.post("/{account_id}/change-password")
async def trigger_change_password(account_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "账号不存在")

    background_tasks.add_task(_run_change, account_id)
    return {"message": "密码修改任务已提交", "account_email": account.email}


async def _run_change(account_id):
    await execute_password_change(account_id, force=True)


@router.post("/{account_id}/confirm-change")
async def confirm_change(account_id: UUID, new_password: str | None = None, db: AsyncSession = Depends(get_db)):
    from app.services.password_changer import confirm_manual_change
    try:
        account = await confirm_manual_change(account_id, new_password)
        return {"message": "已确认密码修改", "email": account.email}
    except ValueError as e:
        raise HTTPException(400, str(e))
