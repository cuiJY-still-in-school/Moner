#!/usr/bin/env python3
"""测试API服务器"""

import asyncio
import aiohttp
import time
import subprocess
import sys
import os

async def test_api():
    """测试API服务器"""
    print("启动API服务器测试...")
    
    # 启动API服务器（子进程）
    api_proc = subprocess.Popen(
        [sys.executable, "-m", "server.api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )
    
    print(f"API服务器PID: {api_proc.pid}")
    
    # 等待服务器启动
    print("等待服务器启动...")
    await asyncio.sleep(5)
    
    try:
        # 测试健康端点
        async with aiohttp.ClientSession() as session:
            print("测试健康端点...")
            try:
                async with session.get("http://localhost:8000/api/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✓ 健康检查通过: {data}")
                    else:
                        print(f"✗ 健康检查失败: {resp.status}")
                        return False
            except Exception as e:
                print(f"✗ 健康检查请求失败: {e}")
                return False
            
            # 测试工具列表
            print("测试工具列表端点...")
            try:
                async with session.get("http://localhost:8000/api/tools") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✓ 工具列表: {data.get('tools', {})}")
                    else:
                        print(f"✗ 工具列表失败: {resp.status}")
            except Exception as e:
                print(f"✗ 工具列表请求失败: {e}")
            
            # 测试OpenAPI文档
            print("测试OpenAPI文档...")
            try:
                async with session.get("http://localhost:8000/api/openapi.json") as resp:
                    if resp.status == 200:
                        print("✓ OpenAPI文档可访问")
                    else:
                        print(f"✗ OpenAPI文档失败: {resp.status}")
            except Exception as e:
                print(f"✗ OpenAPI文档请求失败: {e}")
    
    finally:
        # 停止服务器
        print("停止API服务器...")
        api_proc.terminate()
        try:
            api_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_proc.kill()
            api_proc.wait()
        
        print("API服务器已停止")
    
    return True

async def main():
    """主测试函数"""
    print("=== API服务器测试 ===\n")
    
    success = await test_api()
    
    print("\n" + "="*40)
    if success:
        print("API服务器测试完成")
        return 0
    else:
        print("API服务器测试失败")
        return 1

if __name__ == "__main__":
    # 添加当前目录到Python路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)