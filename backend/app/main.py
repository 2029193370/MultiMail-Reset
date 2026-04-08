from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.api import accounts, dashboard, history

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    from app.database import init_db
    await init_db()
    logger.info("数据库表已就绪")

    from app.services.scheduler import start_scheduler, shutdown_scheduler
    await start_scheduler()

    yield

    shutdown_scheduler()
    logger.info("应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="个人邮箱自动改密码系统 - 周期性自动修改邮箱密码，确保账号安全",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(history.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
