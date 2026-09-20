import io
import json
import sys
import urllib.error
import urllib.request
import uuid

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
        with urllib.request.urlopen(request, timeout=15) as resp:
            return resp.status, resp.read(), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


def post_file(path, filename, content, token, field="file"):
    boundary = uuid.uuid4().hex
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode("utf-8"))
    body.write(b"Content-Type: application/octet-stream\r\n\r\n")
    body.write(content)
    body.write(f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request(BASE + path, data=body.getvalue(), method="POST")
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    request.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


status, raw, headers = call("POST", "/api/auth/login", {"username": "admin", "password": "123456"})
token = json.loads(raw.decode("utf-8"))["data"]["token"]
check(status == 200, "管理员登录")

status, raw, headers = call("GET", "/api/employee/list?sort_by=emp_no&sort_order=asc&page=1&size=10", token=token)
body = json.loads(raw.decode("utf-8"))
emp_nos = [item["emp_no"] for item in body["data"]["items"]]
check(status == 200 and emp_nos == sorted(emp_nos), f"高级查询排序 emp_no 升序: {emp_nos}")

status, raw, headers = call("GET", "/api/employee/list?status=%E5%9C%A8%E8%81%8C", token=token)
body = json.loads(raw.decode("utf-8"))
check(body["data"]["total"] == 5, f"状态筛选在职 total={body['data']['total']}")

status, body = post_file("/api/employee/1/attachment", "测试附件.txt", "hello 阶段4".encode("utf-8"), token)
check(status == 200 and body["data"]["attachment_name"] == "测试附件.txt", "员工附件上传成功")

status, raw, headers = call("GET", "/api/employee/1/attachment", token=token)
check(status == 200 and raw.decode("utf-8") == "hello 阶段4", "员工附件下载内容一致")

status, raw, headers = call("GET", "/api/employee/export", token=token)
check(status == 200 and raw[:2] == b"PK" and "spreadsheetml" in headers.get("Content-Type", ""), "Excel 导出成功（xlsx 二进制）")

doc_text = "资产领用流程：员工提交申请，管理员审批后资产状态从空闲变为已领用；归还后恢复为空闲。报废需管理员确认。".encode("utf-8")
status, body = post_file("/api/ai/document", "业务流程.txt", doc_text, token)
check(status == 200 and body["data"]["chunk_count"] >= 1, f"知识库文档上传成功（{body.get('data', {}).get('chunk_count')} 个切片）")
doc_id = body["data"]["id"]

status, raw, headers = call("GET", "/api/ai/document/list", token=token)
body = json.loads(raw.decode("utf-8"))
check(len(body["data"]) >= 1, "知识库文档列表")

status, raw, headers = call("POST", "/api/ai/ask", {"question": "资产领用流程是什么？", "top_k": 3}, token=token)
body = json.loads(raw.decode("utf-8"))
check(status == 200 and body["data"]["mode"] == "mock" and len(body["data"]["sources"]) >= 1, "RAG 问答返回答案与来源")

status, raw, headers = call("POST", "/api/ai/chat", {"message": "技术部有哪些员工？"}, token=token)
body = json.loads(raw.decode("utf-8"))
check(body["data"]["tool"]["name"] == "query_employees" and body["data"]["data"]["count"] == 2, "工具调用查询员工")

status, raw, headers = call("POST", "/api/ai/chat", {"message": "现在空闲的资产有哪些？"}, token=token)
body = json.loads(raw.decode("utf-8"))
check(body["data"]["tool"]["name"] == "query_assets", "工具调用查询资产")

status, raw, headers = call("POST", "/api/ai/chat", {"message": "最近的领用记录"}, token=token)
body = json.loads(raw.decode("utf-8"))
check(body["data"]["tool"]["name"] == "query_records", "工具调用查询领用记录")

status, raw, headers = call("DELETE", f"/api/ai/document/{doc_id}", token=token)
check(status == 200, "删除知识库文档")
status, raw, headers = call("DELETE", "/api/employee/1/attachment", token=token)
check(status == 200, "清理员工附件")

with urllib.request.urlopen(BASE + "/ai", timeout=10) as r:
    r.read()
    check(r.status == 200, "AI 助手页面可访问")

for ok, msg in results:
    print(("PASS  " if ok else "FAIL  ") + msg)
failed = [m for ok, m in results if not ok]
print()
print(f"总计 {len(results)} 项，通过 {len(results) - len(failed)} 项，失败 {len(failed)} 项")
sys.exit(1 if failed else 0)
