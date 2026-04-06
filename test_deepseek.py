#!/usr/bin/env python3
"""
测试DeepSeek API连接的脚本
使用方法: python test_deepseek.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import AsyncOpenAI

async def test_deepseek():
    """测试DeepSeek API连接"""
    api_key = "sk-070b61cd5efd4a0686c61396a2098415"
    base_url = "https://api.deepseek.com"
    
    print(f"测试DeepSeek API连接...")
    print(f"API密钥: {api_key[:10]}...")
    print(f"Base URL: {base_url}")
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    try:
        # 测试聊天补全
        print("\n发送请求到DeepSeek...")
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Hello, 请用中文回复。你是谁？"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        print("\n响应成功！")
        print(f"模型: {response.model}")
        print(f"完成原因: {response.choices[0].finish_reason}")
        print(f"回复内容: {response.choices[0].message.content}")
        
        # 显示使用情况
        if response.usage:
            print(f"使用情况: {response.usage.total_tokens} tokens")
        
        return True
        
    except Exception as e:
        print(f"\n错误: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_deepseek())
    sys.exit(0 if success else 1)