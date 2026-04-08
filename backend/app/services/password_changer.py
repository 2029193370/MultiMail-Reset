from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.models import Account, PasswordHistory
from app.providers.factory import create_provider
from app.utils.crypto import encrypt, decrypt
from app.utils.password_gen import generate_password


async def execute_password_change(account_id, force: bool = False):
    """
    对单个账号执行密码变更流程：
    1. 生成新密码
    2. 尝试自动化改密
    3. 成功则保存新密码，失败则标记为待手动
    """
    async with async_session() as session:
        account = await session.get(Account, account_id)
        if not account:
            logger.error(f"账号不存在: {account_id}")
            return

        if not force and account.status not in ("active",):
            logger.info(f"账号 {account.email} 状态为 {account.status}，跳过改密")
            return

        current_password = decrypt(account.encrypted_password)
        new_password = generate_password(account.password_rule)

        history = PasswordHistory(
            account_id=account.id,
            encrypted_old_password=account.encrypted_password,
            encrypted_new_password=encrypt(new_password),
            change_method="auto",
            status="pending",
        )
        session.add(history)
        await session.flush()

        try:
            provider = create_provider(account.provider_type)
            result = await provider.change_password(account.email, current_password, new_password)

            if result.success:
                account.encrypted_password = encrypt(new_password)
                account.last_password_change = datetime.utcnow()
                account.next_password_change = datetime.utcnow() + timedelta(days=account.change_interval_days)
                account.status = "active"
                history.status = "success"
                history.change_method = result.method
                logger.info(f"[自动] 密码修改成功: {account.email}")

                if account.auto_change_enabled:
                    from app.services.scheduler import schedule_account
                    schedule_account(account)

            elif result.needs_manual:
                account.status = "pending_manual"
                history.status = "pending"
                history.change_method = "manual"
                history.error_message = result.error_message
                logger.warning(f"[手动] 需手动改密: {account.email} - {result.error_message}")

            else:
                account.status = "error"
                history.status = "failed"
                history.error_message = result.error_message
                logger.error(f"[失败] 密码修改失败: {account.email} - {result.error_message}")

        except Exception as e:
            account.status = "error"
            history.status = "failed"
            history.error_message = str(e)
            logger.exception(f"密码修改异常: {account.email}")

        await session.commit()


async def confirm_manual_change(account_id, new_password: str | None = None):
    """
    用户手动修改密码后确认：
    - 如果提供了 new_password，使用用户提供的密码
    - 否则使用之前生成的密码
    """
    async with async_session() as session:
        account = await session.get(Account, account_id)
        if not account:
            raise ValueError("账号不存在")

        stmt = (
            select(PasswordHistory)
            .where(PasswordHistory.account_id == account_id, PasswordHistory.status == "pending")
            .order_by(PasswordHistory.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        history = result.scalar_one_or_none()

        if not new_password and not history:
            raise ValueError("无待确认的密码变更记录，且未提供新密码")

        if new_password:
            account.encrypted_password = encrypt(new_password)
            if history:
                history.encrypted_new_password = encrypt(new_password)
        elif history:
            account.encrypted_password = history.encrypted_new_password

        account.last_password_change = datetime.utcnow()
        account.next_password_change = datetime.utcnow() + timedelta(days=account.change_interval_days)
        account.status = "active"

        if history:
            history.status = "success"
            history.change_method = "manual"

        await session.commit()

        if account.auto_change_enabled:
            from app.services.scheduler import schedule_account
            schedule_account(account)

        return account
