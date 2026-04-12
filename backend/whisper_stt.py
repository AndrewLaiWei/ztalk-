"""
Whisper 语音识别模块
使用 OpenAI Whisper 进行音频转文字
"""

import os
import asyncio
from typing import List, Dict, Optional
from pathlib import Path

# 清除可能导致问题的代理环境变量
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    if var in os.environ:
        del os.environ[var]

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
        """加载模型"""
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
            
            # 生成时间轴（speaker 待分配）
        for seg in result.get("segments", []):
            timeline.append({
                "time": self._format_timestamp(seg.get("start", 0)),
                "timestamp": round(seg.get("start", 0), 2),
                "text": seg.get("text", "").strip()
            })
        
        # 使用简单的说话人分配算法（保持原始索引对应）
        # 不合并片段，确保 timeline 和 speaker 一一对应
        segments = self._assign_speakers_simple(segments)
        
        # 将 speaker 信息同步到 timeline（基于时间戳匹配）
        for i, item in enumerate(timeline):
            item_ts = item.get("timestamp", 0)
            for seg in segments:
                if abs(seg.get("start", 0) - item_ts) < 0.1:
                    item["speaker"] = seg.get("speaker", "speaker_1")
                    break
        
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
    
    def _assign_speakers_simple(self, segments: List[Dict]) -> List[Dict]:
        """
        【优化版】智能说话人分配算法
        
        增强点：
        1. 基于对话模式的说话人识别 - 通过对话结构分析说话人切换
        2. 基于关键词的角色推断 - 通过常见职场称呼词推断说话人身份
        3. 基于语速一致性判断 - 同一说话人的语速应该相对稳定
        4. 改进的回合边界检测 - 短停顿时考虑是否是同一人继续发言
        
        原理: 
        - 如果当前片段明显是"回应"前一个片段，保持同一人
        - 如果有明确的角色标记（如"好的"、"是的"等），推断说话人身份
        - 短停顿时优先判断是否为同一人继续
        """
        if not segments:
            return segments
        
        LONG_SILENCE = 2.0      # 长停顿 - 肯定换人
        SHORT_GAP = 0.3         # 短停顿 - 可能同一人继续
        VERY_SHORT_GAP = 0.1    # 极短停顿 - 几乎肯定是同一人
        
        # ==================== 新增：辅助数据 ====================
        # 计算每个片段的语速（字/秒）
        for seg in segments:
            duration = seg["end"] - seg["start"]
            word_count = len(seg.get("text", ""))
            seg["speech_rate"] = word_count / max(duration, 0.1)  # 字/秒
        
        # ==================== 新增：角色关键词库 ====================
        # 下位者常用词（应答、顺从、请教）
        SUBORDINATE_MARKERS = [
            "好的", "好的好的", "好", "好嘞", "没问题", "明白", "知道了",
            "我知道了", "好的明白了", "是的是的", "是的", "对对对", "嗯嗯",
            "我试试", "我尽量", "我来", "我来处理", "马上", "好的马上",
            "收到", "好的收到", "好的我", "没问题我", "好的可以的",
            "好的您", "明白的", "我明白", "我知道的"
        ]
        
        # 上位者常用词（命令、评价、指使）
        SUPERIOR_MARKERS = [
            "你们", "你应该", "你要", "你必须", "你赶紧", "给我",
            "你看看", "你自己", "别人", "别人都能", "别人都", "你看看别人",
            "怎么还", "怎么回事", "不是", "不对", "我说的是",
            "你要记住", "你要明白", "你要知道", "你应该知道",
            "我跟你说", "我告诉你", "听明白了吗", "懂了吗"
        ]
        
        # 对话结构标记（通常表示切换说话人）
        TURN_TAKING_MARKERS = [
            "那我来", "我来说", "我说一下", "我来说两句", "我先说",
            "你说", "你说一下", "你说说", "你怎么看", "你觉得呢",
            "好了", "好了好了", "行了", "行了行了", "就这样", "听我说"
        ]
        
        def classify_by_keywords(text: str) -> str:
            """根据关键词推断说话人身份"""
            sub_count = sum(1 for m in SUBORDINATE_MARKERS if m in text)
            sup_count = sum(1 for m in SUPERIOR_MARKERS if m in text)
            if sup_count > sub_count:
                return "superior"
            elif sub_count > sup_count:
                return "subordinate"
            return "unknown"
        
        def is_continuation(seg, prev_seg) -> bool:
            """
            判断当前片段是否是前一片段的延续（同一人继续说）
            
            判断依据：
            1. 极短停顿 - 几乎肯定是同一人
            2. 语速相似 - 同一说话人的语速应该相近
            3. 内容关联 - 没有明显的"回合转换"标记
            """
            gap = seg["start"] - prev_seg["end"]
            
            # 极短停顿 - 同一人继续
            if gap < VERY_SHORT_GAP:
                return True
            
            # 短停顿但语速相近 - 可能是同一人
            if gap < SHORT_GAP:
                rate1 = prev_seg.get("speech_rate", 5)
                rate2 = seg.get("speech_rate", 5)
                rate_diff = abs(rate1 - rate2) / max(rate1, rate2, 1)
                
                # 语速差异小于30%，认为是同一人
                if rate_diff < 0.3:
                    # 但如果有明显的回合转换标记，则换人
                    text = seg.get("text", "")[:10]
                    for marker in TURN_TAKING_MARKERS:
                        if marker in text:
                            return False
                    return True
            
            return False
        
        # ==================== 主算法 ====================
        for i, seg in enumerate(segments):
            if i == 0:
                # 第一个片段 - 根据关键词判断身份
                role = classify_by_keywords(seg.get("text", ""))
                seg["speaker"] = "speaker_1" if role != "subordinate" else "speaker_2"
                seg["inferred_role"] = role
            else:
                prev_seg = segments[i-1]
                prev_speaker = prev_seg.get("speaker", "speaker_1")
                gap = seg["start"] - prev_seg["end"]
                
                # 判断是否为同一人继续
                if is_continuation(seg, prev_seg):
                    seg["speaker"] = prev_speaker
                elif gap >= LONG_SILENCE:
                    # 长停顿后重新开始
                    seg["speaker"] = "speaker_1"
                else:
                    # 正常切换
                    seg["speaker"] = "speaker_2" if prev_speaker == "speaker_1" else "speaker_1"
                
                # 尝试根据关键词修正
                role = classify_by_keywords(seg.get("text", ""))
                if role != "unknown":
                    # 如果有明确的角色标记，尝试修正
                    if role == "subordinate" and seg["speaker"] == "speaker_1":
                        # 检查前面是否有 speaker_2 可供交换
                        if any(s.get("inferred_role") == "superior" for s in segments[:i]):
                            seg["speaker"] = "speaker_2"
                    elif role == "superior" and seg["speaker"] == "speaker_2":
                        if any(s.get("inferred_role") == "subordinate" for s in segments[:i]):
                            seg["speaker"] = "speaker_1"
                    seg["inferred_role"] = role
        
        return segments


def simple_speaker_assignment(segments: List[Dict], num_speakers: int = 2) -> List[Dict]:
    """
    简单的说话人分配 (基于回合检测)
    注意: 此函数已废弃，请使用 WhisperSTT()._assign_speakers_simple(segments)
    """
    if not segments:
        return segments
    
    # 直接创建实例并调用方法
    stt = WhisperSTT.__new__(WhisperSTT)
    stt._model_loaded = True
    return stt._assign_speakers_simple(segments)


def merge_short_pauses(segments: List[Dict], threshold: float = 0.5) -> List[Dict]:
    """
    合并短停顿，减少时间轴噪音
    
    如果两个相邻片段间隔小于阈值，且属于同一说话人，则合并
    """
    if not segments:
        return segments
    
    merged = [segments[0].copy()]
    
    for seg in segments[1:]:
        last = merged[-1]
        gap = seg["start"] - last["end"]
        
        if gap < threshold and seg.get("speaker") == last.get("speaker"):
            # 合并
            last["end"] = seg["end"]
            last["text"] += " " + seg["text"]
        else:
            merged.append(seg.copy())
    
    return merged


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
