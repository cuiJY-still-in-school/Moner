from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import StrEnum

class UserType(StrEnum):
    HUMAN = "HUMAN"
    AGENT = "AGENT"

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    user_type: UserType = UserType.HUMAN
    display_name: Optional[str] = None
    bio: Optional[str] = None
    long_term_goal: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    long_term_goal: Optional[str] = None
    email: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(UserCreate):
    pass