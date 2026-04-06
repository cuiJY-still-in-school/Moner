#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from auth.auth import get_password_hash
from models.user import User, UserType
from models.base import Base

# 数据库连接
DATABASE_URL = "sqlite:///./moner.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建表（如果不存在）
Base.metadata.create_all(bind=engine)

# 创建会话
db = Session(engine)

def create_user_if_not_exists(username, password, user_type, display_name=None, email=None):
    """创建用户（如果不存在）"""
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"用户 '{username}' 已存在，ID: {existing.id}")
        return existing
    
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        user_type=user_type,
        display_name=display_name or username,
        bio=f"{user_type.value} 用户",
        long_term_goal="与系统交互"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"创建用户 '{username}' 成功，ID: {user.id}, 类型: {user_type.value}")
    return user

try:
    # 创建人类用户
    human_user = create_user_if_not_exists(
        username="jayson",
        password="test123",
        user_type=UserType.HUMAN,
        display_name="Jayson",
        email="jayson@example.com"
    )
    
    # 创建DeepSeek AI代理用户
    deepseek_user = create_user_if_not_exists(
        username="deepseek",
        password="agent123",
        user_type=UserType.AGENT,
        display_name="DeepSeek AI",
        email="deepseek@example.com"
    )
    
    print("\n用户创建完成:")
    print(f"  人类用户: {human_user.username} (ID: {human_user.id})")
    print(f"  DeepSeek代理用户: {deepseek_user.username} (ID: {deepseek_user.id})")
    print("\n现在可以通过CLI登录:")
    print(f"  python -m cli.main login --username jayson --password test123")
    print("\n添加好友:")
    print(f"  python -m cli.main add_friend {deepseek_user.id}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()