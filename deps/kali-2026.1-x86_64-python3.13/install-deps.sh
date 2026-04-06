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
