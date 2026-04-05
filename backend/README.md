# 嘴替 ZTalk - AI视频分析后端部署指南

## 📁 项目结构

```
backend/
├── main.py                 # FastAPI 主服务
├── video_processor.py      # FFmpeg 视频处理模块
├── whisper_stt.py          # Whisper 语音识别模块
├── deepseek_analyzer.py    # DeepSeek AI 分析模块
├── requirements.txt        # Python 依赖
├── start.sh               # Linux/Mac 启动脚本
├── start.bat              # Windows 启动脚本
├── .env.example           # 环境变量示例
└── README.md              # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# Linux/Mac
export DEEPSEEK_API_KEY=your-deepseek-api-key

# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"
```

或创建 `.env` 文件：
```
DEEPSEEK_API_KEY=your-deepseek-api-key
```

### 3. 安装 FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
下载 FFmpeg: https://ffmpeg.org/download.html

### 4. 启动服务

```bash
# 方式1: 直接运行
python main.py

# 方式2: 使用启动脚本
# Linux/Mac
chmod +x start.sh
./start.sh

# Windows
start.bat
```

服务将在 http://localhost:8000 启动

## 📡 API 接口

### 健康检查
```
GET /
GET /health
```

### 上传视频
```
POST /api/upload
Content-Type: multipart/form-data

响应:
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "task_id": "uuid",
    "file_path": "path/to/file",
    "file_size": 1234567,
    "duration": 120.5
  }
}
```

### 开始分析
```
POST /api/analyze/{task_id}
```

### 获取状态
```
GET /api/status/{task_id}
```

### WebSocket 实时进度
```
WS /ws/{task_id}
```

### 获取结果
```
GET /api/result/{task_id}
```

## 🎯 分析流程

1. **视频上传** - 接收并保存视频文件
2. **内容撰写** - FFmpeg 提取音频 + Whisper 语音识别
3. **人格分析** - DeepSeek 分析每个说话人的人格特征
4. **关系矩阵** - 分析说话人之间的关系
5. **话术提取** - 识别关键话术和潜台词
6. **综合报告** - 生成学习建议和策略分析

## 🐳 Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 复制应用
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

构建和运行:
```bash
docker build -t ztalk-backend .
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=your-key ztalk-backend
```

## 🌐 Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # 文件上传大小限制
        client_max_body_size 500M;
        
        # 超时设置
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

## ⚙️ 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MAX_FILE_SIZE` | 500 MB | 最大上传文件大小 |
| `WHISPER_MODEL` | base | Whisper 模型: tiny/base/small/medium/large |
| `UPLOAD_DIR` | ./uploads | 上传文件存储目录 |
| `RESULT_DIR` | ./results | 分析结果存储目录 |

## 🔧 常见问题

### Q: Whisper 模型下载慢？
预下载模型到本地:
```python
import whisper
model = whisper.load_model("base", download_root="./models")
```

### Q: 内存不足？
选择更小的 Whisper 模型:
```python
WHISPER_MODEL = "tiny"  # ~39MB
```

### Q: GPU 加速？
安装 PyTorch CUDA 版本:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📝 开发笔记

- 使用 WebSocket 实现实时进度推送
- 失败时自动回退到 HTTP 轮询
- 临时文件自动清理
- 支持断点续传 (预留)

---

**获取 DeepSeek API Key:** https://platform.deepseek.com/
