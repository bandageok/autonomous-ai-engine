"""FastAPI Server - 完整的API服务器"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

# 存储
_agents = {}
_memory_stores = {}
_task_history = []

# 加载历史记录
def load_tasks():
    global _task_history
    try:
        if os.path.exists(TASKS_FILE):
            import json
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                _task_history = json.load(f)
    except Exception:
        _task_history = []

def save_tasks():
    try:
        import json
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_task_history[-1000:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存任务失败: {e}")

# 启动时加载
load_tasks()

# FastAPI app
app = FastAPI(title="Autonomous AI Engine", version="0.1.4")

# 请求模型
class ThinkRequest(BaseModel):
    prompt: str

class AgentRequest(BaseModel):
    name: str = ""
    model: str = "qwen3:8b"

class MemoryRequest(BaseModel):
    content: str = ""
    type: str = "semantic"
    importance: float = 0.5
    tags: list = []

class ConfigRequest(BaseModel):
    config: dict

# ==================== 基础 ====================

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": "0.1.4"}

@app.get("/api/info")
async def info():
    """服务信息"""
    return {
        "name": "Autonomous AI Engine",
        "version": "0.1.4",
        "modules": list(_agents.keys()),
        "memory_stores": list(_memory_stores.keys())
    }

# ==================== Agent ====================

@app.get("/api/agents")
async def list_agents():
    """列出所有Agent"""
    return {
        "agents": [
            {
                "name": name,
                "state": agent.state,
                "tasks_count": len(agent.tasks)
            }
            for name, agent in _agents.items()
        ]
    }

@app.post("/api/agents")
async def create_agent(req: AgentRequest):
    """创建Agent"""
    name = req.name or f"agent_{len(_agents)}"
    
    from agent import AgentCore
    from llm.provider import OllamaLLM
    
    agent = AgentCore(name)
    provider = OllamaLLM(model=req.model)
    agent.set_llm_provider(provider)
    
    _agents[name] = agent
    
    return {
        "agent_id": name,
        "name": name,
        "model": req.model,
        "status": "created"
    }

@app.post("/api/agents/{name}/think")
async def agent_think(name: str, req: ThinkRequest):
    """Agent思考"""
    if name not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent {name} not found")
    
    agent = _agents[name]
    
    # 检查是否有LLM provider
    if not agent.llm_provider:
        return {"error": "Agent has no LLM provider. Please set model when creating agent."}
    
    result = await agent.think(req.prompt)
    
    # 记录历史
    _task_history.append({
        "agent": name,
        "prompt": req.prompt,
        "result": result,
        "timestamp": datetime.now().isoformat()
    })
    save_tasks()
    
    return {
        "agent": name,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }

@app.delete("/api/agents/{name}")
async def delete_agent(name: str):
    """删除Agent"""
    if name in _agents:
        del _agents[name]
        return {"status": "deleted", "agent": name}
    raise HTTPException(status_code=404, detail=f"Agent {name} not found")

# ==================== Memory ====================

@app.get("/api/memory")
async def list_memories():
    """列出记忆存储"""
    return {"stores": list(_memory_stores.keys())}

@app.post("/api/memory")
async def create_memory_store(req: MemoryRequest):
    """创建记忆存储"""
    name = req.content or f"store_{len(_memory_stores)}"
    
    from agent import MemoryStore
    store = MemoryStore(max_size=1000)
    _memory_stores[name] = store
    
    return {
        "store_id": name,
        "status": "created"
    }

@app.post("/api/memory/{name}/add")
async def add_memory(name: str, req: MemoryRequest):
    """添加记忆"""
    if name not in _memory_stores:
        raise HTTPException(status_code=404, detail=f"Store {name} not found")
    
    from agent import MemoryItem, MemoryType
    
    item = MemoryItem(req.content, req.type, req.importance)
    item.tags = req.tags
    
    _memory_stores[name].add(item)
    
    return {
        "memory_id": item.id,
        "status": "added"
    }

@app.get("/api/memory/{name}/search")
async def search_memory(name: str, q: str = "", tag: str = ""):
    """搜索记忆"""
    if name not in _memory_stores:
        raise HTTPException(status_code=404, detail=f"Store {name} not found")
    
    store = _memory_stores[name]
    
    if tag:
        results = store.search_by_tag(tag)
    else:
        results = store.get_recent(10)
    
    return {
        "store": name,
        "count": len(results),
        "results": [
            {
                "id": r.id,
                "content": r.content[:100],
                "type": r.type,
                "importance": r.importance
            }
            for r in results
        ]
    }

# ==================== Tasks ====================

@app.get("/api/tasks")
async def list_tasks(limit: int = 20):
    """列出任务历史"""
    return {
        "tasks": _task_history[-limit:],
        "total": len(_task_history)
    }

@app.delete("/api/tasks")
async def clear_tasks():
    """清空任务历史"""
    _task_history.clear()
    save_tasks()
    return {"status": "cleared"}

# ==================== Config ====================

@app.get("/api/config")
async def get_config():
    """获取配置"""
    from utils.config import AppConfig
    config = AppConfig()
    return config.to_dict()

@app.post("/api/config")
async def update_config(req: ConfigRequest):
    """更新配置"""
    from utils.config import ConfigManager
    
    mgr = ConfigManager()
    for key, value in req.config.items():
        mgr.set(key, value)
    mgr.save()
    
    return {"status": "updated", "changes": list(req.config.keys())}


if __name__ == "__main__":
    print("Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
