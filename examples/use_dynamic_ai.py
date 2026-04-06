#!/usr/bin/env python3
"""
使用动态AI功能示例

这个示例展示如何使用Moner系统的动态AI功能，无需预配置模型。
用户在使用时提供provider、base_url、model_name、api_key等参数。

有两种使用方式：
1. 通过CLI命令
2. 通过REST API直接调用
"""

import json

def print_section(title):
    print(f"\n{'='*60}")
    print(title)
    print(f"{'='*60}")

def main():
    print("Moner 动态AI功能使用示例")
    
    print_section("1. 通过CLI使用动态AI")
    print("""
使用CLI命令调用AI模型（需要先登录）：
    
    moner ai "解释一下人工智能" \\
        --provider openai \\
        --api-key YOUR_OPENAI_API_KEY \\
        --model-name gpt-4 \\
        --max-tokens 500 \\
        --temperature 0.7
    
或使用聊天模式：
    
    moner ai "你好，请介绍一下你自己" \\
        --provider openai \\
        --api-key YOUR_OPENAI_API_KEY \\
        --model-name gpt-3.5-turbo \\
        --mode chat \\
        --max-tokens 1000
    
使用Anthropic Claude：
    
    moner ai "解释一下机器学习" \\
        --provider anthropic \\
        --api-key YOUR_ANTHROPIC_API_KEY \\
        --model-name claude-3-opus-20240229 \\
        --max-tokens 1000
    """)
    
    print_section("2. 通过REST API使用动态AI")
    print("""
直接调用API端点（无需预配置模型）：

补全请求：
    
    curl -X POST http://localhost:8000/api/ai/direct/completions \\
      -H "Content-Type: application/json" \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
      -d '{
        "prompt": "解释一下人工智能",
        "provider": "openai",
        "api_key": "YOUR_OPENAI_API_KEY",
        "model_name": "gpt-3.5-turbo",
        "max_tokens": 1000,
        "temperature": 0.7
      }'
    
聊天请求：
    
    curl -X POST http://localhost:8000/api/ai/direct/chat/completions \\
      -H "Content-Type: application/json" \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
      -d '{
        "messages": [
          {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        "provider": "openai",
        "api_key": "YOUR_OPENAI_API_KEY",
        "model_name": "gpt-4",
        "max_tokens": 1000,
        "temperature": 0.7
      }'
    """)
    
    print_section("3. 通过WebSocket工具系统使用")
    print("""
通过WebSocket工具系统调用（与CLI内部使用相同方式）：
    
    # 使用ai_dynamic工具
    {
      "type": "tool_request",
      "data": {
        "tool": "ai_dynamic",
        "params": {
          "prompt": "解释一下人工智能",
          "provider": "openai",
          "api_key": "YOUR_OPENAI_API_KEY",
          "model_name": "gpt-3.5-turbo",
          "max_tokens": 1000,
          "temperature": 0.7
        }
      }
    }
    """)
    
    print_section("4. 支持的AI提供商和配置")
    print("""
支持的AI提供商：
  • openai - OpenAI GPT系列 (GPT-3.5, GPT-4, GPT-4o等)
    - 需要api_key (sk-...)
    - 可选base_url (用于本地部署或代理)
    - 模型名称示例: gpt-3.5-turbo, gpt-4, gpt-4-turbo-preview
    
  • anthropic - Anthropic Claude系列
    - 需要api_key
    - 模型名称示例: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307
    
通用参数：
  • max_tokens: 最大生成token数 (默认: 1000)
  • temperature: 温度参数，控制随机性 (0.0-2.0，默认: 0.7)
  • top_p: 核采样参数 (默认: 1.0)
  • stop: 停止序列列表 (可选)
    """)
    
    print_section("5. 使用步骤")
    print("""
1. 启动Moner系统：
   ./start_all.sh
   
2. 注册/登录用户：
   moner register --username test --password test
   moner login --username test --password test
   
3. 使用AI功能：
   # 方式A: 使用CLI
   moner ai "你的问题" --provider openai --api-key YOUR_KEY
   
   # 方式B: 使用API
   # 先获取访问令牌（登录后CLI会保存）
   # 然后调用API端点
   
4. 查看API文档：
   http://localhost:8000/api/docs
    """)
    
    print_section("注意事项")
    print("""
• API密钥等敏感信息应在安全环境中使用
• 生产环境应使用环境变量或密钥管理服务
• 本地部署时注意base_url配置
• 动态AI调用不会保存API密钥到数据库
• 如需保存配置以便重用，请使用AI模型管理API
    """)

if __name__ == "__main__":
    main()