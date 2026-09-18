# 阶段3 AI 作业记录（AI 生成 / 人工修改 / 报错排查）

> 对应阶段3作业4：记录哪些代码由 EasyCode 生成、哪些由 OpenCode 生成，AI 代码存在什么问题、人工修改了哪些内容，以及至少 2 个报错的完整排查过程。

## 一、代码生成分工

### EasyCode 负责（模板化、重复代码）

| 内容 | 文件 |
| --- | --- |
| 用户/角色/关联表/领用记录表的 ORM 模型骨架 | `app/models/user.py`、`app/models/asset_record.py` |
| Pydantic Schema 骨架（登录、领用、记录） | `app/schemas/auth.py`、`app/schemas/record.py` |
| 路由文件骨架、CRUD 增删改查模板 | `app/routers/*.py` |
| 前端列表页/弹窗/表单模板结构 | `static/*.html` |
| 建表 SQL 模板 | `sql/init.sql` |

### OpenCode 负责（业务逻辑、查错、优化）

| 内容 | 文件 |
| --- | --- |
| JWT 登录签发/解析、bcrypt 密码哈希 | `app/core/security.py` |
| 全局登录拦截 + 管理员权限校验依赖 | `app/core/deps.py` |
| 领用/归还状态机与事务控制 | `app/routers/asset.py` |
| 记录表联表分页查询 | `app/routers/record.py` |
| 前端 axios 封装（token 注入、401 跳转、角色按钮控制） | `static/app.js` |
| 单元测试（鉴权、状态流转、非法操作） | `tests/test_auth.py`、`tests/test_record.py` |

## 二、AI 代码问题与人工修改

| # | AI 生成的问题 | 人工修改 |
| --- | --- | --- |
| 1 | `security.py` 相对导入层级写错：`from .config import ...` | 改为 `from ..config import ...`（config 在 app 包下，不在 core 包下） |
| 2 | 单元测试直接 `from tests.conftest import ...`，导致 conftest 被重复加载、依赖覆盖指向空的测试库 | 删除该导入，测试文件内定义本地辅助函数 |
| 3 | JWT 的 `sub` 直接放整数用户 ID（PyJWT 2.10+ 要求字符串） | 签发时 `"sub": str(user.id)`，解析后转回 `int` |
| 4 | 领用/归还只有状态赋值，没有事务保护 | 包在 try/except 中，异常时 `db.rollback()` 并返回中文提示 |
| 5 | 归还逻辑未处理「已领用但无领用人」的脏数据 | 增加判断：无领用记录 → 400「该资产没有领用记录，无法归还」 |
| 6 | 写操作权限仅靠前端隐藏按钮 | 后端所有写接口加 `require_admin` 依赖，接口层强制 403 |
| 7 | 前端每个页面重复写 axios 配置与错误处理 | 抽到公共 `app.js`：拦截器统一带 token、401 统一跳登录页 |

## 三、报错排查记录（作业要求 ≥2 个）

### 报错 1：启动测试报错 `ModuleNotFoundError: No module named 'app.core.config'`

**报错信息**
```
tests\conftest.py:8: in <module>
    from app.core.security import hash_password
app\core\security.py:6: in <module>
    from .config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY
E   ModuleNotFoundError: No module named 'app.core.config'
```

**AI 分析**
`security.py` 位于 `app/core/` 包内，`from .config` 表示从 `app/core/config.py` 导入，但配置文件实际在 `app/config.py`（上一层目录），应使用 `..` 向上一级。

**修复代码**
```python
# app/core/security.py
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY
```

### 报错 2：接口 500，`sqlite3.OperationalError: no such table: user`

**报错信息**
```
[ERROR] asset_admin: 数据库异常: (sqlite3.OperationalError) no such table: user
[SQL: SELECT user.id ... FROM user WHERE user.username = ? ...]
```

**AI 分析**
单元测试使用内存测试库并通过 `app.dependency_overrides[get_db]` 覆盖数据库依赖。但 `test_auth.py` 里 `from tests.conftest import login_token` 让 conftest 被第二次导入（一次作为 `conftest`，一次作为 `tests.conftest`）：
- 第一次导入的 conftest 负责建表（fixture 用的测试引擎有表）
- 第二次导入重新创建了另一个内存引擎，并再次覆盖依赖指向这个**空库**
- 于是请求查 user 表时报「no such table」

**修复代码**
```python
# tests/test_auth.py —— 删除对 conftest 的导入，改用本地辅助函数
def login_token(client, username, password="123456"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["data"]["token"]
```

**验证**：修复后 `python -m pytest tests -v` → 38 passed。

### 报错 3（联调）：未登录时页面请求接口全部 401

**现象**：登录前直接打开首页，统计数据不显示。

**AI 分析**：这是预期行为（后端已加登录拦截），需要前端统一处理 401：清空本地登录态并跳转登录页。

**修复代码**
```javascript
// static/app.js
axios.interceptors.response.use(
  function (response) { return response; },
  function (error) {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem(AppAuth.TOKEN_KEY);
      localStorage.removeItem(AppAuth.USER_KEY);
      if (window.location.pathname !== "/login") window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

## 四、验证结果

- 单元测试：`python -m pytest tests -v` → **38 passed**
- 接口冒烟（登录/鉴权/角色/领用/归还/记录/页面）：**21/21 通过**
- 全流程人工验证：登录 → 增删改查 → 领用（状态变已领用）→ 归还（状态变空闲）→ 领用记录可查
