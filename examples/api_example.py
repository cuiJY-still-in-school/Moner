#!/usr/bin/env python3
"""
Moner API 使用示例

确保API服务器正在运行：./start_all.sh
或分别启动：
- WebSocket: python -m server.main
- REST API: python -m server.api
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8000/api"

async def example():
    """API使用示例"""
    print("=== Moner API 示例 ===\n")
    
    async with aiohttp.ClientSession() as session:
        # 1. 健康检查
        print("1. 健康检查...")
        async with session.get(f"{API_BASE}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   状态: {data['status']}")
            else:
                print(f"   失败: {resp.status}")
        
        # 2. 注册用户
        print("\n2. 注册用户...")
        register_data = {
            "username": "api_user",
            "password": "api_password",
            "user_type": "human",
            "display_name": "API Test User"
        }
        
        async with session.post(f"{API_BASE}/auth/register", 
                               json=register_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data["access_token"]
                print(f"   注册成功，令牌: {token[:20]}...")
            else:
                print(f"   注册失败: {resp.status}")
                # 尝试登录（用户可能已存在）
                login_data = {
                    "username": "api_user",
                    "password": "api_password"
                }
                async with session.post(f"{API_BASE}/auth/login",
                                       data=login_data) as login_resp:
                    if login_resp.status == 200:
                        data = await login_resp.json()
                        token = data["access_token"]
                        print(f"   登录成功，令牌: {token[:20]}...")
                    else:
                        print("   注册和登录都失败，停止示例")
                        return
        
        # 3. 获取当前用户信息
        print("\n3. 获取当前用户信息...")
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(f"{API_BASE}/auth/me", 
                              headers=headers) as resp:
            if resp.status == 200:
                user = await resp.json()
                print(f"   用户ID: {user['id']}")
                print(f"   用户名: {user['username']}")
                print(f"   用户类型: {user['user_type']}")
            else:
                print(f"   失败: {resp.status}")
        
        # 4. 列出可用工具
        print("\n4. 列出可用工具...")
        async with session.get(f"{API_BASE}/tools", 
                              headers=headers) as resp:
            if resp.status == 200:
                tools = await resp.json()
                print(f"   可用工具: {', '.join(tools['tools'].keys())}")
            else:
                print(f"   失败: {resp.status}")
        
        # 5. 执行bash命令
        print("\n5. 执行bash命令...")
        tool_data = {
            "command": "echo 'Hello from API' && pwd"
        }
        async with session.post(f"{API_BASE}/tools/bash/execute",
                               headers=headers,
                               json=tool_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                if result["success"]:
                    print(f"   成功！输出:\n{result['output']}")
                else:
                    print(f"   命令执行失败: {result.get('error')}")
            else:
                print(f"   请求失败: {resp.status}")
        
        # 6. 创建目标
        print("\n6. 创建目标...")
        goal_data = {
            "title": "学习Moner API",
            "description": "通过示例学习如何使用Moner REST API",
            "status": "in_progress",
            "progress": 50.0,
            "priority": 1
        }
        async with session.post(f"{API_BASE}/goals",
                               headers=headers,
                               json=goal_data) as resp:
            if resp.status == 200:
                goal = await resp.json()
                print(f"   目标创建成功: {goal['title']} (ID: {goal['id']})")
            else:
                print(f"   创建目标失败: {resp.status}")
        
        # 7. 获取目标列表
        print("\n7. 获取目标列表...")
        async with session.get(f"{API_BASE}/goals",
                              headers=headers) as resp:
            if resp.status == 200:
                goals = await resp.json()
                print(f"   共有 {len(goals)} 个目标:")
                for goal in goals[:3]:  # 显示前3个
                    print(f"     - {goal['title']} ({goal['status']}, {goal['progress']}%)")
                if len(goals) > 3:
                    print(f"     ... 和 {len(goals) - 3} 个更多")
            else:
                print(f"   获取目标失败: {resp.status}")
    
    print("\n=== 示例完成 ===")
    print("\n提示:")
    print("- 查看完整API文档: http://localhost:8000/api/docs")
    print("- 使用CLI客户端: moner --help")
    print("- 同时启动所有服务: ./start_all.sh")

async def main():
    """主函数"""
    try:
        await example()
    except aiohttp.ClientConnectorError:
        print("错误: 无法连接到API服务器")
        print("请确保API服务器正在运行: python -m server.api")
        print("或运行: ./start_all.sh")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())