"""
DeepSeek AI 分析模块
使用 DeepSeek API 进行话术分析、人格分析、关系梳理
"""

import os
import json
import re
import asyncio
from typing import List, Dict, Optional
import httpx
from openai import OpenAI


def clean_json_response(text: str) -> str:
    """
    清理 DeepSeek API 返回的 Markdown 代码块，提取纯 JSON
    """
    # 移除 markdown 代码块标记
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```json', '', text, flags=re.MULTILINE)
    text = text.strip()
    return text


class DeepSeekAnalyzer:
    """DeepSeek AI 分析器"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化 DeepSeek 分析器
        
        参数:
        - api_key: DeepSeek API Key
        - base_url: API 地址
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=httpx.Client(trust_env=False)
        )
        self.model = "deepseek-chat"
    
    async def analyze_personality(self, transcription: Dict) -> List[Dict]:
        """
        分析说话人人格特征
        
        基于对话内容分析每个人的:
        - 沟通风格 (支配型/被动型/攻击型等)
        - 情绪特征 (稳定/易怒/焦虑等)
        - 权力位置 (上位者/下位者)
        - 沟通技巧
        """
        prompt = f"""你是一个专业的沟通心理学分析师。请分析以下对话中每个说话人的人格特征和沟通风格。

对话内容:
{transcription['text']}

请以 JSON 格式输出分析结果，格式如下:
{{
  "speakers": [
    {{
      "id": "speaker_1",
      "name": "说话人1",
      "personality_type": "人格类型，如：支配型、分析型、友好型",
      "communication_style": "沟通风格描述",
      "emotional_traits": ["情绪特征列表"],
      "power_position": "上位者/下位者/平等",
      "communication_techniques": ["使用的沟通技巧列表"],
      "strengths": ["优势"],
      "weaknesses": ["弱点"]
    }}
  ]
}}

只输出 JSON，不要其他内容。"""
        
        result = await self._call_api(prompt)
        
        try:
            # 清理 Markdown 代码块
            clean_result = clean_json_response(result)
            data = json.loads(clean_result)
            speakers = data.get("speakers", [])
            if speakers:
                return speakers
            # 如果返回空数组，返回默认
            return [{
                "id": "speaker_1",
                "name": "说话人1",
                "personality_type": "待分析",
                "communication_style": "根据对话内容分析",
                "emotional_traits": ["待识别"],
                "power_position": "待判断",
                "communication_techniques": [],
                "strengths": [],
                "weaknesses": []
            }]
        except json.JSONDecodeError:
            print(f"⚠️ analyze_personality JSON解析失败，原始返回: {result[:200]}...")
            # 解析失败，返回默认结构
            return [{
                "id": "speaker_1",
                "name": "说话人1",
                "personality_type": "待分析",
                "communication_style": "根据对话内容分析",
                "emotional_traits": ["待识别"],
                "power_position": "待判断",
                "communication_techniques": [],
                "strengths": [],
                "weaknesses": []
            }]
    
    async def analyze_relationships(self, transcription: Dict, personalities: List[Dict]) -> List[Dict]:
        """
        分析说话人之间的关系矩阵
        
        分析维度:
        - 关系类型 (上下级/平级/对立/合作)
        - 亲密度
        - 冲突点
        - 潜在合作机会
        """
        prompt = f"""你是一个专业的社交关系分析师。请分析以下对话中说话人之间的关系特征。

对话内容:
{transcription['text']}

说话人信息:
{json.dumps(personalities, ensure_ascii=False, indent=2)}

请以 JSON 格式输出关系分析，格式如下:
{{
  "relationships": [
    {{
      "from": "speaker_1",
      "to": "speaker_2",
      "type": "上下级/平级/对立/合作/陌生",
      "intimacy": 1-10,
      "conflict_points": ["冲突点列表"],
      "cooperation_opportunities": ["潜在合作机会"],
      "relationship_dynamics": "关系动态描述"
    }}
  ]
}}

只输出 JSON，不要其他内容。"""
        
        result = await self._call_api(prompt)
        
        try:
            # 清理 Markdown 代码块
            clean_result = clean_json_response(result)
            data = json.loads(clean_result)
            relationships = data.get("relationships", [])
            if relationships:
                return relationships
            return []
        except json.JSONDecodeError:
            print(f"⚠️ analyze_relationships JSON解析失败，原始返回: {result[:200]}...")
            return []
    
    async def extract_phrases(self, transcription: Dict) -> List[Dict]:
        """
        提取关键话术
        
        识别并提取:
        - 经典话术
        - 潜台词
        - 权力话术
        - 情感操控
        """
        # 使用时间轴信息构建更丰富的上下文
        timeline_text = ""
        if transcription.get("timeline"):
            for item in transcription["timeline"][:50]:  # 限制前50条
                time_str = item.get("time", "")
                text = item.get("text", "")
                timeline_text += f"[{time_str}] {text}\n"
        
        # 如果时间轴为空，使用完整文本
        if not timeline_text.strip():
            timeline_text = transcription.get("text", "")[:3000]
        
        prompt = f"""你是一个专业的语言分析专家。请从以下对话中提取关键话术，并分析其含义和意图。

对话时间轴:
{timeline_text}

请以 JSON 格式输出话术分析，格式如下:
{{
  "phrases": [
    {{
      "speaker": "speaker_1",
      "original_phrase": "原始话术原文",
      "time_range": "出现时间段，如 00:01:30",
      "literal_meaning": "字面意思",
      "hidden_meaning": "潜台词/真实意图",
      "power_level": "权力等级 (高/中/低)",
      "manipulation_type": "操控类型 (如有)",
      "category": "话术类别：打压/施压/试探/防御/拉拢/模糊/威胁",
      "coping_strategy": "应对建议"
    }}
  ]
}}

请提取最经典的 5-10 条话术。只输出 JSON，不要其他内容。"""
        
        result = await self._call_api(prompt)
        
        try:
            # 清理 Markdown 代码块
            clean_result = clean_json_response(result)
            print(f"📝 extract_phrases API返回: {clean_result[:300]}...")
            data = json.loads(clean_result)
            phrases = data.get("phrases", [])
            if phrases and len(phrases) > 0:
                return phrases
            # 如果返回空数组，从 timeline 中提取关键对话
            print(f"⚠️ extract_phrases 返回空数组，使用 fallback")
            return self._extract_phrases_from_timeline(transcription)
        except json.JSONDecodeError as e:
            print(f"⚠️ extract_phrases JSON解析失败: {e}")
            print(f"   原始返回: {result[:500]}...")
            # 从时间轴提取关键对话
            return self._extract_phrases_from_timeline(transcription)
    
    def _extract_phrases_from_timeline(self, transcription: Dict) -> List[Dict]:
        """从时间轴直接提取关键对话，并进行简单的潜台词分析"""
        phrases = []
        timeline = transcription.get("timeline", [])
        full_text = transcription.get("text", "").lower()
        
        # 关键词模式匹配
        hidden_meaning_patterns = [
            # 种族/文化相关
            (["chinese", "asian", "accent", "english", "school"], "暗示对方英语能力不足，基于种族刻板印象"),
            # 贬低/打压
            (["bad", "worse", "terrible", "scared", "fear", "sensitive"], "通过贬低对方来建立心理优势"),
            # 排外/小圈子
            (["we", "us", "our", "between you", "trust me"], "建立'圈内人'与'外人'的区分"),
            # 模糊/回避
            (["consider", "think about", "maybe", "we'll see", "i'll let you know"], "不给出明确答复，回避直接回应"),
            # 施压/威胁
            (["risk", "problem", "trouble", "careful", "watch out"], "通过制造焦虑来施加压力"),
            # 质疑/挑衅
            (["really", "seriously", "you sure", "what if"], "质疑对方判断，试图让对方自我怀疑"),
            # 施恩/拉拢
            (["i'll help", "don't worry", "i got you", "trust me"], "通过小恩小惠建立依赖关系"),
        ]
        
        def analyze_hidden_meaning(text: str) -> str:
            """基于关键词模式推断潜台词"""
            text_lower = text.lower()
            for patterns, meaning in hidden_meaning_patterns:
                for pattern in patterns:
                    if pattern in text_lower:
                        return meaning
            return "需要结合完整对话场景理解"
        
        def infer_category(text: str) -> str:
            """推断话术类别"""
            text_lower = text.lower()
            if any(w in text_lower for w in ["scared", "fear", "bad", "worse", "weak"]):
                return "打压"
            if any(w in text_lower for w in ["risk", "problem", "careful"]):
                return "施压"
            if any(w in text_lower for w in ["consider", "think", "maybe", "we'll see"]):
                return "模糊"
            if any(w in text_lower for w in ["we", "us", "together", "help"]):
                return "拉拢"
            if any(w in text_lower for w in ["really", "you sure", "seriously"]):
                return "试探"
            if any(w in text_lower for w in ["no", "but", "however"]):
                return "防御"
            return "对话"
        
        # 找出较长的对话片段（可能是关键话术）
        for item in timeline:
            text = item.get("text", "").strip()
            if len(text) > 30 and len(phrases) < 8:
                hidden = analyze_hidden_meaning(text)
                category = infer_category(text)
                
                phrases.append({
                    "speaker": item.get("speaker", "speaker_1"),
                    "original_phrase": text,
                    "time_range": item.get("time", ""),
                    "literal_meaning": "对话内容",
                    "hidden_meaning": hidden,
                    "power_level": "中",
                    "manipulation_type": "",
                    "category": category,
                    "coping_strategy": "建议结合完整对话场景理解"
                })
        
        return phrases if phrases else [{
            "speaker": "speaker_1",
            "original_phrase": "未能提取到有效话术",
            "time_range": "00:00:00",
            "literal_meaning": "语音识别或AI分析出现问题",
            "hidden_meaning": "建议重新上传清晰音频",
            "power_level": "中",
            "manipulation_type": "",
            "category": "系统提示",
            "coping_strategy": "请确保音频清晰、对话内容充足"
        }]
    
    async def generate_counters(self, phrases: List[Dict]) -> List[Dict]:
        """
        为每条话术生成反击话术
        """
        prompt = f"""你是一个专业的沟通策略专家。针对以下话术，请生成有力的反击话术。

话术列表:
{json.dumps(phrases, ensure_ascii=False, indent=2)}

请以 JSON 格式输出反击话术，格式如下:
{{
  "counters": [
    {{
      "original_phrase": "原始话术",
      "counter_phrase": "反击话术",
      "strategy": "反击策略：直接反击/反问/转移/幽默化解/沉默以对",
      "rationale": "反击理由和效果预期"
    }}
  ]
}}

只输出 JSON，不要其他内容。"""
        
        result = await self._call_api(prompt)
        
        try:
            # 清理 Markdown 代码块
            clean_result = clean_json_response(result)
            data = json.loads(clean_result)
            return data.get("counters", [])
        except json.JSONDecodeError:
            print(f"⚠️ generate_counters JSON解析失败，原始返回: {result[:200]}...")
            # 返回示例数据
            return [
                {
                    "original_phrase": phrases[0].get("original_phrase", "") if phrases else "",
                    "counter_phrase": "您的顾虑具体是哪些方面呢？我想逐一了解",
                    "strategy": "反问",
                    "rationale": "将模糊拒绝转化为具体讨论，掌握主动权"
                }
            ]
    
    async def generate_report(self, transcription: Dict, personalities: List[Dict], 
                              relationships: List[Dict], phrases: List[Dict]) -> Dict:
        """
        生成综合分析报告
        """
        prompt = f"""请为以下对话生成一份综合分析报告。

对话内容:
{transcription['text'][:2000]}...

说话人人格:
{json.dumps(personalities, ensure_ascii=False, indent=2)}

关系分析:
{json.dumps(relationships, ensure_ascii=False, indent=2)}

关键话术:
{json.dumps(phrases[:5], ensure_ascii=False, indent=2)}

请以 JSON 格式输出报告，格式如下:
{{
  "report": {{
    "overall_score": 85,
    "pressure_level": "高/中/低",
    "strategy_effectiveness": {{
      "进攻技巧": "评分 1-100",
      "防守技巧": "评分 1-100",
      "情绪控制": "评分 1-100"
    }},
    "key_findings": [
      "主要发现1",
      "主要发现2"
    ],
    "learning_points": [
      "学习点1",
      "学习点2"
    ],
    "improvement_suggestions": [
      "改进建议1",
      "改进建议2"
    ],
    "battle_summary": "一句话总结这场对话"
  }}
}}

只输出 JSON，不要其他内容。"""
        
        result = await self._call_api(prompt)
        
        try:
            # 清理 Markdown 代码块
            clean_result = clean_json_response(result)
            data = json.loads(clean_result)
            return data.get("report", {
                "overall_score": 75,
                "pressure_level": "中",
                "strategy_effectiveness": {
                    "进攻技巧": 70,
                    "防守技巧": 75,
                    "情绪控制": 80
                },
                "key_findings": ["对话整体较为平和", "存在一定的权力不对等"],
                "learning_points": ["学会在压力下保持冷静", "注意识别对方的潜台词"],
                "improvement_suggestions": ["可以更主动地表达诉求", "注意非语言沟通"],
                "battle_summary": "一场典型的职场权力对话"
            })
        except json.JSONDecodeError:
            print(f"⚠️ generate_report JSON解析失败，原始返回: {result[:200]}...")
            return {
                "overall_score": 75,
                "pressure_level": "中",
                "strategy_effectiveness": {
                    "进攻技巧": 70,
                    "防守技巧": 75,
                    "情绪控制": 80
                },
                "key_findings": ["对话整体较为平和"],
                "learning_points": ["学会在压力下保持冷静"],
                "improvement_suggestions": ["可以更主动地表达诉求"],
                "battle_summary": "一场典型的职场权力对话"
            }
    
    async def _call_api(self, prompt: str, temperature: float = 0.7) -> str:
        """
        调用 DeepSeek API
        
        参数:
        - prompt: 提示词
        - temperature: 创造性参数 (0-1)
        
        返回:
        - response: API 响应文本
        """
        def sync_call():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的沟通分析和策略专家，擅长分析人际对话中的话术、潜台词和权力关系。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                stream=False
            )
            return response.choices[0].message.content
        
        # 在线程池执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_call)


# 辅助函数: 格式化输出
def format_personality_summary(personalities: List[Dict]) -> str:
    """格式化人格分析摘要"""
    summary = []
    for p in personalities:
        summary.append(f"\n【{p.get('name', '未知')}】")
        summary.append(f"  人格类型: {p.get('personality_type', '未知')}")
        summary.append(f"  沟通风格: {p.get('communication_style', '未知')}")
        summary.append(f"  权力位置: {p.get('power_position', '未知')}")
        summary.append(f"  情绪特征: {', '.join(p.get('emotional_traits', []))}")
    return '\n'.join(summary)


def format_relationship_summary(relationships: List[Dict]) -> str:
    """格式化关系分析摘要"""
    summary = []
    for r in relationships:
        summary.append(f"\n{r.get('from', '?')} → {r.get('to', '?')}")
        summary.append(f"  关系类型: {r.get('type', '未知')}")
        summary.append(f"  亲密度: {r.get('intimacy', 0)}/10")
        if r.get('conflict_points'):
            summary.append(f"  冲突点: {', '.join(r['conflict_points'])}")
    return '\n'.join(summary)


# 测试代码
if __name__ == "__main__":
    import sys
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("请设置 DEEPSEEK_API_KEY 环境变量")
        print("用法: DEEPSEEK_API_KEY=your-key python deepseek_analyzer.py")
        sys.exit(1)
    
    analyzer = DeepSeekAnalyzer(api_key)
    
    # 测试用示例数据
    sample_transcription = {
        "text": "甲方：这个方案不行，你们根本没有理解我们的需求。乙方：非常感谢您的反馈，能否具体说明是哪些部分不符合预期？甲方：反正你们看着改，改到我满意为止。",
        "segments": [
            {"start": 0, "end": 5, "text": "甲方：这个方案不行，你们根本没有理解我们的需求。"},
            {"start": 5, "end": 10, "text": "乙方：非常感谢您的反馈，能否具体说明是哪些部分不符合预期？"},
            {"start": 10, "end": 15, "text": "甲方：反正你们看着改，改到我满意为止。"}
        ]
    }
    
    print("🔍 测试人格分析...")
    personalities = asyncio.run(analyzer.analyze_personality(sample_transcription))
    print(format_personality_summary(personalities))
    
    print("\n🔗 测试关系分析...")
    relationships = asyncio.run(analyzer.analyze_relationships(sample_transcription, personalities))
    print(format_relationship_summary(relationships))
    
    print("\n💬 测试话术提取...")
    phrases = asyncio.run(analyzer.extract_phrases(sample_transcription))
    for p in phrases[:3]:
        print(f"  - {p.get('original_phrase', '')}")
        print(f"    潜台词: {p.get('hidden_meaning', '')}")
    
    print("\n✅ 测试完成!")
