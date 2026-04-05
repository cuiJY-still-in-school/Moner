from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class RelationshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"

class RelationshipType(str, Enum):
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    MENTOR = "mentor"
    MENTEE = "mentee"
    OTHER = "other"

class RelationshipBase(BaseModel):
    to_user_id: int
    relationship_type: RelationshipType = RelationshipType.FRIEND
    notes: Optional[str] = None

class RelationshipCreate(RelationshipBase):
    pass

class RelationshipUpdate(BaseModel):
    status: Optional[RelationshipStatus] = None
    notes: Optional[str] = None

class RelationshipInDB(RelationshipBase):
    id: int
    from_user_id: int
    status: RelationshipStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    to_user_id: int
    title: str
    content: str

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class ReportInDB(ReportBase):
    id: int
    from_user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True