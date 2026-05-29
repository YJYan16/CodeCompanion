# 码途智伴 — 基于多智能体协作的编程教学 AI 引擎

## 项目简介

**码途智伴**（CodeCompanion）是一款面向高职编程教育的 AI 教学平台，基于国产大模型与多智能体协作框架，实现编程作业自动批改、苏格拉底式追问辅导、学情分析与个性化学习路径推荐。

> 让编程作业批改从数小时缩短到分钟级，为每位学生配备 24 小时在线的 AI 编程导师。

**当前版本**：v2.2.0

---

## 核心功能

### 学生端

- **代码编辑器**：支持 Python / Java，语法高亮，多题目切换
- **流式批改**：提交代码后逐字输出评语，AI 生成扣分明细
- **追问辅导**：苏格拉底式追问，引导学生自主发现错误
- **薄弱知识点讲解**：结合知识图谱识别薄弱点，提供针对性讲解
- **个性化学习路径**：基于知识图谱生成学习路径推荐
- **练习推送**：AI 生成专项练习，一键开始
- **语音交互**：支持语音提问，降低使用门槛
- **学习档案**：能力雷达图、成绩趋势、知识点掌握树

### 教师端

- **多班级管理**：创建 / 切换班级，数据隔离
- **批量批改**：上传 ZIP 包，一键批改全班作业
- **数据驾驶舱**：成绩分布、高频错误、薄弱知识点热力图
- **抄袭检测**：AST 指纹 + 序列比对的代码相似度分析
- **知识图谱**：错误 → 知识点 → 前置知识的诊断链路可视化
- **教案生成**：根据批改结果自动生成复习教案
- **沙箱测试**：Python 受限执行环境 + Java 本地编译运行
- **一键导出**：成绩表 Excel / CSV / JSON，代码包 ZIP 下载

---

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│  前端层                                              │
│  Vue 3 + Vite + Element Plus + CodeMirror + ECharts │
├─────────────────────────────────────────────────────┤
│  后端层                                              │
│  FastAPI + SQLite + 多智能体协作框架                 │
├──────────────┬──────────────┬───────────────────────┤
│  诊断智能体   │  评价 / 导师  │  协调器 Coordinator   │
├──────────────┴──────────────┴───────────────────────┤
│  编程知识图谱 + ChromaDB 向量检索 + LRU / Redis 缓存  │
├─────────────────────────────────────────────────────┤
│  大模型层                                            │
│  智谱 GLM-4-Flash（云端）+ Ollama / Qwen（本地降级）  │
└─────────────────────────────────────────────────────┘
```

| 模块 | 技术选型 |
|------|----------|
| 前端 | Vue 3、Vite、Element Plus、CodeMirror、ECharts |
| 后端 | FastAPI、SQLAlchemy、SQLite |
| 智能体 | 诊断（Diagnostician）、导师（Tutor）、协调器（Coordinator） |
| 知识库 | 内置知识图谱 + ChromaDB + Sentence Transformers |
| 大模型 | 智谱 AI（默认）/ Ollama 本地模型（可选） |
| 缓存 | 内存 LRU + Redis（可选，详见 `PERFORMANCE_OPTIMIZATION.md`） |
| 扩展集成 | Coze 评分规则生成（可选）、Dify 工作流（仓库内附带） |

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- （可选）智谱 API Key：`ZHIPU_API_KEY`
- （可选）Ollama + `qwen2.5:7b`，用于离线 / 降级推理
- （可选）Docker Desktop，用于 Java 沙箱（`eclipse-temurin:17-jdk` 镜像）
- （可选）Redis，用于分布式缓存

### 一键启动（Windows，推荐）

```bash
双击 start.bat
```

脚本会自动创建虚拟环境、安装依赖、启动前后端，并打开浏览器。

### 手动启动

**1. 配置环境变量（项目根目录创建 `.env`）**

```env
ZHIPU_API_KEY=你的智谱API密钥
USE_LOCAL_MODEL=false
LOCAL_MODEL_NAME=qwen2.5:7b
LOCAL_MODEL_URL=http://localhost:11434/api/generate
REDIS_ENABLED=false
JWT_SECRET=your-secret-key
DOCKER_JAVA_IMAGE=eclipse-temurin:17-jdk
DOCKER_JAVA_ENABLED=true
```

**2. 启动后端**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

**3. 启动前端（新终端）**

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

### 构建知识库（首次可选）

```bash
python build_knowledge_base.py
```

将向 `kb_data/` 写入 Python 错误模式与示例向量，供诊断智能体检索使用。

---

## 登录账号

前端采用预设账号（见 `frontend/src/store/auth.js`）：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 学生 | `2024001` | `123456` |
| 学生 | `2024002` | `123456` |
| 学生 | `2024003` | `123456` |
| 教师 | `admin` | `admin123` |

---

## 项目结构

```
CodeCompanion/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── api/endpoints.py        # REST / SSE API
│   │   ├── core/
│   │   │   ├── agents/             # 多智能体（诊断、导师、协调器等）
│   │   │   ├── knowledge/          # 编程知识图谱
│   │   │   ├── languages/          # Python / Java 解析
│   │   │   ├── plagiarism/         # 抄袭检测
│   │   │   ├── sandbox/            # Python 受限执行
│   │   │   ├── coze/               # Coze 集成
│   │   │   └── cache_service.py    # 双层缓存
│   │   ├── models/                 # Pydantic 与数据库模型
│   │   └── main.py                 # 应用入口
│   └── requirements.txt
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── views/                  # 学生端 / 教师端页面
│   │   ├── components/             # 编辑器、辅导聊天等组件
│   │   ├── api/                    # 接口封装
│   │   ├── store/                  # 状态管理
│   │   └── router/                 # 路由
│   └── package.json
├── config/
│   └── settings.py                 # 全局配置（读取 .env）
├── dify/                           # 附带的 Dify 开源工作流平台（可选）
├── build_knowledge_base.py         # 知识库构建脚本
├── kb_data/                        # ChromaDB 持久化目录
├── start.bat                       # 一键启动
├── stop.bat                        # 停止服务
├── pyproject.toml
└── README.md
```

---

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/grade/stream` | 流式代码批改（SSE） |
| `POST` | `/api/tutor/stream` | 流式追问辅导 |
| `POST` | `/api/learning-path` | 个性化学习路径 |
| `POST` | `/api/generate/practice` | 生成专项练习 |
| `POST` | `/api/sandbox/execute` | 沙箱代码执行 |
| `GET` | `/api/ollama/status` | 检查本地模型状态 |
| `POST` | `/api/model/toggle` | 切换云端 / 本地模型 |
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/errors` | 错误日志（管理员） |
| `WS` | `/ws?token=...` | WebSocket 实时推送 |

---

## 测试

```bash
# 后端单元测试
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v

# 前端 E2E 测试（需先安装依赖）
cd frontend
npm install
npx playwright install chromium
npm run test:e2e
```

---

## 项目亮点

- **多智能体协作**：诊断智能体分析代码错误，大模型完成评价与辅导，协调器编排完整流程
- **编程知识图谱**：错误模式 → 知识点 → 前置知识的可追溯诊断链路
- **云端 + 本地双模型**：智谱 GLM 在线推理，网络不可用时可切换 Ollama 本地模型
- **双层缓存**：LRU 内存缓存 + 可选 Redis，显著降低重复批改延迟
- **教学闭环**：批改 → 辅导 → 练习 → 学习路径 → 教案生成
- **多语言支持**：Python / Java 双语言批改与沙箱执行
- **便携部署**：`start.bat` 一键启动，适合课堂演示与 U 盘便携版

---

## 开源协议

MIT License

---

**作者**：杨嘉燕

让每一位学生拥有 AI 编程导师，让每一位教师拥有数据驱动教学能力。
