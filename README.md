# 企业人员资产管理后台系统

FDE 工程师培训项目（8 周迭代）。
阶段1：搭项目底座（建表 + 生成前后端 CRUD）；阶段2：企业级规范化改造（统一返回 + 全局异常 + 参数校验 + 进阶查询 + 单元测试）。

## 技术栈

- 后端：Python 3.11 + FastAPI + SQLAlchemy
- 数据库：默认 SQLite（零配置直接跑），改一行配置即可切换 MySQL 8.0
- 前端：Vue3 + Element Plus + Axios（已下载到 `static/lib/`，离线可用，无需 npm 构建）
- 测试：pytest + httpx

## 目录结构

```
asset-admin/
├── sql/
│   └── init.sql              # MySQL 建表脚本（员工表 + 资产表 + 演示数据）
├── postman/
│   └── asset-admin.postman_collection.json   # Postman 全接口调试集合
├── docs/
│   └── 阶段2-改造记录.md      # AI 协作留痕（AI 生成问题 + 人工修复记录）
└── backend/
    ├── requirements.txt      # 依赖清单
    ├── run.py                # 启动入口（python run.py）
    ├── tests/                # pytest 单元测试
    │   ├── conftest.py       # 内存测试库夹具
    │   ├── test_employee.py
    │   └── test_asset.py
    └── app/
        ├── main.py           # FastAPI 入口：注册路由、异常处理、静态页面
        ├── config.py         # 数据库等配置（SQLite / MySQL 切换点）
        ├── database.py       # SQLAlchemy 引擎与会话
        ├── init_data.py      # 首次启动自动写入演示数据
        ├── core/
        │   ├── response.py   # 统一返回封装（成功/失败/自定义）
        │   └── exception.py  # 全局异常处理（中文提示）
        ├── models/           # ORM 模型：employee.py / asset.py
        ├── schemas/          # Pydantic 校验模型 + 列表输出模型
        ├── routers/          # CRUD 路由：employee.py / asset.py
        └── static/           # 前端页面：index / employee / asset
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
| http://127.0.0.1:8000/ | 系统首页（统计看板） |
| http://127.0.0.1:8000/employee | 员工管理页（增删改查/搜索/分页） |
| http://127.0.0.1:8000/asset | 资产管理页（增删改查/搜索/分页） |
| http://127.0.0.1:8000/docs | Swagger 接口文档（可在线调试） |

## 统一返回格式

所有接口（成功/失败/报错）统一返回：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": { "total": 5, "items": [] }
}
```

- 成功：`code=200`，`data` 为业务数据
- 业务失败：如 `{"code": 400, "msg": "工号已存在，请更换后重试", "data": null}`
- 参数错误：如 `{"code": 422, "msg": "参数错误：手机号格式不正确", "data": null}`
- 系统异常：如 `{"code": 500, "msg": "系统内部错误，请联系管理员", "data": null}`
- HTTP 状态码与 `code` 保持一致

## 单元测试

```bash
cd backend
python -m pytest tests -v
```

覆盖：新增（含非法参数拦截）、重复校验、分页、条件筛选、详情/404、修改、删除（22 个用例）。

## Postman 调试

导入 `postman/asset-admin.postman_collection.json`，确认变量 `base_url`（默认 http://127.0.0.1:8000）后逐项调试。

## 接口清单

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/employee/list | 员工分页列表（name 模糊 / department 精准） |
| GET | /api/employee/{id} | 员工详情 |
| POST | /api/employee | 新增员工 |
| PUT | /api/employee/{id} | 修改员工 |
| DELETE | /api/employee/{id} | 删除员工 |
| GET | /api/asset/list | 资产分页列表（name 模糊 / status 精准） |
| GET | /api/asset/{id} | 资产详情 |
| POST | /api/asset | 新增资产（编号/名称重复校验） |
| PUT | /api/asset/{id} | 修改资产 |
| DELETE | /api/asset/{id} | 删除资产 |

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
- [x] pytest 单元测试全部通过（22 个用例）
- [x] Postman 全接口调试集合（`postman/`）
