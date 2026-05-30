# backend/app/main.py
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def apply_performance_optimizations():
    settings = None
    try:
        from config.settings import get_settings
        settings = get_settings()
    except Exception:
        pass

    use_uvloop = getattr(settings, "use_uvloop", False)
    if use_uvloop:
        try:
            import uvloop
            uvloop.install()
        except ImportError:
            pass


apply_performance_optimizations()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from .api.endpoints import router
from .api.auth_routes import router as auth_router
from .api.draft_routes import router as draft_router
from .api.websocket_routes import router as ws_router
from .core.cache_service import init_cache
from .core.database import SessionLocal
from .core.init_db import init_db, add_initial_data, migrate_schema
from .core.middleware.request_logging import RequestLoggingMiddleware
from .core.utils.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger("main")

app = FastAPI(
    title="码途智伴 API",
    description="基于多智能体协作的编程教学AI引擎",
    version="2.2.0",
)

settings = get_settings()

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(draft_router, prefix="/api")
app.include_router(ws_router)


# ---------- 前端 SPA 静态文件服务（无需 Node.js） ----------
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    _assets = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """SPA 兜底：非 API 路径返回 index.html，由 Vue Router 处理"""
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    logger.info("前端 SPA 模式已启用（dist 目录）")

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        migrate_schema()
        db = SessionLocal()
        try:
            add_initial_data(db)
        finally:
            db.close()
        logger.info("数据库已初始化")
    except Exception as e:
        logger.error("数据库初始化失败: %s", e)

    try:
        init_cache(
            namespace=settings.cache_namespace,
            lru_maxsize=settings.lru_cache_maxsize,
            lru_ttl=settings.lru_cache_ttl,
            redis_host=settings.redis_host,
            redis_port=settings.redis_port,
            redis_db=settings.redis_db,
            redis_password=settings.redis_password if settings.redis_password else None,
            use_redis=settings.redis_enabled,
        )
        logger.info("缓存系统已初始化")
    except Exception as e:
        logger.error("缓存系统初始化失败: %s", e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
