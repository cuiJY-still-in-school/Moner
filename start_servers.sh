#!/bin/bash
set -e

cd "$(dirname "$0")"
source venv/bin/activate

echo "启动WebSocket服务器..."
python -m server.main > ws.log 2>&1 &
WS_PID=$!
sleep 3

echo "启动REST API服务器..."
python -m server.api > api.log 2>&1 &
API_PID=$!
sleep 3

echo "WebSocket服务器 PID: $WS_PID"
echo "REST API服务器 PID: $API_PID"
echo "检查日志文件: ws.log 和 api.log"

# 保存PID到文件以便后续停止
echo $WS_PID > server.pid
echo $API_PID >> server.pid

echo "服务器启动完成"