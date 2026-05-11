# AI 游戏生成助手

基于 DeepSeek API 的 AI 游戏生成工具。输入游戏描述，AI 自动生成可运行的 HTML5 游戏，支持多用户、历史记录、游戏记忆存档。

## 技术栈

| 层级 | 技术 |
|---|---|
| **后端** | Python 3.10+ / FastAPI / SQLAlchemy 2.0 / SQLite |
| **前端** | React 18 / Vite / React Router 6 |
| **AI** | DeepSeek API / OpenAI SDK |
| **向量检索** | ChromaDB（语义搜索游戏记忆） |
| **认证** | JWT / bcrypt |
| **限流** | Redis（可选，无 Redis 时自动降级） |

## 项目结构

```
game/
├── backend/                  # FastAPI 后端
│   ├── main.py               # 应用入口
│   ├── config.py             # 配置（API Key、数据库等）
│   ├── database.py           # 数据库连接
│   ├── models.py             # ORM 模型（User, ChatMessage, GameMemory）
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── auth.py               # JWT + bcrypt 认证
│   ├── requirements.txt      # Python 依赖
│   ├── routes/
│   │   ├── auth_routes.py    # 注册/登录接口
│   │   ├── game_routes.py    # 游戏生成/历史记录接口
│   │   └── memory_routes.py  # 游戏记忆存档接口
│   ├── services/
│   │   ├── ai_service.py     # AI 调用（意图判断、摘要压缩、流式生成）
│   │   └── vector_store.py   # ChromaDB 向量存储
│   └── middleware/
│       └── rate_limit.py     # Redis 限流中间件
│
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── main.jsx          # 入口
│   │   ├── App.jsx           # 路由配置
│   │   ├── App.css           # 全局样式
│   │   ├── api/
│   │   │   └── client.js     # HTTP 请求封装
│   │   ├── context/
│   │   │   ├── AuthContext.jsx   # 登录状态
│   │   │   └── ChatContext.jsx   # 聊天状态（跨页面持久化）
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # 导航栏
│   │   │   ├── ChatMessage.jsx   # 消息气泡（iframe 渲染游戏）
│   │   │   ├── MessageInput.jsx  # 输入框
│   │   │   └── ProtectedRoute.jsx # 路由守卫
│   │   └── pages/
│   │       ├── LoginPage.jsx     # 登录/注册
│   │       ├── ChatPage.jsx      # 主聊天页（游戏生成）
│   │       ├── MemoriesPage.jsx  # 游戏记忆存档
│   │       └── SettingsPage.jsx  # 设置（清空存档）
│   ├── index.html
│   ├── package.json
│   └── vite.config.js        # Vite 配置（含 API 代理）
│
├── .env.example              # 环境变量模板
└── README.md                 # 本文件
```

## 快速启动

### 前置要求

- Python 3.10+
- Node.js 18+
- DeepSeek API Key（[点此获取](https://platform.deepseek.com/)）

### 1. 配置 API Key

在项目根目录创建 `.env` 文件（可参考 `.env.example`）：

```env
OPENAI_API_KEY=sk-your-deepseek-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

### 2. 启动后端

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务（默认 http://localhost:5001）
python -m uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

看到以下日志即启动成功：

```
INFO:     SQLite 数据库就绪
INFO:     Application startup complete.
```

### 3. 启动前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

### 4. 访问

打开浏览器访问 **http://localhost:5173**

- 注册账号 → 登录 → 输入游戏描述 → AI 自动生成

## 使用方式

### 生成游戏

在输入框输入游戏描述，例如：

- "五子棋"
- "贪吃蛇，用键盘方向键控制"
- "一个射击游戏，左右移动，空格射击"
- "2048，合并数字"
- "帮我做一个打砖块游戏"

AI 会实时流式生成完整的 HTML5 游戏代码，并直接在页面中渲染。

### 修改游戏

在已生成的游戏基础上，可以直接提修改要求：

- "增加人机对战功能"
- "改成暗黑主题"
- "加快游戏速度"
- "添加计分系统"

### 游戏记忆存档

每次生成新游戏时，系统会自动压缩当前对话为摘要并存入"游戏记忆"。下次输入相同游戏名称时，AI 会召回之前的存档，保留所有已实现的功能。

在 **记忆存档** 页面可以查看所有已保存的游戏。

### 设置

在 **设置** 页面可以清空当前用户的所有游戏记忆存档。

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `OPENAI_API_KEY` | DeepSeek API Key | **必填** |
| `OPENAI_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `OPENAI_MODEL` | 模型名称 | `deepseek-chat` |
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///./game.db` |
| `SECRET_KEY` | JWT 密钥 | `change-me-in-production-please` |
| `REDIS_URL` | Redis 连接（可选） | `redis://localhost:6379/0` |
| `RATE_LIMIT_PER_MINUTE` | 每分钟请求限制 | `10` |
| `RATE_LIMIT_PER_HOUR` | 每小时请求限制 | `100` |

## API 接口

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | `/api/auth/register` | 注册 | 否 |
| POST | `/api/auth/login` | 登录 | 否 |
| POST | `/api/generate-game` | 生成游戏（流式） | 是 |
| GET | `/api/history` | 获取对话历史 | 是 |
| POST | `/api/clear` | 清空对话历史 | 是 |
| GET | `/api/memories/names` | 获取游戏记忆列表 | 是 |
| GET | `/api/memories/search` | 搜索游戏记忆 | 是 |
| POST | `/api/memories/clear` | 清空当前用户记忆 | 是 |
| GET | `/api/health` | 健康检查 | 否 |

## 核心流程

```
用户输入 → 意图判断（game/feature）
                │
        ┌───────┴───────┐
        │               │
      game            feature
        │               │
  压缩对话为摘要     追加到对话
  存入 SQLite +      历史继续
  ChromaDB           生成
        │
  清空对话历史
        │
  语义搜索 ChromaDB
  （余弦相似度 > 0.8）
        │
  召回历史摘要 →
  AI 保留所有已实现功能
  并基于用户需求增强
        │
  流式生成 HTML5 游戏
  实时渲染到 iframe
```

## 常见问题

**Q: 生成游戏时提示 API Key 错误？**

A: 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确，以及 DeepSeek 账户余额是否充足。

**Q: 前端页面打不开？**

A: 确保后端已启动（端口 5001），前端 dev server 已启动（端口 5173）。Vite 会自动代理 `/api` 请求到后端。

**Q: 重新生成游戏时功能丢失？**

A: 系统使用 ChromaDB 语义搜索召回历史游戏摘要。如果修改较大导致相似度低于 0.8，可能无法召回。可以在"记忆存档"页面查看已保存的游戏摘要。

**Q: 如何更换数据库？**

A: 修改 `DATABASE_URL` 环境变量即可，例如使用 PostgreSQL：`postgresql+asyncpg://user:pass@localhost/dbname`
