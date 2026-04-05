"""
AI模块的CRUD操作
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_

from models.ai_models import AIModel, PromptTemplate, Conversation, Message
from ai.schemas import (
    AIModelCreate, AIModelUpdate, 
    PromptTemplateCreate, PromptTemplateUpdate,
    ConversationCreate, ConversationUpdate,
    MessageCreate
)

# AI模型CRUD

def create_ai_model(db: Session, ai_model: AIModelCreate) -> Optional[AIModel]:
    """创建AI模型"""
    db_ai_model = AIModel(
        name=ai_model.name,
        provider=ai_model.provider,
        model_name=ai_model.model_name,
        api_key=ai_model.api_key,
        base_url=ai_model.base_url,
        config=ai_model.config,
        is_default=ai_model.is_default
    )
    
    try:
        db.add(db_ai_model)
        db.commit()
        db.refresh(db_ai_model)
        return db_ai_model
    except IntegrityError:
        db.rollback()
        return None

def get_ai_model(db: Session, ai_model_id: int) -> Optional[AIModel]:
    """获取AI模型"""
    return db.query(AIModel).filter(AIModel.id == ai_model_id).first()

def get_ai_model_by_name(db: Session, name: str) -> Optional[AIModel]:
    """通过名称获取AI模型"""
    return db.query(AIModel).filter(AIModel.name == name).first()

def get_default_ai_model(db: Session) -> Optional[AIModel]:
    """获取默认AI模型"""
    return db.query(AIModel).filter(AIModel.is_default == True).first()

def get_ai_models(db: Session, skip: int = 0, limit: int = 100, 
                  provider: Optional[str] = None, active_only: bool = True) -> List[AIModel]:
    """获取AI模型列表"""
    query = db.query(AIModel)
    
    if provider:
        query = query.filter(AIModel.provider == provider)
    
    if active_only:
        query = query.filter(AIModel.is_active == True)
    
    return query.offset(skip).limit(limit).all()

def update_ai_model(db: Session, ai_model_id: int, ai_model_update: AIModelUpdate) -> Optional[AIModel]:
    """更新AI模型"""
    db_ai_model = db.query(AIModel).filter(AIModel.id == ai_model_id).first()
    if not db_ai_model:
        return None
    
    update_data = ai_model_update.dict(exclude_unset=True)
    
    # 如果设置is_default=True，需要先取消其他模型的默认状态
    if update_data.get("is_default") == True:
        # 取消所有模型的默认状态
        db.query(AIModel).filter(AIModel.is_default == True).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(db_ai_model, field, value)
    
    db.commit()
    db.refresh(db_ai_model)
    return db_ai_model

def delete_ai_model(db: Session, ai_model_id: int) -> bool:
    """删除AI模型"""
    db_ai_model = db.query(AIModel).filter(AIModel.id == ai_model_id).first()
    if not db_ai_model:
        return False
    
    db.delete(db_ai_model)
    db.commit()
    return True

# 提示模板CRUD

def create_prompt_template(db: Session, prompt_template: PromptTemplateCreate, 
                          user_id: Optional[int] = None) -> Optional[PromptTemplate]:
    """创建提示模板"""
    db_template = PromptTemplate(
        name=prompt_template.name,
        description=prompt_template.description,
        template=prompt_template.template,
        variables=prompt_template.variables,
        category=prompt_template.category,
        tags=prompt_template.tags,
        is_system=prompt_template.is_system,
        is_public=prompt_template.is_public,
        created_by=user_id
    )
    
    try:
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    except IntegrityError:
        db.rollback()
        return None

def get_prompt_template(db: Session, template_id: int) -> Optional[PromptTemplate]:
    """获取提示模板"""
    return db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

def get_prompt_template_by_name(db: Session, name: str) -> Optional[PromptTemplate]:
    """通过名称获取提示模板"""
    return db.query(PromptTemplate).filter(PromptTemplate.name == name).first()

def get_prompt_templates(db: Session, skip: int = 0, limit: int = 100,
                        category: Optional[str] = None,
                        is_system: Optional[bool] = None,
                        user_id: Optional[int] = None) -> List[PromptTemplate]:
    """获取提示模板列表"""
    query = db.query(PromptTemplate)
    
    if category:
        query = query.filter(PromptTemplate.category == category)
    
    if is_system is not None:
        query = query.filter(PromptTemplate.is_system == is_system)
    
    # 用户只能看到公开模板或自己创建的模板
    if user_id:
        query = query.filter(
            or_(
                PromptTemplate.is_public == True,
                PromptTemplate.created_by == user_id
            )
        )
    else:
        query = query.filter(PromptTemplate.is_public == True)
    
    return query.order_by(PromptTemplate.usage_count.desc()).offset(skip).limit(limit).all()

def update_prompt_template(db: Session, template_id: int, 
                          template_update: PromptTemplateUpdate) -> Optional[PromptTemplate]:
    """更新提示模板"""
    db_template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not db_template:
        return None
    
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

def increment_template_usage(db: Session, template_id: int) -> bool:
    """增加模板使用次数"""
    db_template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not db_template:
        return False
    
    db_template.usage_count += 1
    db.commit()
    return True

def delete_prompt_template(db: Session, template_id: int) -> bool:
    """删除提示模板"""
    db_template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not db_template:
        return False
    
    db.delete(db_template)
    db.commit()
    return True

# 对话CRUD

def create_conversation(db: Session, user_id: int, 
                       conversation: ConversationCreate) -> Optional[Conversation]:
    """创建对话"""
    db_conversation = Conversation(
        user_id=user_id,
        title=conversation.title,
        ai_model_id=conversation.ai_model_id,
        config=conversation.config
    )
    
    try:
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    except IntegrityError:
        db.rollback()
        return None

def get_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
    """获取对话"""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()

def get_user_conversations(db: Session, user_id: int, 
                          skip: int = 0, limit: int = 100,
                          active_only: bool = True) -> List[Conversation]:
    """获取用户的对话列表"""
    query = db.query(Conversation).filter(Conversation.user_id == user_id)
    
    if active_only:
        query = query.filter(Conversation.is_active == True)
    
    return query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()

def update_conversation(db: Session, conversation_id: int,
                       conversation_update: ConversationUpdate) -> Optional[Conversation]:
    """更新对话"""
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not db_conversation:
        return None
    
    update_data = conversation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_conversation, field, value)
    
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def delete_conversation(db: Session, conversation_id: int) -> bool:
    """删除对话"""
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not db_conversation:
        return False
    
    db.delete(db_conversation)
    db.commit()
    return True

# 消息CRUD

def create_message(db: Session, message: MessageCreate) -> Optional[Message]:
    """创建消息"""
    db_message = Message(
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        tool_calls=message.tool_calls,
        tool_call_id=message.tool_call_id,
        name=message.name,
        message_metadata=message.message_metadata
    )
    
    try:
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # 更新对话的消息计数和更新时间
        conversation = db.query(Conversation).filter(
            Conversation.id == message.conversation_id
        ).first()
        if conversation:
            conversation.message_count += 1
            db.commit()
        
        return db_message
    except IntegrityError:
        db.rollback()
        return None

def get_conversation_messages(db: Session, conversation_id: int,
                             skip: int = 0, limit: int = 100) -> List[Message]:
    """获取对话的消息"""
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).offset(skip).limit(limit).all()

def get_message(db: Session, message_id: int) -> Optional[Message]:
    """获取消息"""
    return db.query(Message).filter(Message.id == message_id).first()

def delete_message(db: Session, message_id: int) -> bool:
    """删除消息"""
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if not db_message:
        return False
    
    # 更新对话的消息计数
    conversation = db.query(Conversation).filter(
        Conversation.id == db_message.conversation_id
    ).first()
    if conversation:
        conversation.message_count = max(0, conversation.message_count - 1)
    
    db.delete(db_message)
    db.commit()
    return True