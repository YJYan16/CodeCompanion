"""错误监控：持久化记录应用异常。"""
import traceback
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database_models import ErrorLog


def record_error(
    db: Session,
    *,
    message: str,
    error_type: str = "Exception",
    path: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    stack_trace: Optional[str] = None,
    context: Optional[dict] = None,
) -> ErrorLog:
    entry = ErrorLog(
        message=message[:2000],
        error_type=error_type[:128],
        path=path,
        method=method,
        user_id=user_id,
        stack_trace=(stack_trace or "")[:8000],
        context=context,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def record_exception(
    db: Session,
    exc: Exception,
    *,
    path: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    context: Optional[dict] = None,
) -> ErrorLog:
    return record_error(
        db,
        message=str(exc),
        error_type=type(exc).__name__,
        path=path,
        method=method,
        user_id=user_id,
        stack_trace=traceback.format_exc(),
        context=context,
    )
