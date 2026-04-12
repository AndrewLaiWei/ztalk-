"""
角色分析模块
从书籍/文本中提取角色人格特征
基于 Big Five 人格模型 + 语言风格分析
"""

import os
import re
import json
import uuid
import asyncio
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CharacterProfile:
    """角色档案"""
    id: str
    name: str
    book_title: str
    book_author: str = ""
    gender: str = "未知"
    identity: str = ""  # 身份（侦探、商人、学生等）
    era: str = ""  # 时代背景
    
    # Big Five 人格维度 (0.0-1.0)
    neuroticism: float = 0.5  # 神经质
    extraversion: float = 0.5  # 外向性
    openness: float = 0.5  # 开放性
    agreeableness: float = 0.5  # 宜人性
    conscientiousness: float = 0.5  # 尽责性
    
    # 补充特质
    optimism: float = 0.5  # 乐观主义
    resilience: float = 0.5  # 韧性
    self_blame: float = 0.0  # 归因风格-自我 (-1到1)
    external_blame: float = 0.0  # 归因风格-外部 (-1到1)
    
    # 语言风格
    speech_patterns: List[str] = None  # 口头禅/表达习惯
    formality_level: float = 0.5  # 正式度 (0=口语, 1=正式)
    emotion_density: float = 0.5  # 情绪词密度
    first_person_ratio: float = 0.5  # 第一人称使用频率
    
    # 行为模式
    decision_style: str = "理性"  # 决策风格
    conflict_approach: str = "协商"  # 冲突处理
    social_strategy: str = "开放"  # 社交策略
    
    # 核心特征描述
    personality_summary: str = ""
    key_quotes: List[str] = None  # 关键语录
    source_dimension: str = ""  # 来源维度（用于表格类输入）
    
    # 元数据
    confidence: float = 0.7  # 分析置信度
    source_evidence: List[str] = None  # 原文依据
    created_at: str = ""
    tags: List[str] = None  # 标签（推理、爱情、悬疑等）
    
    def __post_init__(self):
        if self.speech_patterns is None:
            self.speech_patterns = []
        if self.key_quotes is None:
            self.key_quotes = []
        if self.source_evidence is None:
            self.source_evidence = []
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CharacterProfile':
        return cls(**data)


class CharacterAnalyzer:
    """角色分析器"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        import httpx
        from openai import OpenAI
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=httpx.Client(trust_env=False)
        )
        self.model = "deepseek-chat"
    
    async def _call_api(self, prompt: str, temperature: float = 0.7) -> str:
        """调用 DeepSeek API"""
        def sync_call():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文学角色分析师，擅长从文本中提取人物性格特征、行为模式和语言风格。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                stream=False
            )
            return response.choices[0].message.content
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_call)
    
    def _clean_json_response(self, text: str) -> str:
        """清理 Markdown 代码块"""
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = text.strip()
        return text
    
    async def extract_characters(self, text: str, book_title: str = "", book_author: str = "") -> List[CharacterProfile]:
        """
        从文本中提取所有角色
        
        Args:
            text: 书籍文本内容（支持小说文本或角色分析表格）
            book_title: 书名
            book_author: 作者
        
        Returns:
            角色档案列表
        """
        # 截取前8000字进行分析（API限制）
        analysis_text = text[:8000]
        
        prompt = f"""你是一个专业的角色分析师。请从以下内容中提取所有角色信息。

⚠️ 重要：输入可能是以下两种格式之一：
1. 【小说文本】：描述角色行为、语言、对话的叙述性文本
2. 【角色分析表格】：包含多个角色及其性格维度的对比分析表（如角色对比图、能力雷达图、人格维度表等）

书籍/资料信息：
- 标题：{book_title or '未知'}
- 作者：{book_author or '未知'}

内容：
{analysis_text}

请识别所有出现的角色（人物），包括：
- 真实人物（演员、历史人物、商界人物等）
- 虚构角色（小说人物、影视角色、游戏角色等）
- 表格/对比图中列出的任何角色

请以JSON数组格式输出角色列表，每个角色包含：
{{
  "characters": [
    {{
      "id": "角色唯一ID",
      "name": "角色名称（必填）",
      "gender": "男/女/未知",
      "identity": "角色身份（如金融精英、政客、律师、侦探等）",
      "era": "时代背景（如现代、维多利亚时代、未来等）",
      "neuroticism": 0.0-1.0,  // 神经质/情绪稳定性（高=易焦虑敏感，低=冷静稳定）
      "extraversion": 0.0-1.0,  // 外向性（高=开朗活泼，低=内敛沉稳）
      "openness": 0.0-1.0,  // 开放性（高=好奇创新，低=保守传统）
      "agreeableness": 0.0-1.0,  // 宜人性（高=友善合作，低=冷淡疏离）
      "conscientiousness": 0.0-1.0,  // 尽责性（高=自律严谨，低=随性散漫）
      "optimism": 0.0-1.0,  // 乐观程度
      "resilience": 0.0-1.0,  // 抗压韧性
      "self_blame": -1.0到1.0,  // 归因风格-自责倾向
      "external_blame": -1.0到1.0,  // 归因风格-归咎他人
      "speech_patterns": ["口头禅或典型表达"],
      "formality_level": 0.0-1.0,  // 正式度（0=口语，1=正式）
      "emotion_density": 0.0-1.0,  // 情绪表达密度
      "first_person_ratio": 0.0-1.0,  // 第一人称使用频率
      "decision_style": "理性/感性/冲动/谨慎/数据驱动/直觉型",
      "conflict_approach": "协商/对抗/回避/操控/妥协",
      "social_strategy": "开放/封闭/选择性社交",
      "personality_summary": "一段描述角色核心性格特征的总结（100-200字）",
      "key_quotes": ["角色的经典语录或代表观点"],
      "tags": ["角色类型标签，如：励志型/权谋型/专业型/反英雄等"],
      "confidence": 0.0-1.0,  // 分析置信度
      "source_dimension": "如果输入是表格，说明该角色在表格中的维度描述"
    }}
  ]
}}

⚠️ 提取规则：
1. 无论输入是小说还是表格，都要提取所有角色
2. 如果是表格输入，优先使用表格中明确给出的维度数据
3. 如果某项信息未提供，基于角色整体表现合理推断
4. personality_summary 应该体现角色的独特性和核心特点
5. 只输出JSON，不要其他内容"""
        
        result = await self._call_api(prompt)
        
        try:
            clean_result = self._clean_json_response(result)
            data = json.loads(clean_result)
            characters = data.get("characters", [])
            
            profiles = []
            for char_data in characters:
                char_data["id"] = str(uuid.uuid4())[:8]
                char_data["book_title"] = book_title
                char_data["book_author"] = book_author
                profiles.append(CharacterProfile.from_dict(char_data))
            
            return profiles
        except json.JSONDecodeError as e:
            print(f"⚠️ 角色提取失败: {e}")
            return []
    
    async def generate_response(self, character: CharacterProfile, question: str) -> str:
        """
        生成角色对问题的回答
        
        Args:
            character: 角色档案
            question: 用户提出的问题
        
        Returns:
            角色的回答
        """
        personality_desc = f"""
角色：{character.name}
身份：{character.identity}
时代：{character.era}

人格特征：
- 神经质：{character.neuroticism:.1f} (高=易焦虑，低=稳定)
- 外向性：{character.extraversion:.1f} (高=开朗，低=内敛)
- 开放性：{character.openness:.1f} (高=好奇，低=保守)
- 宜人性：{character.agreeableness:.1f} (高=友善，低=冷淡)
- 尽责性：{character.conscientiousness:.1f} (高=自律，低=随性)

决策风格：{character.decision_style}
冲突处理：{character.conflict_approach}
社交策略：{character.social_strategy}

语言风格特征：
- 口头禅：{', '.join(character.speech_patterns) if character.speech_patterns else '无'}
- 正式程度：{'正式' if character.formality_level > 0.6 else '口语化' if character.formality_level < 0.4 else '中等'}
- 情绪表达：{'丰富' if character.emotion_density > 0.6 else '克制' if character.emotion_density < 0.4 else '适度'}

性格总结：{character.personality_summary}

经典语录：
{chr(10).join(f'- {q}' for q in (character.key_quotes or ['无']))}
"""
        
        prompt = f"""你正在扮演文学角色 {character.name}，请基于这个角色的性格特征回答用户的问题。

{personality_desc}

---

用户问题：{question}

请以{character.name}的身份和语气回答这个问题。回答要求：
1. 符合角色的人格特征、价值观和说话方式
2. 可以引用角色的经典语录或行为模式来支持观点
3. 如果角色可能会质疑或反对问题的前提，可以表达不同意见
4. 回答长度适中（200-400字），语言风格贴近角色

⚠️ 免责声明（必须添加在回答末尾）：
---
💡 本回答基于文学角色 {character.name} 的性格模型生成，仅供娱乐和启发参考，不构成专业心理咨询、法律意见或医疗建议。

请开始回答："""
        
        return await self._call_api(prompt, temperature=0.8)
    
    async def generate_debate(
        self, 
        character1: CharacterProfile, 
        character2: CharacterProfile, 
        question: str
    ) -> Dict[str, str]:
        """
        生成两个角色的辩论
        
        Args:
            character1: 角色1
            character2: 角色2
            question: 争议问题
        
        Returns:
            包含双方观点的字典
        """
        # 角色1的观点
        prompt1 = f"""你正在扮演文学角色 {character1.name}，与另一个角色 {character2.name} 就以下问题展开辩论。

你的角色信息：
- 身份：{character1.identity}
- 人格：{character1.personality_summary}
- 决策风格：{character1.decision_style}
- 口头禅：{', '.join(character1.speech_patterns) if character1.speech_patterns else '无'}

对方角色信息（你将反驳的观点）：
- {character2.name} 的立场可能基于其人格：{character2.personality_summary}

---

争议问题：{question}

请以 {character1.name} 的身份：
1. 先给出自己对这个问题的核心观点和理由
2. 预测 {character2.name} 可能提出的反驳
3. 准备针对 {character2.name} 观点的驳论
4. 用符合 {character1.name} 性格和说话方式表达

请用JSON格式输出：
{{
  "opening_statement": "开场陈述",
  "predicted_opponent_view": "预测对方观点",
  "counter_argument": "针对对方的驳论",
  "language_style_notes": "使用的语言风格说明"
}}

只输出JSON。"""
        
        # 角色2的观点
        prompt2 = f"""你正在扮演文学角色 {character2.name}，与另一个角色 {character1.name} 就以下问题展开辩论。

你的角色信息：
- 身份：{character2.identity}
- 人格：{character2.personality_summary}
- 决策风格：{character2.decision_style}
- 口头禅：{', '.join(character2.speech_patterns) if character2.speech_patterns else '无'}

对方角色信息（你将反驳的观点）：
- {character1.name} 的立场可能基于其人格：{character1.personality_summary}

---

争议问题：{question}

请以 {character2.name} 的身份：
1. 先给出自己对这个问题的核心观点和理由
2. 预测 {character1.name} 可能提出的反驳
3. 准备针对 {character1.name} 观点的驳论
4. 用符合 {character2.name} 性格和说话方式表达

请用JSON格式输出：
{{
  "opening_statement": "开场陈述",
  "predicted_opponent_view": "预测对方观点",
  "counter_argument": "针对对方的驳论",
  "language_style_notes": "使用的语言风格说明"
}}

只输出JSON。"""
        
        # 并行执行两个角色的思考
        result1, result2 = await asyncio.gather(
            self._call_api(prompt1, temperature=0.8),
            self._call_api(prompt2, temperature=0.8)
        )
        
        try:
            debate1 = json.loads(self._clean_json_response(result1))
            debate2 = json.loads(self._clean_json_response(result2))
        except json.JSONDecodeError:
            return {
                "character1": {"error": "解析失败"},
                "character2": {"error": "解析失败"}
            }
        
        return {
            "character1": {
                "name": character1.name,
                "personality": character1.personality_summary,
                **debate1
            },
            "character2": {
                "name": character2.name,
                "personality": character2.personality_summary,
                **debate2
            },
            "question": question,
            "generated_at": datetime.now().isoformat()
        }
    
    async def generate_group_response(
        self, 
        characters: List[CharacterProfile], 
        question: str
    ) -> List[Dict]:
        """
        生成多角色并行回答
        
        Args:
            characters: 角色列表
            question: 用户问题
        
        Returns:
            每个角色的回答
        """
        tasks = [
            self.generate_response(char, question)
            for char in characters
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for char, response in zip(characters, responses):
            if isinstance(response, Exception):
                results.append({
                    "character_id": char.id,
                    "character_name": char.name,
                    "error": str(response)
                })
            else:
                results.append({
                    "character_id": char.id,
                    "character_name": char.name,
                    "response": response,
                    "personality_summary": char.personality_summary
                })
        
        return results


def clean_json_response(text: str) -> str:
    """清理 Markdown 代码块"""
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = text.strip()
    return text


# 测试代码
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from dotenv import load_dotenv
    load_dotenv()
    
    async def test():
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            print("请设置 DEEPSEEK_API_KEY 环境变量")
            return
        
        analyzer = CharacterAnalyzer(api_key)
        
        # 测试文本
        sample_text = """
        夏洛克·福尔摩斯坐在贝克街的扶手椅上，手指交叉成他著名的思考姿势。
        "华生，"他说，眼睛盯着天花板，"生活就像一盘棋，每一步都有其意义。"
        华生医生放下手中的报纸，看向他的朋友。
        "你又在想什么，福尔摩斯？"
        "人类的行为，华生，人类的行为。"福尔摩斯站起来，踱步到窗边。
        "我能从一个人的步态看出他的职业，从他的领带看出他的婚姻状况。
        生活是一件需要逻辑和理性分析的事情，情感只会干扰判断。"
        """
        
        print("🧪 测试角色提取...")
        characters = await analyzer.extract_characters(
            sample_text, 
            "福尔摩斯探案集", 
            "柯南·道尔"
        )
        
        for char in characters:
            print(f"\n✅ 提取到角色: {char.name}")
            print(f"   人格总结: {char.personality_summary}")
        
        if characters:
            print("\n🧪 测试角色回答...")
            response = await analyzer.generate_response(
                characters[0],
                "我应该如何处理一个总是背后说我坏话的同事？"
            )
            print(f"\n角色回答:\n{response[:500]}...")
    
    asyncio.run(test())
