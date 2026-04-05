#!/usr/bin/env python3
"""测试API导入"""

import sys

def test_import():
    print("测试API导入...")
    try:
        from server.api import app
        print("✓ FastAPI应用导入成功")
        
        from auth.auth import authenticate_user, create_access_token
        print("✓ 认证模块导入成功")
        
        from tools.manager import tool_manager
        print("✓ 工具管理器导入成功")
        
        from relationships.crud import create_relationship
        print("✓ 关系CRUD导入成功")
        
        from goals.crud import create_goal
        print("✓ 目标CRUD导入成功")
        
        print("\n所有导入成功！")
        return True
        
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)