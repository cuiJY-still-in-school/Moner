"""
AI模块的Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AIProvider(str, Enum):
    """AI提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    OTHER = "other"

class AIModelConfig(BaseModel):
    """AI模型配置基类"""
    name: str
    provider: AIProvider
    model_name: str = Field(..., description="模型名称，如gpt-4, claude-3等")
    base_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_default: bool = False

class AIModelCreate(AIModelConfig):
    """创建AI模型"""
    api_key: Optional[str] = None

class AIModelUpdate(BaseModel):
    """更新AI模型"""
    name: Optional[str] = None
    provider: Optional[AIProvider] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class AIModelInDB(AIModelConfig):
    """数据库中的AI模型"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PromptTemplateBase(BaseModel):
    """提示模板基类"""
    name: str
    description: Optional[str] = None
    template: str
    variables: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_system: bool = False
    is_public: bool = True

class PromptTemplateCreate(PromptTemplateBase):
    """创建提示模板"""
    pass

class PromptTemplateUpdate(BaseModel):
    """更新提示模板"""
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_system: Optional[bool] = None
    is_public: Optional[bool] = None

class PromptTemplateInDB(PromptTemplateBase):
    """数据库中的提示模板"""
    id: int
    created_by: Optional[int] = None
    usage_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    """对话基类"""
    title: Optional[str] = None
    ai_model_id: Optional[int] = None
    config: Optional[Dict[str, Any]] = None

class ConversationCreate(ConversationBase):
    """创建对话"""
    pass

class ConversationUpdate(BaseModel):
    """更新对话"""
    title: Optional[str] = None
    ai_model_id: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ConversationInDB(ConversationBase):
    """数据库中的对话"""
    id: int
    user_id: int
    token_count: int = 0
    message_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    """消息基类"""
    role: str = Field(..., description="消息角色: user, assistant, system, tool")
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    """创建消息"""
    conversation_id: int

class MessageInDB(MessageBase):
    """数据库中的消息"""
    id: int
    conversation_id: int
    token_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

# AI请求和响应
class AICompletionRequest(BaseModel):
    """AI补全请求"""
    prompt: str
    model_id: Optional[int] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stop: Optional[List[str]] = None
    stream: bool = False

class AICompletionResponse(BaseModel):
    """AI补全响应"""
    completion: str
    model: str
    tokens_used: int
    finish_reason: Optional[str] = None

class AIChatRequest(BaseModel):
    """AI聊天请求"""
    messages: List[Dict[str, str]]  # [{role: "user", content: "hello"}]
    model_id: Optional[int] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None

class AIChatResponse(BaseModel):
    """AI聊天响应"""
    message: Dict[str, Any]  # {role: "assistant", content: "hello"}
    model: str
    tokens_used: int
    finish_reason: Optional[str] = None

# 直接调用AI请求模型
class DirectAICompletionRequest(BaseModel):
    """直接AI补全请求（无需预配置模型）"""
    prompt: str
    provider: str = Field(..., description="AI提供商: openai, anthropic")
    api_key: str = Field(..., description="API密钥")
    model_name: str = Field(..., description="模型名称")
    base_url: Optional[str] = Field(None, description="API基础URL")
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stop: Optional[List[str]] = None
    stream: bool = False

class DirectAIChatRequest(BaseModel):
    """直接AI聊天请求（无需预配置模型）"""
    messages: List[Dict[str, str]]  # [{role: "user", content: "hello"}]
    provider: str = Field(..., description="AI提供商: openai, anthropic")
    api_key: str = Field(..., description="API密钥")
    model_name: str = Field(..., description="模型名称")
    base_url: Optional[str] = Field(None, description="API基础URL")
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None