def login_token(client, username, password="123456"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["data"]["token"]


EMPLOYEE_PAYLOAD = {
    "emp_no": "E900",
    "name": "鉴权测试员工",
    "gender": "男",
    "department": "技术部",
    "phone": "13800000900",
    "email": "auth900@example.com",
    "hire_date": "2024-01-01",
    "status": "在职",
}


def test_login_ok(raw_client):
    resp = raw_client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    body = resp.json()
    assert resp.status_code == 200
    assert body["code"] == 200
    assert body["msg"] == "登录成功"
    assert body["data"]["token"]
    assert body["data"]["token_type"] == "Bearer"
    assert body["data"]["expires_in"] > 0
    assert body["data"]["user"]["username"] == "admin"
    assert body["data"]["user"]["roles"] == ["admin"]


def test_login_wrong_password(raw_client):
    resp = raw_client.post("/api/auth/login", json={"username": "admin", "password": "wrong123"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 401
    assert resp.json()["msg"] == "账号或密码错误"


def test_login_unknown_user(raw_client):
    resp = raw_client.post("/api/auth/login", json={"username": "nobody", "password": "123456"})
    assert resp.status_code == 401
    assert resp.json()["msg"] == "账号或密码错误"


def test_me(raw_client):
    token = login_token(raw_client, "admin")
    resp = raw_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = resp.json()
    assert body["data"]["username"] == "admin"
    assert body["data"]["real_name"] == "系统管理员"
    assert "admin" in body["data"]["roles"]


def test_business_api_requires_login(raw_client):
    for path in ["/api/employee/list", "/api/asset/list", "/api/record/list"]:
        resp = raw_client.get(path)
        assert resp.status_code == 401, path
        assert resp.json()["code"] == 401
        assert resp.json()["msg"] == "未登录或登录已过期，请先登录"


def test_invalid_token(raw_client):
    resp = raw_client.get("/api/employee/list", headers={"Authorization": "Bearer bad.token.value"})
    assert resp.status_code == 401
    assert resp.json()["msg"] == "登录凭证无效，请重新登录"


def test_employee_can_read_but_not_write(raw_client, employee_client):
    resp = employee_client.get("/api/employee/list")
    assert resp.status_code == 200

    resp = employee_client.post("/api/employee", json=EMPLOYEE_PAYLOAD)
    assert resp.status_code == 403
    assert resp.json()["msg"] == "权限不足，仅管理员可操作"

    resp = employee_client.delete("/api/employee/1")
    assert resp.status_code == 403
