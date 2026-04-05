from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base

class ToolExecution(Base):
    __tablename__ = "tool_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tool_name = Column(String(50), nullable=False)  # bash, webfetch, read, edit
    command = Column(Text, nullable=False)  # 执行的命令或请求
    output = Column(Text)  # 输出结果
    exit_code = Column(Integer, nullable=True)  # bash退出码
    duration_ms = Column(Integer)  # 执行时间毫秒
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="tool_executions")
    
    def __repr__(self):
        return f"<ToolExecution(user={self.user_id}, tool={self.tool_name}, exit={self.exit_code})>"