import json
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000"
results = []


def check(ok, msg):
    results.append((bool(ok), msg))


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


status, body = call("POST", "/api/auth/login", {"username": "admin", "password": "123456"})
token = body["data"]["token"]
check(status == 200, "管理员登录")

status, body = call("GET", "/api/ai/prompt/list", token=token)
versions = {item["key"]: item["version"] for item in body["data"]}
check(status == 200 and versions.get("code_generate") == "v1.1" and versions.get("code_review") == "v1.0", f"提示词固化列表: {versions}")

status, body = call("POST", "/api/ai/prompt/reload", token=token)
check(status == 200 and body["msg"] == "提示词配置已重新加载", "提示词热重载")

status, body = call("POST", "/api/ai/project/reindex", token=token)
stats = body["data"]
check(status == 200 and stats["files"] > 5 and stats["chunks"] > 5, f"项目知识库重建: {stats['files']} 文件 / {stats['chunks']} 切片")

status, body = call("POST", "/api/ai/ask", {"question": "员工表 employee 有哪些字段？", "top_k": 3}, token=token)
sources = body["data"]["sources"]
check(status == 200 and len(sources) >= 1, f"项目 RAG 问答命中 {len(sources)} 个来源: {[s['document'] for s in sources][:3]}")

status, body = call("GET", "/api/ai/skill/list", token=token)
names = [item["name"] for item in body["data"]]
check(len(names) == 5, f"Skills 注册列表: {names}")

status, body = call("POST", "/api/ai/skill/run", {"name": "query_table_schema", "arguments": {"table": "employee"}}, token=token)
check(status == 200 and body["data"]["count"] == 1, "Skill: 查询表结构")

status, body = call("POST", "/api/ai/skill/run", {"name": "read_project_file", "arguments": {"path": "backend/app/routers/employee.py"}}, token=token)
check(status == 200 and "employee" in body["data"]["content"], "Skill: 读取项目文件")

status, body = call("POST", "/api/ai/skill/run", {"name": "read_project_file", "arguments": {"path": "../../Windows/win.ini"}}, token=token)
check(status == 400 and "非法路径" in body["msg"], "Skill: 路径穿越拦截")

status, body = call("POST", "/api/ai/chat", {"message": "员工表有哪些字段？"}, token=token)
check(body["data"]["tool"]["name"] == "query_table_schema", "对话自动调用表结构技能")

status, body = call("POST", "/api/ai/chat", {"message": "查看员工列表接口代码"}, token=token)
check(body["data"]["tool"]["name"] == "read_project_file" and "employee.py" in body["data"]["tool"]["arguments"]["path"], "对话自动调用文件读取技能")

status, body = call("POST", "/api/ai/workflow", {"requirement": "新增员工离职日期字段"}, token=token)
data = body["data"]
step_names = [step["name"] for step in data["steps"]]
check(
    status == 200 and data["status"] == "成功" and len(data["steps"]) >= 6 and data["review_rounds"] >= 1,
    f"Agent 工作流: {len(data['steps'])} 步 / 评审 {data['review_rounds']} 轮 / {data['duration_ms']}ms",
)
check("读取表结构" in step_names and "检索项目知识库" in step_names and "输出最终代码" in step_names, f"工作流步骤: {step_names}")

status, body = call("GET", "/api/ai/workflow/list", token=token)
check(body["data"]["total"] >= 1, f"工作流历史记录 total={body['data']['total']}")

status, body = call("POST", "/api/ai/workflow", {"requirement": "优化员工分页接口"}, token=token)
check(status == 200 and body["data"]["status"] == "成功", "工作流第2个需求: 优化员工分页接口")

status, body = call("POST", "/api/ai/workflow", {"requirement": "新增资产导出功能"}, token=token)
check(status == 200 and body["data"]["status"] == "成功", "工作流第3个需求: 新增资产导出功能")

with urllib.request.urlopen(BASE + "/ai", timeout=10) as r:
    r.read()
    check(r.status == 200, "AI 助手页面可访问")

for ok, msg in results:
    print(("PASS  " if ok else "FAIL  ") + msg)
failed = [m for ok, m in results if not ok]
print()
print(f"总计 {len(results)} 项，通过 {len(results) - len(failed)} 项，失败 {len(failed)} 项")
sys.exit(1 if failed else 0)
