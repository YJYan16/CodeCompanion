# backend/app/main.py
import sys
import os

# 应用性能优化配置
def apply_performance_optimizations():
    """应用性能优化"""
    settings = None
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
        from config.settings import get_settings
        settings = get_settings()
    except Exception:
        pass
    
    # 使用 uvloop 加速异步操作（默认禁用，避免Windows兼容性问题）
    use_uvloop = getattr(settings, 'use_uvloop', False)
    if use_uvloop:
        try:
            import uvloop
            uvloop.install()
            print("uvloop 已启用，异步性能提升中...")
        except ImportError:
            print("uvloop 未安装，使用标准事件循环")

# 在导入其他模块前应用优化
apply_performance_optimizations()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import router
from .core.cache_service import init_cache
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import get_settings

app = FastAPI(
    title="码途智伴 API",
    description="基于多智能体协作的编程教学AI引擎",
    version="2.1.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api")

# 启动事件：初始化缓存
@app.on_event("startup")
async def startup_event():
    try:
        settings = get_settings()
        init_cache(
            namespace=settings.cache_namespace,
            lru_maxsize=settings.lru_cache_maxsize,
            lru_ttl=settings.lru_cache_ttl,
            redis_host=settings.redis_host,
            redis_port=settings.redis_port,
            redis_db=settings.redis_db,
            redis_password=settings.redis_password if settings.redis_password else None,
            use_redis=settings.redis_enabled
        )
        print("缓存系统已初始化")
    except Exception as e:
        print(f"缓存系统初始化失败: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)