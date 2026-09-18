def make_employee(**overrides):
    data = {
        "emp_no": "E300",
        "name": "扩展测试员工",
        "gender": "男",
        "department": "技术部",
        "position": "工程师",
        "phone": "13800000300",
        "email": "ext300@example.com",
        "hire_date": "2024-01-01",
        "status": "在职",
    }
    data.update(overrides)
    return data


def create_employee(client, **overrides):
    return client.post("/api/employee", json=make_employee(**overrides)).json()["data"]["id"]


def test_advanced_filter_and_sort(client):
    create_employee(client, emp_no="E301", name="张三", department="技术部", hire_date="2023-01-01")
    create_employee(client, emp_no="E302", name="李四", department="人事部", hire_date="2024-05-01", status="离职")
    create_employee(client, emp_no="E303", name="王五", department="技术部", hire_date="2022-03-01")

    resp = client.get("/api/employee/list", params={"status": "在职"})
    assert resp.json()["data"]["total"] == 2

    resp = client.get("/api/employee/list", params={"hire_date_start": "2023-01-01", "hire_date_end": "2024-12-31"})
    assert resp.json()["data"]["total"] == 2

    resp = client.get("/api/employee/list", params={"sort_by": "emp_no", "sort_order": "asc"})
    assert [item["emp_no"] for item in resp.json()["data"]["items"]] == ["E301", "E302", "E303"]

    resp = client.get("/api/employee/list", params={"sort_by": "hire_date", "sort_order": "desc"})
    assert [item["hire_date"] for item in resp.json()["data"]["items"]] == ["2024-05-01", "2023-01-01", "2022-03-01"]

    resp = client.get("/api/employee/list", params={"sort_order": "bad"})
    assert resp.status_code == 422


def test_attachment_upload_download_delete(client):
    emp_id = create_employee(client)

    resp = client.post(
        f"/api/employee/{emp_id}/attachment",
        files={"file": ("测试文档.txt", b"hello attachment", "text/plain")},
    )
    body = resp.json()
    assert resp.status_code == 200
    assert body["msg"] == "附件上传成功"
    assert body["data"]["attachment_name"] == "测试文档.txt"

    resp = client.get(f"/api/employee/{emp_id}/attachment")
    assert resp.status_code == 200
    assert resp.content == b"hello attachment"

    resp = client.get("/api/employee/list")
    assert resp.json()["data"]["items"][0]["attachment_name"] == "测试文档.txt"

    resp = client.delete(f"/api/employee/{emp_id}/attachment")
    assert resp.json()["msg"] == "附件已删除"
    assert client.get(f"/api/employee/{emp_id}/attachment").status_code == 404


def test_attachment_reject_bad_extension(client):
    emp_id = create_employee(client)
    resp = client.post(
        f"/api/employee/{emp_id}/attachment",
        files={"file": ("hack.exe", b"x", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "不支持的文件类型" in resp.json()["msg"]


def test_attachment_reject_oversize(client):
    emp_id = create_employee(client)
    big_data = b"0" * (5 * 1024 * 1024 + 1)
    resp = client.post(
        f"/api/employee/{emp_id}/attachment",
        files={"file": ("big.txt", big_data, "text/plain")},
    )
    assert resp.status_code == 400
    assert "5MB" in resp.json()["msg"]


def test_attachment_requires_admin(employee_client):
    resp = employee_client.post(
        "/api/employee/1/attachment",
        files={"file": ("a.txt", b"x", "text/plain")},
    )
    assert resp.status_code == 403


def test_export_excel(client):
    create_employee(client)
    resp = client.get("/api/employee/export")
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert resp.content[:2] == b"PK"
    assert "attachment" in resp.headers["content-disposition"]


def test_export_excel_with_filter(client):
    create_employee(client, emp_no="E311", name="导出甲", department="技术部")
    create_employee(client, emp_no="E312", name="导出乙", department="人事部", phone="13800000312")
    resp = client.get("/api/employee/export", params={"department": "技术部"})
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"
