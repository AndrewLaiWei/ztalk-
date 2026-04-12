#!/usr/bin/env python3
"""测试心理学术语检测"""
import sys
sys.path.insert(0, 'D:/ai-ide-workspace/ZTalk/ZTalk - live/backend')

from deepseek_analyzer import DeepSeekAnalyzer, PSYCHOLOGY_TERMS

# 测试术语检测
analyzer = None  # 不需要实例就能测试 _detect_psychology_terms

# 模拟一个报告文本
test_reports = [
    "检测到煤气灯效应，对方的沟通方式属于心理操纵，可能存在被动攻击行为。",
    "这场对话中涉及微侵犯和权力动态分析。",
    "这是一个典型的有毒职场场景，存在职场PUA现象。",
    "对话中存在情绪劳动的过度使用，沟通风格偏被动攻击型。",
    "关键发现：对方使用了DARVO策略，伴随一定程度的煤气灯效应。",
]

print("=== 心理学/行为学术语检测测试 ===")
print()

for i, text in enumerate(test_reports, 1):
    # 模拟检测
    detected = []
    text_lower = text.lower()

    for term_key, term_info in PSYCHOLOGY_TERMS.items():
        patterns = [
            term_key.lower(),
            term_info["term"].split("/")[0].strip().lower(),
        ]
        if "/" in term_info["term"]:
            patterns.append(term_info["term"].split("/")[1].strip().lower())

        for pattern in patterns:
            if pattern and pattern in text_lower:
                detected.append({
                    "key": term_key,
                    "term": term_info["term"],
                    "severity": term_info["severity"],
                    "zh": term_info["zh"][:80] + "..."
                })
                break

    print(f"测试 {i}: \"{text[:50]}...\"")
    print(f"  检测到 {len(detected)} 个术语:")
    for d in detected:
        print(f"    - {d['term']} [{d['severity']}]")
        print(f"      {d['zh']}")
    print()

print(f"\n共收录 {len(PSYCHOLOGY_TERMS)} 个心理学/行为学专业术语")
print("\n术语列表:")
for key, info in list(PSYCHOLOGY_TERMS.items())[:10]:
    print(f"  - {info['term']}")
print("  ... 更多")
