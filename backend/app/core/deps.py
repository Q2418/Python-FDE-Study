import jwt as pyjwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from .security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录或登录已过期，请先登录")
    try:
        payload = decode_access_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="登录凭证无效，请重新登录")
    try:
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="登录凭证无效，请重新登录")
    user = db.get(User, user_id)
    if not user or user.status != "启用":
        raise HTTPException(status_code=401, detail="账号不存在或已被禁用")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.has_role("admin"):
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可操作")
    return user
