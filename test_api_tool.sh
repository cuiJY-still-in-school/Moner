#!/bin/bash
cd /home/jayson2013/moner
source venv/bin/activate

# 杀死现有服务器
pkill -9 -f "server.api" 2>/dev/null
sleep 1

# 启动服务器并重定向输出
python -m server.api > api_debug.log 2>&1 &
SERVER_PID=$!
sleep 3

echo "服务器PID: $SERVER_PID"

# 检查是否启动
curl -s http://localhost:8000/api/health
echo ""

# 获取token
TOKEN=$(python -c "import json; print(json.load(open('/home/jayson2013/.moner_session.json'))['token'])")
echo "Token长度: ${#TOKEN}"

# 测试工具执行
echo "测试工具执行..."
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command":"echo test"}' \
  http://localhost:8000/api/tools/bash/execute

echo -e "\n\n服务器日志:"
tail -20 api_debug.log

# 清理
kill $SERVER_PID 2>/dev/null