#!/bin/bash

# Moner 一键安装脚本
# 使用: curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash

set -eo pipefail  # 严格模式：出错时停止，管道中任一命令失败则整个管道失败

# 显示帮助信息
show_help() {
    cat << EOF
Moner 一键安装脚本

使用方法:
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash -s -- [选项] [安装目录]

选项:
  -h, --help     显示此帮助信息
  --no-sudo      跳过需要sudo权限的步骤（系统包安装）
  --skip-deps    跳过系统依赖检查

参数:
  安装目录       可选，默认为 ~/.moner

示例:
  # 使用默认安装目录
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash
  
  # 指定安装目录
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash -s -- /opt/moner
  
  # 跳过sudo步骤（无权限时）
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash -s -- --no-sudo
  
  # 本地运行（已下载脚本）
  ./install.sh ~/my-moner

功能:
  - 自动检测和安装系统依赖
  - 下载最新版Moner
  - 创建Python虚拟环境
  - 安装Python依赖
  - 生成配置文件
  - 创建moner命令别名

Moner是一个CLI非冷启动AI系统，支持动态AI调用、WebSocket通信和工具执行。
EOF
    exit 0
}

# 解析命令行参数
NO_SUDO=false
SKIP_DEPS=false
INSTALL_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        --no-sudo)
            NO_SUDO=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        *)
            if [[ "$1" == -* ]]; then
                log_error "未知选项: $1"
                show_help
            else
                INSTALL_DIR="$1"
                shift
            fi
            ;;
    esac
done

# 设置默认安装目录（如果未指定）
if [ -z "$INSTALL_DIR" ]; then
    INSTALL_DIR="$HOME/.moner"
fi

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
    if ! command -v $1 &> /dev/null; then
        log_error "未找到命令: $1"
        return 1
    fi
    return 0
}

# 检查Python版本
check_python_version() {
    local python_cmd="python3"
    if ! command -v python3 &> /dev/null; then
        python_cmd="python"
    fi
    
    if ! command -v $python_cmd &> /dev/null; then
        log_error "未找到Python。请安装Python 3.8或更高版本"
        return 1
    fi
    
    local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    if [ $? -ne 0 ]; then
        log_error "无法获取Python版本"
        return 1
    fi
    
    local major=$($python_cmd -c "import sys; print(sys.version_info.major)" 2>/dev/null)
    local minor=$($python_cmd -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
    
    if [ $major -lt 3 ] || ([ $major -eq 3 ] && [ $minor -lt 8 ]); then
        log_error "需要Python 3.8或更高版本，当前版本: $version"
        return 1
    fi
    
    if [ $major -eq 3 ] && [ $minor -eq 13 ]; then
        log_warning "检测到Python 3.13: 某些包可能不完全兼容，我们会尝试特殊处理"
    fi
    
    log_success "Python $version 检测通过"
    return 0
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    if [ "$NO_SUDO" = true ]; then
        log_warning "跳过系统包安装（--no-sudo模式）"
        log_warning "请手动安装以下依赖:"
        echo "  - Python 3.8+"
        echo "  - pip"
        echo "  - git"
        echo "  - curl"
        echo ""
        echo "安装方法参考:"
        echo "  Debian/Ubuntu: apt-get install python3 python3-pip python3-venv git curl"
        echo "  RHEL/CentOS: yum install python3 python3-pip python3-virtualenv git curl"
        echo "  macOS: brew install python git curl"
        return 0
    fi
    
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        log_info "检测到Debian/Ubuntu系统"
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv git curl
    elif [ -f /etc/redhat-release ] || [ -f /etc/centos-release ]; then
        # RHEL/CentOS
        log_info "检测到RHEL/CentOS系统"
        sudo yum install -y python3 python3-pip python3-virtualenv git curl
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        log_info "检测到macOS系统"
        if ! command -v brew &> /dev/null; then
            log_error "请先安装Homebrew: https://brew.sh/"
            return 1
        fi
        brew install python git curl
    else
        log_warning "无法识别的系统，请手动安装: python3, pip, git, curl"
    fi
}

# 克隆或下载Moner
download_moner() {
    local install_dir="${1:-$HOME/.moner}"
    
    if [ -d "$install_dir" ]; then
        log_warning "目录 $install_dir 已存在，将更新..."
        cd "$install_dir"
        if [ -d ".git" ]; then
            git pull
        else
            log_warning "目录存在但不是git仓库，将备份并重新下载"
            mv "$install_dir" "${install_dir}.backup.$(date +%s)"
            git clone https://github.com/cuiJY-still-in-school/Moner.git "$install_dir"
        fi
    else
        log_info "下载Moner到 $install_dir..."
        git clone https://github.com/cuiJY-still-in-school/Moner.git "$install_dir"
    fi
    
    cd "$install_dir"
    log_success "Moner已下载到 $install_dir"
}

# 获取平台信息（与bundle-deps.sh保持一致）
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

# 设置Python虚拟环境
setup_venv() {
    local install_dir="$1"
    cd "$install_dir"
    
    if [ -d "venv" ]; then
        log_info "虚拟环境已存在，跳过创建"
        return 0
    fi
    
    # 在创建虚拟环境前获取平台信息
    log_info "检测系统平台..."
    local platform_id=$(get_platform_info)
    log_info "检测到平台: $platform_id"
    
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
    
    log_info "激活虚拟环境并安装依赖..."
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    log_info "安装Python依赖..."
    
    # 检查是否有预打包的依赖
    local deps_dir="deps/$platform_id"
    log_info "检查预打包依赖目录: $deps_dir"
    
    # 获取Python版本（用于决定安装策略）
    local python_version_full=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>/dev/null || echo "unknown")
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    
    log_info "Python版本: $python_version_full ($python_version)"
    
    if [ -d "$deps_dir" ] && [ -n "$(ls -A "$deps_dir"/*.whl "$deps_dir"/*.tar.gz "$deps_dir"/*.zip 2>/dev/null)" ]; then
        log_success "找到预打包的依赖目录: $deps_dir"
        log_info "使用本地依赖包安装..."
        
        # 对于Python 3.13，需要特殊处理pydantic-core
        if [[ "$python_version" == "3.13" ]]; then
            log_warning "Python 3.13检测到，为pydantic-core使用--no-binary选项..."
            # 创建临时requirements文件
            local tmp_req_file=$(mktemp)
            cp requirements.txt "$tmp_req_file"
            
            # 使用--no-binary pydantic-core选项
            if pip install --no-index --find-links "$deps_dir" --no-binary pydantic-core -r "$tmp_req_file"; then
                log_success "使用预打包依赖和--no-binary pydantic-core安装成功"
                rm -f "$tmp_req_file"
                deactivate
                return 0
            else
                log_warning "本地依赖包安装失败，尝试在线安装..."
                rm -f "$tmp_req_file"
            fi
        else
            # 正常安装（非Python 3.13）
            if pip install --no-index --find-links "$deps_dir" -r requirements.txt; then
                log_success "使用预打包依赖安装成功"
                deactivate
                return 0
            else
                log_warning "本地依赖包安装失败，尝试在线安装..."
            fi
        fi
    else
        log_info "未找到预打包依赖 ($deps_dir)，将在线安装"
    fi
    
    # 获取Python版本
    local python_version_full=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>/dev/null || echo "unknown")
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    
    # 在线安装依赖（本地依赖不可用或安装失败时执行）
    log_info "开始在线安装依赖..."
    
    # 对于Python 3.13的特殊处理
    if [[ "$python_version" == "3.13" ]]; then
        log_warning "Python 3.13检测到，尝试多种安装方法解决pydantic-core问题..."
        
        # 方法1: 尝试正常安装
        log_info "尝试方法1: 标准安装..."
        if pip install -r requirements.txt; then
            log_success "标准安装成功"
            deactivate
            log_success "虚拟环境设置完成"
            return 0
        fi
        
        # 方法2: 使用--no-binary pydantic-core
        log_info "方法1失败，尝试方法2: 使用--no-binary pydantic-core..."
        local tmp_req_file=$(mktemp)
        cp requirements.txt "$tmp_req_file"
        
        if pip install --no-binary pydantic-core -r "$tmp_req_file"; then
            log_success "使用--no-binary pydantic-core安装成功"
            rm -f "$tmp_req_file"
            deactivate
            log_success "虚拟环境设置完成"
            return 0
        fi
        
        # 方法3: 使用pydantic>=2.6.0
        log_info "方法2失败，尝试方法3: 使用pydantic>=2.6.0..."
        local newer_requirements="requirements_py313.txt"
        cat > "$install_dir/$newer_requirements" << EOF
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
        
        if pip install -r "$install_dir/$newer_requirements"; then
            log_success "使用pydantic>=2.6.0安装成功"
            rm -f "$tmp_req_file" "$install_dir/$newer_requirements" 2>/dev/null
            deactivate
            log_success "虚拟环境设置完成"
            return 0
        else
            log_error "所有在线安装方法都失败了"
            echo ""
            echo "可能的原因和解决方案:"
            echo "  1. 网络问题 - 请检查网络连接"
            echo "  2. Python 3.13兼容性问题 - pydantic-core需要编译，但缺少编译工具"
            echo "  3. 缺少系统依赖 - 可能需要安装 build-essential, python3-dev 等"
            echo ""
            echo "可以尝试:"
            echo "  a) 安装编译工具:"
            echo "     sudo apt-get install build-essential python3-dev"
            echo "  b) 使用 --skip-deps 选项重新安装，然后手动安装依赖"
            echo "  c) 使用系统Python 3.12或更低版本"
            echo ""
            rm -f "$tmp_req_file" "$install_dir/$newer_requirements" 2>/dev/null
            return 1
        fi
    else
        # Python 3.12或更低版本，正常在线安装
        log_info "Python $python_version 检测到，正常在线安装..."
        if pip install -r requirements.txt; then
            log_success "在线安装成功"
            deactivate
            log_success "虚拟环境设置完成"
            return 0
        else
            log_error "在线安装失败"
            echo ""
            echo "可能的原因:"
            echo "  1. 网络问题 - 请检查网络连接"
            echo "  2. Python版本不兼容 - 需要 Python 3.8-3.12"
            echo "  3. 缺少编译工具"
            echo ""
            echo "解决方案:"
            echo "  使用 --skip-deps 选项重新安装，然后手动安装依赖"
            echo ""
            return 1
        fi
    fi
}

# 创建配置文件
create_config() {
    local install_dir="$1"
    cd "$install_dir"
    
    if [ -f ".env" ]; then
        log_info ".env 文件已存在，跳过创建"
    else
        log_info "创建环境配置文件..."
        cp .env.example .env
        
        # 生成JWT密钥
        local jwt_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s|jwt_secret_key=.*|jwt_secret_key=$jwt_secret|" .env
        
        log_success "配置文件已创建，请编辑 .env 文件进行自定义配置"
    fi
}

# 创建启动脚本
create_launcher() {
    local install_dir="$1"
    
    # 创建moner命令
    local launcher_script="/usr/local/bin/moner"
    local user_launcher="$HOME/.local/bin/moner"
    
    log_info "创建启动脚本..."
    
    # 创建启动脚本内容
    # 使用反斜杠转义heredoc中的$符号，但允许$install_dir扩展
    cat > "$install_dir/moner-launcher.sh" << EOF
#!/bin/bash
# Moner启动脚本

# 获取脚本所在目录（处理符号链接）
if [ -L "\$0" ]; then
    # 如果是符号链接，获取链接目标
    SCRIPT_FILE="\$(readlink -f "\$0")"
else
    SCRIPT_FILE="\$0"
fi
MONER_DIR="\$(cd "\$(dirname "\$SCRIPT_FILE")" && pwd)"

# 检查是否在虚拟环境中
if [ -z "\$VIRTUAL_ENV" ]; then
    # 激活虚拟环境
    if [ -f "\$MONER_DIR/venv/bin/activate" ]; then
        source "\$MONER_DIR/venv/bin/activate"
    fi
fi

# 运行Moner
cd "\$MONER_DIR"
exec python -m cli.main "\$@"
EOF
    
    chmod +x "$install_dir/moner-launcher.sh"
    
    # 安装moner命令
    install_link "$install_dir/moner-launcher.sh" "moner"
}

# 检测shell类型
detect_shell() {
    if [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    elif [ -n "$BASH_VERSION" ]; then
        echo "bash"
    else
        # 默认使用当前shell
        echo "$SHELL" | grep -o "[^/]*$"
    fi
}

# 检查目录是否在PATH中
is_in_path() {
    local dir="$1"
    echo ":$PATH:" | grep -q ":$dir:"
    return $?
}

# 安装符号链接
install_link() {
    local source_file="$1"
    local command_name="$2"
    
    # 首先尝试 ~/.local/bin（用户目录，不需要sudo）
    mkdir -p "$HOME/.local/bin" 2>/dev/null
    if [ -w "$HOME/.local/bin" ]; then
        ln -sf "$source_file" "$HOME/.local/bin/$command_name"
        log_success "$command_name命令已安装到 ~/.local/bin/$command_name"
        
        # 检查是否在PATH中
        if ! is_in_path "$HOME/.local/bin"; then
            log_warning "~/.local/bin 不在你的PATH中"
            local shell_type=$(detect_shell)
            local shell_rc=""
            case "$shell_type" in
                bash)
                    shell_rc="~/.bashrc"
                    ;;
                zsh)
                    shell_rc="~/.zshrc"
                    ;;
                fish)
                    shell_rc="~/.config/fish/config.fish"
                    ;;
                *)
                    shell_rc="你的shell配置文件"
                    ;;
            esac
            
            echo "  请将以下行添加到 $shell_rc 文件中:"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            echo "  然后运行以下命令使其生效:"
            case "$shell_type" in
                bash)
                    echo "    source ~/.bashrc"
                    ;;
                zsh)
                    echo "    source ~/.zshrc"
                    ;;
                fish)
                    echo "    source ~/.config/fish/config.fish"
                    ;;
                *)
                    echo "    重新启动终端或重新加载shell配置"
                    ;;
            esac
            echo ""
            echo "  或者临时添加到当前会话:"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            
            # 直接尝试添加到当前shell的PATH
            if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
                export PATH="$HOME/.local/bin:$PATH"
                log_info "已将 ~/.local/bin 添加到当前会话的PATH"
            fi
        fi
    elif [ -w "/usr/local/bin" ]; then
        # 备选方案：/usr/local/bin（需要sudo权限）
        ln -sf "$source_file" "/usr/local/bin/$command_name"
        log_success "$command_name命令已安装到 /usr/local/bin/$command_name"
    else
        log_warning "无法自动安装$command_name命令，请手动创建:"
        echo "  # 创建符号链接到 ~/.local/bin（推荐）:"
        echo "  mkdir -p ~/.local/bin"
        echo "  ln -s $source_file ~/.local/bin/$command_name"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        echo "  # 或者使用完整路径运行:"
        echo "  $source_file"
    fi
}

# 创建服务启动脚本
create_service_scripts() {
    local install_dir="$1"
    
    # 创建启动所有服务的脚本
    cat > "$install_dir/start-all" << EOF
#!/bin/bash
cd "$install_dir"
./start_all.sh
EOF
    
    # 创建启动单个服务的脚本
    cat > "$install_dir/start-server" << EOF
#!/bin/bash
cd "$install_dir"
./start.sh
EOF
    
    # 创建moner-start脚本
    cat > "$install_dir/moner-start" << EOF
#!/bin/bash
cd "$install_dir"
./start_all.sh
EOF
    
    chmod +x "$install_dir/start-all" "$install_dir/start-server" "$install_dir/moner-start"
    
    # 安装moner-start命令
    install_link "$install_dir/moner-start" "moner-start"
}

# 验证安装
verify_installation() {
    local install_dir="$1"
    
    log_info "验证安装..."
    
    echo ""
    echo -e "${YELLOW}=== 安装验证 ===${NC}"
    
    # 检查安装目录是否存在
    if [ -d "$install_dir" ]; then
        log_success "安装目录存在: $install_dir"
    else
        log_error "安装目录不存在: $install_dir"
        return 1
    fi
    
    # 检查启动脚本是否存在
    if [ -f "$install_dir/moner-launcher.sh" ]; then
        log_success "启动脚本存在: $install_dir/moner-launcher.sh"
        chmod +x "$install_dir/moner-launcher.sh" 2>/dev/null
    else
        log_error "启动脚本不存在: $install_dir/moner-launcher.sh"
        return 1
    fi
    
    # 检查虚拟环境是否存在
    if [ -d "$install_dir/venv" ]; then
        log_success "Python虚拟环境存在"
    else
        log_error "Python虚拟环境不存在"
        return 1
    fi
    
    # 检查moner命令是否在PATH中可用
    local moner_found=false
    local moner_path=""
    
    # 首先检查命令是否在PATH中
    if command -v moner &> /dev/null; then
        moner_found=true
        moner_path=$(command -v moner)
        log_success "moner命令在PATH中可用: $moner_path"
    else
        # 检查常见位置
        local possible_paths=(
            "$HOME/.local/bin/moner"
            "/usr/local/bin/moner"
            "/usr/bin/moner"
            "$install_dir/moner-launcher.sh"
        )
        
        for path in "${possible_paths[@]}"; do
            if [ -f "$path" ] && [ -x "$path" ]; then
                moner_found=true
                moner_path="$path"
                log_success "找到moner可执行文件: $path"
                break
            fi
        done
        
        if [ "$moner_found" = false ]; then
            log_warning "moner命令未找到"
            echo ""
            echo "  你可以使用以下方式运行Moner:"
            echo "    1. 直接运行启动脚本:"
            echo "       $install_dir/moner-launcher.sh --help"
            echo ""
            echo "    2. 手动创建符号链接:"
            echo "       ln -s $install_dir/moner-launcher.sh ~/.local/bin/moner"
            echo "       export PATH=\"\$HOME/.local/bin:\$PATH\""
            echo ""
            echo "    3. 或者将以下别名添加到你的shell配置:"
            echo "       alias moner='$install_dir/moner-launcher.sh'"
        fi
    fi
    
    # 如果找到moner命令，测试基本功能
    if [ "$moner_found" = true ] && [ -n "$moner_path" ]; then
        log_info "测试moner命令基本功能..."
        if "$moner_path" --help &>/dev/null; then
            log_success "moner命令测试通过"
        else
            log_warning "moner命令测试失败，但文件存在"
        fi
    fi
    
    # 检查moner-start命令是否在PATH中可用
    if command -v moner-start &> /dev/null; then
        log_success "moner-start命令在PATH中可用"
    else
        log_warning "moner-start命令未在PATH中找到"
        echo "  你可以使用以下方式启动Moner系统:"
        echo "    cd $install_dir && ./start_all.sh"
    fi
    
    echo -e "${YELLOW}================${NC}"
    echo ""
}

# 显示安装完成信息
show_completion() {
    local install_dir="$1"
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    Moner 安装完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "安装目录: $install_dir"
    echo ""
    # 验证安装
    verify_installation "$install_dir"
    echo ""
    echo "使用方法:"
    echo "1. 启动系统:"
    echo "   cd $install_dir && ./start_all.sh"
    echo "   或使用: $install_dir/start-all"
    if [ -f "/usr/local/bin/moner-start" ] || [ -f "$HOME/.local/bin/moner-start" ]; then
        echo "   或使用: moner-start"
    fi
    echo ""
    echo "2. 使用CLI命令:"
    # 检查moner命令是否可用
    if command -v moner &>/dev/null || [ -f "$HOME/.local/bin/moner" ] || [ -f "/usr/local/bin/moner" ]; then
        echo "   moner --help"
        echo ""
        echo "   快速测试（如果moner命令可用）:"
        echo "     moner --version"
        echo "     moner --help"
    else
        echo "   $install_dir/moner-launcher.sh --help"
        echo ""
        echo "   快速测试:"
        echo "     $install_dir/moner-launcher.sh --help"
    fi
    echo ""
    echo "3. 注册用户:"
    echo "   moner register --username <用户名> --password <密码>"
    echo ""
    echo "4. 使用AI功能:"
    echo "   moner ai \"你的问题\" --provider openai --api-key YOUR_KEY"
    echo ""
    echo "5. API文档:"
    echo "   启动后访问: http://localhost:8000/api/docs"
    echo ""
    echo "6. 配置说明:"
    echo "   编辑 $install_dir/.env 文件进行配置"
    echo ""
    echo -e "${YELLOW}重要提示:${NC}"
    if ! command -v moner &>/dev/null; then
        echo -e "${YELLOW}- moner命令可能不在PATH中${NC}"
        echo "  如果'moner'命令未找到，请尝试:"
        echo "    1. 重新打开终端"
        echo "    2. 运行: source ~/.bashrc 或 source ~/.zshrc"
        echo "    3. 或者直接使用: $install_dir/moner-launcher.sh"
        echo ""
    fi
    echo "- 首次启动会初始化数据库"
    echo "- 需要有效的AI API密钥才能使用AI功能"
    echo "- 生产环境请修改 .env 中的默认配置"
    echo ""
    echo "更多信息请查看 README.md"
    echo -e "${GREEN}========================================${NC}"
}

# 主安装函数
main() {
    log_info "开始安装 Moner..."
    echo ""
    
    # 使用解析后的安装目录
    local install_dir="$INSTALL_DIR"
    
    log_info "安装目录: $install_dir"
    log_info "跳过sudo步骤: $NO_SUDO"
    log_info "跳过依赖检查: $SKIP_DEPS"
    echo ""
    
    # 检查系统依赖
    if [ "$SKIP_DEPS" = false ]; then
        log_info "检查系统依赖..."
        check_python_version || {
            if [ "$NO_SUDO" = false ]; then
                log_warning "Python版本检查失败，尝试安装依赖..."
                install_system_deps
                check_python_version || {
                    log_error "Python安装失败，请手动安装Python 3.8+"
                    exit 1
                }
            else
                log_error "需要Python 3.8或更高版本，请手动安装"
                exit 1
            fi
        }
        
        check_command "git" || {
            if [ "$NO_SUDO" = false ]; then
                log_warning "git未安装，尝试安装..."
                install_system_deps
                check_command "git" || {
                    log_error "git安装失败，请手动安装git"
                    exit 1
                }
            else
                log_error "需要git，请手动安装"
                exit 1
            fi
        }
        
        check_command "curl" || {
            if [ "$NO_SUDO" = false ]; then
                log_warning "curl未安装，尝试安装..."
                install_system_deps
            else
                log_error "需要curl，请手动安装"
                exit 1
            fi
        }
    else
        log_warning "跳过系统依赖检查，请确保已安装: python3, pip, git, curl"
    fi
    
    # 下载Moner
    download_moner "$install_dir"
    
    # 设置虚拟环境
    setup_venv "$install_dir"
    
    # 创建配置文件
    create_config "$install_dir"
    
    # 创建启动脚本
    create_launcher "$install_dir"
    
    # 创建服务启动脚本
    create_service_scripts "$install_dir"
    
    # 显示完成信息
    show_completion "$install_dir"
}

# 直接运行主函数
main "$@"