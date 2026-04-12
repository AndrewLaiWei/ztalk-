"""
DeepSeek AI 分析模块
使用 DeepSeek API 进行话术分析、人格分析、关系梳理
集成 language-psychology-analyzer skill 提供本地快速分析能力
"""

import os
import sys
import json
import re
import asyncio
from typing import List, Dict, Optional
import httpx
from openai import OpenAI

# ============================================================
# 集成 language-psychology-analyzer skill
# ============================================================

SKILL_PATH = os.path.join(
    os.path.dirname(__file__),
    '..',
    'skills',
    'language-psychology-analyzer',
    'scripts'
)

# 添加 skill 路径到 sys.path
if SKILL_PATH not in sys.path:
    sys.path.insert(0, SKILL_PATH)

try:
    from analyze_speech import LanguagePsychologyAnalyzer
    LOCAL_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 无法导入本地分析器: {e}")
    LOCAL_ANALYZER_AVAILABLE = False
    LanguagePsychologyAnalyzer = None


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


# ============================================================
# 心理学与行为学专业术语表（双语）
# ============================================================
PSYCHOLOGY_TERMS = {
    # 操控与操纵
    "gaslighting": {
        "term": "煤气灯效应 / Gaslighting",
        "en": "A form of psychological manipulation where the manipulator makes the victim question their own reality, memory, or sanity.",
        "zh": "一种心理操控手段，施控者让被控者质疑自己的记忆、感知或理智。源于1944年电影《Gaslight》，片中丈夫通过扭曲事实让妻子以为自己疯了。常见于职场PUA、情感操控等场景。",
        "example": "施控者否认说过某些话，或坚称被控者'记错了'，长期以往被控者丧失自我判断能力。",
        "severity": "高危"
    },
    "manipulation": {
        "term": "心理操纵 / Manipulation",
        "en": "Influencing someone to control or utilize them to one's own advantage, often through unfair or deceptive means.",
        "zh": "通过不正当或欺骗性手段影响他人，使其按自己的意图行事。包括情感绑架、故意误导、利用内疚感等技巧。",
        "example": "通过引发对方愧疚感来达成目的，而非直接表达需求。",
        "severity": "中-高"
    },
    "passive_aggressive": {
        "term": "被动攻击 / Passive-Aggressive",
        "en": "Indirect expression of hostility through procrastination, stubbornness, sullenness, or deliberate inefficiency.",
        "zh": "通过间接方式表达敌意，如拖延、固执、沉默、故意低效等。区别于直接攻击，是较为隐蔽的敌意表达方式。",
        "example": "嘴上说'好的'，但总是拖延或找借口不执行。",
        "severity": "中"
    },
    "microaggression": {
        "term": "微侵犯 / Microaggression",
        "en": "Indirect, subtle, or unintentional discrimination against members of a marginalized group.",
        "zh": "对边缘群体成员的间接、微妙或无意的歧视性言行。虽非明显恶意，但传递出对特定群体的偏见或刻板印象。",
        "example": "'你的英语真好，你是从哪里来的？'——表面赞美，实则暗示对方'不是本地人'的身份。",
        "severity": "中"
    },
    
    # 权力与地位
    "power_dynamic": {
        "term": "权力动态 / Power Dynamic",
        "en": "The shifting balance of power and influence between individuals in a relationship or interaction.",
        "zh": "人际交往中双方权力和影响力的动态变化。权力可来源于职位、专业知识、人际关系、情感依赖等多种因素。",
        "example": "上下级对话中，上位者通过信息控制、情绪施压等方式维持权力优势。",
        "severity": "背景"
    },
    "dominance": {
        "term": "支配行为 / Dominance",
        "en": "Behavior aimed at establishing control or authority over others in social interactions.",
        "zh": "在社交互动中确立控制权或权威的行为模式。包括语言打断、话题控制、立场强加等。",
        "example": "频繁打断对方发言，或将个人意见表述为唯一正确答案。",
        "severity": "中"
    },
    "submissive": {
        "term": "顺从型 / Submissive",
        "en": "Tending to yield to the will of others, often at the expense of one's own needs or opinions.",
        "zh": "倾向于屈服于他人意志，常以牺牲自身需求或观点为代价。可能是性格特质，也可能是习得性无助的表现。",
        "example": "即使不同意也点头称是，或主动退让以避免冲突。",
        "severity": "背景"
    },
    
    # 情绪与情感
    "emotional_labor": {
        "term": "情绪劳动 / Emotional Labor",
        "en": "The process of managing feelings and expressions to fulfill the emotional requirements of a job or social role.",
        "zh": "为满足工作或社会角色的情绪要求而管理和表达情感的过程。最早由社会学家Hochschild提出，常见于服务业和管理场景。",
        "example": "客服人员被要求在受委屈时仍保持微笑，或下属在不满时表现恭敬。",
        "severity": "背景"
    },
    "emotional_blackmail": {
        "term": "情感绑架 / Emotional Blackmail",
        "en": "A manipulation tactic where someone uses emotions to pressure or control another person.",
        "zh": "利用情绪来胁迫或控制他人的操控策略。包括引发恐惧、义务感、罪恶感等手段。",
        "example": "'如果你真的爱我，你就会...''都是因为你，我才...'",
        "severity": "高危"
    },
    "DARVO": {
        "term": "DARVO（否认-攻击-反向受害者）/ Deny-Attack-Reverse Victim & Offender",
        "en": "A manipulation tactic: Deny the behavior, Attack the person raising the concern, Reverse roles to become the victim.",
        "zh": "一种操控策略：先否认自己的行为，然后攻击提出质疑的人，最后反转角色将自己变成受害者。常见于权力不对等的关系中。",
        "example": "被指出不当行为时，先说'我没做'，然后说'你怎么可以这样说我'，最后声称自己是受害者。",
        "severity": "高危"
    },
    
    # 防御与攻击机制
    "defensive_communication": {
        "term": "防御性沟通 / Defensive Communication",
        "en": "Responding to perceived threats with heightened self-protection, often blocking effective dialogue.",
        "zh": "面对感知到的威胁时采取过度自我保护的回应方式，常阻碍有效对话。包括反驳、解释过度、转移责任等。",
        "example": "在对话中频繁说'不是这样的'、'你不懂'，而不回应对方的具体观点。",
        "severity": "中"
    },
    "projection": {
        "term": "心理投射 / Projection",
        "en": "Attributing one's own unacceptable thoughts, feelings, or motives to another person.",
        "zh": "将自己的不可接受的思维、情感或动机归因于他人。是常见的无意识防御机制。",
        "example": "内心嫉妒却指责对方'你是在嫉妒我吧'。",
        "severity": "中"
    },
    "stonewalling": {
        "term": "冷暴力 / Stonewalling",
        "en": "Shutting down and refusing to communicate or engage during conflict, often as a power move.",
        "zh": "在冲突中关闭沟通、拒绝回应，常作为一种权力手段使用。是被动攻击的一种形式。",
        "example": "面对质问时沉默不语、转身离开、或用'随便''你说了算'来结束对话。",
        "severity": "中-高"
    },
    
    # 认知偏差
    "confirmation_bias": {
        "term": "确认偏误 / Confirmation Bias",
        "en": "The tendency to search for, interpret, and recall information that confirms one's pre-existing beliefs.",
        "zh": "倾向于搜索、解读和回忆符合自己既有信念的信息。是人类认知的常见偏误，影响客观判断。",
        "example": "只关注支持自己观点的证据，忽视或贬低反对意见。",
        "severity": "背景"
    },
    "authority_bias": {
        "term": "权威偏误 / Authority Bias",
        "en": "The tendency to attribute greater accuracy to the opinion of an authority figure.",
        "zh": "倾向于赋予权威人物的意见更高的准确性。即使权威也可能犯错，但人们往往过度服从。",
        "example": "因为对方是领导就认为其观点一定正确，放弃独立思考。",
        "severity": "背景"
    },
    
    # 人格特质
    "narcissism": {
        "term": "自恋型人格 / Narcissism",
        "en": "Excessive interest in one's own appearance, success, or power, often with a lack of empathy for others.",
        "zh": "对自身外表、成功或权力的过度关注，常伴随对他人共情能力的缺失。自恋程度过高则可能构成自恋型人格障碍(NPD)。",
        "example": "在对话中总是将话题引向自己，或对他人的感受漠不关心。",
        "severity": "中-高"
    },
    "machiavellianism": {
        "term": "马基雅维利主义 / Machiavellianism",
        "en": "The use of cunning and duplicity in social interactions to achieve one's goals.",
        "zh": "在社交互动中使用狡猾和欺骗手段达成目标。以文艺复兴时期政治思想家马基雅维利命名。",
        "example": "为了达成目的而操纵他人，但表面上装作好意。",
        "severity": "中"
    },
    "psychopathy": {
        "term": "心理病态 / Psychopathy",
        "en": "A personality disorder characterized by persistent antisocial behavior, impaired empathy, and bold interpersonal traits.",
        "zh": "一种人格障碍，特征为持续的反社会行为、共情能力受损、以及大胆的人际特质。需专业诊断。",
        "example": "冷酷无情的行为模式，缺乏悔意或良心谴责。",
        "severity": "高"
    },
    
    # 职场特定
    "toxic_workplace": {
        "term": "有毒职场 / Toxic Workplace",
        "en": "An environment where negative behaviors, poor communication, and unhealthy power dynamics are normalized.",
        "zh": "消极行为、沟通不良、不健康权力动态被正常化的工作环境。长期处于其中会影响心理健康。",
        "example": "职场欺凌、过度竞争、领导滥用权力等被视作'正常'。",
        "severity": "背景"
    },
    "职场PUA": {
        "term": "职场PUA / Workplace Gaslighting",
        "en": "Workplace manipulation tactics similar to gaslighting, where employees are made to doubt their abilities or sanity.",
        "zh": "类似煤气灯效应的职场操控手段，使员工质疑自身能力或理智。包括否定成绩、制造焦虑、树立权威等。",
        "example": "'离开了这个平台你什么都不是''换成别人早就被开除了'。",
        "severity": "高危"
    },
    "hostile_communication": {
        "term": "敌意沟通 / Hostile Communication",
        "en": "Communication characterized by aggression, antagonism, or intent to harm the other party.",
        "zh": "以攻击、敌对或伤害对方为目的的沟通方式。包括言语攻击、轻蔑态度、贬低言论等。",
        "example": "公开贬低对方的工作成果，或使用讽刺、嘲笑的语气。",
        "severity": "中-高"
    }
}


class DeepSeekAnalyzer:
    """DeepSeek AI 分析器（增强版：集成本地语言心理分析）"""

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

        # 初始化本地语言分析器（来自 language-psychology-analyzer skill）
        if LOCAL_ANALYZER_AVAILABLE and LanguagePsychologyAnalyzer:
            self.local_analyzer = LanguagePsychologyAnalyzer()
            print("✅ 本地语言分析器已加载 (language-psychology-analyzer skill)")
        else:
            self.local_analyzer = None
            print("⚠️ 本地语言分析器不可用，将仅使用 DeepSeek API")

    def _map_style_to_type(self, style: str) -> str:
        """将分析风格映射为人格类型（双语）"""
        mapping = {
            "assertive": "自信型/Assertive",
            "passive": "被动型/Passive",
            "aggressive": "攻击型/Aggressive",
            "passive_aggressive": "隐性攻击型/Passive-Aggressive",
            "neutral": "中立型/Neutral",
        }
        return mapping.get(style, "待分析/To Analyze")

    def _map_power_level(self, level: str) -> str:
        """映射权力级别（双语）"""
        mapping = {"high": "上位者/High Power", "medium": "平等/Equal", "low": "下位者/Low Power"}
        return mapping.get(level, "待判断/Pending")

    def _quick_local_analysis(self, transcription: Dict) -> List[Dict]:
        """
        使用本地分析器快速分析对话（毫秒级响应）
        作为 DeepSeek 分析的快速预处理或 fallback
        """
        if not self.local_analyzer:
            return []

        timeline = transcription.get("timeline", [])

        # 按说话人分组
        speaker_texts = {}
        for item in timeline:
            speaker = item.get("speaker", "speaker_1")
            text = item.get("text", "")
            if speaker not in speaker_texts:
                speaker_texts[speaker] = []
            speaker_texts[speaker].append(text)

        results = []

        # 分析每个说话人
        for speaker, texts in speaker_texts.items():
            full_text = " ".join(texts)
            if not full_text.strip():
                continue

            # 使用本地分析器
            try:
                result = self.local_analyzer.analyze_utterance(speaker, full_text)

                results.append({
                    "id": speaker,
                    "name": speaker,
                    "personality_type": self._map_style_to_type(
                        result.psychological_profile.communication_style
                    ),
                    "communication_style": result.psychological_profile.communication_style,
                    "emotional_traits": [result.psychological_profile.emotional_state],
                    "power_position": self._map_power_level(
                        result.power_analysis.power_level
                    ),
                    "communication_techniques": result.communication_strategy.tactics,
                    "strengths": self._extract_strengths(result),
                    "weaknesses": self._extract_weaknesses(result),
                    # 来自 language-psychology-analyzer skill 的增强字段
                    "big_five": result.psychological_profile.personality_traits,
                    "confidence_level": result.psychological_profile.confidence_level,
                    "sincerity_score": result.communication_strategy.sincerity_score,
                    "subtext_hint": result.subtext_analysis.underlying_meaning,
                    "emotional_undercurrent": result.subtext_analysis.emotional_undercurrent,
                    "hidden_intent": result.subtext_analysis.hidden_intent,
                    "defense_mechanisms": result.psychological_profile.defense_mechanisms,
                    "analysis_source": "local",  # 标记数据来源
                })
            except Exception as e:
                print(f"⚠️ 本地分析器处理 {speaker} 时出错: {e}")

        return results

    def _extract_strengths(self, result) -> List[str]:
        """从分析结果中提取优势（双语）"""
        strengths = []

        # 基于自信程度
        if result.psychological_profile.confidence_level > 0.7:
            strengths.append("表达清晰、自信 / Clear and confident expression")

        # 基于沟通风格
        if result.psychological_profile.communication_style == "assertive":
            strengths.append("沟通直接、有主见 / Direct and assertive communication")

        # 基于真诚度
        if result.communication_strategy.sincerity_score > 0.7:
            strengths.append("表达真诚度高 / High sincerity in expression")

        # 基于情绪控制
        if result.psychological_profile.emotional_state in ["中性", "愉悦", "中性/Neutral", "愉悦/Positive"]:
            strengths.append("情绪稳定 / Emotionally stable")

        return strengths if strengths else ["待进一步分析 / Needs further analysis"]

    def _extract_weaknesses(self, result) -> List[str]:
        """从分析结果中提取弱点（双语）"""
        weaknesses = []

        # 基于防御机制
        if result.psychological_profile.defense_mechanisms:
            weakness_labels = {
                "denial": "可能存在否认倾向 / May have denial tendency",
                "rationalization": "可能过度合理化 / May over-rationalize",
                "projection": "可能存在投射心理 / May have projection",
                "passive-aggressive": "沟通方式偏隐性攻击 / Tends toward passive-aggressive",
            }
            for mechanism in result.psychological_profile.defense_mechanisms:
                if mechanism in weakness_labels:
                    weaknesses.append(weakness_labels[mechanism])

        # 基于情绪状态
        if result.psychological_profile.emotional_state in ["愤怒", "焦虑", "愤怒/Anger", "焦虑/Anxiety"]:
            weaknesses.append("情绪较激动，可能影响判断 / Emotionally agitated, may affect judgment")

        # 基于操纵指标
        if result.communication_strategy.manipulation_indicators:
            weaknesses.append("存在一定操纵性话术 / Contains manipulative language")

        return weaknesses if weaknesses else ["待进一步分析 / Needs further analysis"]
    
    async def analyze_personality(self, transcription: Dict) -> List[Dict]:
        """
        分析说话人人格特征

        基于对话内容分析每个人的:
        - 沟通风格 (支配型/被动型/攻击型等)
        - 情绪特征 (稳定/易怒/焦虑等)
        - 权力位置 (上位者/下位者)
        - 沟通技巧

        增强：集成本地分析器的快速预分析结果
        """
        # 1. 先用本地分析器快速分析（毫秒级）
        local_results = self._quick_local_analysis(transcription)

        # 2. 调用 DeepSeek 进行深度分析
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

        try:
            result = await self._call_api(prompt)

            # 清理 Markdown 代码块
            clean_result = clean_json_response(result)
            data = json.loads(clean_result)
            deepseek_speakers = data.get("speakers", [])

            if deepseek_speakers:
                # 3. 合并本地和 DeepSeek 结果
                return self._merge_personality_results(local_results, deepseek_speakers)

        except json.JSONDecodeError as e:
            print(f"⚠️ analyze_personality JSON解析失败: {e}")

        # Fallback: 如果 DeepSeek 失败但本地分析成功，返回本地结果
        if local_results:
            print("🔄 使用本地分析器结果作为 Fallback")
            return local_results

        # 全部失败，返回默认结构
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

    def _merge_personality_results(self, local_results: List[Dict],
                                   deepseek_results: List[Dict]) -> List[Dict]:
        """
        合并本地分析器和 DeepSeek 的分析结果
        DeepSeek 结果作为主要来源，本地结果作为增强字段
        """
        if not deepseek_results:
            return local_results

        if not local_results:
            return deepseek_results

        # 创建本地结果的映射
        local_map = {r["id"]: r for r in local_results}

        merged_results = []

        for ds_result in deepseek_results:
            speaker_id = ds_result.get("id", "speaker_1")

            # 如果本地分析有这个说话人，合并
            if speaker_id in local_map:
                local = local_map[speaker_id]

                # DeepSeek 字段优先，本地字段作为增强
                merged = {**ds_result}

                # 添加本地分析器的增强字段
                for key in ["big_five", "confidence_level", "sincerity_score",
                           "subtext_hint", "emotional_undercurrent", "hidden_intent",
                           "defense_mechanisms"]:
                    if key in local and local[key]:
                        merged[key] = local[key]

                merged["analysis_source"] = "hybrid"  # 标记为混合来源
                merged_results.append(merged)
            else:
                # DeepSeek 独有的分析结果
                merged_results.append({**ds_result, "analysis_source": "deepseek"})

        return merged_results
    
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

        增强：使用本地分析器提供更深层的语言心理分析
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

        try:
            result = await self._call_api(prompt)

            # 清理 Markdown 代码块
            clean_result = clean_json_response(result)
            print(f"📝 extract_phrases API返回: {clean_result[:300]}...")
            data = json.loads(clean_result)
            phrases = data.get("phrases", [])

            if phrases and len(phrases) > 0:
                # 使用本地分析器增强每条话术
                return self._enhance_phrases_with_local(phrases, transcription)

            # 如果返回空数组，从 timeline 中提取关键对话
            print(f"⚠️ extract_phrases 返回空数组，使用 fallback")
            return self._extract_phrases_from_timeline(transcription)

        except json.JSONDecodeError as e:
            print(f"⚠️ extract_phrases JSON解析失败: {e}")
            print(f"   原始返回: {result[:500]}...")
            # 从时间轴提取关键对话
            return self._extract_phrases_from_timeline(transcription)

    def _enhance_phrases_with_local(self, phrases: List[Dict],
                                    transcription: Dict) -> List[Dict]:
        """
        使用本地分析器增强话术分析结果
        添加深层心理分析、潜台词解读等
        """
        if not self.local_analyzer:
            return phrases

        # 获取时间轴用于匹配
        timeline_map = {}
        for item in transcription.get("timeline", []):
            speaker = item.get("speaker", "speaker_1")
            text = item.get("text", "")
            time_str = item.get("time", "")
            if text not in timeline_map:
                timeline_map[text] = {"speaker": speaker, "time": time_str}

        enhanced_phrases = []

        for phrase in phrases:
            original_text = phrase.get("original_phrase", "")

            # 在时间轴中查找匹配
            match_info = timeline_map.get(original_text, {})

            # 使用本地分析器分析这句话
            if original_text and self.local_analyzer:
                try:
                    local_result = self.local_analyzer.analyze_utterance(
                        phrase.get("speaker", "speaker_1"),
                        original_text
                    )

                    # 添加本地分析器的增强字段
                    phrase["local_analysis"] = {
                        "emotional_state": local_result.psychological_profile.emotional_state,
                        "confidence_level": local_result.psychological_profile.confidence_level,
                        "sincerity_score": local_result.communication_strategy.sincerity_score,
                        "subtext_deep": local_result.subtext_analysis.underlying_meaning,
                        "emotional_undercurrent": local_result.subtext_analysis.emotional_undercurrent,
                        "hidden_intent": local_result.subtext_analysis.hidden_intent,
                        "attack_indicators": local_result.communication_strategy.attack_indicators,
                        "defense_indicators": local_result.communication_strategy.defense_indicators,
                        "manipulation_indicators": local_result.communication_strategy.manipulation_indicators,
                        "power_markers": local_result.power_analysis.power_markers,
                    }

                    # 如果 DeepSeek 没有提供潜台词，使用本地分析结果
                    if not phrase.get("hidden_meaning") or "待" in phrase.get("hidden_meaning", ""):
                        phrase["hidden_meaning"] = local_result.subtext_analysis.underlying_meaning

                    # 如果没有提供类别，使用本地分析结果
                    if not phrase.get("category") or "待" in phrase.get("category", ""):
                        tactics = local_result.communication_strategy.tactics
                        if tactics:
                            phrase["category"] = ", ".join(tactics)

                    # 如果没有提供 power_level 或类别为中性，使用本地分析结果
                    if not phrase.get("power_level") or phrase.get("category", "").startswith("中性"):
                        # 优先使用本地分析器的 power_level 结果
                        local_power = local_result.power_analysis.power_level
                        
                        # 基于微侵犯检测强制设置高权力
                        if local_result.subtext_analysis.microaggression_detected:
                            phrase["power_level"] = "高"  # 微侵犯通常来自上位者
                        # 基于攻击性指标强制设置高权力
                        elif local_result.communication_strategy.attack_indicators:
                            phrase["power_level"] = "高"
                        # 基于防御性指标设置中权力
                        elif local_result.communication_strategy.defense_indicators:
                            phrase["power_level"] = "中"
                        # 否则直接使用本地分析器的结果
                        else:
                            power_map = {"high": "高", "medium": "中", "low": "低"}
                            phrase["power_level"] = power_map.get(local_power, "中")

                    # 如果没有提供应对策略，添加本地建议
                    if not phrase.get("coping_strategy") or "待" in phrase.get("coping_strategy", ""):
                        if local_result.psychological_profile.emotional_state == "愤怒":
                            phrase["coping_strategy"] = "建议保持冷静，避免正面冲突，可以尝试转移话题或表示理解对方情绪"
                        elif local_result.communication_strategy.attack_indicators:
                            phrase["coping_strategy"] = "识别为攻击性话术，建议不正面回应，可采用反问或转移策略"
                        else:
                            phrase["coping_strategy"] = "建议根据具体场景选择合适的回应方式"

                except Exception as e:
                    print(f"⚠️ 本地分析器处理话术时出错: {e}")

            enhanced_phrases.append(phrase)

        return enhanced_phrases
    
    def _extract_phrases_from_timeline(self, transcription: Dict) -> List[Dict]:
        """
        从时间轴直接提取关键对话
        使用本地分析器进行潜台词分析（Fallback 方案）
        """
        phrases = []
        timeline = transcription.get("timeline", [])

        # 找出较长的对话片段（可能是关键话术）
        for item in timeline:
            text = item.get("text", "").strip()
            if len(text) > 30 and len(phrases) < 10:
                speaker = item.get("speaker", "speaker_1")
                time_str = item.get("time", "")

                # 使用本地分析器进行分析（Fallback 方案）
                local_result = None
                if self.local_analyzer:
                    try:
                        local_result = self.local_analyzer.analyze_utterance(speaker, text)
                    except Exception as e:
                        print(f"⚠️ 本地分析器处理话术时出错: {e}")

                # 构建话术分析结果
                phrase_entry = {
                    "speaker": speaker,
                    "original_phrase": text,
                    "time_range": time_str,
                    "literal_meaning": text,
                    "hidden_meaning": "需要结合完整对话场景理解",
                    "power_level": "中",
                    "manipulation_type": "",
                    "category": "对话",
                    "coping_strategy": "建议结合完整对话场景理解"
                }

                # 如果本地分析成功，应用分析结果
                if local_result:
                    phrase_entry.update({
                        "hidden_meaning": local_result.subtext_analysis.underlying_meaning,
                        "category": ", ".join(local_result.communication_strategy.tactics) if local_result.communication_strategy.tactics else "对话",
                        "power_level": local_result.power_analysis.power_level.capitalize(),
                        "coping_strategy": self._generate_coping_suggestion_from_result(local_result),
                        "local_analysis": {
                            "emotional_state": local_result.psychological_profile.emotional_state,
                            "confidence_level": local_result.psychological_profile.confidence_level,
                            "sincerity_score": local_result.communication_strategy.sincerity_score,
                            "subtext_deep": local_result.subtext_analysis.underlying_meaning,
                            "emotional_undercurrent": local_result.subtext_analysis.emotional_undercurrent,
                            "hidden_intent": local_result.subtext_analysis.hidden_intent,
                            "power_level": local_result.power_analysis.power_level,
                            "attack_indicators": local_result.communication_strategy.attack_indicators,
                            "defense_indicators": local_result.communication_strategy.defense_indicators,
                            "manipulation_indicators": local_result.communication_strategy.manipulation_indicators,
                        }
                    })

                phrases.append(phrase_entry)

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

    def _detect_psychology_terms(self, text: str) -> List[Dict]:
        """
        检测文本中提到的心理学和行为学术语
        并返回术语解释列表
        """
        detected_terms = []
        text_lower = text.lower()
        
        # 检测每个术语
        for term_key, term_info in PSYCHOLOGY_TERMS.items():
            # 多种匹配模式
            patterns = [
                term_key.lower(),
                term_info["term"].split("/")[0].strip().lower(),  # 中文名
                term_info["term"].split("/")[1].strip().lower() if "/" in term_info["term"] else "",  # 英文名
            ]
            
            for pattern in patterns:
                if pattern and pattern in text_lower:
                    detected_terms.append({
                        "key": term_key,
                        "term": term_info["term"],
                        "en": term_info["en"],
                        "zh": term_info["zh"],
                        "example": term_info["example"],
                        "severity": term_info["severity"]
                    })
                    break  # 每个术语只添加一次
        
        # 去重
        seen = set()
        unique_terms = []
        for t in detected_terms:
            if t["key"] not in seen:
                seen.add(t["key"])
                unique_terms.append(t)
        
        return unique_terms

    def _generate_coping_suggestion_from_result(self, result) -> str:
        """根据本地分析结果生成应对建议"""
        # 基于情绪状态
        if result.psychological_profile.emotional_state == "愤怒":
            return "对方情绪激动，建议保持冷静，避免正面冲突，可以尝试表示理解或转移话题"

        if result.psychological_profile.emotional_state == "焦虑":
            return "对方可能感到不安，建议表达支持和理解，帮助对方降低压力"

        if result.psychological_profile.emotional_state == "冷漠":
            return "对方态度冷淡，可能在试探或防御，建议主动但不过分热情"

        # 基于话术类型
        if result.communication_strategy.attack_indicators:
            return "检测到攻击性话术，建议不正面回应，可采用反问、转移或幽默化解"

        if result.communication_strategy.manipulation_indicators:
            return "检测到操纵性话术，建议保持警惕，坚守底线，不被情绪绑架"

        if result.communication_strategy.defense_indicators:
            return "对方处于防御状态，建议先建立信任或安全感，再深入讨论"

        # 基于权力分析
        if result.power_analysis.power_level == "high":
            return "对方处于上位，注意沟通方式和语气，可采用请教或建议的方式"

        if result.power_analysis.power_level == "low":
            return "对方可能感到弱势，建议给予尊重和肯定，避免进一步施压"

        # 默认建议
        return "建议根据具体场景选择合适的回应方式"
    
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
            report = data.get("report", {
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
            
            # 检测报告中提到的心理学术语
            report_text = json.dumps(report, ensure_ascii=False)
            report["psychology_terms"] = self._detect_psychology_terms(report_text)
            
            return report
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
                "battle_summary": "一场典型的职场权力对话",
                "psychology_terms": []
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
