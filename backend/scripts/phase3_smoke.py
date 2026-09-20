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
        with urllib.request.urlopen(request, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


for path in ["/", "/login", "/employee", "/asset", "/record", "/docs", "/static/app.js"]:
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        r.read()
        check(r.status == 200, f"页面/资源 {path} -> {r.status}")

status, body = call("POST", "/api/auth/login", {"username": "admin", "password": "123456"})
check(status == 200 and body["msg"] == "登录成功", "管理员登录成功")
admin_token = body["data"]["token"]
check(body["data"]["user"]["roles"] == ["admin"], "返回管理员角色")

status, body = call("POST", "/api/auth/login", {"username": "zhangsan", "password": "123456"})
check(status == 200 and body["data"]["user"]["roles"] == ["employee"], "普通员工登录成功")
employee_token = body["data"]["token"]

status, body = call("POST", "/api/auth/login", {"username": "admin", "password": "wrong123"})
check(status == 401 and body["msg"] == "账号或密码错误", "密码错误返回 401 中文提示")

status, body = call("GET", "/api/employee/list")
check(status == 401 and body["code"] == 401, "未登录访问业务接口被拦截 401")

status, body = call("GET", "/api/employee/list", token=admin_token)
check(status == 200 and body["data"]["total"] == 5, f"带 token 查询员工 total={body['data']['total']}")

status, body = call("GET", "/api/asset/list", token=admin_token)
assets = body["data"]["items"]
idle_asset = next((a for a in assets if a["status"] == "空闲"), None)
check(idle_asset is not None, "存在空闲资产可用于领用测试")

status, body = call(
    "POST",
    f"/api/asset/{idle_asset['id']}/borrow",
    {"employee_id": 1, "remark": "冒烟测试领用"},
    token=admin_token,
)
check(status == 200 and body["data"]["status"] == "已领用" and body["data"]["user_id"] == 1, "资产领用成功且状态变更")

status, body = call("POST", f"/api/asset/{idle_asset['id']}/borrow", {"employee_id": 1}, token=admin_token)
check(status == 400 and "无法领用" in body["msg"], f"重复领用被拦截: {body['msg']}")

status, body = call("POST", f"/api/asset/{idle_asset['id']}/return", {}, token=admin_token)
check(status == 200 and body["data"]["status"] == "空闲" and body["data"]["user_id"] is None, "资产归还成功且状态还原")

status, body = call("POST", f"/api/asset/{idle_asset['id']}/return", {}, token=admin_token)
check(status == 400 and "无需归还" in body["msg"], f"未领用归还被拦截: {body['msg']}")

status, body = call("GET", "/api/record/list?page=1&size=10", token=admin_token)
actions = [item["action"] for item in body["data"]["items"]]
check(status == 200 and body["data"]["total"] >= 2 and "领用" in actions and "归还" in actions, f"领用记录已保存 total={body['data']['total']}")

status, body = call("POST", "/api/asset/1/borrow", {"employee_id": 1}, token=employee_token)
check(status == 403 and body["msg"] == "权限不足，仅管理员可操作", "普通员工写操作被拦截 403")

status, body = call("GET", "/api/record/list", token=employee_token)
check(status == 200, "普通员工可查看领用记录")

for ok, msg in results:
    print(("PASS  " if ok else "FAIL  ") + msg)
failed = [m for ok, m in results if not ok]
print()
print(f"总计 {len(results)} 项，通过 {len(results) - len(failed)} 项，失败 {len(failed)} 项")
sys.exit(1 if failed else 0)
