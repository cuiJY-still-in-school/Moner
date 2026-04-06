#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import typer
from typing import Optional
import websockets
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()

# 版本信息
VERSION = "1.0.0"

@app.command()
def version():
    """显示Moner版本"""
    typer.echo(f"Moner v{VERSION}")
    typer.echo("CLI非冷启动AI系统")
    typer.echo("支持动态AI调用、WebSocket通信和工具执行")

# 配置
WS_URL = "ws://localhost:8765"
API_URL = "http://localhost:8000"
SESSION_FILE = os.path.expanduser("~/.moner_session.json")
current_token = None
current_user = None
websocket_connection = None

# 会话管理函数
def save_session(token: str, user: dict):
    """保存会话到文件"""
    session_data = {
        "token": token,
        "user": user,
        "timestamp": asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 0
    }
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(session_data, f)
        logger.info(f"会话已保存到 {SESSION_FILE}")
    except Exception as e:
        logger.error(f"保存会话失败: {e}")

def load_session():
    """从文件加载会话"""
    global current_token, current_user
    if not os.path.exists(SESSION_FILE):
        return False
    
    try:
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)
        
        current_token = session_data.get("token")
        current_user = session_data.get("user")
        
        if current_token and current_user:
            logger.info(f"会话已加载，用户: {current_user.get('username')}")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"加载会话失败: {e}")
        return False

def clear_session():
    """清除会话"""
    global current_token, current_user
    current_token = None
    current_user = None
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            logger.info("会话已清除")
    except Exception as e:
        logger.error(f"清除会话失败: {e}")

# 启动时加载会话
load_session()

async def connect_to_server():
    """连接到WebSocket服务器"""
    try:
        ws = await websockets.connect(WS_URL)
        return ws
    except Exception as e:
        logger.error(f"连接失败: {e}")
        return None

async def send_message(ws, msg_type: str, data: dict):
    """发送消息到服务器"""
    message = json.dumps({"type": msg_type, "data": data})
    await ws.send(message)
    
    # 等待响应
    try:
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        return json.loads(response)
    except asyncio.TimeoutError:
        return {"type": "error", "data": {"error": "请求超时"}}
    except Exception as e:
        return {"type": "error", "data": {"error": str(e)}}

async def register_user(username: str, password: str, email: Optional[str] = None, 
                       user_type: str = "human", display_name: Optional[str] = None):
    """注册新用户"""
    ws = await connect_to_server()
    if not ws:
        return False
    
    data = {
        "username": username,
        "password": password,
        "email": email,
        "user_type": user_type,
        "display_name": display_name or username
    }
    
    response = await send_message(ws, "register", data)
    await ws.close()
    
    if response.get("type") == "login":
        global current_token, current_user
        current_token = response["data"]["access_token"]
        current_user = response["data"]["user"]
        logger.info(f"注册成功，用户ID: {current_user['id']}")
        # 保存会话
        save_session(current_token, current_user)
        return True
    else:
        error_msg = response.get("data", {}).get("error", "未知错误")
        logger.error(f"注册失败: {error_msg}")
        return False

async def login_user(username: str, password: str):
    """登录用户"""
    ws = await connect_to_server()
    if not ws:
        return False
    
    data = {
        "username": username,
        "password": password
    }
    
    response = await send_message(ws, "login", data)
    await ws.close()
    
    if response.get("type") == "login":
        global current_token, current_user
        current_token = response["data"]["access_token"]
        current_user = response["data"]["user"]
        logger.info(f"登录成功，用户ID: {current_user['id']}")
        # 保存会话
        save_session(current_token, current_user)
        return True
    else:
        error_msg = response.get("data", {}).get("error", "未知错误")
        logger.error(f"登录失败: {error_msg}")
        return False

def make_api_request(method: str, endpoint: str, data: dict = None):
    """发送HTTP请求到REST API"""
    if not current_token and endpoint not in ["/api/auth/login", "/api/auth/register"]:
        logger.error("请先登录")
        return None
    
    url = f"{API_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if current_token and endpoint not in ["/api/auth/login", "/api/auth/register"]:
        headers["Authorization"] = f"Bearer {current_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            logger.error(f"不支持的HTTP方法: {method}")
            return None
        
        if response.status_code >= 400:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            return None
        
        return response.json()
    except Exception as e:
        logger.error(f"API请求异常: {e}")
        return None

def make_login_request(username: str, password: str):
    """发送登录请求（使用form data）"""
    url = f"{API_URL}/api/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        # 使用form data格式
        response = requests.post(url, data=data)
        if response.status_code >= 400:
            logger.error(f"登录失败: {response.status_code} - {response.text}")
            return None
        return response.json()
    except Exception as e:
        logger.error(f"登录请求异常: {e}")
        return None

def login_user_http(username: str, password: str):
    """通过HTTP登录用户"""
    result = make_login_request(username, password)
    if not result:
        return False
    
    global current_token, current_user
    
    # 获取token
    current_token = result.get("access_token")
    if not current_token:
        return False
    
    # 获取用户信息
    user_result = make_api_request("GET", "/api/users/me")
    if not user_result:
        return False
    
    current_user = {
        "id": user_result.get("id"),
        "username": user_result.get("username"),
        "user_type": user_result.get("user_type"),
        "display_name": user_result.get("display_name")
    }
    
    # 保存会话
    save_session(current_token, current_user)
    return True

def register_user_http(username: str, password: str, email: Optional[str] = None, 
                      user_type: str = "human", display_name: Optional[str] = None):
    """通过HTTP注册用户"""
    data = {
        "username": username,
        "password": password,
        "email": email,
        "user_type": user_type,
        "display_name": display_name or username
    }
    
    result = make_api_request("POST", "/api/auth/register", data)
    if not result:
        return False
    
    global current_token, current_user
    
    # 获取token
    current_token = result.get("access_token")
    if not current_token:
        return False
    
    # 获取用户信息
    user_result = make_api_request("GET", "/api/users/me")
    if not user_result:
        return False
    
    current_user = {
        "id": user_result.get("id"),
        "username": user_result.get("username"),
        "user_type": user_result.get("user_type"),
        "display_name": user_result.get("display_name")
    }
    
    # 保存会话
    save_session(current_token, current_user)
    return True

async def execute_tool(tool_name: str, **kwargs):
    """执行工具（HTTP版本）"""
    if not current_token:
        logger.error("请先登录")
        return None
    
    url = f"{API_URL}/api/tools/{tool_name}/execute"
    headers = {
        "Authorization": f"Bearer {current_token}",
        "Content-Type": "application/json"
    }
    
    try:
        import requests
        response = requests.post(url, headers=headers, json=kwargs)
        
        if response.status_code >= 400:
            logger.error(f"工具执行失败: {response.status_code} - {response.text}")
            return None
        
        result = response.json()
        
        # 转换为WebSocket响应格式以保持兼容
        return {
            "type": "tool_response",
            "data": {
                "tool": tool_name,
                "success": result.get("success", False),
                "output": result.get("output"),
                "error": result.get("error"),
                "metadata": result.get("metadata", {})
            }
        }
    except Exception as e:
        logger.error(f"工具执行异常: {e}")
        return None

@app.command()
def register(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    email: Optional[str] = typer.Option(None),
    user_type: str = typer.Option("human", help="用户类型: human 或 agent"),
    display_name: Optional[str] = typer.Option(None)
):
    """注册新用户"""
    success = asyncio.run(register_user(username, password, email, user_type, display_name))
    if success:
        typer.echo("注册成功！")
    else:
        typer.echo("注册失败")
        raise typer.Exit(code=1)

@app.command()
def login(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True)
):
    """登录用户"""
    success = asyncio.run(login_user(username, password))
    if success:
        typer.echo("登录成功！")
    else:
        typer.echo("登录失败")
        raise typer.Exit(code=1)

@app.command()
def bash(
    command: str = typer.Argument(..., help="要执行的bash命令")
):
    """执行bash命令"""
    if not current_token:
        typer.echo("错误：请先登录")
        raise typer.Exit(code=1)
    
    response = asyncio.run(execute_tool("bash", command=command))
    if response and response.get("type") == "tool_response":
        data = response["data"]
        if data.get("success"):
            typer.echo(data.get("output", ""))
        else:
            typer.echo(f"错误: {data.get('error', '未知错误')}")
    else:
        typer.echo("执行失败")

@app.command()
def webfetch(
    url: str = typer.Argument(..., help="要获取的URL")
):
    """获取网页内容"""
    if not current_token:
        typer.echo("错误：请先登录")
        raise typer.Exit(code=1)
    
    response = asyncio.run(execute_tool("webfetch", url=url))
    if response and response.get("type") == "tool_response":
        data = response["data"]
        if data.get("success"):
            typer.echo(data.get("output", "")[:1000] + ("..." if len(data.get("output", "")) > 1000 else ""))
        else:
            typer.echo(f"错误: {data.get('error', '未知错误')}")
    else:
        typer.echo("执行失败")

@app.command()
def read(
    file_path: str = typer.Argument(..., help="要读取的文件路径")
):
    """读取文件内容"""
    if not current_token:
        typer.echo("错误：请先登录")
        raise typer.Exit(code=1)
    
    response = asyncio.run(execute_tool("read", file_path=file_path))
    if response and response.get("type") == "tool_response":
        data = response["data"]
        if data.get("success"):
            typer.echo(data.get("output", ""))
        else:
            typer.echo(f"错误: {data.get('error', '未知错误')}")
    else:
        typer.echo("执行失败")

@app.command()
def edit(
    file_path: str = typer.Argument(..., help="文件路径"),
    old_string: Optional[str] = typer.Option(None, help="要替换的字符串（replace模式）"),
    new_string: Optional[str] = typer.Option(None, help="替换后的字符串（replace模式）"),
    content: Optional[str] = typer.Option(None, help="整个文件内容（overwrite模式）"),
    mode: str = typer.Option("replace", help="模式: replace 或 overwrite")
):
    """编辑文件"""
    if not current_token:
        typer.echo("错误：请先登录")
        raise typer.Exit(code=1)
    
    params = {"file_path": file_path, "mode": mode}
    if mode == "replace" and old_string and new_string:
        params["old_string"] = old_string
        params["new_string"] = new_string
    elif mode == "overwrite" and content:
        params["content"] = content
    else:
        typer.echo("错误：参数不匹配模式")
        raise typer.Exit(code=1)
    
    response = asyncio.run(execute_tool("edit", **params))
    if response and response.get("type") == "tool_response":
        data = response["data"]
        if data.get("success"):
            typer.echo(data.get("output", ""))
        else:
            typer.echo(f"错误: {data.get('error', '未知错误')}")
    else:
        typer.echo("执行失败")

@app.command()
def add_friend(
    user_id: int = typer.Argument(..., help="要添加的用户ID"),
    relationship_type: str = typer.Option("friend", help="关系类型: friend, colleague, mentor, mentee, other"),
    notes: Optional[str] = typer.Option(None, help="备注")
):
    """添加好友/关系"""
    if not current_token:
        typer.echo("错误：请先登录")
        raise typer.Exit(code=1)
    
    data = {
        "to_user_id": user_id,
        "relationship_type": relationship_type.upper(),
        "notes": notes or ""
    }
    
    result = make_api_request("POST", "/api/relationships", data)
    if result:
        typer.echo(f"关系请求已发送，ID: {result.get('id')}")
    else:
        typer.echo("发送关系请求失败")

@app.command()
def status():
    """显示当前状态"""
    if current_user:
        typer.echo(f"当前用户: {current_user['username']} (ID: {current_user['id']})")
        typer.echo(f"用户类型: {current_user['user_type']}")
        if current_token:
            typer.echo("已认证: 是")
    else:
        typer.echo("未登录")

@app.command()
def logout():
    """退出登录"""
    clear_session()
    typer.echo("已退出登录")

@app.command()
def ai(
    prompt: str = typer.Argument(..., help="AI提示词"),
    provider: str = typer.Option("openai", help="AI提供商: openai, anthropic"),
    api_key: Optional[str] = typer.Option(None, help="API密钥（如未在.env中配置）"),
    model_name: Optional[str] = typer.Option(None, help="模型名称（默认从配置获取）"),
    base_url: Optional[str] = typer.Option(None, help="API基础URL（如使用本地部署）"),
    max_tokens: int = typer.Option(1000, help="最大生成token数"),
    temperature: float = typer.Option(0.7, help="温度参数（0.0-2.0）"),
    mode: str = typer.Option("complete", help="模式: complete（补全）或 chat（聊天）")
):
    """使用AI模型进行推理（动态配置）"""
    if not current_token:
        typer.echo("错误：请先登录")
        raise typer.Exit(code=1)
    
    # 从配置获取API密钥（如果未提供）
    from config import settings
    if not api_key:
        if provider == "openai" and settings.openai_api_key:
            api_key = settings.openai_api_key
        elif provider == "anthropic" and settings.anthropic_api_key:
            api_key = settings.anthropic_api_key
    
    if not api_key:
        typer.echo(f"错误：未提供{provider} API密钥且未在配置中找到")
        typer.echo("请通过--api-key参数提供或在.env文件中设置")
        raise typer.Exit(code=1)
    
    # 设置默认模型名称（如果未提供）
    if model_name is None:
        model_name = settings.default_ai_model or ("gpt-3.5-turbo" if provider == "openai" else "claude-2")
    
    if mode == "complete":
        # 使用补全模式
        params = {
            "prompt": prompt,
            "provider": provider,
            "api_key": api_key,
            "model_name": model_name,
            "base_url": base_url,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = asyncio.run(execute_tool("ai_dynamic", **params))
    elif mode == "chat":
        # 使用聊天模式，需要将提示词转换为消息格式
        messages = [{"role": "user", "content": prompt}]
        params = {
            "messages": messages,
            "provider": provider,
            "api_key": api_key,
            "model_name": model_name,
            "base_url": base_url,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = asyncio.run(execute_tool("ai_dynamic", **params))
    else:
        typer.echo(f"错误：不支持的模式 '{mode}'，使用 'complete' 或 'chat'")
        raise typer.Exit(code=1)
    
    if response and response.get("type") == "tool_response":
        data = response["data"]
        if data.get("success"):
            output = data.get("output", "")
            typer.echo(output)
            
            # 显示元数据（如果存在）
            metadata = data.get("metadata", {})
            if metadata:
                typer.echo("\n--- 元数据 ---")
                for key, value in metadata.items():
                    typer.echo(f"{key}: {value}")
        else:
            typer.echo(f"错误: {data.get('error', '未知错误')}")
    else:
        typer.echo("执行失败")

# 添加--version选项支持
def version_callback(value: bool):
    if value:
        typer.echo(f"Moner v{VERSION}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(None, "--version", callback=version_callback, 
                                 is_eager=True, help="显示版本信息")
):
    """
    Moner - CLI非冷启动AI系统
    
    支持动态AI调用、WebSocket通信和工具执行
    """
    pass

if __name__ == "__main__":
    app()