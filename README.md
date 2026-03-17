# 🤖 Autonomous AI Engine

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/bandageok/autonomous-ai-engine)](https://github.com/bandageok/autonomous-ai-engine/stargazers)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-34%20passed-success)](https://github.com/bandageok/autonomous-ai-engine/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)

</div>

---

## 📖 简介

**Autonomous AI Engine** 是一个完全自主的 AI 引擎系统，具备自我学习、代码生成、任务规划能力。系统可以自动从技术趋势中学习并生成高质量代码，是一个万行代码级别的生产级 AI Agent 框架。

### 核心特性

- 🧠 **自主思考** - 基于大模型的推理与规划
- 📚 **持续学习** - RAG 向量检索 + 记忆系统
- 🔧 **代码生成** - 自动生成高质量 Python 代码
- ⚡ **任务调度** - 定时任务与工作流引擎
- 🌐 **API 服务** - FastAPI RESTful 接口
- 🐳 **容器化** - Docker 一键部署

---

## 🏗️ 架构

```
autonomous-ai-engine/
├── agent/          # 智能体核心 (AgentCore, Memory, Planner)
├── core/           # 核心模块重新导出
├── llm/            # LLM 管理 (Ollama, OpenAI)
├── rag/            # RAG 向量检索
├── memory/         # 记忆系统 (向量索引 + 语义搜索)
├── reasoning/      # 思维链推理 (CoT, ToT, ReAct)
├── scheduler/      # 任务调度
├── workflow/       # 工作流引擎
├── api/            # FastAPI 服务
├── db/             # SQLite 持久化
├── context/        # 上下文管理
├── sandbox/        # 沙箱执行
├── security/       # 安全分析
├── evaluation/     # 评估系统
├── evolve/         # 自我进化引擎
├── mcp/            # MCP 协议
├── multiagent/     # 多智能体
├── utils/          # 工具函数
└── tests/          # 单元测试
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/bandageok/autonomous-ai-engine.git
cd autonomous-ai-engine

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Ollama (本地 LLM)
# 参考: https://github.com/ollama/ollama

# 拉取模型
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 2. 使用 CLI

```bash
# 运行智能体
python __main__.py run --prompt "分析这段代码的功能"

# 启动 API 服务
python __main__.py serve --port 8000

# 查看配置
python __main__.py config --show
```

### 3. 使用 Docker

```bash
# 一键启动
docker-compose up

# 或者手动构建
docker build -t autonomous-ai-engine .
docker run -p 8000:8000 autonomous-ai-engine
```

---

## 📦 模块详解

### 🤖 Agent 模块

智能体核心，负责任务执行和决策。

```python
from agent import AgentCore

agent = AgentCore("assistant")
agent.set_llm_provider(OllamaLLM(model="qwen3:8b"))

result = await agent.think("帮我写一个排序算法")
```

### 🧠 Memory 模块

记忆系统，支持向量索引和语义搜索。

```python
from agent import MemoryStore, MemoryItem, MemoryType

store = MemoryStore(max_size=10000)
item = MemoryItem("重要的技术笔记", MemoryType.SEMANTIC)
store.add(item)
```

### 📚 RAG 模块

向量检索 + 混合搜索。

```python
from rag import VectorStore, BM25Retriever, HybridRetriever

store = VectorStore()
store.add("doc1", [0.1, 0.2, ...], {"text": "内容"})
results = store.search(query_vector, top_k=5)
```

### ⚡ Scheduler 模块

任务调度器。

```python
from scheduler import TaskScheduler

scheduler = TaskScheduler()
await scheduler.run()
```

### 🌐 API 模块

FastAPI 服务接口。

```python
from api import APIServer

server = APIServer(host="0.0.0.0", port=8000)
await server.start()
```

---

## ⚡ 优势

### 1. 纯本地部署

- 无需 OpenAI API Key
- 使用 Ollama 本地模型
- 数据完全自主可控

### 2. 模块化设计

- 清晰的模块职责划分
- 支持灵活扩展
- 统一的导入接口

### 3. 生产级质量

- 34 个单元测试
- CI/CD 自动测试
- 类型注解支持

### 4. 多种部署方式

- 本地运行
- Docker 容器
- API 服务

### 5. 持续进化

- 自我学习能力
- 代码自动生成
- 定时任务驱动

---

## 📊 项目统计

| 指标 | 数值 |
|------|------|
| 代码行数 | 10,000+ |
| 模块数量 | 24 |
| 测试数量 | 34 |
| Python 版本 | 3.10+ |

---

## 🔧 配置

### 环境变量

```bash
# .env
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=qwen2.5:7b
API_PORT=8000
LOG_LEVEL=INFO
```

### 配置文件

```json
// config.json
{
  "app_name": "AIEngine",
  "version": "0.1.0",
  "ollama_url": "http://localhost:11434",
  "default_model": "qwen2.5:7b",
  "api_port": 8000
}
```

---

## 🐳 Docker 部署

```yaml
# docker-compose.yml
services:
  ai-engine:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./data:/app/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行覆盖率
pytest tests/ --cov=. --cov-report=html
```

---

## 📝 License

MIT License - 查看 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<div align="center">

**由 AI 自主驱动** 🚀

</div>
