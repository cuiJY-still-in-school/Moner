#!/usr/bin/env python3
"""
AI API使用示例

这个示例展示如何使用Moner系统的AI API功能。
首先启动服务器: ./start_all.sh
然后运行此脚本: python examples/ai_api_example.py
"""

import requests
import json
import sys

# API基础URL
BASE_URL = "http://localhost:8000/api"

def print_step(step):
    print(f"\n{'='*60}")
    print(f"步骤: {step}")
    print(f"{'='*60}")

def main():
    print("Moner AI API 使用示例")
    print("确保服务器正在运行 (./start_all.sh)\n")
    
    # 1. 注册用户
    print_step("1. 注册用户")
    register_data = {
        "username": "ai_user",
        "password": "ai_password",
        "user_type": "human"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"✓ 用户注册成功")
            print(f"  访问令牌: {access_token[:20]}...")
        else:
            # 用户可能已存在，尝试登录
            print(f"⚠ 注册失败 (可能用户已存在)，尝试登录...")
            login_data = {
                "username": "ai_user",
                "password": "ai_password"
            }
            response = requests.post(
                f"{BASE_URL}/auth/login", 
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"✓ 登录成功")
                print(f"  访问令牌: {access_token[:20]}...")
            else:
                print(f"✗ 登录失败: {response.status_code}")
                print(response.text)
                sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务器。请确保服务器正在运行。")
        sys.exit(1)
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 创建AI模型配置（需要API密钥，这里创建占位符配置）
    print_step("2. 创建AI模型配置")
    ai_model_data = {
        "name": "openai-gpt-4",
        "provider": "openai",
        "model_name": "gpt-4",
        "api_key": "sk-xxx",  # 替换为实际的API密钥
        "base_url": "https://api.openai.com/v1",
        "is_default": True
    }
    
    response = requests.post(f"{BASE_URL}/ai/models", json=ai_model_data, headers=headers)
    if response.status_code in [200, 201]:
        model = response.json()
        model_id = model["id"]
        print(f"✓ AI模型创建成功 (ID: {model_id})")
        print(f"  名称: {model['name']}, 提供商: {model['provider']}")
    else:
        print(f"⚠ AI模型创建失败 (可能已存在): {response.status_code}")
        # 尝试获取现有模型
        response = requests.get(f"{BASE_URL}/ai/models", headers=headers)
        if response.status_code == 200:
            models = response.json()
            if models:
                model_id = models[0]["id"]
                print(f"  使用现有模型 ID: {model_id}")
            else:
                print(f"✗ 没有可用的AI模型")
                model_id = None
        else:
            model_id = None
    
    # 3. 创建提示模板
    print_step("3. 创建提示模板")
    prompt_template_data = {
        "name": "代码助手",
        "description": "帮助编写和解释代码",
        "template": "你是一个专业的编程助手。请帮助用户解决以下编程问题：\n\n{problem}",
        "variables": ["problem"],
        "category": "programming",
        "tags": ["code", "assistant"],
        "is_system": True,
        "is_public": True
    }
    
    response = requests.post(f"{BASE_URL}/ai/prompts", json=prompt_template_data, headers=headers)
    if response.status_code in [200, 201]:
        template = response.json()
        template_id = template["id"]
        print(f"✓ 提示模板创建成功 (ID: {template_id})")
        print(f"  名称: {template['name']}, 描述: {template['description']}")
    else:
        print(f"⚠ 提示模板创建失败: {response.status_code}")
        template_id = None
    
    # 4. 创建对话
    print_step("4. 创建对话")
    conversation_data = {
        "title": "测试对话",
        "ai_model_id": model_id if model_id else None
    }
    
    response = requests.post(f"{BASE_URL}/ai/conversations", json=conversation_data, headers=headers)
    if response.status_code in [200, 201]:
        conversation = response.json()
        conversation_id = conversation["id"]
        print(f"✓ 对话创建成功 (ID: {conversation_id})")
        print(f"  标题: {conversation['title']}")
    else:
        print(f"✗ 对话创建失败: {response.status_code}")
        print(response.text)
        conversation_id = None
    
    if conversation_id:
        # 5. 发送消息到对话
        print_step("5. 发送消息到对话")
        message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": "你好，请介绍一下你自己。"
        }
        
        response = requests.post(f"{BASE_URL}/ai/messages", json=message_data, headers=headers)
        if response.status_code in [200, 201]:
            message = response.json()
            print(f"✓ 消息发送成功 (ID: {message['id']})")
            print(f"  内容: {message['content'][:50]}...")
        else:
            print(f"⚠ 消息发送失败: {response.status_code}")
            print(response.text)
    
    # 6. 获取对话消息
    print_step("6. 获取对话消息")
    if conversation_id:
        response = requests.get(f"{BASE_URL}/ai/conversations/{conversation_id}/messages", headers=headers)
        if response.status_code == 200:
            messages = response.json()
            print(f"✓ 获取到 {len(messages)} 条消息")
            for msg in messages:
                print(f"  [{msg['role']}] {msg['content'][:60]}...")
        else:
            print(f"⚠ 获取消息失败: {response.status_code}")
    
    # 7. 使用AI补全API（需要有效的API密钥）
    print_step("7. 测试AI补全API")
    print("注意: 需要有效的API密钥才能实际调用AI服务")
    print("这里演示API调用格式，但不会实际调用AI服务")
    
    completion_data = {
        "prompt": "解释一下人工智能的概念",
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = requests.post(f"{BASE_URL}/ai/completions", json=completion_data, headers=headers)
    if response.status_code == 200:
        completion = response.json()
        print(f"✓ AI补全成功")
        print(f"  模型: {completion['model']}")
        print(f"  补全: {completion['completion'][:100]}...")
    elif response.status_code == 400:
        print(f"⚠ AI补全失败 (可能缺少API密钥或模型配置)")
        print(f"  响应: {response.text}")
    else:
        print(f"⚠ AI补全响应: {response.status_code}")
    
    # 8. 列出所有可用工具
    print_step("8. 列出所有可用工具")
    response = requests.get(f"{BASE_URL}/tools", headers=headers)
    if response.status_code == 200:
        tools = response.json()
        tool_names = tools.get("tools", {})
        print(f"✓ 可用的工具: {', '.join(tool_names.keys()) if isinstance(tool_names, dict) else str(tool_names)}")
    
    print("\n" + "="*60)
    print("示例完成！")
    print("="*60)
    print("\n接下来可以:")
    print("1. 配置真实的AI API密钥")
    print("2. 通过 /api/docs 查看完整的API文档")
    print("3. 使用CLI客户端与系统交互")
    print("4. 探索其他API端点")

if __name__ == "__main__":
    main()