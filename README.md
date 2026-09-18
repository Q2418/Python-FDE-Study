# 企业人员资产管理后台系统

FDE 工程师培训项目（8 周迭代）。
- 阶段1：搭项目底座（建表 + 生成前后端 CRUD）
- 阶段2：企业级规范化改造（统一返回 + 全局异常 + 参数校验 + 进阶查询 + 单元测试）
- 阶段3：登录认证与角色权限 + 前端联调 + 资产领用/归还状态流转 + 领用记录

## 技术栈

- 后端：Python 3.11 + FastAPI + SQLAlchemy + JWT（PyJWT）+ bcrypt
- 数据库：默认 SQLite（零配置直接跑），改一行配置即可切换 MySQL 8.0
- 前端：Vue3 + Element Plus + Axios（已下载到 `static/lib/`，离线可用，无需 npm 构建）
- 测试：pytest + httpx

## 目录结构

```
asset-admin/
├── sql/
│   └── init.sql              # MySQL 建表脚本（全部表 + 演示数据 + 演示账号）
├── postman/
│   └── asset-admin.postman_collection.json   # Postman 全接口调试集合（登录自动保存 token）
├── docs/
│   ├── 阶段2-改造记录.md      # AI 协作留痕
│   └── 阶段3-AI作业记录.md    # AI 生成/人工修改 + 报错排查记录
└── backend/
    ├── requirements.txt      # 依赖清单
    ├── run.py                # 启动入口（python run.py）
    ├── tests/                # pytest 单元测试（38 个用例）
    └── app/
        ├── main.py           # FastAPI 入口：注册路由、异常处理、静态页面
        ├── config.py         # 数据库 / JWT 配置（SQLite / MySQL 切换点）
        ├── database.py       # SQLAlchemy 引擎与会话
        ├── init_data.py      # 首次启动自动写入演示数据（含演示账号）
        ├── core/
        │   ├── response.py   # 统一返回封装（成功/失败/自定义）
        │   ├── exception.py  # 全局异常处理（中文提示）
        │   ├── security.py   # 密码哈希 + JWT 签发/解析
        │   └── deps.py       # 登录拦截 get_current_user / 管理员校验 require_admin
        ├── models/           # ORM 模型：employee / asset / user / asset_record
        ├── schemas/          # Pydantic 校验模型
        ├── routers/          # 路由：auth / employee / asset / record
        └── static/           # 前端页面：login / index / employee / asset / record
            ├── app.js        # axios 封装：自动带 token、401 跳登录、权限判断
            └── lib/          # 前端依赖本地库（vue / element-plus / axios）
```

## 快速启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

启动后访问：

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/login | 登录页 |
| http://127.0.0.1:8000/ | 系统首页（统计看板） |
| http://127.0.0.1:8000/employee | 员工管理页 |
| http://127.0.0.1:8000/asset | 资产管理页（领用/归还） |
| http://127.0.0.1:8000/record | 领用记录页 |
| http://127.0.0.1:8000/docs | Swagger 接口文档（可在线调试） |

## 演示账号

| 账号 | 密码 | 角色 | 权限 |
| --- | --- | --- | --- |
| admin | 123456 | 管理员 | 全部操作（增删改查、领用、归还） |
| zhangsan | 123456 | 普通员工 | 只读（页面按钮自动隐藏，接口写操作返回 403） |

## 登录与权限设计

- 登录接口签发 JWT（HS256，默认 120 分钟过期），前端存 localStorage
- 所有业务接口挂 `get_current_user` 依赖：未登录/令牌无效 → 401 中文提示
- 写操作（新增/修改/删除/领用/归还）额外挂 `require_admin`：非管理员 → 403
- 前端 axios 拦截器自动携带 `Authorization: Bearer <token>`，401 自动跳登录页

## 资产领用/归还状态流转

```
空闲 --领用--> 已领用 --归还--> 空闲
维修 / 报废（管理维护状态，不可领用）
```

业务规则：
- 仅「空闲」资产可领用；已领用/维修/报废 → 400 中文提示
- 仅「已领用」资产可归还；重复归还 → 400
- 离职员工不可领用
- 领用/归还同事务写入领用记录表（asset_record），失败自动回滚

## 统一返回格式

```json
{ "code": 200, "msg": "操作成功", "data": { } }
```

- 业务失败：`{"code": 400, "msg": "该资产当前状态为「已领用」，无法领用", "data": null}`
- 参数错误：`{"code": 422, "msg": "参数错误：手机号格式不正确", "data": null}`
- 未登录：`{"code": 401, "msg": "未登录或登录已过期，请先登录", "data": null}`
- 无权限：`{"code": 403, "msg": "权限不足，仅管理员可操作", "data": null}`

## 单元测试

```bash
cd backend
python -m pytest tests -v
```

覆盖：登录/鉴权/角色权限、员工与资产 CRUD、参数校验、分页筛选、领用/归还状态流转（38 个用例）。

## Postman 调试

1. 导入 `postman/asset-admin.postman_collection.json`
2. 先执行「登录认证 → 登录」请求（测试脚本会自动把 token 存入集合变量）
3. 其余请求通过集合级 Bearer Token 自动携带鉴权

## 接口清单

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | /api/auth/login | 账号登录，签发 JWT | 公开 |
| GET | /api/auth/me | 当前登录用户信息 | 登录 |
| GET | /api/employee/list | 员工分页列表（name/department 筛选） | 登录 |
| GET | /api/employee/{id} | 员工详情 | 登录 |
| POST | /api/employee | 新增员工 | 管理员 |
| PUT | /api/employee/{id} | 修改员工 | 管理员 |
| DELETE | /api/employee/{id} | 删除员工 | 管理员 |
| GET | /api/asset/list | 资产分页列表（name/status 筛选） | 登录 |
| GET | /api/asset/{id} | 资产详情 | 登录 |
| POST | /api/asset | 新增资产 | 管理员 |
| PUT | /api/asset/{id} | 修改资产 | 管理员 |
| DELETE | /api/asset/{id} | 删除资产 | 管理员 |
| POST | /api/asset/{id}/borrow | 资产领用（状态流转 + 记录） | 管理员 |
| POST | /api/asset/{id}/return | 资产归还（状态流转 + 记录） | 管理员 |
| GET | /api/record/list | 领用记录分页列表（asset_name/action 筛选） | 登录 |

## 切换 MySQL

1. 执行建表脚本：`sql/init.sql`（Navicat 或 mysql 命令行）
2. 修改 `backend/app/config.py`：

```python
# 注释 SQLite 一行，放开 MySQL 一行，改成自己的密码
# DATABASE_URL = f"sqlite:///{BASE_DIR / 'asset_admin.db'}"
DATABASE_URL = "mysql+pymysql://root:你的密码@127.0.0.1:3306/asset_admin?charset=utf8mb4"
```

3. 重新启动项目即可，代码零改动。

## 阶段作业对照

**阶段1**
- [x] 建两张数据库表：员工表、资产表，写好建表 SQL（`sql/init.sql`）
- [x] 新建 FastAPI 项目，装好依赖（`requirements.txt`）
- [x] 前后端 CRUD 代码生成（模型 / Schema / 路由 / 页面）
- [x] 项目正常启动，无报错

**阶段2**
- [x] 完善核心业务接口：新增、分页查询、按姓名/部门/状态筛选
- [x] 接入统一接口返回格式（`app/core/response.py`）
- [x] 全局异常捕获，报错返回中文提示（`app/core/exception.py`）
- [x] 新增接口参数校验（手机号/邮箱/枚举/长度/价格范围）
- [x] pytest 单元测试全部通过
- [x] Postman 全接口调试集合（`postman/`）

**阶段3**
- [x] 用户、角色、用户角色关联表设计与代码生成
- [x] 登录、Token 拦截、权限控制（未登录禁止访问业务页面与接口）
- [x] 登录页 + 员工管理页 + 资产管理页 + 领用记录页，前后端联调
- [x] 资产领用、归还完整流程（状态自动变更、禁止非法流转、事务控制）
- [x] 领用历史记录保存与查询
- [x] 边界异常友好中文提示
- [x] pytest 单元测试（38 个用例）+ AI 作业记录（`docs/阶段3-AI作业记录.md`）
