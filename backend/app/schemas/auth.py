from typing import List, Optional

from pydantic import BaseModel, Field

from ..models.user import User


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="登录账号")
    password: str = Field(..., min_length=1, max_length=50, description="密码")


class UserInfo(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    roles: List[str] = []

    @classmethod
    def from_user(cls, user: User) -> "UserInfo":
        return cls(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            roles=[role.code for role in user.roles],
        )


class LoginResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserInfo
