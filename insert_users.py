#!/usr/bin/env python3
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth.auth import get_password_hash

# 连接到SQLite数据库
conn = sqlite3.connect('moner.db')
cursor = conn.cursor()

# 检查users表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
if not cursor.fetchone():
    print("错误: users表不存在")
    sys.exit(1)

# 生成密码哈希
human_password_hash = get_password_hash("test123")
deepseek_password_hash = get_password_hash("agent123")

# 插入人类用户
cursor.execute("""
    INSERT OR IGNORE INTO users 
    (username, email, hashed_password, user_type, display_name, bio, long_term_goal, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
""", (
    "jayson",
    "jayson@example.com",
    human_password_hash,
    "human",  # 枚举值
    "Jayson",
    "人类用户",
    "使用Moner系统",
    True
))

# 插入DeepSeek代理用户
cursor.execute("""
    INSERT OR IGNORE INTO users 
    (username, email, hashed_password, user_type, display_name, bio, long_term_goal, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
""", (
    "deepseek",
    "deepseek@example.com",
    deepseek_password_hash,
    "agent",  # 枚举值
    "DeepSeek AI",
    "AI代理用户",
    "提供AI助手服务",
    True
))

conn.commit()

# 获取插入的用户ID
cursor.execute("SELECT id, username, user_type FROM users WHERE username IN ('jayson', 'deepseek')")
users = cursor.fetchall()

print("用户创建成功:")
for user_id, username, user_type in users:
    print(f"  ID: {user_id}, 用户名: {username}, 类型: {user_type}")

cursor.close()
conn.close()

print("\n现在可以通过CLI登录:")
print("  python -m cli.main login --username jayson --password test123")
print("\n添加好友:")
print("  python -m cli.main add_friend <deepseek用户ID>")