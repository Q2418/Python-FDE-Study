import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  确保模型注册到 Base
from .config import APP_TITLE, APP_VERSION
from .core.exception import register_exception_handlers
from .core.logging_conf import setup_logging
from .database import Base, engine, ensure_schema
from .init_data import init_demo_data
from .routers import ai, asset, auth, employee, record

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    init_demo_data()
    logging.getLogger("asset_admin").info("系统启动完成：%s v%s", APP_TITLE, APP_VERSION)
    yield


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(asset.router)
app.include_router(record.router)
app.include_router(ai.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index_page():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/employee", include_in_schema=False)
def employee_page():
    return FileResponse(STATIC_DIR / "employee.html")


@app.get("/asset", include_in_schema=False)
def asset_page():
    return FileResponse(STATIC_DIR / "asset.html")


@app.get("/record", include_in_schema=False)
def record_page():
    return FileResponse(STATIC_DIR / "record.html")


@app.get("/ai", include_in_schema=False)
def ai_page():
    return FileResponse(STATIC_DIR / "ai.html")
