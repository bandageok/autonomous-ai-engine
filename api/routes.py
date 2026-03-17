"""API Routes - 完整的API路由实现"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict, Any

# 存储
_agents = {}
_memory_stores = {}
_task_history = []


def create_routes(server):
    """创建API路由"""
    
    # ==================== 基础 ====================
    
    @server.route("/health", "GET")
    async def health(request):
        """健康检查"""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.4"
        }
        
    @server.route("/api/info", "GET")
    async def info(request):
        """服务信息"""
        return {
            "name": "Autonomous AI Engine",
            "version": "0.1.4",
            "modules": list(_agents.keys()),
            "memory_stores": list(_memory_stores.keys())
        }
    
    # ==================== Agent ====================
    
    @server.route("/api/agents", "GET")
    async def list_agents(request):
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
    
    @server.route("/api/agents", "POST")
    async def create_agent(request):
        """创建Agent"""
        body = request.body or {}
        name = body.get("name", f"agent_{len(_agents)}")
        model = body.get("model", "qwen3:8b")
        
        from agent import AgentCore
        from llm.provider import OllamaLLM
        
        agent = AgentCore(name)
        provider = OllamaLLM(model=model)
        agent.set_llm_provider(provider)
        
        _agents[name] = agent
        
        return {
            "agent_id": name,
            "name": name,
            "model": model,
            "status": "created"
        }
    
    @server.route("/api/agents/{name}/think", "POST")
    async def agent_think(request):
        """Agent思考"""
        name = request.path.split("/")[-2]  # 简单解析
        body = request.body or {}
        prompt = body.get("prompt", "")
        
        if name not in _agents:
            return {"error": f"Agent {name} not found"}, 404
        
        agent = _agents[name]
        result = await agent.think(prompt)
        
        # 记录历史
        _task_history.append({
            "agent": name,
            "prompt": prompt,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "agent": name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    @server.route("/api/agents/{name}", "DELETE")
    async def delete_agent(request):
        """删除Agent"""
        name = request.path.split("/")[-1]
        
        if name in _agents:
            del _agents[name]
            return {"status": "deleted", "agent": name}
        return {"error": f"Agent {name} not found"}, 404
    
    # ==================== Memory ====================
    
    @server.route("/api/memory", "GET")
    async def list_memories(request):
        """列出记忆存储"""
        return {
            "stores": list(_memory_stores.keys())
        }
    
    @server.route("/api/memory", "POST")
    async def create_memory_store(request):
        """创建记忆存储"""
        body = request.body or {}
        name = body.get("name", f"store_{len(_memory_stores)}")
        max_size = body.get("max_size", 1000)
        
        from agent import MemoryStore
        store = MemoryStore(max_size=max_size)
        _memory_stores[name] = store
        
        return {
            "store_id": name,
            "max_size": max_size,
            "status": "created"
        }
    
    @server.route("/api/memory/{name}/add", "POST")
    async def add_memory(request):
        """添加记忆"""
        name = request.path.split("/")[-2]
        body = request.body or {}
        
        if name not in _memory_stores:
            return {"error": f"Store {name} not found"}, 404
        
        from agent import MemoryItem, MemoryType
        
        content = body.get("content", "")
        memory_type = body.get("type", "semantic")
        importance = body.get("importance", 0.5)
        
        item = MemoryItem(content, memory_type, importance)
        
        # 添加标签
        tags = body.get("tags", [])
        if tags:
            item.tags = tags
        
        _memory_stores[name].add(item)
        
        return {
            "memory_id": item.id,
            "status": "added"
        }
    
    @server.route("/api/memory/{name}/search", "GET")
    async def search_memory(request):
        """搜索记忆"""
        name = request.path.split("/")[-2]
        query = request.query_params.get("q", "")
        tag = request.query_params.get("tag", "")
        
        if name not in _memory_stores:
            return {"error": f"Store {name} not found"}, 404
        
        store = _memory_stores[name]
        
        if tag:
            results = store.search_by_tag(tag)
        else:
            # 简单返回最近的
            results = store.get_recent(10)
        
        return {
            "store": name,
            "count": len(results),
            "results": [
                {
                    "id": r.id,
                    "content": r.content[:100],  # 截断
                    "type": r.type,
                    "importance": r.importance
                }
                for r in results
            ]
        }
    
    # ==================== Tasks ====================
    
    @server.route("/api/tasks", "GET")
    async def list_tasks(request):
        """列出任务历史"""
        limit = int(request.query_params.get("limit", 20))
        return {
            "tasks": _task_history[-limit:],
            "total": len(_task_history)
        }
    
    @server.route("/api/tasks", "DELETE")
    async def clear_tasks(request):
        """清空任务历史"""
        _task_history.clear()
        return {"status": "cleared"}
    
    # ==================== Config ====================
    
    @server.route("/api/config", "GET")
    async def get_config(request):
        """获取配置"""
        from utils.config import AppConfig
        config = AppConfig()
        return config.to_dict()
    
    @server.route("/api/config", "POST")
    async def update_config(request):
        """更新配置"""
        body = request.body or {}
        from utils.config import ConfigManager
        
        mgr = ConfigManager()
        for key, value in body.items():
            mgr.set(key, value)
        mgr.save()
        
        return {"status": "updated", "changes": list(body.keys())}
