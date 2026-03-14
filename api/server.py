"""API Server - API服务"""
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import asyncio

class HTTPMethod:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class Response:
    """HTTP响应"""
    def __init__(self, status_code: int = 200, data: Any = None, error: Optional[str] = None):
        self.status_code = status_code
        self.data = data
        self.error = error
        
    def to_dict(self):
        return {"status": self.status_code, "data": self.data, "error": self.error}
        
    def to_json(self):
        return json.dumps(self.to_dict())

class Request:
    """HTTP请求"""
    def __init__(self, method: str, path: str, headers: Dict = None, body: Any = None, query_params: Dict = None):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.body = body
        self.query_params = query_params or {}
        self.context: Dict = {}

class Route:
    """路由"""
    def __init__(self, path: str, method: str, handler: Callable):
        self.path = path
        self.method = method
        self.handler = handler

class Middleware:
    """中间件"""
    def __init__(self, name: str):
        self.name = name
        
    async def process(self, request: Request, next_handler: Callable):
        return await next_handler(request)

class APIServer:
    """API服务器"""
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.routes: List[Route] = []
        self.middlewares: List[Middleware] = []
        
    def route(self, path: str, method: str = "GET"):
        """路由装饰器"""
        def decorator(func):
            self.routes.append(Route(path, method, func))
            return func
        return decorator
        
    def use(self, middleware: Middleware):
        """添加中间件"""
        self.middlewares.append(middleware)
        
    async def handle_request(self, request: Request) -> Response:
        """处理请求"""
        # 查找路由
        for r in self.routes:
            if r.path == request.path and r.method == request.method:
                try:
                    if asyncio.iscoroutinefunction(r.handler):
                        return await r.handler(request)
                    else:
                        return r.handler(request)
                except Exception as e:
                    return Response(500, error=str(e))
        return Response(404, error="Not Found")
        
    async def start(self):
        """启动服务器"""
        print(f"API Server started at {self.host}:{self.port}")
        
    async def stop(self):
        """停止服务器"""
        print("API Server stopped")

class Router:
    """路由器"""
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.routes = []
        
    def add_route(self, path: str, method: str, handler: Callable):
        full_path = self.prefix + path
        self.routes.append(Route(full_path, method, handler))
        
    def get_routes(self):
        return self.routes
