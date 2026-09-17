# 企业人员资产管理后台系统（阶段1 Demo）

FDE 工程师培训 · 第一阶段作业 Demo：搭出项目底座，用工具生成前后端基础代码，项目可正常启动。

## 技术栈

- 后端：Python 3.11 + FastAPI + SQLAlchemy
- 数据库：默认 SQLite（零配置直接跑），改一行配置即可切换 MySQL 8.0
- 前端：Vue3 + Element Plus + Axios（已下载到 `static/lib/`，离线可用，无需 npm 构建）

## 目录结构

```
asset-admin/
├── sql/
│   └── init.sql              # MySQL 建表脚本（员工表 + 资产表 + 演示数据）
└── backend/
    ├── requirements.txt      # 依赖清单
    ├── run.py                # 启动入口（python run.py）
    └── app/
        ├── main.py           # FastAPI 入口：注册路由、挂载静态页面
        ├── config.py         # 数据库等配置（SQLite / MySQL 切换点）
        ├── database.py       # SQLAlchemy 引擎与会话
        ├── init_data.py      # 首次启动自动写入演示数据
        ├── models/           # ORM 模型：employee.py / asset.py
        ├── schemas/          # Pydantic 校验模型：employee.py / asset.py
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
| POST | /api/asset | 新增资产 |
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

## 阶段1 作业对照

- [x] 建两张数据库表：员工表、资产表，写好建表 SQL（`sql/init.sql`）
- [x] 新建 FastAPI 项目，装好依赖（`requirements.txt`）
- [x] 前后端 CRUD 代码生成（模型 / Schema / 路由 / 页面）
- [x] 项目正常启动，无报错
