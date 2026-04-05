"""
AI API端点
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import openai
from openai import AsyncOpenAI

from database import get_db
from auth.auth import get_current_user
from models.user import User
from fastapi.security import OAuth2PasswordBearer
from ai.crud import (
    create_ai_model, get_ai_model, get_ai_model_by_name, get_ai_models, 
    update_ai_model, delete_ai_model, get_default_ai_model, 
    create_prompt_template, get_prompt_template, get_prompt_templates, 
    update_prompt_template, delete_prompt_template, increment_template_usage, 
    create_conversation, get_conversation, get_user_conversations, 
    update_conversation, delete_conversation, create_message, 
    get_conversation_messages, delete_message
)
from ai.schemas import (
    AIModelCreate, AIModelUpdate, AIModelInDB,
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateInDB,
    ConversationCreate, ConversationUpdate, ConversationInDB,
    MessageCreate, MessageInDB,
    AICompletionRequest, AICompletionResponse,
    AIChatRequest, AIChatResponse,
    DirectAICompletionRequest, DirectAIChatRequest
)
from ai.tools import OpenAITool, AnthropicTool
from config import settings

logger = logging.getLogger(__name__)

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 依赖项
async def get_current_user_api(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户（API版本）"""
    user = get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

router = APIRouter(prefix="/api/ai", tags=["AI"])

# AI模型管理
@router.post("/models", response_model=AIModelInDB)
async def create_ai_model_endpoint(
    ai_model: AIModelCreate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """创建AI模型配置"""
    # 检查权限：只有管理员可以创建AI模型
    # 简化：所有用户都可以创建
    result = create_ai_model(db, ai_model)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create AI model"
        )
    
    return result

@router.get("/models", response_model=List[AIModelInDB])
async def list_ai_models(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取AI模型列表"""
    models = get_ai_models(db, provider=provider)
    return models

@router.get("/models/{model_id}", response_model=AIModelInDB)
async def get_ai_model_endpoint(
    model_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取AI模型详情"""
    model = get_ai_model(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model not found"
        )
    
    # 隐藏API密钥
    if model.api_key:
        model.api_key = "***"  # 不返回真实的API密钥
    
    return model

@router.put("/models/{model_id}", response_model=AIModelInDB)
async def update_ai_model_endpoint(
    model_id: int,
    model_update: AIModelUpdate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """更新AI模型"""
    model = update_ai_model(db, model_id, model_update)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model not found"
        )
    
    # 隐藏API密钥
    if model.api_key:
        model.api_key = "***"
    
    return model

@router.delete("/models/{model_id}")
async def delete_ai_model_endpoint(
    model_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """删除AI模型"""
    success = delete_ai_model(db, model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model not found"
        )
    
    return {"message": "AI model deleted"}

# 提示模板管理
@router.post("/prompts", response_model=PromptTemplateInDB)
async def create_prompt_template_endpoint(
    prompt_template: PromptTemplateCreate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """创建提示模板"""
    result = create_prompt_template(db, prompt_template, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create prompt template"
        )
    
    return result

@router.get("/prompts", response_model=List[PromptTemplateInDB])
async def list_prompt_templates(
    category: Optional[str] = None,
    is_system: Optional[bool] = None,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取提示模板列表"""
    templates = get_prompt_templates(
        db, 
        category=category, 
        is_system=is_system,
        user_id=current_user.id
    )
    return templates

@router.get("/prompts/{template_id}", response_model=PromptTemplateInDB)
async def get_prompt_template_endpoint(
    template_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取提示模板详情"""
    template = get_prompt_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # 检查权限：只能访问公开模板或自己创建的模板
    if not template.is_public and template.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this template"
        )
    
    # 增加使用计数
    increment_template_usage(db, template_id)
    
    return template

@router.put("/prompts/{template_id}", response_model=PromptTemplateInDB)
async def update_prompt_template_endpoint(
    template_id: int,
    template_update: PromptTemplateUpdate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """更新提示模板"""
    template = get_prompt_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # 检查权限：只能更新自己创建的模板
    if template.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this template"
        )
    
    updated = update_prompt_template(db, template_id, template_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update prompt template"
        )
    
    return updated

@router.delete("/prompts/{template_id}")
async def delete_prompt_template_endpoint(
    template_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """删除提示模板"""
    template = get_prompt_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # 检查权限：只能删除自己创建的模板
    if template.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this template"
        )
    
    success = delete_prompt_template(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete prompt template"
        )
    
    return {"message": "Prompt template deleted"}

# 对话管理
@router.post("/conversations", response_model=ConversationInDB)
async def create_conversation_endpoint(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """创建对话"""
    result = create_conversation(db, current_user.id, conversation)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create conversation"
        )
    
    return result

@router.get("/conversations", response_model=List[ConversationInDB])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取用户的对话列表"""
    conversations = get_user_conversations(db, current_user.id, skip=skip, limit=limit)
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationInDB)
async def get_conversation_endpoint(
    conversation_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取对话详情"""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # 检查权限：只能访问自己的对话
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation"
        )
    
    return conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """删除对话"""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # 检查权限：只能删除自己的对话
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this conversation"
        )
    
    success = delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete conversation"
        )
    
    return {"message": "Conversation deleted"}

# 消息管理
@router.post("/messages", response_model=MessageInDB)
async def create_message_endpoint(
    message: MessageCreate,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """创建消息"""
    # 检查对话是否存在且属于当前用户
    conversation = get_conversation(db, message.conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add message to this conversation"
        )
    
    result = create_message(db, message)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create message"
        )
    
    return result

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageInDB])
async def list_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """获取对话的消息"""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # 检查权限：只能访问自己的对话
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation"
        )
    
    messages = get_conversation_messages(db, conversation_id, skip=skip, limit=limit)
    return messages

# AI推理端点
@router.post("/completions", response_model=AICompletionResponse)
async def create_completion(
    request: AICompletionRequest,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """AI补全"""
    # 获取AI模型配置
    ai_model = None
    if request.model_id:
        ai_model = get_ai_model(db, request.model_id)
    elif request.model_name:
        ai_model = get_ai_model_by_name(db, request.model_name)
    else:
        # 使用默认模型
        ai_model = get_default_ai_model(db)
    
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AI model configured"
        )
    
    # 根据提供商调用相应的API
    try:
        if ai_model.provider == "openai":
            client = AsyncOpenAI(api_key=ai_model.api_key, base_url=ai_model.base_url)
            
            response = await client.completions.create(
                model=ai_model.model_name,
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop,
                stream=request.stream
            )
            
            if request.stream:
                # 处理流式响应
                async def stream_generator():
                    async for chunk in response:
                        yield chunk
                
                return stream_generator()
            else:
                completion = response.choices[0].text
                
                return AICompletionResponse(
                    completion=completion,
                    model=response.model,
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    finish_reason=response.choices[0].finish_reason
                )
        
        elif ai_model.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=ai_model.api_key)
            
            response = client.completions.create(
                model=ai_model.model_name,
                prompt=f"{anthropic.HUMAN_PROMPT} {request.prompt} {anthropic.AI_PROMPT}",
                max_tokens_to_sample=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop_sequences=request.stop
            )
            
            return AICompletionResponse(
                completion=response.completion,
                model=response.model,
                tokens_used=0,  # Anthropic不返回token使用量
                finish_reason=response.stop_reason
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider: {ai_model.provider}"
            )
    
    except Exception as e:
        logger.error(f"AI completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI completion failed: {str(e)}"
        )

@router.post("/chat/completions", response_model=AIChatResponse)
async def create_chat_completion(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """AI聊天补全"""
    # 获取AI模型配置
    ai_model = None
    if request.model_id:
        ai_model = get_ai_model(db, request.model_id)
    elif request.model_name:
        ai_model = get_ai_model_by_name(db, request.model_name)
    else:
        # 使用默认模型
        ai_model = get_default_ai_model(db)
    
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AI model configured"
        )
    
    # 根据提供商调用相应的API
    try:
        if ai_model.provider == "openai":
            client = AsyncOpenAI(api_key=ai_model.api_key, base_url=ai_model.base_url)
            
            response = await client.chat.completions.create(
                model=ai_model.model_name,
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=request.stream,
                tools=request.tools,
                tool_choice=request.tool_choice
            )
            
            if request.stream:
                # 处理流式响应
                async def stream_generator():
                    async for chunk in response:
                        yield chunk
                
                return stream_generator()
            else:
                message = response.choices[0].message
                
                result_message = {
                    "role": message.role,
                    "content": message.content,
                    "tool_calls": message.tool_calls
                }
                
                return AIChatResponse(
                    message=result_message,
                    model=response.model,
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    finish_reason=response.choices[0].finish_reason
                )
        
        elif ai_model.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=ai_model.api_key)
            
            # 转换消息格式为Anthropic格式
            prompt = ""
            for msg in request.messages:
                if msg["role"] == "user":
                    prompt += f"{anthropic.HUMAN_PROMPT} {msg['content']}"
                elif msg["role"] == "assistant":
                    prompt += f"{anthropic.AI_PROMPT} {msg['content']}"
                elif msg["role"] == "system":
                    prompt += f"{anthropic.HUMAN_PROMPT} System: {msg['content']}"
            
            prompt += f"{anthropic.AI_PROMPT}"
            
            response = client.completions.create(
                model=ai_model.model_name,
                prompt=prompt,
                max_tokens_to_sample=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p
            )
            
            result_message = {
                "role": "assistant",
                "content": response.completion
            }
            
            return AIChatResponse(
                message=result_message,
                model=response.model,
                tokens_used=0,
                finish_reason=response.stop_reason
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider: {ai_model.provider}"
            )
    
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI chat failed: {str(e)}"
        )

# 直接AI调用（无需预配置模型）
@router.post("/direct/completions", response_model=AICompletionResponse)
async def direct_completion(
    request: DirectAICompletionRequest,
    current_user: User = Depends(get_current_user_api)
):
    """直接AI补全（无需预配置模型）"""
    try:
        if request.provider.lower() == "openai":
            client = AsyncOpenAI(api_key=request.api_key, base_url=request.base_url)
            
            response = await client.completions.create(
                model=request.model_name,
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop,
                stream=request.stream
            )
            
            if request.stream:
                # 处理流式响应
                async def stream_generator():
                    async for chunk in response:
                        yield chunk
                
                return stream_generator()
            else:
                completion = response.choices[0].text
                
                return AICompletionResponse(
                    completion=completion,
                    model=response.model,
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    finish_reason=response.choices[0].finish_reason
                )
        
        elif request.provider.lower() == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=request.api_key)
            
            response = client.completions.create(
                model=request.model_name,
                prompt=f"{anthropic.HUMAN_PROMPT} {request.prompt} {anthropic.AI_PROMPT}",
                max_tokens_to_sample=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop_sequences=request.stop
            )
            
            return AICompletionResponse(
                completion=response.completion,
                model=response.model,
                tokens_used=0,  # Anthropic不返回token使用量
                finish_reason=response.stop_reason
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider: {request.provider}"
            )
    
    except Exception as e:
        logger.error(f"Direct AI completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Direct AI completion failed: {str(e)}"
        )

@router.post("/direct/chat/completions", response_model=AIChatResponse)
async def direct_chat_completion(
    request: DirectAIChatRequest,
    current_user: User = Depends(get_current_user_api)
):
    """直接AI聊天补全（无需预配置模型）"""
    try:
        if request.provider.lower() == "openai":
            client = AsyncOpenAI(api_key=request.api_key, base_url=request.base_url)
            
            response = await client.chat.completions.create(
                model=request.model_name,
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=request.stream,
                tools=request.tools,
                tool_choice=request.tool_choice
            )
            
            if request.stream:
                # 处理流式响应
                async def stream_generator():
                    async for chunk in response:
                        yield chunk
                
                return stream_generator()
            else:
                message = response.choices[0].message
                
                result_message = {
                    "role": message.role,
                    "content": message.content,
                    "tool_calls": message.tool_calls
                }
                
                return AIChatResponse(
                    message=result_message,
                    model=response.model,
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    finish_reason=response.choices[0].finish_reason
                )
        
        elif request.provider.lower() == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=request.api_key)
            
            # 转换消息格式为Anthropic格式
            prompt = ""
            for msg in request.messages:
                if msg["role"] == "user":
                    prompt += f"{anthropic.HUMAN_PROMPT} {msg['content']}"
                elif msg["role"] == "assistant":
                    prompt += f"{anthropic.AI_PROMPT} {msg['content']}"
                elif msg["role"] == "system":
                    prompt += f"{anthropic.HUMAN_PROMPT} System: {msg['content']}"
            
            prompt += f"{anthropic.AI_PROMPT}"
            
            response = client.completions.create(
                model=request.model_name,
                prompt=prompt,
                max_tokens_to_sample=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p
            )
            
            result_message = {
                "role": "assistant",
                "content": response.completion
            }
            
            return AIChatResponse(
                message=result_message,
                model=response.model,
                tokens_used=0,
                finish_reason=response.stop_reason
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported AI provider: {request.provider}"
            )
    
    except Exception as e:
        logger.error(f"Direct AI chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Direct AI chat failed: {str(e)}"
        )

# 工具调用
@router.post("/tools/execute")
async def execute_ai_tool(
    tool_name: str,
    params: dict,
    current_user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    """执行AI工具"""
    # 这里可以集成到工具系统
    # 暂时返回占位符
    return {
        "message": "AI tool execution endpoint",
        "tool": tool_name,
        "params": params,
        "user_id": current_user.id
    }