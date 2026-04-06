#!/bin/bash
# 打包依赖脚本
# 将Python依赖包下载到本地目录，便于离线安装

set -eo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "未找到命令: $1"
        return 1
    fi
    return 0
}

# 获取平台和Python信息
get_platform_info() {
    local python_version_full=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>/dev/null || echo "unknown")
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    
    # 获取平台信息
    local platform=""
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # 尝试获取具体的Linux发行版
        if [[ -f /etc/os-release ]]; then
            source /etc/os-release
            platform="${ID}-${VERSION_ID}"
        else
            platform="linux-unknown"
        fi
        # 添加架构信息
        local arch=$(uname -m)
        platform="${platform}-${arch}"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        platform="macos-$(uname -m)"
    else
        platform="unknown"
    fi
    
    echo "${platform}-python${python_version}"
}

# 主函数
main() {
    log_info "开始打包Python依赖..."
    echo ""
    
    # 检查必要命令
    check_command python3 || exit 1
    check_command pip3 || {
        log_warning "pip3未找到，尝试使用pip..."
        check_command pip || exit 1
    }
    
    # 获取平台标识
    local platform_id=$(get_platform_info)
    log_info "平台标识: $platform_id"
    
    # 创建依赖目录
    local deps_dir="deps/$platform_id"
    log_info "创建依赖目录: $deps_dir"
    mkdir -p "$deps_dir"
    
    # 检查requirements.txt是否存在
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt 不存在"
        exit 1
    fi
    
    # 激活虚拟环境（如果存在）
    local use_venv=false
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        log_info "使用虚拟环境..."
        source venv/bin/activate
        use_venv=true
    fi
    
    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip
    
    # 下载依赖包
    log_info "下载依赖包到 $deps_dir ..."
    
    # 设置pip下载参数
    local pip_download_cmd="pip download"
    
    # 如果是Python 3.13，特殊处理pydantic-core
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    if [[ "$python_version" == "3.13" ]]; then
        log_warning "Python 3.13检测到，为pydantic-core使用--no-binary选项..."
        # 创建临时requirements文件
        local tmp_req_file=$(mktemp)
        # 复制requirements.txt，为pydantic-core添加注释
        cp requirements.txt "$tmp_req_file"
        
        # 尝试下载，如果失败则尝试其他方法
        if ! $pip_download_cmd -r "$tmp_req_file" --dest "$deps_dir"; then
            log_warning "标准下载失败，尝试使用--no-binary pydantic-core..."
            if ! $pip_download_cmd --no-binary pydantic-core -r "$tmp_req_file" --dest "$deps_dir"; then
                log_warning "尝试下载pydantic>=2.6.0..."
                # 创建新的requirements文件
                local newer_req_file=$(mktemp)
                cat > "$newer_req_file" << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic>=2.6.0
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
EOF
                if ! $pip_download_cmd -r "$newer_req_file" --dest "$deps_dir"; then
                    log_error "所有下载方法都失败了"
                    rm -f "$tmp_req_file" "$newer_req_file"
                    exit 1
                fi
                rm -f "$newer_req_file"
            fi
        fi
        rm -f "$tmp_req_file"
    else
        # 正常下载
        if ! $pip_download_cmd -r requirements.txt --dest "$deps_dir"; then
            log_error "依赖下载失败"
            exit 1
        fi
    fi
    
    # 创建安装脚本
    log_info "创建安装脚本..."
    cat > "$deps_dir/install-deps.sh" << 'EOF'
#!/bin/bash
# 本地依赖安装脚本
# 从当前目录安装所有依赖包

set -eo pipefail

deploy_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "从 $deploy_dir 安装依赖包..."

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ] && [ -f "../../venv/bin/activate" ]; then
    echo "激活虚拟环境..."
    source ../../venv/bin/activate
fi

# 安装依赖
pip install --no-index --find-links "$deploy_dir" -r ../../requirements.txt

echo "依赖安装完成"
EOF
    
    chmod +x "$deps_dir/install-deps.sh"
    
    # 创建README文件
    cat > "$deps_dir/README.md" << EOF
# 依赖包目录
平台: $platform_id
打包时间: $(date)

## 包含的包
$(ls -1 "$deps_dir"/*.whl "$deps_dir"/*.tar.gz "$deps_dir"/*.zip 2>/dev/null | wc -l) 个包

## 使用方法
1. 确保在项目根目录
2. 运行安装脚本:
   \`\`\`bash
   cd $deps_dir
   ./install-deps.sh
   \`\`\`

或使用pip直接安装:
\`\`\`bash
pip install --no-index --find-links $deps_dir -r requirements.txt
\`\`\`

## 注意事项
- 这些包是针对特定平台和Python版本编译的
- 如果平台或Python版本不匹配，可能需要重新打包
- 对于Python 3.13，pydantic-core可能需要特殊处理
EOF
    
    # 统计包数量
    local package_count=$(ls -1 "$deps_dir"/*.whl "$deps_dir"/*.tar.gz "$deps_dir"/*.zip 2>/dev/null | wc -l)
    
    # 退出虚拟环境
    if [ "$use_venv" = true ]; then
        deactivate
    fi
    
    echo ""
    log_success "依赖打包完成!"
    echo ""
    echo "平台: $platform_id"
    echo "包数量: $package_count"
    echo "目录: $deps_dir"
    echo ""
    echo "安装方法:"
    echo "  cd $deps_dir && ./install-deps.sh"
    echo ""
    echo "可以将此目录上传到GitHub，安装时从中获取依赖包。"
}

# 如果是直接运行，而不是被source
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi