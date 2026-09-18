from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_TITLE = "企业人员资产管理后台系统"
APP_VERSION = "0.1.0"

# ------------------------------------------------------------
# 数据库配置
# 默认使用 SQLite（零配置，开箱即跑）
# 切换 MySQL：注释下面一行，放开再下面一行（密码改成自己的）
# ------------------------------------------------------------
DATABASE_URL = f"sqlite:///{BASE_DIR / 'asset_admin.db'}"
# DATABASE_URL = "mysql+pymysql://root:你的密码@127.0.0.1:3306/asset_admin?charset=utf8mb4"

# ------------------------------------------------------------
# 登录认证配置（JWT）
# ------------------------------------------------------------
SECRET_KEY = "asset-admin-jwt-secret-please-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# ------------------------------------------------------------
# 文件上传配置
# ------------------------------------------------------------
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".txt", ".md", ".zip"}

# ------------------------------------------------------------
# 日志配置
# ------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"

# ------------------------------------------------------------
# AI 配置（OpenAI 兼容接口，如 DeepSeek / 通义 / 智谱）
# AI_API_KEY 留空时自动使用内置模拟模式，全流程可跑通
# 配置示例：AI_API_KEY = "sk-xxxxxx"
# ------------------------------------------------------------
AI_BASE_URL = "https://api.deepseek.com/v1"
AI_API_KEY = ""
AI_MODEL = "deepseek-chat"
AI_TIMEOUT_SECONDS = 30
AI_ENABLED = bool(AI_API_KEY)
