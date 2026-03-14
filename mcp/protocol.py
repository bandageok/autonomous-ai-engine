"""MCP Protocol - Model Context Protocol实现"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import aiohttp

class MCPMessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class MCPMethod(Enum):
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_RENDER = "prompts/render"

@dataclass
class MCPMessage:
    """MCP消息"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Dict = field(default_factory=dict)
    result: Any = None
    error: Optional[Dict] = None

@dataclass
class MCPTool:
    """MCP工具"""
    name: str
    description: str
    input_schema: Dict

@dataclass
class MCPResource:
    """MCP资源"""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"

@dataclass
class MCPPrompt:
    """MCP提示"""
    name: str
    description: str
    arguments: List[Dict] = field(default_factory=list)

class MCPClient:
    """MCP客户端"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.capabilities: Dict = {}
        self.server_info: Dict = {}
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.prompts: List[MCPPrompt] = []
        
    async def connect(self):
        """连接服务器"""
        # 初始化
        response = await self.send_request(MCPMethod.INITIALIZE.value, {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        })
        
        if response and "result" in response:
            self.server_info = response["result"].get("serverInfo", {})
            self.capabilities = response["result"].get("capabilities", {})
            
        # 获取工具列表
        await self.refresh_tools()
        
        # 获取资源列表
        await self.refresh_resources()
        
        # 获取提示列表
        await self.refresh_prompts()
        
    async def send_request(self, method: str, params: Dict = None) -> Optional[Dict]:
        """发送请求"""
        message = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or {}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.server_url, json=message) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"MCP request error: {e}")
            
        return None
        
    async def refresh_tools(self):
        """刷新工具列表"""
        response = await self.send_request(MCPMethod.TOOLS_LIST.value)
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            self.tools = [MCPTool(**t) for t in tools]
            
    async def refresh_resources(self):
        """刷新资源列表"""
        response = await self.send_request(MCPMethod.RESOURCES_LIST.value)
        if response and "result" in response:
            resources = response["result"].get("resources", [])
            self.resources = [MCPResource(**r) for r in resources]
            
    async def refresh_prompts(self):
        """刷新提示列表"""
        response = await self.send_request(MCPMethod.PROMPTS_LIST.value)
        if response and "result" in response:
            prompts = response["result"].get("prompts", [])
            self.prompts = [MCPPrompt(**p) for p in prompts]
            
    async def call_tool(self, tool_name: str, arguments: Dict = None) -> Any:
        """调用工具"""
        response = await self.send_request(MCPMethod.TOOLS_CALL.value, {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        if response and "result" in response:
            return response["result"].get("content", [])
        return None
        
    async def read_resource(self, uri: str) -> Optional[str]:
        """读取资源"""
        response = await self.send_request(MCPMethod.RESOURCES_READ.value, {
            "uri": uri
        })
        
        if response and "result" in response:
            contents = response["result"].get("contents", [])
            if contents:
                return contents[0].get("text", "")
        return None
        
    async def render_prompt(self, prompt_name: str, arguments: Dict = None) -> Optional[str]:
        """渲染提示"""
        response = await self.send_request(MCPMethod.PROMPTS_RENDER.value, {
            "name": prompt_name,
            "arguments": arguments or {}
        })
        
        if response and "result" in response:
            messages = response["result"].get("messages", [])
            if messages:
                return messages[0].get("content", {}).get("text", "")
        return None

class MCPServer:
    """MCP服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.capabilities: Dict = {}
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, str] = {}
        self.prompts: Dict[str, Dict] = {}
        self.request_handlers: Dict[str, Callable] = {}
        
        self._init_handlers()
        
    def _init_handlers(self):
        """初始化处理器"""
        self.request_handlers = {
            MCPMethod.INITIALIZE.value: self._handle_initialize,
            MCPMethod.TOOLS_LIST.value: self._handle_tools_list,
            MCPMethod.TOOLS_CALL.value: self._handle_tools_call,
            MCPMethod.RESOURCES_LIST.value: self._handle_resources_list,
            MCPMethod.RESOURCES_READ.value: self._handle_resources_read,
            MCPMethod.PROMPTS_LIST.value: self._handle_prompts_list,
            MCPMethod.PROMPTS_RENDER.value: self._handle_prompts_render,
        }
        
    def register_tool(self, name: str, description: str, handler: Callable, input_schema: Dict = None):
        """注册工具"""
        self.tools[name] = handler
        
    def register_resource(self, uri: str, content: str, name: str = "", mime_type: str = "text/plain"):
        """注册资源"""
        self.resources[uri] = content
        
    def register_prompt(self, name: str, template: str, description: str = "", arguments: List[Dict] = None):
        """注册提示"""
        self.prompts[name] = {
            "template": template,
            "description": description,
            "arguments": arguments or []
        }
        
    async def _handle_initialize(self, params: Dict) -> Dict:
        """处理初始化"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": "mcp-server",
                "version": "1.0.0"
            }
        }
        
    async def _handle_tools_list(self, params: Dict) -> Dict:
        """处理工具列表"""
        tools = [
            {
                "name": name,
                "description": f"Tool: {name}",
                "inputSchema": {"type": "object", "properties": {}}
            }
            for name in self.tools.keys()
        ]
        return {"tools": tools}
        
    async def _handle_tools_call(self, params: Dict) -> Dict:
        """处理工具调用"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name not in self.tools:
            return {"error": {"code": -32601, "message": f"Tool not found: {name}"}}
            
        handler = self.tools[name]
        
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)
                
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        except Exception as e:
            return {"error": {"code": -32603, "message": str(e)}}
            
    async def _handle_resources_list(self, params: Dict) -> Dict:
        """处理资源列表"""
        resources = [
            {
                "uri": uri,
                "name": name or uri,
                "description": f"Resource: {uri}",
                "mimeType": "text/plain"
            }
            for uri, content in self.resources.items()
        ]
        return {"resources": resources}
        
    async def _handle_resources_read(self, params: Dict) -> Dict:
        """处理资源读取"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return {"error": {"code": -32601, "message": f"Resource not found: {uri}"}}
            
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": self.resources[uri]
                }
            ]
        }
        
    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """处理提示列表"""
        prompts = [
            {
                "name": name,
                "description": data["description"],
                "arguments": data.get("arguments", [])
            }
            for name, data in self.prompts.items()
        ]
        return {"prompts": prompts}
        
    async def _handle_prompts_render(self, params: Dict) -> Dict:
        """处理提示渲染"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name not in self.prompts:
            return {"error": {"code": -32601, "message": f"Prompt not found: {name}"}}
            
        template = self.prompts[name]["template"]
        
        # 简单模板替换
        for key, value in arguments.items():
            template = template.replace(f"{{{key}}}", str(value))
            
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": template
                    }
                }
            ]
        }
        
    async def handle_message(self, message: Dict) -> Dict:
        """处理消息"""
        method = message.get("method")
        params = message.get("params", {})
        
        handler = self.request_handlers.get(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
            
        try:
            result = await handler(params)
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": str(e)}
            }

class MCPClientPool:
    """MCP客户端池"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        
    async def add_client(self, name: str, server_url: str):
        """添加客户端"""
        client = MCPClient(server_url)
        await client.connect()
        self.clients[name] = client
        
    def get_client(self, name: str) -> Optional[MCPClient]:
        """获取客户端"""
        return self.clients.get(name)
        
    async def call_tool(self, client_name: str, tool_name: str, **kwargs) -> Any:
        """调用工具"""
        client = self.get_client(client_name)
        if not client:
            raise ValueError(f"Client not found: {client_name}")
        return await client.call_tool(tool_name, kwargs)
        
    def list_tools(self) -> Dict[str, List[MCPTool]]:
        """列出所有工具"""
        return {
            name: client.tools 
            for name, client in self.clients.items()
        }
