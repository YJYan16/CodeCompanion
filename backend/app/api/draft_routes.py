from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.core.monitoring.error_tracker import record_error
from app.models.database_models import ErrorLog, StudentDraft, User
from app.models.schemas import ClientErrorReport, DraftRequest

router = APIRouter(tags=["drafts", "monitoring"])


@router.get("/drafts/{question_id}")
async def get_draft(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = (
        db.query(StudentDraft)
        .filter(
            StudentDraft.user_id == current_user.id,
            StudentDraft.question_id == question_id,
        )
        .first()
    )
    if not draft:
        return {"draft": None}
    return {
        "draft": {
            "question_id": draft.question_id,
            "code": draft.code,
            "language": draft.language,
            "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
        }
    }


@router.put("/drafts")
async def save_draft(
    request: DraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = (
        db.query(StudentDraft)
        .filter(
            StudentDraft.user_id == current_user.id,
            StudentDraft.question_id == request.question_id,
        )
        .first()
    )
    if draft:
        draft.code = request.code
        draft.language = request.language
        draft.updated_at = datetime.now()
    else:
        draft = StudentDraft(
            user_id=current_user.id,
            question_id=request.question_id,
            code=request.code,
            language=request.language,
        )
        db.add(draft)
    db.commit()
    return {"success": True}


@router.post("/errors/report")
async def report_client_error(
    report: ClientErrorReport,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    record_error(
        db,
        message=report.message,
        error_type="ClientError",
        path=report.url,
        method="CLIENT",
        user_id=current_user.id if current_user else None,
        stack_trace=report.stack,
        context={"component": report.component},
    )
    return {"success": True}


@router.get("/errors")
async def list_errors(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    logs = (
        db.query(ErrorLog)
        .order_by(ErrorLog.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return {
        "errors": [
            {
                "id": log.id,
                "message": log.message,
                "error_type": log.error_type,
                "path": log.path,
                "method": log.method,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }
