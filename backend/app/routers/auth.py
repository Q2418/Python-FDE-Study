from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import ACCESS_TOKEN_EXPIRE_MINUTES
from ..core.deps import get_current_user
from ..core.response import success
from ..core.security import create_access_token, verify_password
from ..database import get_db
from ..models.user import User
from ..schemas.auth import LoginRequest, LoginResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["登录认证"])


@router.post("/login", summary="账号登录")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if user.status != "启用":
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    role_codes = [role.code for role in user.roles]
    token = create_access_token(user.id, user.username, role_codes)
    payload = LoginResponse(
        token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo.from_user(user),
    )
    return success(payload.model_dump(), msg="登录成功")


@router.get("/me", summary="当前登录用户信息")
def me(user: User = Depends(get_current_user)):
    return success(UserInfo.from_user(user))
