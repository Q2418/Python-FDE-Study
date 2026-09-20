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

# ------------------------------------------------------------
# 阶段5：提示词固化 / 项目 RAG / Skills / Agent 工作流 配置
# ------------------------------------------------------------
PROJECT_ROOT = BASE_DIR.parent
PROMPTS_FILE = BASE_DIR / "config" / "prompts.yaml"

RAG_CHUNK_SIZE = 400
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 3
RAG_MIN_SCORE = 0.05

PROJECT_CHUNK_SIZE = 800
PROJECT_CHUNK_OVERLAP = 100
PROJECT_SCAN_DIRS = ["backend/app", "sql", "docs"]
PROJECT_SCAN_FILES = ["README.md"]
PROJECT_ALLOWED_EXTENSIONS = {".py", ".sql", ".md", ".yaml", ".json"}

SKILL_FILE_MAX_CHARS = 4000
SKILL_FILE_MAX_BYTES = 200 * 1024
SKILL_ALLOWED_EXTENSIONS = {".py", ".sql", ".md", ".json", ".yaml", ".yml", ".html", ".js", ".css", ".txt", ".bat", ".ini"}

WORKFLOW_MAX_REVIEW_ROUNDS = 2
WORKFLOW_MAX_CONTEXT_CHARS = 6000
