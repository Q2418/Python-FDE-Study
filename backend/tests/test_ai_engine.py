def test_prompt_list_and_reload(client):
    resp = client.get("/api/ai/prompt/list")
    body = resp.json()
    assert resp.status_code == 200
    versions = {item["key"]: item["version"] for item in body["data"]}
    assert versions.get("code_generate") == "v1.1"
    assert versions.get("code_review") == "v1.0"

    resp = client.post("/api/ai/prompt/reload")
    assert resp.json()["msg"] == "提示词配置已重新加载"


def test_prompt_render_variables():
    from app.core.prompt_manager import render_prompt

    prompt = render_prompt("code_generate", requirement="新增离职字段", table_schema="employee 表结构", code_style="旧代码")
    assert "新增离职字段" in prompt["user"]
    assert "employee 表结构" in prompt["user"]
    assert "{requirement}" not in prompt["user"]
    assert prompt["version"] == "v1.1"
    assert "pytest 测试用例建议" in prompt["user"]

    review = render_prompt("code_review", requirement="新增接口", code="def foo(): pass")
    assert '"passed"' in review["user"]


def test_skill_list_and_run(client):
    resp = client.get("/api/ai/skill/list")
    names = {item["name"] for item in resp.json()["data"]}
    assert {"query_employees", "query_assets", "query_records", "query_table_schema", "read_project_file"} <= names

    resp = client.post("/api/ai/skill/run", json={"name": "query_table_schema", "arguments": {"table": "employee"}})
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["count"] == 1
    assert body["data"]["tables"][0]["表名"] == "employee"
    field_names = [field["字段"] for field in body["data"]["tables"][0]["字段"]]
    assert "emp_no" in field_names and "attachment_name" in field_names


def test_skill_read_project_file(client):
    resp = client.post("/api/ai/skill/run", json={"name": "read_project_file", "arguments": {"path": "backend/app/main.py"}})
    body = resp.json()
    assert body["code"] == 200
    assert "FastAPI" in body["data"]["content"]


def test_skill_read_file_security(client):
    resp = client.post(
        "/api/ai/skill/run",
        json={"name": "read_project_file", "arguments": {"path": "../../Windows/win.ini"}},
    )
    assert resp.status_code == 400
    assert "非法路径" in resp.json()["msg"]

    resp = client.post(
        "/api/ai/skill/run",
        json={"name": "read_project_file", "arguments": {"path": "backend/app/config.py.exe"}},
    )
    assert resp.status_code == 400
    assert "不支持" in resp.json()["msg"]

    resp = client.post("/api/ai/skill/run", json={"name": "unknown_skill", "arguments": {}})
    assert resp.status_code == 400
    assert "未知工具" in resp.json()["msg"]


def test_skill_run_requires_admin(employee_client):
    resp = employee_client.post("/api/ai/skill/run", json={"name": "query_table_schema", "arguments": {}})
    assert resp.status_code == 403


def test_project_reindex_and_ask(client):
    resp = client.post("/api/ai/project/reindex")
    body = resp.json()
    assert resp.status_code == 200
    assert body["data"]["files"] > 5
    assert body["data"]["chunks"] > 5

    resp = client.get("/api/ai/document/list")
    project_docs = [item for item in resp.json()["data"] if item["category"] == "project"]
    assert len(project_docs) == body["data"]["files"]
    filenames = [item["filename"] for item in project_docs]
    assert "sql/init.sql" in filenames

    resp = client.post("/api/ai/ask", json={"question": "员工表 employee 有哪些字段？", "top_k": 3})
    body = resp.json()
    assert body["data"]["sources"]
    assert len(body["data"]["sources"]) >= 1

    resp = client.post("/api/ai/project/reindex")
    assert resp.json()["data"]["files"] == len(project_docs)


def test_project_reindex_requires_admin(employee_client):
    resp = employee_client.post("/api/ai/project/reindex")
    assert resp.status_code == 403


def test_workflow_mock_run(client):
    resp = client.post("/api/ai/workflow", json={"requirement": "新增员工离职字段"})
    body = resp.json()
    assert resp.status_code == 200
    data = body["data"]
    assert data["status"] == "成功"
    assert 1 <= data["review_rounds"] <= 2
    assert len(data["steps"]) >= 6
    assert "模拟模式" in data["result"]
    step_names = [step["name"] for step in data["steps"]]
    assert "接收需求" in step_names
    assert "读取表结构" in step_names
    assert "检索项目知识库" in step_names
    assert "输出最终代码" in step_names

    resp = client.get("/api/ai/workflow/list")
    body = resp.json()["data"]
    assert body["total"] >= 1
    assert body["items"][0]["requirement"] == "新增员工离职字段"

    resp = client.get(f"/api/ai/workflow/{data['id']}")
    detail = resp.json()["data"]
    assert detail["requirement"] == "新增员工离职字段"
    assert len(detail["steps"]) >= 6
    assert detail["result"]

    resp = client.get("/api/ai/workflow/99999")
    assert resp.status_code == 404


def test_workflow_requires_login(raw_client):
    resp = raw_client.post("/api/ai/workflow", json={"requirement": "新增字段"})
    assert resp.status_code == 401


def test_chat_mock_schema_skill(client):
    resp = client.post("/api/ai/chat", json={"message": "员工表有哪些字段？"})
    body = resp.json()["data"]
    assert body["tool"]["name"] == "query_table_schema"
    assert body["tool"]["arguments"]["table"] == "employee"
    assert "真实表结构" in body["answer"]


def test_chat_mock_file_skill(client):
    resp = client.post("/api/ai/chat", json={"message": "查看员工列表接口代码"})
    body = resp.json()["data"]
    assert body["tool"]["name"] == "read_project_file"
    assert body["tool"]["arguments"]["path"] == "backend/app/routers/employee.py"
    assert "已读取项目文件" in body["answer"]
