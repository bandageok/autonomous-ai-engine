# Autonomous AI Engine

一个可以自己学习、生成代码、做任务规划的 AI 系统。支持本地部署，通过 API 或命令行使用。

## 特性

- 基于大模型的推理和规划能力
- 向量检索 + 记忆系统
- 定时任务和工作流
- RESTful API 接口
- Docker 部署

## 安装

```bash
git clone https://github.com/bandageok/autonomous-ai-engine.git
cd autonomous-ai-engine
pip install -r requirements.txt
```

需要先装好 [Ollama](https://github.com/ollama/ollama) 和模型：

```bash
ollama pull qwen3:8b
```

## 使用

命令行：

```bash
# 运行智能体
python __main__.py run --prompt "写个排序算法"

# 启动服务
python __main__.py serve --port 8000

# 查看配置
python __main__.py config --show
```

Docker：

```bash
docker-compose up
```

## 模块

| 模块 | 用途 |
|------|------|
| agent | 智能体核心 |
| memory | 记忆存储 |
| rag | 向量检索 |
| scheduler | 任务调度 |
| api | HTTP 接口 |
| db | 数据持久化 |

## 配置

环境变量或 `config.json`：

```json
{
  "ollama_url": "http://localhost:11434",
  "default_model": "qwen2.5:7b",
  "api_port": 8000
}
```

## 测试

```bash
pytest tests/ -v
```

## 部署

Docker 一键启动：

```bash
docker-compose up -d
```

或手动构建：

```bash
docker build -t ai-engine .
docker run -p 8000:8000 ai-engine
```

---

有问题欢迎提 Issue。
