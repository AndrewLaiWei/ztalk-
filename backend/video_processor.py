"""
视频处理模块
使用 FFmpeg 进行视频处理
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

class VideoProcessor:
    """视频处理器 - 使用 FFmpeg"""
    
    def __init__(self):
        self.ffprobe_path = "ffprobe"  # 系统安装的 ffprobe
        self.ffmpeg_path = "ffmpeg"    # 系统安装的 ffmpeg
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        获取视频信息
        
        返回:
        - duration: 时长 (秒)
        - resolution: 分辨率 (如 "1920x1080")
        - width: 宽度
        - height: 高度
        - fps: 帧率
        - codec: 视频编码
        - size: 文件大小 (字节)
        """
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"error": "无法读取视频信息"}
            
            info = json.loads(result.stdout)
            
            # 找到视频流
            video_stream = None
            audio_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video" and not video_stream:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and not audio_stream:
                    audio_stream = stream
            
            duration = float(info.get("format", {}).get("duration", 0))
            
            if video_stream:
                width = video_stream.get("width", 0)
                height = video_stream.get("height", 0)
                resolution = f"{width}x{height}"
                
                # 解析帧率
                fps_str = video_stream.get("r_frame_rate", "30/1")
                try:
                    num, denom = fps_str.split("/")
                    fps = round(int(num) / int(denom))
                except:
                    fps = 30
                
                return {
                    "duration": duration,
                    "resolution": resolution,
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "codec": video_stream.get("codec_name", "unknown"),
                    "size": int(info.get("format", {}).get("size", 0)),
                    "has_audio": audio_stream is not None
                }
            
            return {"duration": duration, "size": int(info.get("format", {}).get("size", 0))}
            
        except Exception as e:
            return {"error": str(e)}
    
    def extract_audio(self, video_path: str, output_dir: str) -> str:
        """
        从视频中提取音频
        
        参数:
        - video_path: 视频文件路径
        - output_dir: 输出目录
        
        返回:
        - audio_path: 音频文件路径 (.wav 格式)
        """
        output_path = os.path.join(output_dir, "audio.wav")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # FFmpeg 命令：提取音频为 WAV 格式 (Whisper 最佳格式)
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,           # 输入文件
            "-vn",                        # 不处理视频
            "-acodec", "pcm_s16le",      # 音频编码：16bit PCM
            "-ar", "16000",              # 采样率：16kHz (Whisper 最佳)
            "-ac", "1",                  # 单声道
            "-y",                        # 覆盖已存在的文件
            output_path
        ]
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            stderr=subprocess.PIPE
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"音频提取失败: {result.stderr}")
        
        return output_path
    
    def extract_frames(self, video_path: str, output_dir: str, interval: int = 5) -> List[str]:
        """
        按时间间隔提取视频帧
        
        参数:
        - video_path: 视频文件路径
        - output_dir: 输出目录
        - interval: 提取间隔 (秒)
        
        返回:
        - frames: 帧图片路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频时长
        info = self.get_video_info(video_path)
        duration = info.get("duration", 60)
        
        frames = []
        current_time = 0
        
        while current_time < duration:
            output_path = os.path.join(output_dir, f"frame_{current_time:.1f}.jpg")
            
            cmd = [
                self.ffmpeg_path,
                "-ss", str(current_time),    # 跳转时间
                "-i", video_path,
                "-vframes", "1",             # 只取一帧
                "-q:v", "2",                 # 质量
                "-y",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                frames.append(output_path)
            
            current_time += interval
        
        return frames
    
    def get_video_thumbnail(self, video_path: str, output_path: str, timestamp: float = 1) -> str:
        """
        获取视频缩略图
        
        参数:
        - video_path: 视频文件路径
        - output_path: 输出图片路径
        - timestamp: 截图时间点 (秒)
        
        返回:
        - output_path: 缩略图路径
        """
        cmd = [
            self.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"缩略图生成失败: {result.stderr}")
        
        return output_path
    
    def get_audio_waveform(self, audio_path: str, output_path: str, width: int = 1920, height: int = 100) -> str:
        """
        生成音频波形图
        
        参数:
        - audio_path: 音频文件路径
        - output_path: 输出图片路径
        - width: 图片宽度
        - height: 图片高度
        
        返回:
        - output_path: 波形图路径
        """
        cmd = [
            self.ffmpeg_path,
            "-i", audio_path,
            "-filter_complex", f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}:colors=0x10B981",
            "-frames:v", "1",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"波形图生成失败: {result.stderr}")
        
        return output_path


# 测试代码
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python video_processor.py <视频文件路径>")
        sys.exit(1)
    
    processor = VideoProcessor()
    
    video_path = sys.argv[1]
    print(f"📹 分析视频: {video_path}")
    
    info = processor.get_video_info(video_path)
    print(f"\n📊 视频信息:")
    for key, value in info.items():
        print(f"   {key}: {value}")
