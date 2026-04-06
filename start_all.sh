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

# 获取Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
python_version_full=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>/dev/null || echo "unknown")

echo "Python版本: $python_version_full ($python_version)"

# 检查Python 3.13兼容性问题
if [[ "$python_version" == "3.13" ]]; then
    echo "检测到Python 3.13，检查pydantic和SQLAlchemy兼容性..."
    
    # 检查已安装的包版本
    pydantic_version=$(python3 -c "import pydantic; print(pydantic.__version__)" 2>/dev/null || echo "not installed")
    sqlalchemy_version=$(python3 -c "import sqlalchemy; print(sqlalchemy.__version__)" 2>/dev/null || echo "not installed")
    
    echo "当前pydantic版本: $pydantic_version"
    echo "当前SQLAlchemy版本: $sqlalchemy_version"
    
    # 检查是否需要更新
    need_update=0
    if [[ "$pydantic_version" == "not installed" ]] || [[ "$pydantic_version" < "2.6.0" ]]; then
        echo "需要更新pydantic到>=2.6.0..."
        need_update=1
    fi
    
    if [[ "$sqlalchemy_version" == "not installed" ]] || [[ "$sqlalchemy_version" < "2.0.26" ]]; then
        echo "需要更新SQLAlchemy到>=2.0.26..."
        need_update=1
    fi
    
    if [[ $need_update -eq 1 ]]; then
        echo "创建兼容性requirements文件..."
        cat > requirements_py313_fix.txt << EOF
fastapi>=0.115.0
uvicorn[standard]==0.24.0
websockets==12.0
sqlalchemy>=2.0.26
alembic==1.12.1
pydantic>=2.9.0
pydantic-settings==2.1.0
pyjwt[crypto]==2.8.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
click==8.1.7
typer==0.9.0
rich==13.7.0
requests==2.31.0
aiohttp==3.9.1
aiosqlite==0.19.0
openai>=1.0.0
anthropic>=0.25.0
tiktoken>=0.5.0
python-multipart>=0.0.24
EOF
        
        echo "更新Python包以兼容Python 3.13..."
        pip install -r requirements_py313_fix.txt
        rm -f requirements_py313_fix.txt
        echo "包更新完成"
    else
        echo "包版本已兼容Python 3.13"
        pip install -r requirements.txt
    fi
else
    # Python 3.12或更低版本，正常安装
    pip install -r requirements.txt
fi

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