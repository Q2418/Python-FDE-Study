from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """为存量数据库补充新增字段（新库由 create_all 直接建好，列已存在时报错忽略）"""
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
