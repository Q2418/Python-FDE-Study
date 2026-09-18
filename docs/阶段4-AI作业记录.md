# 阶段4 AI 作业记录（AI 问题清单 / 风险识别 / 部署交付）

> 对应阶段4综合作业要求：记录开发过程中 AI 生成代码存在的问题与人工修改点，输出部署文档。

## 一、本阶段改动清单

| # | 功能 | 涉及文件 | 生成方式 | 人工修改点 |
| --- | --- | --- | --- | --- |
| 1 | 员工附件上传/下载/删除 | `app/routers/employee.py` | OpenCode 生成 | 增加扩展名白名单、5MB 限制、UUID 重命名、替换时删除旧文件 |
| 2 | 存量数据库自动补列 | `app/database.py` | OpenCode 生成 | 发现 `create_all` 不会给已有表加列，改为 `ALTER TABLE` + 异常忽略 |
| 3 | Excel 导出 | `app/routers/employee.py` | OpenCode 生成 | 中文文件名用 RFC 5987 编码（`filename*=UTF-8''`），否则浏览器乱码 |
| 4 | 高级查询排序 | `app/routers/employee.py`、`asset.py` | OpenCode 生成 | 排序字段改白名单映射，禁止直接把参数拼进 SQL |
| 5 | 日志落地 | `app/core/logging_conf.py`、`logger.py` | EasyCode 模板 + OpenCode 补充 | 关键操作逐点埋日志（登录/增删改/领用/导出/AI） |
| 6 | 大模型客户端（真实+模拟） | `app/core/llm.py` | OpenCode 生成 | 增加超时、HTTP 错误、返回格式异常三类兜底；无 key 自动降级模拟模式 |
| 7 | RAG 知识库 | `app/core/rag.py`、`routers/ai.py` | OpenCode 生成 | 切片带重叠；检索用字符二元组相似度（免向量库依赖），阈值过滤无关内容 |
| 8 | 工具调用 | `app/core/tools.py`、`routers/ai.py` | OpenCode 生成 | 工具参数限制条数上限 20；只执行白名单工具，未知工具直接拒绝 |
| 9 | AI 助手页面 | `static/ai.html` | EasyCode 页面模板 + OpenCode 逻辑 | 上传/删除文档仅管理员可见；模拟模式显式提示 |

## 二、AI 生成代码风险识别（人工审核后修复）

| 风险类型 | AI 初稿问题 | 人工修复 |
| --- | --- | --- |
| SQL 注入 | 排序参数直接拼接进 `order_by` 字符串 | 白名单字典映射字段，非法值回落默认排序 |
| 路径穿越/覆盖 | 上传文件用原始文件名直接保存 | UUID 重命名存储，原始名仅存数据库用于下载展示 |
| 非法文件上传 | 未校验扩展名与大小 | 扩展名白名单 + 5MB 上限 + 空文件拦截 |
| 资源未释放 | `httpx.get/post` 直接调用 | 改用 `with httpx.Client(...)` 上下文管理器，保证连接释放 |
| 异常未处理 | AI 调用失败直接把异常抛给前端 | 超时 → 504 中文提示；HTTP 错误 → 502；格式异常 → 兜底提示，全部记录日志 |
| 越权操作 | 文档上传/删除接口未加权限 | 挂 `require_admin` 依赖，普通员工 403 |
| 大模型幻觉 | RAG 提示词未约束 | 系统提示词强制「只依据参考资料回答，资料不足必须明说，禁止编造」 |
| 无限流/超限 | 工具返回条数不限、问答长度不限 | `limit` 上限 20、`question/message` 最长 500 字、`top_k` 1~10 |

## 三、报错排查记录

### 报错 1：存量数据库新增字段不生效（`no such column: employee.attachment_path`）

**背景**：员工表新增附件字段后，新库由 `Base.metadata.create_all` 直接建好，但本机已有的 `asset_admin.db` 不会自动加列。若直接启动上传附件会报：
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: employee.attachment_path
```

**AI 分析**：`create_all` 只创建缺失的表，不会修改已存在的表结构，需要用 `ALTER TABLE ADD COLUMN` 做一次轻量迁移；列已存在时会报错，可忽略。

**修复代码**
```python
# app/database.py
def ensure_schema():
    statements = [
        "ALTER TABLE employee ADD COLUMN attachment_path VARCHAR(255)",
        "ALTER TABLE employee ADD COLUMN attachment_name VARCHAR(255)",
    ]
    with engine.connect() as conn:
        for statement in statements:
            try:
                conn.execute(text(statement))
                conn.commit()
            except Exception:
                conn.rollback()
```
启动时调用：`create_all()` → `ensure_schema()` → `init_demo_data()`。

### 报错 2：Excel 导出冒烟测试失败（实际接口正常）

**现象**：接口手动调用返回 200、内容以 `PK` 开头、Content-Type 正确，但冒烟脚本判定失败。

**AI 分析**：脚本把响应头 `resp.headers` 转成普通字典 `dict(...)` 后判断 `Content-Type`，而 HTTP/1.1 头名大小写不敏感且服务器可能下发小写 `content-type`，字典是大小写敏感的，导致误判。

**修复代码**
```python
# 直接用 headers 对象（HTTPMessage，大小写不敏感），不要 dict() 转换
return resp.status, resp.read(), resp.headers
```

**结论**：接口无 bug，是测试脚本问题——排查时先用最小复现（直接 urllib 调用打印状态/头部/前 8 字节）确认服务端正常。

### 报错 3：未配置大模型 key 时 AI 接口不可用

**现象**：RAG 问答、工具调用接口在无 API key 环境下直接报错，页面不可演示。

**AI 分析**：真实调用需要 key，但开发/教学环境未必具备；应在客户端做降级：无 key 时用内置模拟模式（检索结果直接拼接回答、关键词路由选择工具），保证全流程可演示，配置 key 后零代码切换。

**修复代码**
```python
# app/core/llm.py
def is_mock_mode() -> bool:
    return not AI_ENABLED   # AI_ENABLED = bool(AI_API_KEY)
```
问答与工具调用接口按 `is_mock_mode()` 分支：模拟模式返回检索片段/数据库查询结果 + 【模拟模式】标识；真实模式走大模型。

## 四、验证与交付

**验证结果**
- 单元测试：`python -m pytest tests -v` → **50 passed**（新增附件/导出/高级查询/AI 共 12 个用例）
- 接口冒烟：登录、排序筛选、附件上传下载、Excel 导出、RAG 问答、工具调用、页面访问 → **15/15 通过**
- 日志：`backend/logs/app.log` 记录登录、附件、导出、AI 调用等操作

**交付物清单**
| 交付物 | 位置 |
| --- | --- |
| 源码 | 项目根目录（Git 仓库，分支 main） |
| 建表脚本 | `sql/init.sql` |
| 一键启动 | `backend/start.bat` |
| 部署/使用文档 | `README.md`（部署运行、AI 配置、功能清单、作业对照） |
| 接口调试集合 | `postman/asset-admin.postman_collection.json`（24 个请求） |
| 单元测试 | `backend/tests/`（50 个用例） |
| AI 作业记录 | `docs/阶段2/3/4-AI作业记录.md` |
