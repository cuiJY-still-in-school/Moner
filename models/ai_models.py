"""
AI相关数据库模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base

class AIModel(Base):
    """AI模型配置"""
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    provider = Column(String(50), nullable=False)  # openai, anthropic, local, etc.
    model_name = Column(String(100), nullable=False)  # gpt-4, claude-3, etc.
    api_key = Column(String(500), nullable=True)  # 加密存储
    base_url = Column(String(500), nullable=True)  # 自定义API端点
    config = Column(JSON, nullable=True)  # 额外配置
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AIModel(id={self.id}, name={self.name}, provider={self.provider})>"

class PromptTemplate(Base):
    """提示模板"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    template = Column(Text, nullable=False)  # 提示模板内容
    variables = Column(JSON, nullable=True)  # 模板变量定义
    category = Column(String(50), nullable=True)  # 分类
    tags = Column(JSON, nullable=True)  # 标签列表
    is_system = Column(Boolean, default=False)  # 是否是系统提示
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=True)  # 是否公开
    usage_count = Column(Integer, default=0)  # 使用次数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name={self.name})>"

class Conversation(Base):
    """对话会话"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    ai_model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=True)
    config = Column(JSON, nullable=True)  # 对话配置
    token_count = Column(Integer, default=0)  # 总token数
    message_count = Column(Integer, default=0)  # 消息数量
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", backref="conversations")
    ai_model = relationship("AIModel")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title})>"

class Message(Base):
    """对话消息"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)  # 工具调用
    tool_call_id = Column(String(100), nullable=True)  # 工具调用ID
    name = Column(String(100), nullable=True)  # 工具名称
    token_count = Column(Integer, default=0)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation={self.conversation_id})>"