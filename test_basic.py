#!/usr/bin/env python3
"""基本功能测试"""

import sys
import asyncio

def test_imports():
    """测试导入"""
    print("测试导入...")
    try:
        from config import settings
        print("✓ 配置导入成功")
        
        from database import init_db
        print("✓ 数据库导入成功")
        
        from tools.manager import tool_manager
        print("✓ 工具管理器导入成功")
        
        from auth.auth import verify_password, get_password_hash
        print("✓ 认证模块导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

async def test_tools():
    """测试工具"""
    print("\n测试工具...")
    from tools.manager import tool_manager
    
    try:
        # 测试工具列表
        tools = tool_manager.list_tools()
        print(f"可用工具: {', '.join(tools.keys())}")
        
        # 测试bash工具（简单命令）
        result = await tool_manager.execute_tool("bash", command="echo 'test'")
        if result.success:
            print("✓ Bash工具工作正常")
        else:
            print(f"✗ Bash工具失败: {result.error}")
        
        # 测试read工具（读取自身）
        result = await tool_manager.execute_tool("read", file_path="test_basic.py")
        if result.success:
            print("✓ Read工具工作正常")
        else:
            print(f"✗ Read工具失败: {result.error}")
        
        return True
    except Exception as e:
        print(f"✗ 工具测试失败: {e}")
        return False

def test_database():
    """测试数据库"""
    print("\n测试数据库...")
    try:
        from database import init_db
        init_db()
        print("✓ 数据库初始化成功")
        
        # 测试连接
        from database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✓ 数据库连接成功")
        
        return True
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False

async def main():
    print("=== Moner 基本测试 ===\n")
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_database():
        all_passed = False
    
    if not await test_tools():
        all_passed = False
    
    print("\n" + "="*40)
    if all_passed:
        print("所有基本测试通过！")
        return 0
    else:
        print("部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))