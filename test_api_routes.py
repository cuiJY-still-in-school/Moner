#!/usr/bin/env python3
"""测试API路由"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_routes():
    """测试路由注册"""
    print("测试API路由...")
    
    try:
        from server.api import app
        
        # 检查路由
        routes = []
        for route in app.routes:
            routes.append({
                "path": getattr(route, "path", "unknown"),
                "methods": getattr(route, "methods", set()),
                "name": getattr(route, "name", "unknown")
            })
        
        print(f"找到 {len(routes)} 个路由:")
        for route in routes[:10]:  # 只显示前10个
            print(f"  {route['path']} - {route['methods']}")
        
        if len(routes) > 10:
            print(f"  ... 和 {len(routes) - 10} 个更多路由")
        
        # 检查关键路由
        key_routes = {
            "/api/health": "健康检查",
            "/api/auth/register": "用户注册",
            "/api/auth/login": "用户登录",
            "/api/auth/me": "获取当前用户",
            "/api/tools": "工具列表",
            "/api/relationships": "关系管理",
            "/api/goals": "目标管理",
        }
        
        print("\n检查关键路由:")
        all_ok = True
        for path, desc in key_routes.items():
            found = False
            for route in app.routes:
                if hasattr(route, "path") and route.path == path:
                    found = True
                    break
            
            if found:
                print(f"  ✓ {path} - {desc}")
            else:
                print(f"  ✗ {path} - {desc} (未找到)")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== API路由测试 ===\n")
    
    success = test_routes()
    
    print("\n" + "="*40)
    if success:
        print("路由测试通过")
        sys.exit(0)
    else:
        print("路由测试失败")
        sys.exit(1)