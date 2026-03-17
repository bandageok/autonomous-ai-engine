# Autonomous AI Engine 🧠

[![GitHub stars](https://img.shields.io/github/stars/bandageok/autonomous-ai-engine)](https://github.com/bandageok/autonomous-ai-engine/stargazers)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 概述
完全自主的AI引擎系统，具备自我学习、代码生成、任务规划能力。每日自动从技术趋势中学习并生成高质量代码。

## 架构

```
autonomous-ai-engine/
├── agent/          # 智能体实现 (TaskAgent, Memory, Planner)
├── api/            # RESTful API服务
├── cache/          # LRU缓存
├── context/        # 上下文管理
├── core/           # 核心模块 (重新导出层)
├── db/             # SQLite数据库
├── evaluation/     # 评估系统
├── evolve/         # 自我进化引擎
├── llm/            # LLM模型管理
├── mcp/            # MCP协议
├── monitoring/     # 监控指标
├── multiagent/     # 多智能体系统
├── rag/            # RAG向量检索
├── reasoning/      # 思维链推理
├── sandbox/        # 沙箱执行
├── scheduler/      # 任务调度
├── security/       # 安全分析
├── skills/         # 技能系统
├── tools/          # 工具注册
├── utils/          # 工具函数
├── validation/     # 验证系统
├── webhooks/       # Webhook处理
└── workflow/       # 工作流引擎
```

## 核心模块

| 模块 | 描述 |
|------|------|
| `agent/` | 自主智能体核心实现 |
| `core/` | 核心模块入口 (重新导出 agent) |
| `llm/` | Ollama LLM 管理 |
| `rag/` | 向量检索 + RAG |
| `api/` | FastAPI 服务器 |
| `db/` | SQLite 持久化 |
| `evolve/` | 自我进化与代码修复 |
| `reasoning/` | 思维链推理 (CoT, ToT, ReAct) |

## 安装

```bash
pip install -r requirements.txt

# 安装 Ollama
# 参考: https://github.com/ollama/ollama

# 拉取模型
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

## 快速开始

```python
from agent import AgentCore
from llm import OllamaProvider

# 初始化
agent = AgentCore("assistant")
provider = OllamaProvider(model="qwen3:8b")
agent.set_llm_provider(provider)

# 运行
result = await agent.think("分析这段代码...")
```

## 当前代码行数
**10,000+** 行

## 许可证
MIT

---
*每日自动更新，由AI自主驱动*
