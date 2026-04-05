"""
AI模块 - 提供AI工具和API接口
"""

from .schemas import *
from models.ai_models import AIModel, PromptTemplate, Conversation, Message
from .tools import *

__all__ = [
    # schemas
    "AIModelConfig",
    "AIModelCreate",
    "AIModelUpdate",
    "AIModelInDB",
    "PromptTemplate",
    "PromptTemplateCreate",
    "PromptTemplateUpdate",
    "PromptTemplateInDB",
    "Conversation",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationInDB",
    "Message",
    "MessageCreate",
    "MessageInDB",
    "AICompletionRequest",
    "AICompletionResponse",
    "AIChatRequest",
    "AIChatResponse",
    
    # tools
    "AITool",
    "OpenAITool",
    "AnthropicTool",
    
    # models
    "AIModel",
    "PromptTemplate",
    "Conversation",
    "Message",
]