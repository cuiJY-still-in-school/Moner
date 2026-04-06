import asyncio
import json
import logging
from typing import Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol
from sqlalchemy.orm import Session

from config import settings
from database import get_db, init_db
from server.connection_manager import connection_manager
from auth.auth import authenticate_user, create_access_token, get_current_user
from auth.crud import create_user, get_user_by_username
from auth.schemas import UserCreate, UserType, LoginRequest, RegisterRequest
from tools.manager import tool_manager
from models.relationship import Relationship, RelationshipStatus
from models.tool_execution import ToolExecution
from relationships.crud import create_relationship, get_pending_requests_to_user, update_relationship_status
from relationships.schemas import RelationshipCreate
from goals.crud import create_goal, get_goals_by_user
from goals.schemas import GoalCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库
init_db()

class MessageType:
    REGISTER = "register"
    LOGIN = "login"
    AUTH_TOKEN = "auth_token"
    TOOL_REQUEST = "tool_request"
    TOOL_RESPONSE = "tool_response"
    REPORT = "report"
    RELATIONSHIP_REQUEST = "relationship_request"
    RELATIONSHIP_RESPONSE = "relationship_response"
    GOAL_UPDATE = "goal_update"
    GOAL_CREATE = "goal_create"
    ERROR = "error"
    INFO = "info"
    PING = "ping"
    PONG = "pong"

async def handle_message(websocket: WebSocketServerProtocol, connection_id: str, message: dict):
    """处理WebSocket消息"""
    msg_type = message.get("type")
    data = message.get("data", {})
    
    logger.info(f"收到消息: type={msg_type}, data keys={list(data.keys())}")
    
    # 需要数据库会话
    db = next(get_db())
    
    # 检查用户是否已认证（除了注册、登录、认证token和ping）
    user_id = None
    if msg_type not in [MessageType.REGISTER, MessageType.LOGIN, MessageType.AUTH_TOKEN, MessageType.PING]:
        user_id = connection_manager.get_connection_user(connection_id)
        
        # 如果连接未认证，但消息包含token，尝试通过token认证
        if not user_id and msg_type == MessageType.TOOL_REQUEST:
            token = data.get("token")
            if token:
                try:
                    user = get_current_user(token, db)
                    if user:
                        user_id = user.id
                        # 注册连接到用户
                        connection_manager.register_user(connection_id, user_id)
                        logger.info(f"通过token认证用户: {user_id}")
                except Exception as e:
                    logger.error(f"token认证失败: {e}")
        
        if not user_id:
            logger.warning(f"连接 {connection_id} 未认证，消息类型: {msg_type}")
            await send_error(websocket, "未认证，请先登录")
            return
    
    if msg_type == MessageType.REGISTER:
        await handle_register(db, websocket, connection_id, data)
    elif msg_type == MessageType.LOGIN:
        await handle_login(db, websocket, connection_id, data)
    elif msg_type == MessageType.TOOL_REQUEST:
        await handle_tool_request(db, websocket, user_id, data)
    elif msg_type == MessageType.REPORT:
        await handle_report(db, websocket, user_id, data)
    elif msg_type == MessageType.RELATIONSHIP_REQUEST:
        await handle_relationship_request(db, websocket, user_id, data)
    elif msg_type == MessageType.RELATIONSHIP_RESPONSE:
        await handle_relationship_response(db, websocket, user_id, data)
    elif msg_type == MessageType.GOAL_CREATE:
        await handle_goal_create(db, websocket, user_id, data)
    elif msg_type == MessageType.GOAL_UPDATE:
        await handle_goal_update(db, websocket, user_id, data)
    elif msg_type == MessageType.AUTH_TOKEN:
        await handle_auth_token(db, websocket, connection_id, data)
    elif msg_type == MessageType.PING:
        await send_message(websocket, MessageType.PONG, {"message": "pong"})
    else:
        await send_error(websocket, "未知消息类型")

async def handle_register(db: Session, websocket: WebSocketServerProtocol, connection_id: str, data: dict):
    """处理用户注册"""
    try:
        register_data = RegisterRequest(**data)
        
        # 检查用户名是否已存在
        existing_user = get_user_by_username(db, register_data.username)
        if existing_user:
            await send_error(websocket, "用户名已存在")
            return
        
        # 创建用户
        user_create = UserCreate(
            username=register_data.username,
            password=register_data.password,
            email=register_data.email,
            user_type=register_data.user_type,
            display_name=register_data.display_name,
            bio=register_data.bio,
            long_term_goal=register_data.long_term_goal
        )
        
        user = create_user(db, user_create)
        if not user:
            await send_error(websocket, "注册失败")
            return
        
        # 生成token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        # 注册连接到用户
        connection_manager.register_user(connection_id, user.id)
        
        await send_message(websocket, MessageType.LOGIN, {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "user_type": user.user_type.value,
                "display_name": user.display_name
            }
        })
        
    except Exception as e:
        logger.error(f"注册错误: {e}")
        await send_error(websocket, f"注册失败: {str(e)}")

async def handle_login(db: Session, websocket: WebSocketServerProtocol, connection_id: str, data: dict):
    """处理用户登录"""
    try:
        login_data = LoginRequest(**data)
        user = authenticate_user(db, login_data.username, login_data.password)
        
        if not user:
            await send_error(websocket, "用户名或密码错误")
            return
        
        if not user.is_active:
            await send_error(websocket, "用户已被禁用")
            return
        
        # 生成token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        # 注册连接到用户
        connection_manager.register_user(connection_id, user.id)
        
        await send_message(websocket, MessageType.LOGIN, {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "user_type": user.user_type.value,
                "display_name": user.display_name
            }
        })
        
    except Exception as e:
        logger.error(f"登录错误: {e}")
        await send_error(websocket, f"登录失败: {str(e)}")

async def handle_auth_token(db: Session, websocket: WebSocketServerProtocol, connection_id: str, data: dict):
    """使用token认证"""
    try:
        token = data.get("token")
        if not token:
            await send_error(websocket, "缺少token")
            return
        
        user = get_current_user(token, db)
        if not user:
            await send_error(websocket, "无效token")
            return
        
        if not user.is_active:
            await send_error(websocket, "用户已被禁用")
            return
        
        # 注册连接到用户
        connection_manager.register_user(connection_id, user.id)
        
        await send_message(websocket, MessageType.LOGIN, {
            "access_token": token,  # 返回相同token
            "user": {
                "id": user.id,
                "username": user.username,
                "user_type": user.user_type.value,
                "display_name": user.display_name
            }
        })
        
    except Exception as e:
        logger.error(f"token认证错误: {e}")
        await send_error(websocket, f"认证失败: {str(e)}")

async def handle_tool_request(db: Session, websocket: WebSocketServerProtocol, user_id: int, data: dict):
    """处理工具请求"""
    import time
    tool_name = data.get("tool")
    params = data.get("params", {})
    
    logger.info(f"处理工具请求: user_id={user_id}, tool={tool_name}, params={params}")
    
    if not tool_name:
        await send_error(websocket, "缺少工具名称")
        return
    
    # 执行工具
    start_time = time.time()
    result = await tool_manager.execute_tool(tool_name, **params)
    duration_ms = int((time.time() - start_time) * 1000)
    
    logger.info(f"工具执行结果: success={result.success}, error={result.error}")
    
    # 保存工具执行记录到数据库
    try:
        # 构建命令字符串
        command_str = str(params)
        # 对于特定工具，提取关键信息
        if tool_name == "bash" and "command" in params:
            command_str = params["command"]
        elif tool_name == "read" and "file_path" in params:
            command_str = f"read: {params['file_path']}"
        elif tool_name == "webfetch" and "url" in params:
            command_str = f"fetch: {params['url']}"
        elif tool_name == "edit" and "file_path" in params:
            command_str = f"edit: {params['file_path']}"
        
        # 创建工具执行记录
        tool_exec = ToolExecution(
            user_id=user_id,
            tool_name=tool_name,
            command=command_str,
            output=str(result.output) if result.output else None,
            exit_code=0 if result.success else 1,
            duration_ms=duration_ms
        )
        db.add(tool_exec)
        db.commit()
        logger.info(f"工具执行记录已保存: id={tool_exec.id}")
    except Exception as db_error:
        logger.error(f"保存工具执行记录失败: {db_error}", exc_info=True)
        # 不中断主要流程，仅记录错误
    
    await send_message(websocket, MessageType.TOOL_RESPONSE, {
        "tool": tool_name,
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "metadata": result.metadata
    })

async def handle_report(db: Session, websocket: WebSocketServerProtocol, user_id: int, data: dict):
    """处理汇报"""
    to_user_id = data.get("to_user_id")
    title = data.get("title")
    content = data.get("content")
    
    if not to_user_id or not title or not content:
        await send_error(websocket, "缺少必要参数: to_user_id, title, content")
        return
    
    try:
        # 导入相关函数
        from relationships.crud import create_report
        from relationships.schemas import ReportCreate
        
        # 创建汇报
        report_data = ReportCreate(
            to_user_id=to_user_id,
            title=title,
            content=content
        )
        
        report = create_report(db, user_id, report_data)
        if not report:
            await send_error(websocket, "创建汇报失败")
            return
        
        logger.info(f"汇报已创建: id={report.id}, from={user_id}, to={to_user_id}")
        
        # 发送成功响应
        await send_message(websocket, MessageType.INFO, {
            "message": "汇报已发送",
            "report_id": report.id
        })
        
        # 通知接收用户（如果在线）
        from server.connection_manager import connection_manager
        receiver_ws = connection_manager.get_user_connection(to_user_id)
        if receiver_ws:
            await send_message(receiver_ws, MessageType.REPORT, {
                "message": "您收到新的汇报",
                "report_id": report.id,
                "from_user_id": user_id,
                "title": title,
                "content": content[:100] + "..." if len(content) > 100 else content
            })
            
    except Exception as e:
        logger.error(f"处理汇报失败: {e}", exc_info=True)
        await send_error(websocket, f"处理汇报失败: {str(e)}")

async def handle_relationship_request(db: Session, websocket: WebSocketServerProtocol, user_id: int, data: dict):
    """处理关系请求"""
    to_user_id = data.get("to_user_id")
    relationship_type = data.get("relationship_type", "friend")
    notes = data.get("notes", "")
    
    if not to_user_id:
        await send_error(websocket, "缺少目标用户ID")
        return
    
    # 创建关系请求
    relationship_create = RelationshipCreate(
        to_user_id=to_user_id,
        relationship_type=relationship_type,
        notes=notes
    )
    
    relationship = create_relationship(db, user_id, relationship_create)
    
    if not relationship:
        await send_error(websocket, "无法创建关系请求（可能已存在）")
        return
    
    await send_message(websocket, MessageType.INFO, {
        "message": "关系请求已发送",
        "relationship_id": relationship.id
    })
    
    # 通知目标用户（如果在线）
    target_websocket = connection_manager.get_user_connection(to_user_id)
    if target_websocket:
        await send_message(target_websocket, MessageType.RELATIONSHIP_REQUEST, {
            "from_user_id": user_id,
            "relationship_id": relationship.id,
            "relationship_type": relationship_type,
            "notes": notes
        })

async def handle_relationship_response(db: Session, websocket: WebSocketServerProtocol, user_id: int, data: dict):
    """处理关系响应"""
    relationship_id = data.get("relationship_id")
    accepted = data.get("accepted", False)
    
    if not relationship_id:
        await send_error(websocket, "缺少关系ID")
        return
    
    # 获取关系
    relationship = db.query(Relationship).filter(
        Relationship.id == relationship_id,
        Relationship.to_user_id == user_id,
        Relationship.status == RelationshipStatus.PENDING
    ).first()
    
    if not relationship:
        await send_error(websocket, "关系请求未找到或已处理")
        return
    
    # 更新状态
    new_status = RelationshipStatus.ACCEPTED if accepted else RelationshipStatus.REJECTED
    relationship.status = new_status
    db.commit()
    
    await send_message(websocket, MessageType.INFO, {
        "message": f"关系请求已{'接受' if accepted else '拒绝'}"
    })
    
    # 通知发送方
    from_user_websocket = connection_manager.get_user_connection(relationship.from_user_id)
    if from_user_websocket:
        await send_message(from_user_websocket, MessageType.RELATIONSHIP_RESPONSE, {
            "relationship_id": relationship_id,
            "accepted": accepted,
            "by_user_id": user_id
        })

async def handle_goal_create(db: Session, websocket: WebSocketServerProtocol, user_id: int, data: dict):
    """处理目标创建"""
    try:
        goal_create = GoalCreate(**data)
        goal = create_goal(db, user_id, goal_create)
        
        await send_message(websocket, MessageType.GOAL_CREATE, {
            "message": "目标已创建",
            "goal_id": goal.id
        })
    except Exception as e:
        await send_error(websocket, f"创建目标失败: {str(e)}")

async def handle_goal_update(db: Session, websocket: WebSocketServerProtocol, user_id: int, data: dict):
    """处理目标更新"""
    goal_id = data.get("goal_id")
    progress = data.get("progress")
    status = data.get("status")
    title = data.get("title")
    description = data.get("description")
    
    if not goal_id:
        await send_error(websocket, "缺少目标ID")
        return
    
    # 至少提供一个更新字段
    if progress is None and status is None and title is None and description is None:
        await send_error(websocket, "至少提供一个更新字段: progress, status, title, description")
        return
    
    try:
        from goals.crud import get_goal, update_goal, update_goal_progress
        from goals.schemas import GoalUpdate
        
        # 检查目标是否存在且属于用户
        goal = get_goal(db, goal_id)
        if not goal:
            await send_error(websocket, "目标不存在")
            return
        
        if goal.user_id != user_id:
            await send_error(websocket, "无权更新此目标")
            return
        
        # 更新目标
        if progress is not None:
            # 更新进度
            updated = update_goal_progress(db, goal_id, progress)
            if not updated:
                await send_error(websocket, "更新进度失败")
                return
        else:
            # 更新其他字段
            goal_update = GoalUpdate(
                title=title,
                description=description,
                status=status
            )
            updated = update_goal(db, goal_id, goal_update)
            if not updated:
                await send_error(websocket, "更新目标失败")
                return
        
        logger.info(f"目标已更新: id={goal_id}, user={user_id}")
        await send_message(websocket, MessageType.GOAL_UPDATE, {
            "message": "目标已更新",
            "goal_id": goal_id
        })
        
    except Exception as e:
        logger.error(f"更新目标失败: {e}", exc_info=True)
        await send_error(websocket, f"更新目标失败: {str(e)}")

async def send_message(websocket: WebSocketServerProtocol, msg_type: str, data: dict):
    """发送消息给客户端"""
    message = json.dumps({"type": msg_type, "data": data})
    await websocket.send(message)

async def send_error(websocket: WebSocketServerProtocol, error_msg: str):
    """发送错误消息"""
    await send_message(websocket, MessageType.ERROR, {"error": error_msg})

async def connection_handler(websocket):
    """处理WebSocket连接"""
    connection_id = str(id(websocket))
    await connection_manager.connect(websocket, connection_id)
    
    try:
        async for message in websocket:
            logger.info(f"收到原始消息: {message[:100]}...")
            try:
                data = json.loads(message)
                await handle_message(websocket, connection_id, data)
            except json.JSONDecodeError:
                await send_error(websocket, "无效的JSON格式")
            except Exception as e:
                logger.error(f"处理消息错误: {e}")
                await send_error(websocket, f"内部服务器错误: {str(e)}")
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"连接关闭: {connection_id}, 原因: {e}")
    except Exception as e:
        logger.error(f"连接处理错误: {e}")
    finally:
        connection_manager.disconnect(connection_id)

async def main():
    """启动WebSocket服务器"""
    server = await websockets.serve(
        connection_handler,
        settings.ws_host,
        settings.ws_port
    )
    logger.info(f"WebSocket服务器启动于 ws://{settings.ws_host}:{settings.ws_port}")
    
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"服务器错误: {e}")
        import traceback
        traceback.print_exc()