# 码途智伴（CodeCompanion）

> 基于多智能体协作的编程教学 AI 引擎 · v2.2.0

面向高职编程教育的 AI 教学平台，支持编程作业自动批改、苏格拉底式追问辅导、学情分析与个性化学习路径推荐。

**让编程作业批改从数小时缩短到分钟级，为每位学生配备 24 小时在线的 AI 编程导师。**

---

## 目录

- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [登录账号](#登录账号)
- [项目结构](#项目结构)
- [API 概览](#api-概览)
- [测试](#测试)
- [项目亮点](#项目亮点)
- [开源协议](#开源协议)

---

## 核心功能

### 学生端

| 功能 | 说明 |
|------|------|
| 代码编辑器 | Python / Java 语法高亮，多题目切换 |
| 流式批改 | SSE 逐字输出评语，AI 生成扣分明细 |
| 追问辅导 | 苏格拉底式引导，帮助学生自主发现错误 |
| 薄弱点讲解 | 结合知识图谱识别薄弱知识点 |
| 学习路径 | 基于知识图谱的个性化推荐 |
| 练习推送 | AI 生成专项练习，一键开始 |
| 语音交互 | 支持语音提问 |
| 学习档案 | 能力雷达图、成绩趋势、知识点掌握树 |
| 代码草稿 | 自动保存至后端数据库，跨设备恢复 |

### 教师端

| 功能 | 说明 |
|------|------|
| 多班级管理 | 创建 / 切换班级，数据按班级隔离 |
| 批量批改 | 上传 ZIP 包，一键批改全班作业 |
| 数据驾驶舱 | 成绩分布、高频错误、薄弱知识点热力图 |
| 抄袭检测 | AST 指纹 + 序列比对的相似度分析 |
| 知识图谱 | 错误 → 知识点 → 前置知识，可视化诊断链路 |
| 教案生成 | 根据批改结果自动生成复习教案 |
| 沙箱测试 | Python 受限执行 + Docker OpenJDK 运行 Java |
| 实时更新 | WebSocket 推送成绩提交等事件 |
| 一键导出 | 成绩表 Excel / CSV / JSON，代码包 ZIP |

---

## 技术架构

```
┌──────────────────────────────────────────────────────────┐
│  前端  Vue 3 + Vite + Element Plus + CodeMirror + ECharts │
├──────────────────────────────────────────────────────────┤
│  后端  FastAPI + SQLAlchemy + SQLite + JWT 认证           │
├─────────────┬─────────────┬──────────────────────────────┤
│ 诊断智能体   │  导师智能体  │  协调器 Coordinator          │
├─────────────┴─────────────┴──────────────────────────────┤
│  知识图谱 + ChromaDB 向量检索 + LRU / Redis 双层缓存       │
├──────────────────────────────────────────────────────────┤
│  智谱 GLM-4-Flash（云端）  /  Ollama · Qwen（本地降级）    │
└──────────────────────────────────────────────────────────┘
```

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3、Vite、Element Plus、CodeMirror、ECharts |
| 后端 | FastAPI、SQLAlchemy、SQLite、JWT（bcrypt） |
| 智能体 | Diagnostician（诊断）、Tutor（导师）、Coordinator（协调） |
| 知识库 | 内置编程知识图谱 + ChromaDB + Sentence Transformers |
| 大模型 | 智谱 AI（默认）/ Ollama 本地模型（可选） |
| 缓存 | 内存 LRU + Redis（可选，见 `PERFORMANCE_OPTIMIZATION.md`） |
| 沙箱 | RestrictedPython（Python）/ Docker `eclipse-temurin:17-jdk`（Java） |
| 实时通信 | WebSocket（成绩推送、连接保活） |
| 可观测性 | 结构化日志（`logs/`）+ 错误持久化（`error_logs` 表） |
| 扩展 | Coze 评分规则（可选）、Dify 工作流平台（仓库内附带，非必需） |

---

## 快速开始

### 环境要求

| 依赖 | 版本 / 说明 | 必需 |
|------|-------------|------|
| Python | 3.10+ | 是 |
| Node.js | 18+ | 是 |
| 智谱 API Key | `ZHIPU_API_KEY` | 推荐（云端批改） |
| Docker Desktop | Java 沙箱镜像 `eclipse-temurin:17-jdk` | 推荐 |
| Ollama | 模型 `qwen2.5:7b`，离线降级 | 可选 |
| Redis | 分布式缓存 | 可选 |

### 方式一：一键启动（Windows）

```bash
双击 start.bat
```

脚本将自动创建虚拟环境、安装依赖、启动前后端并打开浏览器。

### 方式二：手动启动

**1. 配置环境变量**

在项目根目录创建 `.env`（参考下方[配置说明](#配置说明)）。

**2. 启动后端**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

**3. 启动前端**（新终端）

```bash
cd frontend
npm install
npm run dev
```

**4. 访问应用**

| 入口 | 地址 |
|------|------|
| 学生端 | http://localhost:5173 |
| 教师端 | http://localhost:5173/admin |
| API 文档 | http://localhost:8001/docs |
| 健康检查 | http://localhost:8001/api/health |

### 构建知识库（首次可选）

```bash
python build_knowledge_base.py
```

向 `kb_data/` 写入 Python 错误模式与示例向量，供诊断智能体检索使用。

> **注意**：若从旧版本升级，请删除 `backend/app.db` 后重启后端，以应用新的用户密码哈希与数据表结构。

---

## 配置说明

在项目根目录 `.env` 中配置（变量名不区分大小写）：

```env
# 大模型
ZHIPU_API_KEY=你的智谱API密钥
USE_LOCAL_MODEL=false
LOCAL_MODEL_NAME=qwen2.5:7b
LOCAL_MODEL_URL=http://localhost:11434/api/generate

# 认证（生产环境务必修改）
JWT_SECRET=your-production-secret

# Java 沙箱
DOCKER_JAVA_ENABLED=true
DOCKER_JAVA_IMAGE=eclipse-temurin:17-jdk
DOCKER_JAVA_TIMEOUT=10

# 缓存（可选）
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379

# 日志
LOG_DIR=./logs
LOG_LEVEL=INFO
```

---

## 登录账号

账号由后端数据库初始化（`backend/app/core/init_db.py`），通过 `POST /api/login` 获取 JWT 令牌。

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 学生 | `2024001` | `123456` |
| 学生 | `2024002` | `123456` |
| 学生 | `2024003` | `123456` |
| 教师 | `admin` | `admin123` |

前端将 Token 保存在 `sessionStorage`，业务数据（成绩、班级、草稿等）均存储于后端 SQLite，不再依赖 `localStorage`。

---

## 项目结构

```
CodeCompanion/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints.py          # 核心业务 API（批改、沙箱、成绩等）
│   │   │   ├── auth_routes.py        # 登录 / 用户信息
│   │   │   ├── draft_routes.py       # 代码草稿、错误上报
│   │   │   └── websocket_routes.py   # WebSocket 连接
│   │   ├── core/
│   │   │   ├── agents/               # 多智能体
│   │   │   ├── auth.py               # JWT 与密码哈希
│   │   │   ├── knowledge/            # 编程知识图谱
│   │   │   ├── languages/            # Python / Java 解析
│   │   │   ├── plagiarism/           # 抄袭检测
│   │   │   ├── sandbox/              # Python 受限执行 + Docker Java
│   │   │   ├── websocket/            # 连接管理器
│   │   │   ├── monitoring/           # 错误追踪
│   │   │   ├── middleware/           # 请求日志中间件
│   │   │   └── cache_service.py      # 双层缓存
│   │   ├── models/                   # Pydantic 与 ORM 模型
│   │   └── main.py                   # 应用入口
│   ├── tests/                        # 单元测试（pytest）
│   └── requirements.txt
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── views/                    # 学生端 / 教师端页面
│   │   ├── components/               # 编辑器、辅导聊天等
│   │   ├── api/                      # Axios 封装（含 Token 拦截）
│   │   ├── store/                    # 状态管理
│   │   ├── composables/              # WebSocket 等组合式函数
│   │   └── router/                   # 路由（懒加载 + 代码分割）
│   ├── e2e/                          # Playwright E2E 测试
│   └── package.json
├── config/
│   └── settings.py                   # 全局配置（读取 .env）
├── build_knowledge_base.py           # 知识库构建脚本
├── docker-compose.yml                # Docker 沙箱参考配置
├── kb_data/                          # ChromaDB 持久化目录
├── logs/                             # 应用日志（运行时生成）
├── start.bat / stop.bat              # 启停脚本
└── README.md
```

---

## API 概览

### 认证与数据

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/login` | 登录，返回 JWT |
| `GET` | `/api/me` | 获取当前用户信息 |
| `GET/POST` | `/api/grades` | 查询 / 保存成绩 |
| `PUT` | `/api/drafts` | 保存代码草稿 |
| `GET` | `/api/drafts/{question_id}` | 读取代码草稿 |

### 教学核心

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/grade/stream` | 流式代码批改（SSE） |
| `POST` | `/api/tutor/stream` | 流式追问辅导 |
| `POST` | `/api/learning-path` | 个性化学习路径 |
| `POST` | `/api/generate/practice` | 生成专项练习 |
| `POST` | `/api/sandbox/execute` | 沙箱代码执行 |

### 运维与监控

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/ollama/status` | 本地模型状态 |
| `POST` | `/api/model/toggle` | 切换云端 / 本地模型 |
| `POST` | `/api/errors/report` | 前端错误上报 |
| `GET` | `/api/errors` | 错误日志（管理员） |
| `WS` | `/ws?token=<JWT>` | WebSocket 实时推送 |

完整接口文档：启动后端后访问 http://localhost:8001/docs

---

## 测试

### 后端单元测试

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

覆盖：认证、沙箱（Python / Docker Java）、成绩保存、代码草稿等。

### 前端 E2E 测试

```bash
cd frontend
npm install
npx playwright install chromium
npm run test:e2e
```

---

## 项目亮点

- **AI for AI 开发模式**：项目开发过程中充分发挥生成式AI的辅助作用，从提示词工程设计到后端API实现，全程采用"AI生成+人工审核"模式，体现了AI赋能软件开发的典型实践
- **多智能体协作**：诊断 → 评价 → 辅导，协调器编排完整批改流程
- **编程知识图谱**：错误模式 → 知识点 → 前置知识，可追溯诊断链路
- **云端 + 本地双模型**：智谱 GLM 在线推理，网络不可用时自动切换 Ollama 本地模型（支持 Qwen2.5-7B 量化版本），确保离线环境下教学连续性
- **双层缓存**：LRU 内存 + 可选 Redis，降低重复批改延迟
- **安全沙箱**：Python 受限执行；Java 在 Docker 隔离环境中编译运行
- **后端一体化**：JWT 认证、SQLite 持久化、WebSocket 实时推送、错误监控
- **教学闭环**：批改 → 辅导 → 练习 → 学习路径 → 教案生成
- **便携部署**：`start.bat` 一键启动，适合课堂演示与 U 盘便携版

---

## 开源协议

MIT License

---

**作者**：杨嘉燕

让每一位学生拥有 AI 编程导师，让每一位教师拥有数据驱动教学能力。
