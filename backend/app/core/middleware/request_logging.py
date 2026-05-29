"""HTTP 请求日志与全局异常处理中间件。"""
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import SessionLocal
from app.core.monitoring.error_tracker import record_exception
from app.core.utils.logging_config import get_logger

logger = get_logger("http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.perf_counter()

        logger.info(
            "→ %s %s [%s]",
            request.method,
            request.url.path,
            request_id,
        )

        try:
            response = await call_next(request)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "← %s %s %s %.1fms [%s]",
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
                request_id,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.exception(
                "✗ %s %s failed %.1fms [%s]: %s",
                request.method,
                request.url.path,
                elapsed,
                request_id,
                exc,
            )
            db = SessionLocal()
            try:
                record_exception(
                    db,
                    exc,
                    path=str(request.url.path),
                    method=request.method,
                    context={"request_id": request_id},
                )
            finally:
                db.close()
            return JSONResponse(
                status_code=500,
                content={"detail": "服务器内部错误", "request_id": request_id},
            )
