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
