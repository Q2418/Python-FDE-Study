def make_employee(**overrides):
    data = {
        "emp_no": "E100",
        "name": "测试员工",
        "gender": "男",
        "department": "技术部",
        "position": "工程师",
        "phone": "13800000099",
        "email": "test100@example.com",
        "hire_date": "2024-01-01",
        "status": "在职",
    }
    data.update(overrides)
    return data


def test_create_employee_ok(client):
    resp = client.post("/api/employee", json=make_employee())
    body = resp.json()
    assert resp.status_code == 200
    assert body["code"] == 200
    assert body["msg"] == "新增成功"
    assert body["data"]["emp_no"] == "E100"
    assert body["data"]["hire_date"] == "2024-01-01"


def test_create_employee_missing_name(client):
    data = make_employee()
    del data["name"]
    resp = client.post("/api/employee", json=data)
    body = resp.json()
    assert resp.status_code == 422
    assert body["code"] == 422
    assert "姓名" in body["msg"]


def test_create_employee_bad_phone(client):
    resp = client.post("/api/employee", json=make_employee(phone="abc123"))
    assert resp.status_code == 422
    assert "手机号" in resp.json()["msg"]


def test_create_employee_bad_email(client):
    resp = client.post("/api/employee", json=make_employee(email="not-an-email"))
    assert resp.status_code == 422
    assert "邮箱" in resp.json()["msg"]


def test_create_employee_bad_status(client):
    resp = client.post("/api/employee", json=make_employee(status="随便填"))
    assert resp.status_code == 422
    assert "状态" in resp.json()["msg"]


def test_create_duplicate_emp_no(client):
    assert client.post("/api/employee", json=make_employee()).status_code == 200
    resp = client.post("/api/employee", json=make_employee(name="另一个人"))
    assert resp.status_code == 400
    assert resp.json()["msg"] == "工号已存在，请更换后重试"


def test_list_pagination_and_filter(client):
    for i in range(3):
        client.post(
            "/api/employee",
            json=make_employee(emp_no=f"E10{i}", name=f"员工{i}", phone=f"1380000000{i}"),
        )
    resp = client.get("/api/employee/list", params={"page": 1, "size": 2})
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 3
    assert len(body["data"]["items"]) == 2
    assert "create_time" not in body["data"]["items"][0]

    resp = client.get("/api/employee/list", params={"name": "员工1"})
    assert resp.json()["data"]["total"] == 1

    resp = client.get("/api/employee/list", params={"department": "技术部"})
    assert resp.json()["data"]["total"] == 3

    resp = client.get("/api/employee/list", params={"department": "不存在的部门"})
    assert resp.json()["data"]["total"] == 0


def test_get_employee_and_404(client):
    eid = client.post("/api/employee", json=make_employee()).json()["data"]["id"]
    resp = client.get(f"/api/employee/{eid}")
    assert resp.json()["data"]["name"] == "测试员工"

    resp = client.get("/api/employee/999")
    assert resp.status_code == 404
    assert resp.json()["msg"] == "员工不存在"


def test_update_employee(client):
    eid = client.post("/api/employee", json=make_employee()).json()["data"]["id"]
    resp = client.put(f"/api/employee/{eid}", json={"position": "高级工程师", "status": "离职"})
    body = resp.json()
    assert body["msg"] == "修改成功"
    assert body["data"]["position"] == "高级工程师"
    assert body["data"]["status"] == "离职"
    assert body["data"]["emp_no"] == "E100"


def test_update_duplicate_emp_no(client):
    eid = client.post("/api/employee", json=make_employee()).json()["data"]["id"]
    client.post("/api/employee", json=make_employee(emp_no="E200", name="二号员工", phone="13800000100"))
    resp = client.put(f"/api/employee/{eid}", json={"emp_no": "E200"})
    assert resp.status_code == 400
    assert resp.json()["msg"] == "工号已存在，请更换后重试"


def test_delete_employee(client):
    eid = client.post("/api/employee", json=make_employee()).json()["data"]["id"]
    resp = client.delete(f"/api/employee/{eid}")
    assert resp.json()["msg"] == "删除成功"
    assert client.get(f"/api/employee/{eid}").status_code == 404
