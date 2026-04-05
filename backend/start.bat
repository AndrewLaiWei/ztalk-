@echo off
chcp 65001 > nul
echo ========================================
echo   嘴替 ZTalk - AI视频分析后端服务
echo ========================================
echo.

REM 检查 Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查依赖
python -c "import fastapi" > nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖...
    pip install -r requirements.txt
)

REM 检查 FFmpeg
where ffmpeg > nul 2>&1
if errorlevel 1 (
    echo [警告] 未安装 FFmpeg，请先安装: https://ffmpeg.org/download.html
    echo.
)

REM 检查 API Key
if "%DEEPSEEK_API_KEY%"=="" (
    echo [警告] 未设置 DEEPSEEK_API_KEY 环境变量
    echo [提示] 请运行: set DEEPSEEK_API_KEY=your-key
    echo.
)

echo [启动] 后端服务...
echo.
echo 访问地址: http://localhost:8000
echo 文档地址: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 启动服务
python main.py
