@echo off
setlocal

where uv >nul 2>nul
if %errorlevel%==0 (
    uv run python main.py
) else (
    python -m pip install -r requirements.txt
    python main.py
)
