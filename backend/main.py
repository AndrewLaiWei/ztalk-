"""
嘴替 ZTalk - AI视频分析后端服务
基于 FastAPI + FFmpeg + Whisper + DeepSeek

功能流程：
1. 视频上传 → 2. 内容撰写 → 3. 人格分析 → 4. 关系矩阵 → 5. 话术提取 → 6. 综合报告
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

# 清除可能导致问题的代理环境变量
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']:
    if var in os.environ:
        del os.environ[var]

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 导入处理模块
from video_processor import VideoProcessor
from whisper_stt import WhisperSTT
from deepseek_analyzer import DeepSeekAnalyzer
from routes import roleplay_router

# ==================== 配置 ====================
class Config:
    # 上传文件存储目录
    UPLOAD_DIR = Path("./uploads")
    # 处理结果存储目录
    RESULT_DIR = Path("./results")
    # 黑话数据文件
    SLANG_DATA_FILE = Path("./data/slang.json")
    # 支持的视频格式
    VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"]
    # 最大文件大小 (MB)
    MAX_FILE_SIZE = 500
    # Whisper 模型大小 (tiny/base/small/medium/large)
    WHISPER_MODEL = "base"
    # DeepSeek API Key (从环境变量或 .env 读取)
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 创建目录
Config.UPLOAD_DIR.mkdir(exist_ok=True)
Config.RESULT_DIR.mkdir(exist_ok=True)

# ==================== 数据模型 ====================
class AnalysisRequest(BaseModel):
    task_id: str
    video_path: str

class AnalysisProgress(BaseModel):
    task_id: str
    step: int  # 1-6
    step_name: str
    progress: int  # 0-100
    message: str
    data: Optional[dict] = None

class AnalysisResult(BaseModel):
    task_id: str
    status: str  # success/error/processing
    phrases: list
    counters: list
    personalities: list
    relationships: list
    timeline: list
    report: dict

# ==================== FastAPI 应用 ====================
app = FastAPI(
    title="嘴替 ZTalk - AI视频分析",
    description="上传视频，AI自动解析说话人人格特征与互动关系",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(roleplay_router)

# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_progress(self, task_id: str, progress: AnalysisProgress):
        if task_id in self.active_connections:
            await self.active_connections[task_id].send_json(progress.model_dump())

manager = ConnectionManager()

# ==================== 初始化处理模块 ====================
print("🚀 初始化 AI 视频分析服务...")
print(f"   - 视频处理: FFmpeg")
print(f"   - 语音识别: Whisper ({Config.WHISPER_MODEL})")
print(f"   - AI 分析: DeepSeek")
print()

# ==================== API 路由 ====================

@app.get("/")
async def root():
    """服务健康检查"""
    return {
        "status": "ok",
        "service": "嘴替 ZTalk - AI视频分析",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/api/upload",
            "analyze": "/api/analyze/{task_id}",
            "status": "/api/status/{task_id}",
            "ws": "/ws/{task_id}"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/slang")
async def get_slang_data(category: str = None):
    """
    获取黑话数据
    
    参数:
    - category: 可选，按分类筛选（职场/恋爱/酒桌/金融/网络）
    
    返回:
    - categories: 所有分类列表
    - slangs: 黑话列表
    """
    import json
    
    if not Config.SLANG_DATA_FILE.exists():
        raise HTTPException(status_code=500, detail="黑话数据文件不存在")
    
    with open(Config.SLANG_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 如果指定了分类，筛选结果
    if category and category != "all":
        data["slangs"] = [s for s in data["slangs"] if s.get("category") == category]
    
    return {
        "code": 0,
        "data": data
    }

@app.post("/api/slang/add")
async def add_slang(request: Request):
    """添加新黑话到数据库"""
    import json
    body = await request.json()
    slang = body.get("slang", "")
    surface = body.get("surface", "")
    hidden = body.get("hidden", "")
    scene = body.get("scene", "")
    strategy = body.get("strategy", "")
    category = body.get("category", "colleague")
    risk = body.get("risk", "medium")
    
    if not slang:
        raise HTTPException(status_code=400, detail="黑话内容不能为空")
    
    slang_data = {
        "id": f"u{int(datetime.now().timestamp())}",
        "slang": slang,
        "surface": surface,
        "hidden": hidden,
        "scene": scene,
        "strategy": strategy,
        "category": category,
        "risk": risk,
        "source": "user",
        "created_at": datetime.now().isoformat()
    }
    
    if Config.SLANG_DATA_FILE.exists():
        with open(Config.SLANG_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"slangs": [], "user_slangs": []}
    
    if "user_slangs" not in data:
        data["user_slangs"] = []
    
    exists = any(s.get("slang") == slang for s in data.get("user_slangs", []))
    if exists:
        return {"code": 1, "message": "该黑话已存在"}
    
    data["user_slangs"].append(slang_data)
    
    with open(Config.SLANG_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {"code": 0, "message": "添加成功", "data": slang_data}

@app.get("/api/slang/user")
async def get_user_slangs():
    """获取用户贡献的黑话"""
    import json
    if not Config.SLANG_DATA_FILE.exists():
        return {"code": 0, "data": {"user_slangs": []}}
    with open(Config.SLANG_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"code": 0, "data": {"user_slangs": data.get("user_slangs", [])}}

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    上传视频文件
    
    返回:
    - task_id: 任务ID
    - file_path: 文件路径
    - file_size: 文件大小
    - duration: 视频时长 (秒)
    """
    # 检查文件格式
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in Config.VIDEO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的视频格式: {file_ext}，支持的格式: {Config.VIDEO_FORMATS}"
        )
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 保存文件
    file_path = Config.UPLOAD_DIR / f"{task_id}{file_ext}"
    file_size = 0
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            file_size = len(content)
            buffer.write(content)
        
        # 检查文件大小
        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb > Config.MAX_FILE_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"文件过大: {file_size_mb:.1f}MB，最大支持 {Config.MAX_FILE_SIZE}MB"
            )
        
        # 获取视频信息
        processor = VideoProcessor()
        video_info = processor.get_video_info(str(file_path))
        
        return {
            "code": 0,
            "message": "上传成功",
            "data": {
                "task_id": task_id,
                "file_path": str(file_path),
                "file_name": file.filename,
                "file_size": file_size,
                "file_size_mb": round(file_size_mb, 2),
                "duration": video_info.get("duration", 0),
                "resolution": video_info.get("resolution", "未知")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/api/analyze/{task_id}")
async def start_analysis(task_id: str):
    """
    开始分析视频
    
    参数:
    - task_id: 任务ID (从上传返回)
    
    返回:
    - status: 任务状态
    - message: 状态消息
    """
    video_path = Config.UPLOAD_DIR / f"{task_id}.mp4"
    
    # 尝试其他格式
    if not video_path.exists():
        for ext in Config.VIDEO_FORMATS:
            path = Config.UPLOAD_DIR / f"{task_id}{ext}"
            if path.exists():
                video_path = path
                break
        else:
            raise HTTPException(status_code=404, detail="视频文件不存在或已过期")
    
    # 异步执行分析
    asyncio.create_task(run_analysis(task_id, str(video_path)))
    
    return {
        "code": 0,
        "message": "分析已启动",
        "data": {
            "task_id": task_id,
            "status": "processing"
        }
    }

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """获取分析状态"""
    result_path = Config.RESULT_DIR / f"{task_id}.json"
    
    if result_path.exists():
        import json
        with open(result_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        return {
            "code": 0,
            "data": {
                "task_id": task_id,
                "status": "completed",
                "result": result
            }
        }
    
    return {
        "code": 0,
        "data": {
            "task_id": task_id,
            "status": "processing"
        }
    }

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket 实时推送分析进度"""
    await manager.connect(task_id, websocket)
    try:
        # 立即发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "WebSocket 连接成功"
        })
        
        # 持续监听直到分析完成或断开
        while True:
            try:
                # 等待接收消息（带超时，避免永久阻塞）
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                # 如果收到消息，可以根据需要处理
                # 例如：前端发送心跳 ping，后端响应 pong
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # 超时，继续检查是否需要发送进度
                # 注意：进度由 run_analysis 中的 send_progress 函数主动发送
                continue
    except WebSocketDisconnect:
        manager.disconnect(task_id)

@app.get("/api/result/{task_id}")
async def get_result(task_id: str):
    """获取分析结果"""
    result_path = Config.RESULT_DIR / f"{task_id}.json"
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    import json
    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)
    
    return {
        "code": 0,
        "data": result
    }

# ==================== 分析流程 ====================

async def run_analysis(task_id: str, video_path: str):
    """执行完整的视频分析流程"""
    
    steps = [
        {"step": 1, "name": "视频上传", "progress": 0, "message": "视频文件读取完成"},
        {"step": 2, "name": "内容撰写", "progress": 20, "message": "正在处理音视频轨道..."},
        {"step": 3, "name": "人格分析", "progress": 40, "message": "正在进行人格分析..."},
        {"step": 4, "name": "关系矩阵", "progress": 60, "message": "正在构建关系矩阵..."},
        {"step": 5, "name": "话术提取", "progress": 80, "message": "正在提取关键话术..."},
        {"step": 6, "name": "综合报告", "progress": 100, "message": "正在生成综合报告..."},
    ]
    
    try:
        # 初始化处理器
        video_processor = VideoProcessor()
        whisper = WhisperSTT(model_size=Config.WHISPER_MODEL)
        analyzer = DeepSeekAnalyzer(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
        
        # ====== 步骤 1: 视频上传 (已完成) ======
        await send_progress(task_id, 1, "视频上传", 5, "视频文件读取完成")
        await asyncio.sleep(0.5)
        
        # ====== 步骤 2: 内容撰写 (音频提取 + 语音识别) ======
        await send_progress(task_id, 2, "内容撰写", 20, "正在提取音频轨道...")
        
        # 提取音频
        audio_path = video_processor.extract_audio(video_path, str(Config.UPLOAD_DIR / task_id))
        await send_progress(task_id, 2, "内容撰写", 30, "音频提取完成，正在进行语音识别...")
        
        # Whisper 语音识别 (自动检测语言)
        await send_progress(task_id, 2, "内容撰写", 40, "Whisper 语音识别中...")
        transcription = await whisper.transcribe(audio_path, language="auto")
        await send_progress(task_id, 2, "内容撰写", 50, f"识别完成，共 {len(transcription.get('segments', []))} 个片段")
        
        # ====== 步骤 3: 人格分析 ======
        await send_progress(task_id, 3, "人格分析", 55, "正在分析说话人人格...")
        personalities = await analyzer.analyze_personality(transcription)
        await send_progress(task_id, 3, "人格分析", 70, f"发现 {len(personalities)} 个说话人")
        
        # ====== 步骤 4: 关系矩阵 ======
        await send_progress(task_id, 4, "关系矩阵", 75, "正在构建说话人关系矩阵...")
        relationships = await analyzer.analyze_relationships(transcription, personalities)
        await send_progress(task_id, 4, "关系矩阵", 85, "关系矩阵构建完成")
        
        # ====== 步骤 5: 话术提取 ======
        await send_progress(task_id, 5, "话术提取", 90, "正在提取关键话术...")
        phrases = await analyzer.extract_phrases(transcription)
        counters = await analyzer.generate_counters(phrases)
        await send_progress(task_id, 5, "话术提取", 95, f"提取 {len(phrases)} 条关键话术")
        
        # ====== 步骤 6: 综合报告 ======
        await send_progress(task_id, 6, "综合报告", 98, "正在生成综合报告...")
        report = await analyzer.generate_report(
            transcription=transcription,
            personalities=personalities,
            relationships=relationships,
            phrases=phrases
        )
        await send_progress(task_id, 6, "综合报告", 100, "分析完成！")
        
        # ====== 保存结果 ======
        result = {
            "task_id": task_id,
            "status": "success",
            "phrases": phrases,
            "counters": counters,
            "personalities": personalities,
            "relationships": relationships,
            "timeline": transcription.get("timeline", []),
            "report": report,
            "created_at": datetime.now().isoformat()
        }
        
        result_path = Config.RESULT_DIR / f"{task_id}.json"
        import json
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 发送完成消息
        await send_progress(task_id, 6, "综合报告", 100, "分析完成！", data=result)
        
        # 清理临时文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        print(f"✅ 任务 {task_id} 分析完成")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ 任务 {task_id} 分析失败: {str(e)}")
        await send_progress(task_id, 0, "错误", 0, f"分析失败: {str(e)}", is_error=True)

async def send_progress(task_id: str, step: int, step_name: str, progress: int, message: str, data: dict = None, is_error: bool = False):
    """发送进度更新"""
    progress_data = AnalysisProgress(
        task_id=task_id,
        step=step,
        step_name=step_name,
        progress=progress,
        message=message,
        data=data
    )
    await manager.send_progress(task_id, progress_data)

# ==================== 启动服务 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
