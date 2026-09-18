DOC_TEXT = (
    "资产领用流程：员工提交领用申请，管理员审批后，资产状态从空闲变为已领用。"
    "归还流程：管理员确认归还后，资产状态从已领用恢复为空闲。"
    "资产报废需要管理员确认，报废后不可再领用。"
).encode("utf-8")


def create_employee(client, **overrides):
    data = {
        "emp_no": "E400",
        "name": "AI测试员工",
        "gender": "男",
        "department": "技术部",
        "phone": "13800000400",
        "email": "ai400@example.com",
        "hire_date": "2024-01-01",
        "status": "在职",
    }
    data.update(overrides)
    return client.post("/api/employee", json=data).json()["data"]["id"]


def create_asset(client, **overrides):
    data = {
        "asset_no": "ZCAI01",
        "name": "AI测试资产",
        "category": "电脑设备",
        "price": 100.0,
        "status": "空闲",
    }
    data.update(overrides)
    return client.post("/api/asset", json=data).json()["data"]["id"]


def test_ai_document_flow(client):
    resp = client.post("/api/ai/document", files={"file": ("流程说明.txt", DOC_TEXT, "text/plain")})
    body = resp.json()
    assert resp.status_code == 200
    assert body["msg"] == "文档上传成功"
    assert body["data"]["chunk_count"] >= 1
    doc_id = body["data"]["id"]

    resp = client.get("/api/ai/document/list")
    assert resp.json()["data"][0]["filename"] == "流程说明.txt"

    resp = client.post("/api/ai/ask", json={"question": "资产领用流程是什么？", "top_k": 3})
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["mode"] == "mock"
    assert "模拟模式" in body["data"]["answer"]
    assert len(body["data"]["sources"]) >= 1
    assert body["data"]["sources"][0]["document"] == "流程说明.txt"

    resp = client.delete(f"/api/ai/document/{doc_id}")
    assert resp.json()["msg"] == "删除成功"
    assert client.get("/api/ai/document/list").json()["data"] == []


def test_ai_ask_empty_knowledge_base(client):
    resp = client.post("/api/ai/ask", json={"question": "资产领用流程是什么？"})
    assert resp.status_code == 200
    assert "没有找到相关信息" in resp.json()["data"]["answer"]


def test_ai_document_reject_bad_extension(client):
    resp = client.post("/api/ai/document", files={"file": ("恶意.exe", b"x", "application/octet-stream")})
    assert resp.status_code == 400
    assert "txt / md / docx" in resp.json()["msg"]


def test_ai_document_requires_admin(employee_client):
    resp = employee_client.post("/api/ai/document", files={"file": ("a.txt", b"x", "text/plain")})
    assert resp.status_code == 403


def test_ai_chat_tool_mock(client):
    create_employee(client, emp_no="E401", name="工具甲", department="技术部", phone="13800000401")
    create_employee(client, emp_no="E402", name="工具乙", department="技术部", phone="13800000402")
    create_asset(client, asset_no="ZCAI02", name="空闲设备", status="空闲")
    create_asset(client, asset_no="ZCAI03", name="维修设备", status="维修")

    resp = client.post("/api/ai/chat", json={"message": "技术部有哪些员工？"})
    body = resp.json()["data"]
    assert body["tool"]["name"] == "query_employees"
    assert body["tool"]["arguments"]["department"] == "技术部"
    assert body["data"]["count"] == 2

    resp = client.post("/api/ai/chat", json={"message": "现在空闲的资产有哪些？"})
    body = resp.json()["data"]
    assert body["tool"]["name"] == "query_assets"
    assert body["tool"]["arguments"]["status"] == "空闲"
    assert body["data"]["count"] == 1

    resp = client.post("/api/ai/chat", json={"message": "最近的领用记录"})
    body = resp.json()["data"]
    assert body["tool"]["name"] == "query_records"

    assert body["mode"] == "mock"
    assert "模拟模式" in body["answer"]
