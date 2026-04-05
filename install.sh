#!/bin/bash

# Moner 一键安装脚本
# 使用: curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash

set -e  # 出错时停止

# 显示帮助信息
show_help() {
    cat << EOF
Moner 一键安装脚本

使用方法:
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash -s -- [安装目录]

参数:
  安装目录    可选，默认为 ~/.moner

示例:
  # 使用默认安装目录
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash
  
  # 指定安装目录
  curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash -s -- /opt/moner
  
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

# 检查是否请求帮助
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
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
    
    log_success "Python $version 检测通过"
    return 0
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv git curl
    elif [ -f /etc/redhat-release ] || [ -f /etc/centos-release ]; then
        # RHEL/CentOS
        sudo yum install -y python3 python3-pip python3-virtualenv git curl
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
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

# 设置Python虚拟环境
setup_venv() {
    local install_dir="$1"
    cd "$install_dir"
    
    if [ -d "venv" ]; then
        log_info "虚拟环境已存在，跳过创建"
        return 0
    fi
    
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
    
    log_info "激活虚拟环境并安装依赖..."
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    deactivate
    log_success "虚拟环境设置完成"
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
    cat > "$install_dir/moner-launcher.sh" << EOF
#!/bin/bash
# Moner启动脚本

MONER_DIR="$install_dir"

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
    
    # 尝试安装到系统路径
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$install_dir/moner-launcher.sh" "/usr/local/bin/moner"
        log_success "moner命令已安装到 /usr/local/bin/moner"
    elif [ -d "$HOME/.local/bin" ]; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$install_dir/moner-launcher.sh" "$HOME/.local/bin/moner"
        log_success "moner命令已安装到 ~/.local/bin/moner"
        log_warning "请确保 ~/.local/bin 在你的PATH中"
    else
        log_warning "无法自动安装moner命令，请手动创建:"
        echo "  ln -s $install_dir/moner-launcher.sh /usr/local/bin/moner"
        echo "或运行: $install_dir/moner-launcher.sh"
    fi
    
    # 安装moner-start命令
    install_link "$install_dir/moner-start" "moner-start"
}

# 安装符号链接
install_link() {
    local source_file="$1"
    local command_name="$2"
    
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$source_file" "/usr/local/bin/$command_name"
        log_success "$command_name命令已安装到 /usr/local/bin/$command_name"
    elif [ -d "$HOME/.local/bin" ]; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$source_file" "$HOME/.local/bin/$command_name"
        log_success "$command_name命令已安装到 ~/.local/bin/$command_name"
    else
        log_warning "无法自动安装$command_name命令，请手动创建:"
        echo "  ln -s $source_file /usr/local/bin/$command_name"
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
    echo "使用方法:"
    echo "1. 启动系统:"
    echo "   cd $install_dir && ./start_all.sh"
    echo "   或使用: $install_dir/start-all"
    if [ -f "/usr/local/bin/moner-start" ] || [ -f "$HOME/.local/bin/moner-start" ]; then
        echo "   或使用: moner-start"
    fi
    echo ""
    echo "2. 使用CLI命令:"
    if [ -f "/usr/local/bin/moner" ] || [ -f "$HOME/.local/bin/moner" ]; then
        echo "   moner --help"
    else
        echo "   $install_dir/moner-launcher.sh --help"
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
    echo -e "${YELLOW}注意事项:${NC}"
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
    
    # 默认安装目录
    local install_dir="$HOME/.moner"
    
    # 检查是否需要自定义安装目录
    if [ $# -ge 1 ]; then
        install_dir="$1"
    fi
    
    # 检查系统依赖
    log_info "检查系统依赖..."
    check_python_version || {
        log_warning "Python版本检查失败，尝试安装依赖..."
        install_system_deps
        check_python_version || {
            log_error "Python安装失败，请手动安装Python 3.8+"
            exit 1
        }
    }
    
    check_command "git" || {
        log_warning "git未安装，尝试安装..."
        install_system_deps
        check_command "git" || {
            log_error "git安装失败，请手动安装git"
            exit 1
        }
    }
    
    check_command "curl" || {
        log_warning "curl未安装，尝试安装..."
        install_system_deps
    }
    
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

# 如果是直接运行，而不是被source
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi