"""
测试 DeepSeek API 是否正常工作
"""

import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

api_key = os.getenv("DEEPSEEK_API_KEY")
print(f"API Key: {api_key[:10]}..." if api_key else "No API Key")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "你好，返回JSON格式: {\"status\": \"ok\", \"message\": \"API正常工作\"}"}
        ],
        temperature=0.7
    )
    print("✅ API 调用成功!")
    print(f"响应: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ API 调用失败: {e}")
