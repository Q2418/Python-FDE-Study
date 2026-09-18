@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo   企业人员资产管理后台系统 - 一键启动
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+ 并勾选 Add to PATH
    pause
    exit /b 1
)
if not exist .venv (
    echo [1/3] 首次运行，创建虚拟环境...
    python -m venv .venv
)
echo [2/3] 安装/更新依赖...
call .venv\Scripts\python.exe -m pip install -r requirements.txt --disable-pip-version-check -q
echo [3/3] 启动服务：http://127.0.0.1:8000/login
start "" http://127.0.0.1:8000/login
call .venv\Scripts\python.exe run.py
pause
