from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: GoalStatus = GoalStatus.NOT_STARTED
    progress: float = 0.0
    priority: int = 1
    deadline: Optional[datetime] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    progress: Optional[float] = None
    priority: Optional[int] = None
    deadline: Optional[datetime] = None

class GoalInDB(GoalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True