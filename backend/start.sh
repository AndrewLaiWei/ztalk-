#!/bin/bash

# ========================================
#   嘴替 ZTalk - AI视频分析后端服务
# ========================================

echo "========================================"
echo "   嘴替 ZTalk - AI视频分析后端服务"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未安装 Python，请先安装 Python 3.10+"
    exit 1
fi

# 检查依赖
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "[提示] 正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[警告] 未安装 FFmpeg，请先安装"
    echo "Ubuntu/Debian: sudo apt install ffmpeg"
    echo "macOS: brew install ffmpeg"
    echo ""
fi

# 检查 API Key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "[警告] 未设置 DEEPSEEK_API_KEY 环境变量"
    echo "[提示] 请运行: export DEEPSEEK_API_KEY=your-key"
    echo ""
fi

echo "[启动] 后端服务..."
echo ""
echo "访问地址: http://localhost:8000"
echo "文档地址: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
python3 main.py
