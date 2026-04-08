import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.models import Account

scheduler = AsyncIOScheduler()


def _job_id(account_id) -> str:
    return f"pwd_change_{account_id}"


async def _run_change(account_id):
    from app.services.password_changer import execute_password_change
    logger.info(f"[调度器] 触发自动改密: {account_id}")
    await execute_password_change(account_id)


def schedule_account(account: Account):
    """为单个账号设置定时任务"""
    job_id = _job_id(account.id)

    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    if not account.auto_change_enabled or account.status not in ("active",):
        return

    next_run = account.next_password_change
    if not next_run or next_run <= datetime.utcnow():
        next_run = datetime.utcnow() + timedelta(minutes=1)

    scheduler.add_job(
        _run_change,
        trigger=DateTrigger(run_date=next_run),
        args=[account.id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info(f"[调度器] 已设置定时任务: {account.email} -> {next_run}")


def unschedule_account(account_id):
    """移除某账号的定时任务"""
    try:
        scheduler.remove_job(_job_id(account_id))
    except Exception:
        pass


async def load_all_schedules():
    """启动时加载所有需要自动改密的账号"""
    async with async_session() as session:
        stmt = select(Account).where(
            Account.auto_change_enabled == True,
            Account.status == "active",
        )
        result = await session.execute(stmt)
        accounts = result.scalars().all()

        count = 0
        for account in accounts:
            schedule_account(account)
            count += 1

        logger.info(f"[调度器] 已加载 {count} 个自动改密计划")


async def start_scheduler():
    """启动调度器"""
    if not scheduler.running:
        scheduler.add_job(
            _check_overdue,
            trigger=IntervalTrigger(hours=1),
            id="check_overdue",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("[调度器] 已启动")
        await load_all_schedules()


async def _check_overdue():
    """定期检查是否有到期未执行的账号"""
    async with async_session() as session:
        stmt = select(Account).where(
            Account.auto_change_enabled == True,
            Account.status == "active",
            Account.next_password_change <= datetime.utcnow(),
        )
        result = await session.execute(stmt)
        overdue = result.scalars().all()

        for account in overdue:
            logger.info(f"[调度器] 发现到期账号: {account.email}")
            schedule_account(account)


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[调度器] 已关闭")
