"""
REST API for Moner system
"""
import logging
import time
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta

from config import settings
from database import get_db, init_db
from auth.auth import authenticate_user, create_access_token, get_password_hash, verify_password
from auth.crud import get_user_by_username, create_user, get_user, update_user
from auth.schemas import UserCreate, UserInDB, UserUpdate, LoginRequest, Token
from tools.manager import tool_manager
from tools.base import ToolResult
from relationships.crud import (
    create_relationship, get_relationship, get_relationships_by_user, 
    update_relationship_status, delete_relationship, get_pending_requests_to_user,
    create_report, get_report, get_reports_by_user, update_report_status, update_report, delete_report
)
from relationships.schemas import (
    RelationshipCreate, RelationshipInDB, RelationshipUpdate, 
    RelationshipStatus, ReportCreate, ReportInDB, ReportUpdate
)
from goals.crud import (
    create_goal, get_goal, get_goals_by_user, update_goal, 
    delete_goal, update_goal_progress
)
from goals.schemas import GoalCreate, GoalInDB, GoalUpdate, GoalStatus
from models.user import User
from models.tool_execution import ToolExecution

# 导入AI API路由器（可选）
try:
    from server.ai_api import router as ai_router
    ai_router_available = True
except ImportError as e:
    logger.warning(f"AI API不可用: {e}")
    # 创建空路由器作为占位符
    from fastapi import APIRouter
    ai_router = APIRouter()
    ai_router_available = False

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化数据库
init_db()

# 创建FastAPI应用
app = FastAPI(
    title="Moner API",
    description="REST API for Moner - CLI Non-Cold-Start AI System",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 依赖项
async def get_current_user_api(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户（API版本）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# 包含AI API路由（如果可用）
if ai_router_available:
    app.include_router(ai_router)
else:
    logger.info("AI API路由未启用")

# API路由
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# 认证相关路由
@app.post("/api/auth/register", response_model=Token)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """注册新用户"""
    # 检查用户名是否已存在
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 创建用户
    user = create_user(db, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # 生成访问令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(access_token=access_token, token_type="bearer")

@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成访问令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(access_token=access_token, token_type="bearer")

@app.get("/api/auth/me", response_model=UserInDB)
async def get_me(
    current_user: User = Depends(get_current_user_api)
):
    """获取当前用户信息"""
    return current_user

# 用户管理路由
@app.get("/api/users/{user_id}", response_model=UserInDB)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取用户信息（需要权限检查）"""
    # 简单实现：只能获取自己的信息
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@app.put("/api/users/{user_id}", response_model=UserInDB)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# 工具执行路由
@app.post("/api/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    params: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_api)
):
    """执行工具"""
    # 检查工具是否存在
    tool = tool_manager.get_tool(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )
    
    # 执行工具
    start_time = time.time()
    try:
        logger.info(f"执行工具: {tool_name}, 参数: {params}, 用户: {current_user.id}")
        result: ToolResult = await tool_manager.execute_tool(tool_name, **params)
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
                user_id=current_user.id,
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
        
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "metadata": result.metadata,
            "executed_by": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"工具执行异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )

@app.get("/api/tools")
async def list_tools():
    """列出所有可用工具"""
    tools = tool_manager.list_tools()
    return {"tools": tools}

# 关系管理路由
@app.post("/api/relationships", response_model=RelationshipInDB)
async def create_new_relationship(
    relationship: RelationshipCreate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """创建关系请求"""
    # 不能向自己发送请求
    if current_user.id == relationship.to_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create relationship with yourself"
        )
    
    result = create_relationship(db, current_user.id, relationship)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relationship request already exists or invalid"
        )
    
    return result

@app.get("/api/relationships", response_model=List[RelationshipInDB])
async def get_my_relationships(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取当前用户的关系"""
    relationships = get_relationships_by_user(db, current_user.id, status)
    return relationships

@app.get("/api/relationships/pending", response_model=List[RelationshipInDB])
async def get_pending_relationship_requests(
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取待处理的关系请求"""
    requests = get_pending_requests_to_user(db, current_user.id)
    return requests

@app.put("/api/relationships/{relationship_id}")
async def update_relationship(
    relationship_id: int,
    status_update: RelationshipUpdate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """更新关系状态（接受/拒绝）"""
    relationship = get_relationship(db, relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    # 检查权限：只能是接收方才能更新状态
    if relationship.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this relationship"
        )
    
    if status_update.status:
        updated = update_relationship_status(db, relationship_id, status_update.status)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update relationship"
            )
        
        return {"message": f"Relationship {status_update.status.value}"}
    
    return {"message": "No update performed"}

# 汇报管理路由
@app.post("/api/reports", response_model=ReportInDB)
async def create_new_report(
    report: ReportCreate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """创建汇报"""
    result = create_report(db, current_user.id, report)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create report"
        )
    
    return result

@app.get("/api/reports", response_model=List[ReportInDB])
async def get_my_reports(
    direction: str = "received",  # received 或 sent
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取当前用户的汇报"""
    reports = get_reports_by_user(db, current_user.id, direction)
    return reports

@app.put("/api/reports/{report_id}")
async def update_report(
    report_id: int,
    report_update: ReportUpdate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """更新汇报（发送者可更新标题和内容，接收者可更新状态）"""
    report = get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # 检查权限：发送者或接收者
    is_sender = report.from_user_id == current_user.id
    is_receiver = report.to_user_id == current_user.id
    
    if not (is_sender or is_receiver):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this report"
        )
    
    # 验证字段权限
    if not is_sender:
        # 接收者只能更新状态
        if report_update.title is not None or report_update.content is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only sender can update title and content"
            )
    
    # 更新汇报
    updated = update_report(db, report_id, report_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update report"
        )
    
    return {"message": "Report updated"}

# 目标管理路由
@app.post("/api/goals", response_model=GoalInDB)
async def create_new_goal(
    goal: GoalCreate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """创建新目标"""
    result = create_goal(db, current_user.id, goal)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create goal"
        )
    
    return result

@app.get("/api/goals", response_model=List[GoalInDB])
async def get_my_goals(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取当前用户的目标"""
    goals = get_goals_by_user(db, current_user.id, status)
    return goals

@app.get("/api/goals/{goal_id}", response_model=GoalInDB)
async def get_goal_by_id(
    goal_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取目标详情"""
    goal = get_goal(db, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # 检查权限：只能访问自己的目标
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this goal"
        )
    
    return goal

@app.put("/api/goals/{goal_id}", response_model=GoalInDB)
async def update_goal_by_id(
    goal_id: int,
    goal_update: GoalUpdate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """更新目标"""
    goal = get_goal(db, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # 检查权限：只能更新自己的目标
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this goal"
        )
    
    updated = update_goal(db, goal_id, goal_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update goal"
        )
    
    return updated

@app.put("/api/goals/{goal_id}/progress")
async def update_goal_progress_api(
    goal_id: int,
    progress: float,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """更新目标进度"""
    goal = get_goal(db, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # 检查权限：只能更新自己的目标
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this goal"
        )
    
    updated = update_goal_progress(db, goal_id, progress)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update goal progress"
        )
    
    return updated

# WebSocket端点（与现有系统集成）
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点（转发到现有WebSocket服务器）"""
    await websocket.accept()
    
    # 现有WebSocket服务器地址
    ws_url = f"ws://{settings.ws_host}:{settings.ws_port}"
    
    try:
        # 连接到现有WebSocket服务器
        import websockets
        async with websockets.connect(ws_url) as remote_ws:
            logger.info(f"WebSocket代理已连接: {ws_url}")
            
            # 创建双向转发任务
            async def forward_to_remote():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await remote_ws.send(data)
                except Exception as e:
                    logger.info(f"客户端连接关闭: {e}")
                    return
            
            async def forward_to_client():
                try:
                    while True:
                        data = await remote_ws.recv()
                        await websocket.send_text(data)
                except Exception as e:
                    logger.info(f"远程服务器连接关闭: {e}")
                    return
            
            # 运行两个转发任务
            import asyncio
            await asyncio.gather(
                forward_to_remote(),
                forward_to_client(),
                return_exceptions=True
            )
            
    except Exception as e:
        logger.error(f"WebSocket代理失败: {e}")
        await websocket.send_text(f"Error connecting to WebSocket server: {str(e)}")
        await websocket.send_text(f"Please connect directly to: {ws_url}")
    finally:
        logger.info("WebSocket代理连接关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.api:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )