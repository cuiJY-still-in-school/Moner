#!/bin/bash

# 启动Moner系统

echo "正在启动Moner..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3"
    exit 1
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
SERVER_PID=$!

# 等待服务器启动
sleep 3

echo "WebSocket服务器已启动 (PID: $SERVER_PID)"
echo ""
echo "使用以下命令测试CLI:"
echo "  python3 -m cli.main --help"
echo ""
echo "示例:"
echo "  注册用户: python3 -m cli.main register --username test --password test"
echo "  登录: python3 -m cli.main login --username test --password test"
echo "  执行命令: python3 -m cli.main bash 'ls -la'"
echo ""
echo "按Ctrl+C停止服务器"

# 等待用户中断
trap "kill $SERVER_PID 2>/dev/null; echo '服务器已停止'; exit" INT TERM
wait $SERVER_PID