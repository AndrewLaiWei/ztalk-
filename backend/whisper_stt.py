"""
Whisper 语音识别模块
使用 OpenAI Whisper 进行音频转文字
"""

import os
import asyncio
from typing import List, Dict, Optional
from pathlib import Path

# Whisper 模型大小选项
MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]


class WhisperSTT:
    """Whisper 语音识别"""
    
    def __init__(self, model_size: str = "base"):
        """
        初始化 Whisper
        
        参数:
        - model_size: 模型大小
          - tiny: ~39M 参数，最快，精度较低
          - base: ~74M 参数，快速，基础精度
          - small: ~244M 参数，中等速度，较好精度
          - medium: ~769M 参数，较慢，高精度
          - large: ~1550M 参数，最慢，最高精度
        """
        self.model_size = model_size
        self.model = None
        self.device = "cuda" if self._check_cuda() else "cpu"
        
        # 首次调用时加载模型
        self._model_loaded = False
    
    def _check_cuda(self) -> bool:
        """检查是否有 CUDA (GPU) 可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_model(self):
        """懒加载模型"""
        if not self._model_loaded:
            print(f"📦 加载 Whisper 模型: {self.model_size} (设备: {self.device})")
            import whisper
            self.model = whisper.load_model(self.model_size, device=self.device)
            self._model_loaded = True
            print(f"✅ Whisper 模型加载完成")
    
    async def transcribe(self, audio_path: str, language: str = "zh") -> Dict:
        """
        异步转录音频
        
        参数:
        - audio_path: 音频文件路径 (支持 mp3, wav, m4a, flac 等)
        - language: 语言代码 (zh=中文, en=英文, auto=自动检测)
        
        返回:
        {
            "text": "完整文本",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "这段话的内容",
                    "speaker": "speaker_1"  # 如果启用了说话人分离
                },
                ...
            ],
            "timeline": [
                {
                    "time": "00:00:05",
                    "timestamp": 5.0,
                    "text": "这段话的内容",
                    "speaker": "speaker_1"
                },
                ...
            ],
            "language": "zh",
            "duration": 120.5  # 音频时长
        }
        """
        # 异步加载模型
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)
        
        def do_transcribe():
            # 执行转录
            result = self.model.transcribe(
                audio_path,
                language=language if language != "auto" else None,
                task="transcribe",
                verbose=False,
                # 启用时间戳
                condition_on_previous_text=True,
                # 初始提示 (有助于专业术语)
                initial_prompt="这是一个职场对话场景，涉及项目管理、团队协作等内容。"
            )
            return result
        
        # 在线程池执行转录
        result = await loop.run_in_executor(None, do_transcribe)
        
        # 处理结果
        segments = []
        timeline = []
        
        for seg in result.get("segments", []):
            segment = {
                "id": seg.get("id", 0),
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "text": seg.get("text", "").strip(),
                "confidence": round(seg.get("probability", 0.9), 2)
            }
            segments.append(segment)
            
            # 生成时间轴
            timeline.append({
                "time": self._format_timestamp(seg.get("start", 0)),
                "timestamp": round(seg.get("start", 0), 2),
                "text": seg.get("text", "").strip()
            })
        
        return {
            "text": result.get("text", "").strip(),
            "segments": segments,
            "timeline": timeline,
            "language": result.get("language", language),
            "duration": result.get("duration", 0),
            "word_count": len(result.get("text", "").split())
        }
    
    async def transcribe_with_diarization(self, audio_path: str, num_speakers: int = 2) -> Dict:
        """
        转录 + 说话人分离 (使用 pyannote)
        
        注意: 需要安装 pyannote.audio 并获取 Hugging Face token
        
        参数:
        - audio_path: 音频文件路径
        - num_speakers: 预估说话人数量
        """
        # 先转录
        result = await self.transcribe(audio_path)
        
        try:
            from pyannote.audio import Pipeline
            
            # 加载说话人分离模型
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization",
                use_auth_token=os.getenv("HF_TOKEN")
            )
            
            # 执行说话人分离
            diarization = pipeline(audio_path)
            
            # 将说话人标签分配给每个片段
            speaker_mapping = {}
            current_speaker = None
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_label = speaker.replace("SPEAKER_", "speaker_")
                
                # 将时间范围内的片段分配给当前说话人
                for seg in result["segments"]:
                    if turn.start <= seg["start"] < turn.end:
                        seg["speaker"] = speaker_label
                    elif turn.start <= seg["end"] <= turn.end:
                        seg["speaker"] = speaker_label
                
                speaker_mapping[speaker_label] = {
                    "start": turn.start,
                    "end": turn.end
                }
            
            # 更新说话人统计
            speaker_stats = {}
            for seg in result["segments"]:
                spk = seg.get("speaker", "unknown")
                speaker_stats[spk] = speaker_stats.get(spk, 0) + 1
            
            result["speakers"] = list(speaker_stats.keys())
            result["speaker_stats"] = speaker_stats
            
        except ImportError:
            print("⚠️ pyannote.audio 未安装，跳过说话人分离")
            # 分配默认说话人
            for i, seg in enumerate(result["segments"]):
                seg["speaker"] = f"speaker_{(i % num_speakers) + 1}"
        
        return result
    
    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为 HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_supported_languages(self) -> List[str]:
        """获取 Whisper 支持的语言列表"""
        return [
            "zh", "en", "es", "fr", "de", "it", "ja", "ko", "ru", "ar",
            "pt", "pl", "nl", "sv", "fi", "da", "no", "tr", "el", "hu",
            "cs", "ro", "bg", "hr", "sk", "sl", "et", "lv", "lt", "uk"
        ]


# 简单的说话人分离 (不需要 pyannote)
def simple_speaker_assignment(segments: List[Dict], num_speakers: int = 2) -> List[Dict]:
    """
    简单的说话人分配 (基于静音检测)
    
    原理: 在静音处切换说话人
    """
    SILENCE_THRESHOLD = 2.0  # 静音阈值 (秒)
    
    for i, seg in enumerate(segments):
        if i == 0:
            seg["speaker"] = f"speaker_1"
        else:
            prev_end = segments[i-1]["end"]
            curr_start = seg["start"]
            
            # 如果间隔大于阈值，切换说话人
            if curr_start - prev_end > SILENCE_THRESHOLD:
                # 轮流分配
                prev_speaker = segments[i-1].get("speaker", "speaker_1")
                if prev_speaker == "speaker_1":
                    seg["speaker"] = "speaker_2"
                else:
                    seg["speaker"] = "speaker_1"
            else:
                # 继承上一个说话人
                seg["speaker"] = segments[i-1].get("speaker", "speaker_1")
    
    return segments


# 测试代码
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python whisper_stt.py <音频文件路径>")
        sys.exit(1)
    
    stt = WhisperSTT(model_size="base")
    
    audio_path = sys.argv[1]
    print(f"🎙️ 转录音频: {audio_path}")
    
    result = asyncio.run(stt.transcribe(audio_path))
    
    print(f"\n📝 转录结果:")
    print(f"   语种: {result['language']}")
    print(f"   时长: {result['duration']:.1f}秒")
    print(f"   片段数: {len(result['segments'])}")
    print(f"\n📄 完整文本:")
    print(result["text"])
    print(f"\n⏱️ 时间轴:")
    for item in result["timeline"][:10]:  # 只显示前10条
        print(f"   [{item['time']}] {item['text']}")
