# 性能优化说明

## 优化概述

本次优化为码途智伴项目引入了多层缓存机制和CPU加速优化，显著提升系统响应速度。

---

## 优化内容

### 1. 依赖更新 (`backend/requirements.txt`)

新增以下性能优化依赖：
- `redis` - 支持Redis缓存
- `orjson` - 超高速JSON解析库
- `msgpack` - 二进制序列化格式
- `uvloop` - 超高速异步事件循环
- `aioredis` - 异步Redis客户端

### 2. 新增缓存服务模块 (`backend/app/core/cache_service.py`)

实现了双层缓存架构：

#### 第一层：内存LRU缓存
- 使用 `cachetools.TTLCache`
- 最大容量：1000项
- 默认TTL：1小时
- 提供极快的读取速度

#### 第二层：Redis缓存
- 可选的持久化缓存
- 支持分布式部署
- 连接失败时自动降级为仅内存缓存

#### 功能特性：
- 缓存键自动生成（使用SHA-256哈希）
- 命名空间隔离
- 缓存命中率统计
- 缓存清空接口
- 自动降级机制

### 3. 配置文件优化 (`config/settings.py`)

新增配置项：
```python
# Redis配置
redis_host: str = "localhost"
redis_port: int = 6379
redis_db: int = 0
redis_password: str = ""
redis_enabled: bool = True
redis_ttl: int = 3600

# 缓存配置
cache_namespace: str = "code_companion"
lru_cache_maxsize: int = 1000
lru_cache_ttl: int = 3600

# 性能优化配置
use_uvloop: bool = True
use_orjson: bool = True
```

### 4. 主应用优化 (`backend/app/main.py`)

- 自动应用 `uvloop` 加速异步I/O
- 启动时初始化缓存系统
- 新增缓存统计接口
- 新增缓存清空接口

### 5. API端点优化 (`backend/app/api/endpoints.py`)

新增接口：
- `GET /api/cache/stats` - 获取缓存统计信息
- `POST /api/cache/clear` - 清空所有缓存

已缓存的接口：
- `/api/grade` - 代码批改结果缓存
- `/api/grade/stream` - 流式批改缓存（检测到缓存时非流式返回）
- `/api/generate/practice` - 练习题生成缓存
- `/api/learning-path` - 学习路径生成缓存

### 6. 诊断智能体优化 (`src/agents/diagnostician.py`)

新增缓存：
- 向量查询结果缓存 (`knowledge_cache`)
- 知识图谱诊断结果缓存 (`kg_cache`)
- 减少重复计算开销

---

## 使用方法

### 启动Redis（可选但推荐）

```bash
# 使用Docker快速启动
docker run -d -p 6379:6379 --name code-companion-redis redis:alpine
```

### 环境变量配置

在 `.env` 文件中可配置：
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_ENABLED=true
CACHE_NAMESPACE=code_companion
USE_UVLOOP=true
USE_ORJSON=true
```

### 验证优化

启动应用后访问：
```
GET http://localhost:8001/api/cache/stats
```

可查看缓存命中情况。

---

## 性能提升

### 预期效果

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首次代码批改 | ~3-5秒 | ~3-5秒 | 相同 |
| 重复代码批改 | ~3-5秒 | <50毫秒 | 60-100倍 |
| 向量查询 | ~100-500毫秒 | ~1-10毫秒 | 10-100倍 |
| 学习路径生成 | ~50毫秒 | <1毫秒 | 50倍 |
| 异步I/O性能 | 基准 | 约2-4倍 | 提升 |

### 缓存命中率

实际场景下预期缓存命中率：
- 开发测试环境：60-80%
- 班级教学场景：40-60%
- 大规模部署：20-40%

---

## 故障降级

### Redis不可用时
- 自动降级为仅内存缓存
- 系统完全正常运行
- 性能仅略微下降

### 依赖库缺失时
- 自动使用标准库替代
- `orjson` → `json`
- `uvloop` → `asyncio`

---

## 监控与管理

### 查看缓存统计
```bash
curl http://localhost:8001/api/cache/stats
```

### 清空缓存
```bash
curl -X POST http://localhost:8001/api/cache/clear
```

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `backend/app/core/cache_service.py` | 缓存服务核心模块（新增） |
| `backend/app/api/endpoints.py` | API端点（已优化） |
| `backend/app/main.py` | 主应用（已优化） |
| `config/settings.py` | 配置文件（已更新） |
| `backend/requirements.txt` | 依赖文件（已更新） |
| `src/agents/diagnostician.py` | 诊断智能体（已优化） |
