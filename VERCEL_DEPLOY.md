# 嘴替 ZTalk - Vercel 前端部署指南

## 📁 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vercel (Frontend)                     │
│                   https://your-app.vercel.app           │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   首页.html   │  │ AI视频教学.html │  │   其他页面   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS (CORS)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              你的服务器 (Backend)                         │
│              https://your-backend-server.com           │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              FastAPI 后端服务                      │  │
│  │  • POST /api/upload  - 上传视频                   │  │
│  │  • POST /api/analyze/{task_id} - 开始分析         │  │
│  │  • WS /ws/{task_id}  - 实时进度                   │  │
│  │  • FFmpeg + Whisper + DeepSeek                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 部署步骤

### 第一步：准备代码

确保你的项目结构如下：

```
Website/
├── vercel.json           ✅ 已创建
├── index.html
├── config/
│   └── api.js            ✅ 已创建 (API 配置)
├── pages/
│   ├── AI视频教学.html   ✅ 已更新 (集成 API)
│   └── 其他页面...
└── assets/
    └── js/
        └── loader.js
```

### 第二步：配置后端地址

编辑 `Website/config/api.js`，将生产环境地址改为你实际的服务器地址：

```javascript
prod: {
  // ⚠️ 替换为你部署后端服务器的地址
  BASE_URL: 'https://api.yourdomain.com',  // 或 http://your-server-ip:8000
  WS_URL: 'wss://api.yourdomain.com'
}
```

### 第三步：上传到 GitHub

1. 在 GitHub 创建新仓库
2. 将 Website 目录推送到仓库

```bash
cd Website
git init
git add .
git commit -m "Add ZTalk frontend"
git branch -M main
git remote add origin https://github.com/你的用户名/ztalk-frontend.git
git push -u origin main
```

### 第四步：部署到 Vercel

1. 访问 [vercel.com](https://vercel.com) 并登录
2. 点击 "Add New Project"
3. 选择 "Import Git Repository"
4. 选择你刚创建的 GitHub 仓库
5. 配置项目：
   - **Framework Preset**: 其他 (Other)
   - **Root Directory**: `./`
   - **Build Command**: 不需要
   - **Output Directory**: `.`
6. 点击 "Deploy"

### 第五步：配置环境变量 (可选)

如果你的后端需要特定的环境变量，可以在 Vercel 项目设置中添加。

---

## 🔧 后端部署选项

### 选项 1: 云服务器 (推荐)

**国内服务器推荐：**
- 阿里云 ECS
- 腾讯云 CVM
- 华为云 ECS

**海外服务器推荐：**
- AWS EC2
- DigitalOcean
- Vultr
- Linode

**部署步骤：**

```bash
# 1. SSH 连接到服务器
ssh root@your-server-ip

# 2. 安装依赖
apt update && apt install -y python3 python3-pip ffmpeg

# 3. 上传后端代码
cd /root/WorkBuddy/20260405125553/backend

# 4. 安装 Python 依赖
pip3 install -r requirements.txt

# 5. 配置环境变量
export DEEPSEEK_API_KEY=your-api-key

# 6. 启动服务 (后台运行)
nohup python3 main.py > server.log 2>&1 &

# 7. 配置 Nginx 反向代理 (可选)
```

### 选项 2: Docker 部署

```bash
# 构建 Docker 镜像
cd backend
docker build -t ztalk-backend .

# 运行容器
docker run -d -p 8000:8000 \
  -e DEEPSEEK_API_KEY=your-api-key \
  --name ztalk-backend \
  ztalk-backend
```

### 选项 3: 使用 Railway/Render (简单)

1. **Railway** (railway.app)
   - 支持 Node.js、Python、Go 等
   - 有免费额度
   - 支持环境变量配置

2. **Render** (render.com)
   - 支持 Python 后端
   - 有免费 tier
   - 配置简单

3. **PythonAnywhere** (pythonanywhere.com)
   - 专门支持 Python
   - 有免费账户
   - 适合轻量级应用

---

## 🌐 Nginx 反向代理配置

如果使用 Nginx 将域名代理到后端服务：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        
        # 文件上传大小
        client_max_body_size 500M;
    }
}
```

---

## 🔐 HTTPS 配置

### 使用 Let's Encrypt (免费)

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d api.yourdomain.com

# 自动续期
certbot renew --dry-run
```

### 云服务商免费证书

- 阿里云: 免费证书
- 腾讯云: 免费证书
- Cloudflare: 免费 SSL

---

## ⚠️ 常见问题

### 1. CORS 跨域错误

后端需要配置 CORS 允许前端域名访问：

```python
# main.py 中已配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. WebSocket 连接失败

确保服务器 WebSocket 端口已开放，并且 Nginx 配置了 WebSocket 支持：

```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection 'upgrade';
```

### 3. 文件上传大小限制

Nginx 默认限制 1MB，需要配置：
```nginx
client_max_body_size 500M;
```

### 4. 502 Bad Gateway

检查后端服务是否正常运行：
```bash
curl http://localhost:8000/health
```

---

## 📋 部署检查清单

- [ ] 代码已推送到 GitHub
- [ ] Vercel 项目已创建
- [ ] `config/api.js` 中的生产地址已更新
- [ ] 后端服务器已部署并运行
- [ ] 后端 API 可访问 (`/health` 返回正常)
- [ ] CORS 配置正确
- [ ] 文件上传大小限制已配置
- [ ] HTTPS 证书已配置 (可选但推荐)

---

## 🔗 相关链接

- [Vercel 官网](https://vercel.com)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [Whisper GitHub](https://github.com/openai/whisper)
- [DeepSeek API](https://platform.deepseek.com/)
- [FFmpeg 下载](https://ffmpeg.org/download.html)

---

**有问题？** 欢迎提 Issue 或联系开发者！
