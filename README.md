# 企业人员资产管理后台系统

FDE 工程师培训项目（8 周迭代，同一项目逐阶段升级）：
- 阶段1：搭项目底座（建表 + 生成前后端 CRUD）
- 阶段2：企业级规范化改造（统一返回 + 全局异常 + 参数校验 + 进阶查询 + 单元测试）
- 阶段3：登录认证与角色权限 + 前端联调 + 资产领用/归还状态流转 + 领用记录
- 阶段4：附件上传/Excel 导出/高级查询/日志 + AI 知识库问答（RAG）+ 工具调用 + 部署交付
- 阶段5：AI 工程化（提示词固化 + 项目专属 RAG + Skills 工具 + Agent 自动开发工作流）

## 技术栈

- 后端：Python 3.11 + FastAPI + SQLAlchemy + JWT（PyJWT）+ bcrypt
- 数据库：默认 SQLite（零配置直接跑），改一行配置即可切换 MySQL 8.0
- 前端：Vue3 + Element Plus + Axios（依赖本地化，离线可用，无需 npm 构建）
- 文件/报表：python-multipart（上传）+ openpyxl（Excel 导出）+ python-docx（知识库文档解析）
- AI：OpenAI 兼容接口（DeepSeek/通义/智谱等），未配置 key 时自动使用内置模拟模式
- AI 工程化：固化提示词（YAML）+ 项目 RAG 知识库 + Skills 工具注册表 + Agent 工作流编排
- 测试：pytest + httpx（62 个用例）

## 目录结构

```
asset-admin/
├── sql/
│   └── init.sql              # MySQL 建表脚本（全部表 + 演示数据 + 演示账号）
├── postman/
│   └── asset-admin.postman_collection.json   # Postman 集合（登录自动保存 token）
├── docs/
│   ├── 阶段2-改造记录.md
│   ├── 阶段3-AI作业记录.md
│   └── 阶段4-AI作业记录.md    # AI 问题清单 + 风险识别 + 部署交付说明
└── backend/
    ├── config/
    │   └── prompts.yaml      # 固化提示词配置（5 段结构：角色/任务/约束/输出格式/示例）
    ├── start.bat             # 一键启动（自动建虚拟环境 + 装依赖 + 启动）
    ├── requirements.txt      # 依赖清单
    ├── run.py                # 启动入口（python run.py）
    ├── uploads/              # 上传文件（员工附件 / 知识库文档，运行时生成）
    ├── logs/                 # 运行日志（app.log 按 5MB 滚动，运行时生成）
    ├── tests/                # pytest 单元测试
    └── app/
        ├── main.py           # 入口：路由注册、异常处理、日志、静态页面
        ├── config.py         # 数据库 / JWT / 上传 / 日志 / AI 配置
        ├── database.py       # 引擎与会话 + 存量库字段自动升级
        ├── init_data.py      # 演示数据（含演示账号）
        ├── core/
        │   ├── response.py   # 统一返回封装
        │   ├── exception.py  # 全局异常处理（中文提示）
        │   ├── security.py   # 密码哈希 + JWT
        │   ├── deps.py       # 登录拦截 / 管理员校验
        │   ├── logging_conf.py  # 日志配置（文件滚动）
        │   ├── logger.py     # 关键操作日志
        │   ├── llm.py        # 大模型客户端（真实 + 模拟模式 + 超时异常）
        │   ├── prompts.py    # 基础问答/工具提示词
        │   ├── prompt_manager.py  # 固化提示词加载/渲染/版本（读 config/prompts.yaml）
        │   ├── rag.py        # 文档解析/切片/检索 + 项目知识库重建
        │   ├── skills.py     # Skills 注册表（数据/表结构/项目文件读取，沙箱防护）
        │   └── workflow.py   # Agent 自动开发工作流（六步 + 循环评审 + 防护机制）
        ├── models/           # ORM：employee/asset/user/asset_record/ai_document/ai_chunk
        ├── schemas/          # Pydantic 校验模型
        ├── routers/          # auth / employee / asset / record / ai
        └── static/           # 页面：login / index / employee / asset / record / ai
            ├── app.js        # axios 封装（token、401 跳转、权限）
            └── lib/          # 前端依赖本地库
```

## 部署运行（交付说明）

**方式一：一键启动（Windows）**

```bash
cd backend
start.bat
```

脚本自动完成：创建虚拟环境 → 安装依赖 → 启动服务 → 打开浏览器。

**方式二：手动启动**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

**访问地址**

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/login | 登录页 |
| http://127.0.0.1:8000/ | 首页统计看板 |
| http://127.0.0.1:8000/employee | 员工管理（附件/导出/高级筛选） |
| http://127.0.0.1:8000/asset | 资产管理（领用/归还） |
| http://127.0.0.1:8000/record | 领用记录 |
| http://127.0.0.1:8000/ai | AI 助手（知识库问答 + 数据助手） |
| http://127.0.0.1:8000/docs | Swagger 接口文档 |

**演示账号**：`admin / 123456`（管理员）、`zhangsan / 123456`（普通员工，只读）

## AI 助手配置

默认使用**内置模拟模式**（无需 key，全流程可跑通，回答带【模拟模式】前缀）。
配置真实大模型：修改 `backend/app/config.py`

```python
AI_BASE_URL = "https://api.deepseek.com/v1"   # 或通义/智谱等 OpenAI 兼容地址
AI_API_KEY = "sk-你的key"
AI_MODEL = "deepseek-chat"
```

重启后自动切换为真实模型：知识库问答（RAG）由模型总结并引用来源；数据助手由模型选择工具查询真实数据；Agent 工作流由模型完成代码生成与评审。

**固化提示词**：位于 `backend/config/prompts.yaml`（5 段结构，支持 `{requirement}` `{table_schema}` `{code_style}` `{code}` 变量），修改后调用 `POST /api/ai/prompt/reload` 或重启服务生效，改 Prompt 不用改业务代码。

## 功能清单

- 登录认证：JWT + 角色权限（管理员/普通员工），未登录拦截、越权 403
- 员工/资产：增删改查、分页、多条件筛选（姓名/部门/状态/日期范围）、排序（字段白名单）
- 员工附件：类型白名单 + 5MB 限制 + UUID 重命名防覆盖，支持上传/下载/替换/删除
- Excel 导出：按当前筛选条件导出员工报表（openpyxl）
- 领用归还：状态流转（空闲⇄已领用）、非法操作拦截、事务控制、记录追溯
- 日志：`logs/app.log` 滚动记录登录、增删改、领用归还、导出、AI 调用等关键操作
- AI 知识库（RAG）：上传 txt/md/docx → 切片入库 → 检索 Top-K → 问答并附来源
- AI 数据助手：自然语言 → 模型选择工具（员工/资产/记录查询）→ 真实数据回答
- AI 提示词固化：`config/prompts.yaml` 两套标准 Prompt（代码生成/代码评审），变量渲染 + 热重载
- 项目 RAG：一键扫描项目文档与代码入库（表结构 SQL / README / docs / 后端代码），检索参数可调
- Skills 工具：数据查询、表结构查询、项目文件读取（路径沙箱 + 扩展名白名单 + 大小限制），统一注册表与异常兜底
- Agent 工作流：六步自动开发（读表结构→检索知识库→生成→评审→回炉→输出），循环轮次上限 + 上下文截断 + 每步异常兜底，运行记录可追溯
- 统一返回、全局异常中文提示、pytest 62 个用例、Postman 30 个请求集合

## 单元测试

```bash
cd backend
python -m pytest tests -v
```

## 切换 MySQL

1. 执行 `sql/init.sql`（Navicat 或 mysql 命令行）
2. 修改 `backend/app/config.py` 的 `DATABASE_URL`（注释 SQLite 一行，放开 MySQL 一行）
3. 重启项目，代码零改动

## 阶段作业对照

**阶段1**
- [x] 员工表、资产表建表 SQL（`sql/init.sql`）
- [x] FastAPI 项目 + 依赖 + 前后端 CRUD + 正常启动

**阶段2**
- [x] 统一返回格式 / 全局异常中文提示 / 参数校验
- [x] 分页 + 条件筛选 + pytest + Postman

**阶段3**
- [x] 用户/角色/关联表 + 登录 + Token 拦截 + 权限控制
- [x] 登录页 + 员工页 + 资产页前后端联调
- [x] 领用/归还状态流转 + 记录追溯 + 边界提示

**阶段4**
- [x] 人员附件上传（类型/大小限制 + 路径管理）
- [x] 人员列表多条件筛选、分页、排序
- [x] 人员数据 Excel 导出
- [x] 关键操作日志落地（文件滚动）
- [x] AI 知识库问答（RAG）：文档上传、检索、问答页面
- [x] 工具调用：自然语言查询员工/资产/领用记录
- [x] AI 调用超时与异常捕获
- [x] 打包部署（start.bat + 部署文档）+ 完整交付清单
- [x] AI 作业记录（`docs/阶段4-AI作业记录.md`）

**阶段5**
- [x] 两套标准化 Prompt（代码生成 / 代码评审）固化到配置文件，支持版本与热重载
- [x] 专属项目 RAG 知识库：表结构/接口文档/目录规范/业务逻辑一键入库，检索参数可调优
- [x] Skills 工具：数据库查询（数据 + 表结构）、项目文件读取（沙箱防护），统一注册可用
- [x] Agent 自动开发工作流：六步流水线 + 循环校验 + 防护机制（最大轮次/上下文截断/异常兜底）
- [x] 3 个真实需求全自动跑通：新增离职字段 / 优化分页接口 / 新增导出功能
- [x] 排错与迭代记录（`docs/阶段5-AI作业记录.md`）
