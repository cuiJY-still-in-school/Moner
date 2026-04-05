# Moner

一个CLI非冷启动AI系统，支持人类和AI代理注册，配置长期目标，并通过有限工具（bash、webfetch、read、edit）进行交互。系统包含社交关系功能，用户可以互相添加和汇报。

## 核心功能

1. **非冷启动AI系统**：AI代理可以立即启动并开始工作
2. **用户注册**：人类和AI代理都可以通过WebSocket服务器注册账号
3. **长期目标配置**：用户可以设置长期目标，AI代理会协助实现
4. **有限工具集**：
   - `bash`：执行bash命令（有安全限制）
   - `webfetch`：获取网页内容
   - `read`：读取文件
   - `edit`：编辑文件
5. **社交关系系统**：
   - 每个用户有唯一ID
   - 可以互相添加为联系人
   - 可以互相汇报进展
6. **WebSocket服务器**：实时通信和事件推送

## 系统架构

### 组件

1. **WebSocket服务器** (`server/`)：处理连接、注册、消息路由
2. **REST API服务器** (`server/api.py`)：提供HTTP RESTful API接口
3. **用户管理** (`auth/`)：用户/代理注册、认证、会话管理
4. **工具系统** (`tools/`)：实现bash、webfetch、read、edit工具
5. **目标系统** (`goals/`)：长期目标配置和追踪
6. **关系系统** (`relationships/`)：联系人管理、汇报功能
7. **CLI客户端** (`cli/`)：命令行界面

### 数据模型

- **User**：用户/代理，有类型（human/agent）、ID、用户名、密码哈希、长期目标等
- **Relationship**：用户之间的关系，状态（pending/accepted）、类型（friend/colleague等）
- **Report**：用户之间的汇报，包含内容、时间戳、发送者、接收者
- **Goal**：用户长期目标，包含描述、状态、进度
- **ToolExecution**：工具执行记录，用于审计

## 安装

### 一键安装（推荐）

使用以下命令一键安装Moner：

```bash
curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash
```

或指定安装目录：

```bash
curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash -s -- /path/to/install
```

安装完成后，可以直接使用 `moner` 命令：

```bash
# 查看帮助
moner --help

# 注册用户
moner register --username test --password test

# 使用AI功能
moner ai "解释一下人工智能" --provider openai --api-key YOUR_API_KEY
```

### 手动安装

#### 使用虚拟环境（推荐）

```bash
# 克隆或进入项目目录
cd /path/to/moner

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境（Linux/macOS）
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 系统依赖

- Python 3.8+
- SQLite（默认）或 PostgreSQL
- git（用于一键安装）
- curl（用于一键安装）

## 快速开始

### 一键安装后快速开始

```bash
# 1. 一键安装
curl -sSL https://raw.githubusercontent.com/cuiJY-still-in-school/Moner/main/install.sh | bash

# 2. 启动系统
moner-start  # 或: cd ~/.moner && ./start_all.sh

# 3. 在另一个终端中，注册用户
moner register --username test --password test

# 4. 登录
moner login --username test --password test

# 5. 使用AI功能（需要API密钥）
moner ai "解释一下人工智能" --provider openai --api-key YOUR_API_KEY

# 6. 执行其他命令
moner bash "ls -la"
moner webfetch "https://example.com"
moner status
```

### 传统启动方式（手动安装）

#### 1. 启动服务器

```bash
# 激活虚拟环境后
python -m server.main
```

服务器将在 `ws://localhost:8765` 启动。

#### 2. 启动完整系统（WebSocket + REST API）

```bash
./start_all.sh
```

#### 3. 使用CLI客户端

```bash
# 在另一个终端中

# 显示帮助
python -m cli.main --help

# 注册新用户
python -m cli.main register --username test --password test

# 登录
python -m cli.main login --username test --password test

# 执行bash命令
python -m cli.main bash "ls -la"

# 获取网页内容
python -m cli.main webfetch "https://example.com"

# 读取文件
python -m cli.main read "README.md"

# 编辑文件
python -m cli.main edit --file-path test.txt --mode overwrite --content "Hello World"
```

### 3. 使用启动脚本（简化）

```bash
# 启动服务器并显示使用说明
./start.sh
```

### 4. 使用REST API

系统提供完整的RESTful API，可通过HTTP访问所有功能：

```bash
# 使用curl测试API

# 健康检查
curl http://localhost:8000/api/health

# 注册用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test","user_type":"human"}'

# 登录获取令牌
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"

# 使用令牌访问受保护端点
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_token>"

# 执行bash命令
curl -X POST http://localhost:8000/api/tools/bash/execute \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}'

# 查看API文档
# 访问 http://localhost:8000/api/docs 或 http://localhost:8000/api/redoc
```

### 5. 使用启动脚本（同时启动WebSocket和REST API）

```bash
# 启动所有服务（WebSocket + REST API）
./start_all.sh
```

## 配置

复制 `.env.example` 为 `.env` 并修改设置：

```bash
cp .env.example .env
```

主要配置项：

- `SERVER_HOST`, `SERVER_PORT`：REST API服务器地址（默认: 0.0.0.0:8000）
- `WS_HOST`, `WS_PORT`：WebSocket服务器地址（默认: 0.0.0.0:8765）
- `DATABASE_URL`：数据库连接字符串
- `JWT_SECRET_KEY`：JWT密钥
- `JWT_ALGORITHM`：JWT算法（默认: HS256）
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`：JWT令牌过期时间（默认: 30分钟）
- `ALLOWED_BASH_PATHS`：允许执行bash命令的路径
- `MAX_BASH_TIMEOUT`：bash命令最大执行时间（秒）
- `ALLOWED_READ_PATHS`：允许读取文件的路径
- `ALLOWED_EDIT_PATHS`：允许编辑文件的路径

## 协议

WebSocket消息使用JSON格式：

```json
{
  "type": "register|login|tool_request|relationship_request|goal_create|...",
  "data": {...}
}
```

消息类型：
- `register`：用户注册
- `login`：用户登录
- `tool_request`：工具执行请求
- `tool_response`：工具执行响应
- `relationship_request`：关系请求
- `relationship_response`：关系响应
- `goal_create`：创建目标
- `goal_update`：更新目标
- `report`：发送汇报
- `error`：错误消息
- `info`：信息消息

## 安全考虑

- 工具执行有安全限制（不能访问敏感目录）
- WebSocket连接使用JWT认证
- 所有工具执行记录审计
- 路径白名单限制文件访问

## AI功能

Moner系统提供完整的AI功能，支持多种AI提供商，无需预配置即可使用。

### AI功能特性

1. **动态AI调用**：使用时提供provider、base_url、model_name、api_key即可调用AI，无需预配置
2. **多种AI提供商**：
   - **OpenAI**：支持GPT-3.5、GPT-4等模型
   - **Anthropic**：支持Claude系列模型
3. **多种使用方式**：
   - CLI命令行接口
   - REST API直接调用
   - WebSocket工具系统
4. **预配置模型管理**：可保存AI模型配置以便重用
5. **对话管理**：保存对话历史和消息

### 快速开始使用AI

#### 通过CLI使用AI

```bash
# 登录后使用AI
python -m cli.main login --username test --password test

# 使用OpenAI GPT-4
python -m cli.main ai "解释一下人工智能" \
  --provider openai \
  --api-key YOUR_OPENAI_API_KEY \
  --model-name gpt-4 \
  --max-tokens 500

# 使用Anthropic Claude
python -m cli.main ai "解释一下机器学习" \
  --provider anthropic \
  --api-key YOUR_ANTHROPIC_API_KEY \
  --model-name claude-3-opus-20240229 \
  --mode chat
```

#### 通过REST API使用AI

```bash
# 直接调用AI补全（无需预配置模型）
curl -X POST http://localhost:8000/api/ai/direct/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "prompt": "解释一下人工智能",
    "provider": "openai",
    "api_key": "YOUR_OPENAI_API_KEY",
    "model_name": "gpt-3.5-turbo",
    "max_tokens": 1000
  }'

# 调用AI聊天
curl -X POST http://localhost:8000/api/ai/direct/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "openai",
    "api_key": "YOUR_OPENAI_API_KEY",
    "model_name": "gpt-4"
  }'
```

#### API端点

- `POST /api/ai/direct/completions` - 直接AI补全（动态配置）
- `POST /api/ai/direct/chat/completions` - 直接AI聊天（动态配置）
- `GET /api/ai/models` - 获取预配置的AI模型
- `POST /api/ai/models` - 创建AI模型配置
- `GET /api/ai/prompts` - 获取提示模板
- `POST /api/ai/conversations` - 创建对话
- `POST /api/ai/messages` - 发送消息

#### 预配置模型管理

如需保存AI配置以便重用，可使用AI模型管理API：

```bash
# 创建OpenAI模型配置
curl -X POST http://localhost:8000/api/ai/models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "openai-gpt-4",
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key": "YOUR_OPENAI_API_KEY",
    "is_default": true
  }'

# 然后使用模型ID调用AI，无需每次都提供API密钥
curl -X POST http://localhost:8000/api/ai/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "prompt": "解释一下人工智能",
    "model_id": 1,
    "max_tokens": 1000
  }'
```

### AI工具

系统提供两个AI工具：
1. **ai** - 简单AI工具（需要预配置API密钥）
2. **ai_dynamic** - 动态AI工具（使用时提供完整配置）

通过WebSocket工具系统调用：
```json
{
  "type": "tool_request",
  "data": {
    "tool": "ai_dynamic",
    "params": {
      "prompt": "解释一下人工智能",
      "provider": "openai",
      "api_key": "YOUR_API_KEY",
      "model_name": "gpt-3.5-turbo"
    }
  }
}
```

### 查看API文档

启动系统后访问：http://localhost:8000/api/docs

## 项目结构

```
moner/
├── server/           # WebSocket服务器
├── auth/             # 用户认证和管理
├── tools/            # 工具系统
├── relationships/    # 关系系统
├── goals/            # 目标系统
├── cli/              # CLI客户端
├── models/           # 数据库模型
├── utils/            # 工具函数
├── tests/            # 测试
├── config.py         # 配置
├── database.py       # 数据库连接
├── requirements.txt  # 依赖
├── start.sh          # 启动脚本
└── README.md         # 本文档
```

## 开发

### 运行测试

```bash
python test_basic.py
```

### 添加新工具

1. 在 `tools/` 目录中创建新工具类，继承 `Tool` 基类
2. 实现 `execute` 方法
3. 在 `tools/manager.py` 中注册工具

### 数据库迁移

项目使用SQLAlchemy，可通过Alembic进行迁移（待实现）。

## 待实现功能

- [x] 完整的AI代理集成 ✓
- [ ] 数据库迁移（Alembic）
- [x] REST API接口 ✓
- [ ] 前端管理界面
- [ ] 移动客户端
- [ ] 更复杂的关系和汇报系统
- [ ] 工具执行审计和回滚
- [ ] 更细粒度的权限控制
- [ ] 流式AI响应支持
- [ ] 更多AI提供商支持（本地模型等）
- [ ] AI工具调用集成（函数调用）

## 许可证

MIT

## 贡献

欢迎提交Issue和Pull Request。