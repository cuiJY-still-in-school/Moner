#!/bin/bash

# 启动Moner系统（WebSocket + REST API）

echo "正在启动Moner系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3"
    exit 1
fi

# 使用虚拟环境
if [ -d "venv" ]; then
    echo "使用虚拟环境..."
    source venv/bin/activate
else
    echo "警告: 未找到虚拟环境，使用系统Python"
fi

# 检查依赖
echo "检查Python依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
python3 -c "
from database import init_db
init_db()
print('数据库初始化完成')
"

# 启动WebSocket服务器
echo "启动WebSocket服务器..."
python3 -m server.main &
WS_PID=$!
sleep 2

# 启动REST API服务器
echo "启动REST API服务器..."
python3 -m server.api &
API_PID=$!
sleep 3

echo "========================================"
echo "WebSocket服务器已启动 (PID: $WS_PID)"
echo "监听: ws://localhost:8765"
echo ""
echo "REST API服务器已启动 (PID: $API_PID)"
echo "API文档: http://localhost:8000/api/docs"
echo "健康检查: http://localhost:8000/api/health"
echo ""
echo "使用以下命令测试CLI:"
echo "  python -m cli.main --help"
echo ""
echo "示例命令:"
echo "  注册用户: python -m cli.main register --username test --password test"
echo "  登录: python -m cli.main login --username test --password test"
echo "  执行命令: python -m cli.main bash 'ls -la'"
echo ""
echo "使用curl测试API:"
echo "  curl -X POST http://localhost:8000/api/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"username\":\"test\",\"password\":\"test\",\"user_type\":\"human\"}'"
echo ""
echo "按Ctrl+C停止所有服务器"
echo "========================================"

# 清理函数
cleanup() {
    echo "正在停止服务器..."
    kill $WS_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    echo "服务器已停止"
    exit 0
}

# 捕获中断信号
trap cleanup INT TERM

# 等待子进程
wait $WS_PID $API_PID 2>/dev/null