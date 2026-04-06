#!/usr/bin/env python3
import asyncio
import json
import logging
import typer
from typing import Optional
import websockets

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
current_token = None
current_user = None
websocket_connection = None

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
        return True
    else:
        error_msg = response.get("data", {}).get("error", "未知错误")
        logger.error(f"登录失败: {error_msg}")
        return False

async def execute_tool(tool_name: str, **kwargs):
    """执行工具"""
    if not current_token:
        logger.error("请先登录")
        return None
    
    ws = await connect_to_server()
    if not ws:
        return None
    
    # 发送认证（通过连接管理器，这里简化）
    # 实际应该先登录，然后使用同一个连接
    # 这里我们重新连接并发送工具请求（需要服务器处理认证）
    # 简化：先登录，然后发送工具请求
    
    data = {
        "tool": tool_name,
        "params": kwargs
    }
    
    response = await send_message(ws, "tool_request", data)
    await ws.close()
    
    return response

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
    
    typer.echo("功能待实现")

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
def ai(
    prompt: str = typer.Argument(..., help="AI提示词"),
    provider: str = typer.Option("openai", help="AI提供商: openai, anthropic"),
    api_key: str = typer.Option(..., prompt=True, hide_input=True, help="API密钥"),
    model_name: str = typer.Option("gpt-3.5-turbo", help="模型名称"),
    base_url: Optional[str] = typer.Option(None, help="API基础URL（如使用本地部署）"),
    max_tokens: int = typer.Option(1000, help="最大生成token数"),
    temperature: float = typer.Option(0.7, help="温度参数（0.0-2.0）"),
    mode: str = typer.Option("complete", help="模式: complete（补全）或 chat（聊天）")
):
    """使用AI模型进行推理（动态配置）"""
    if not current_token:
        typer.echo("错误：请先登录")
        raise typer.Exit(code=1)
    
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