from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import authenticate_user, create_access_token, get_current_user
from app.core.database import get_db
from app.models.database_models import User
from app.models.schemas import LoginRequest, LoginResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": user.username, "role": user.role})
    return LoginResponse(
        success=True,
        token=token,
        user={
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "class_name": user.class_name or "",
        },
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "role": current_user.role,
        "class_name": current_user.class_name or "",
    }
