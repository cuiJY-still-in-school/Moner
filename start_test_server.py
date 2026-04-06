import subprocess
import time
import requests
import sys
import os

# 启动服务器
print("启动API服务器...")
server_process = subprocess.Popen(
    [sys.executable, "-m", "server.api"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    # 等待服务器启动
    time.sleep(3)
    
    # 测试健康端点
    print("测试健康端点...")
    response = requests.get("http://localhost:8000/api/health")
    print(f"健康检查: {response.status_code} - {response.text}")
    
    # 读取会话token
    session_file = os.path.expanduser("~/.moner_session.json")
    import json
    with open(session_file, "r") as f:
        session = json.load(f)
    
    token = session["token"]
    print(f"Token: {token[:50]}...")
    
    # 测试工具执行
    print("\n测试工具执行端点...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"command": "echo test"}
    
    response = requests.post(
        "http://localhost:8000/api/tools/bash/execute",
        headers=headers,
        json=data
    )
    
    print(f"工具执行响应: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code >= 400:
        print(f"错误详情: {response.headers}")
    
finally:
    # 清理
    print("\n清理服务器进程...")
    server_process.terminate()
    server_process.wait()