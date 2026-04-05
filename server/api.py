"""
REST API for Moner system
"""
import logging
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
    create_report, get_report, get_reports_by_user, update_report_status, delete_report
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

# 导入AI API路由器
from server.ai_api import router as ai_router

logging.basicConfig(level=logging.INFO)
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

# 包含AI API路由
app.include_router(ai_router)

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
    try:
        result: ToolResult = await tool_manager.execute_tool(tool_name, **params)
        
        # 记录工具执行（简化）
        # TODO: 保存到数据库
        
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "metadata": result.metadata,
            "executed_by": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
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
    """更新汇报状态（标记为已读等）"""
    report = get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # 检查权限：只能是接收方才能更新状态
    if report.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this report"
        )
    
    # 更新汇报
    if report_update.status:
        updated = update_report_status(db, report_id, report_update.status)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update report"
            )
    
    # TODO: 支持更新标题和内容
    
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
    # TODO: 与现有WebSocket服务器集成
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.api:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )