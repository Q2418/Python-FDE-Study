import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  确保模型注册到 Base
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.user import Role, User

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

ADMIN_PASSWORD_HASH = hash_password("123456")
EMPLOYEE_PASSWORD_HASH = hash_password("123456")


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def seed_users():
    db = TestingSessionLocal()
    try:
        admin_role = Role(code="admin", name="管理员")
        employee_role = Role(code="employee", name="普通员工")
        db.add_all([admin_role, employee_role])
        db.flush()
        admin = User(username="admin", password_hash=ADMIN_PASSWORD_HASH, real_name="系统管理员")
        admin.roles.append(admin_role)
        zhangsan = User(username="zhangsan", password_hash=EMPLOYEE_PASSWORD_HASH, real_name="张伟")
        zhangsan.roles.append(employee_role)
        db.add_all([admin, zhangsan])
        db.commit()
    finally:
        db.close()


class AuthClient:
    """自动携带登录 Token 的测试客户端"""

    def __init__(self, client: TestClient, headers: dict):
        self.client = client
        self.headers = headers

    def request(self, method, url, **kwargs):
        headers = dict(self.headers)
        headers.update(kwargs.pop("headers", None) or {})
        return self.client.request(method, url, headers=headers, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)


def login_token(client: TestClient, username: str, password: str = "123456") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["data"]["token"]


@pytest.fixture()
def raw_client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_users()
    return TestClient(app)


@pytest.fixture()
def client(raw_client):
    token = login_token(raw_client, "admin")
    return AuthClient(raw_client, {"Authorization": f"Bearer {token}"})


@pytest.fixture()
def employee_client(raw_client):
    token = login_token(raw_client, "zhangsan")
    return AuthClient(raw_client, {"Authorization": f"Bearer {token}"})
