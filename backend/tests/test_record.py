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


def make_asset(**overrides):
    data = {
        "asset_no": "ZC100",
        "name": "测试资产",
        "category": "电脑设备",
        "brand": "TestBrand",
        "model": "T-1",
        "price": 1000.0,
        "purchase_date": "2024-01-01",
        "status": "空闲",
        "remark": "测试数据",
    }
    data.update(overrides)
    return data


def create_employee(client, **overrides):
    return client.post("/api/employee", json=make_employee(**overrides)).json()["data"]["id"]


def create_asset(client, **overrides):
    return client.post("/api/asset", json=make_asset(**overrides)).json()["data"]["id"]


def test_borrow_flow(client):
    emp_id = create_employee(client)
    asset_id = create_asset(client)

    resp = client.post(f"/api/asset/{asset_id}/borrow", json={"employee_id": emp_id, "remark": "测试领用"})
    body = resp.json()
    assert resp.status_code == 200
    assert body["code"] == 200
    assert body["msg"].endswith("领用成功")
    assert body["data"]["status"] == "已领用"
    assert body["data"]["user_id"] == emp_id

    resp = client.post(f"/api/asset/{asset_id}/borrow", json={"employee_id": emp_id})
    assert resp.status_code == 400
    assert "无法领用" in resp.json()["msg"]

    resp = client.get("/api/record/list", params={"action": "领用"})
    assert resp.json()["data"]["total"] == 1
    item = resp.json()["data"]["items"][0]
    assert item["asset_no"] == "ZC100"
    assert item["employee_name"] == "测试员工"
    assert item["operator_name"] == "系统管理员"
    assert item["remark"] == "测试领用"


def test_return_flow(client):
    emp_id = create_employee(client)
    asset_id = create_asset(client)
    client.post(f"/api/asset/{asset_id}/borrow", json={"employee_id": emp_id})

    resp = client.post(f"/api/asset/{asset_id}/return", json={"remark": "测试归还"})
    body = resp.json()
    assert resp.status_code == 200
    assert body["msg"].endswith("归还成功")
    assert body["data"]["status"] == "空闲"
    assert body["data"]["user_id"] is None

    resp = client.get("/api/record/list")
    assert resp.json()["data"]["total"] == 2
    actions = [item["action"] for item in resp.json()["data"]["items"]]
    assert "领用" in actions and "归还" in actions

    resp = client.post(f"/api/asset/{asset_id}/return", json={})
    assert resp.status_code == 400
    assert "无需归还" in resp.json()["msg"]


def test_return_not_borrowed(client):
    asset_id = create_asset(client)
    resp = client.post(f"/api/asset/{asset_id}/return", json={})
    assert resp.status_code == 400
    assert "无需归还" in resp.json()["msg"]


def test_borrow_asset_not_found(client):
    resp = client.post("/api/asset/999/borrow", json={"employee_id": 1})
    assert resp.status_code == 404
    assert resp.json()["msg"] == "资产不存在"


def test_borrow_employee_not_found(client):
    asset_id = create_asset(client)
    resp = client.post(f"/api/asset/{asset_id}/borrow", json={"employee_id": 999})
    assert resp.status_code == 404
    assert resp.json()["msg"] == "领用人员工不存在"


def test_borrow_employee_left(client):
    emp_id = create_employee(client, status="离职")
    asset_id = create_asset(client)
    resp = client.post(f"/api/asset/{asset_id}/borrow", json={"employee_id": emp_id})
    assert resp.status_code == 400
    assert "已离职" in resp.json()["msg"]


def test_borrow_not_idle_asset(client):
    emp_id = create_employee(client)
    asset_id = create_asset(client, status="维修")
    resp = client.post(f"/api/asset/{asset_id}/borrow", json={"employee_id": emp_id})
    assert resp.status_code == 400
    assert "维修" in resp.json()["msg"]


def test_borrow_requires_admin(employee_client):
    resp = employee_client.post("/api/asset/1/borrow", json={"employee_id": 1})
    assert resp.status_code == 403
    assert resp.json()["msg"] == "权限不足，仅管理员可操作"

    resp = employee_client.post("/api/asset/1/return", json={})
    assert resp.status_code == 403


def test_record_list_filter(client):
    emp_id = create_employee(client)
    asset1 = create_asset(client, asset_no="ZC101", name="资产甲")
    asset2 = create_asset(client, asset_no="ZC102", name="资产乙")
    client.post(f"/api/asset/{asset1}/borrow", json={"employee_id": emp_id})
    client.post(f"/api/asset/{asset2}/borrow", json={"employee_id": emp_id})
    client.post(f"/api/asset/{asset2}/return", json={})

    resp = client.get("/api/record/list", params={"asset_name": "资产乙"})
    assert resp.json()["data"]["total"] == 2

    resp = client.get("/api/record/list", params={"action": "归还"})
    assert resp.json()["data"]["total"] == 1

    resp = client.get("/api/record/list", params={"page": 1, "size": 2})
    body = resp.json()
    assert body["data"]["total"] == 3
    assert len(body["data"]["items"]) == 2
