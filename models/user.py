from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base

class UserType(enum.Enum):
    HUMAN = "HUMAN"
    AGENT = "AGENT"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.HUMAN)
    display_name = Column(String(100))
    bio = Column(Text)
    long_term_goal = Column(Text, nullable=True)  # 长期目标配置
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    sent_relationships = relationship(
        "Relationship",
        foreign_keys="[Relationship.from_user_id]",
        back_populates="from_user"
    )
    received_relationships = relationship(
        "Relationship",
        foreign_keys="[Relationship.to_user_id]",
        back_populates="to_user"
    )
    sent_reports = relationship(
        "Report",
        foreign_keys="[Report.from_user_id]",
        back_populates="from_user"
    )
    received_reports = relationship(
        "Report",
        foreign_keys="[Report.to_user_id]",
        back_populates="to_user"
    )
    goals = relationship("Goal", back_populates="user")
    tool_executions = relationship("ToolExecution", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, type={self.user_type})>"