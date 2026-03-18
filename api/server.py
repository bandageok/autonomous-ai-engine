import uvicorn
from api.fastapi_server import app

if __name__ == "__main__":
    print("Starting FastAPI server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)

```python
import asyncio
import aiohttp
from aiohttp import web
import jwt
import json
import datetime
import uuid
from typing import Optional, Dict, Any, List, Tuple, AsyncGenerator, Callable, Awaitable
from functools import wraps
import time
import hashlib
import logging

logging.basicConfig(level=logging.INFO)

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, client_ip: str) -> bool:
        async with self.lock:
            current_time = time.time()
            if client_ip not in self.requests:
                self.requests[client_ip] = []
            self.requests[client_ip] = [t for t in self.requests[client_ip] if current_time - t < self.window_seconds]
            
            if len(self.requests[client_ip]) >= self.max_requests:
                return False
            self.requests[0].append(current_time)
            return True

class CacheManager:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Any] = {}
        self.lock = asyncio.Lock()

    async def get_cache(self, key: str) -> Optional[Any]:
        async with self.lock:
            if key in self.cache:
                if time.time() - self.cache[key]["timestamp"] < self.ttl_seconds:
                    return self.cache[key]["value"]
                del self.cache[key]
        return None

    async def set_cache(self, key: str, value: Any) -> None:
        async with self.lock:
            self.cache[key] = {
                "value": value,
                "timestamp": time.time()
            }

class AuthMiddleware:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    async def __call__(self, request: web.Request, handler: Callable[[web.Request], Awaitable[web.Response]]) -> web.Response:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return web.json_response({"error": "Missing or invalid token"}, status=401)
        
        token = auth_header.split("Bearer ")[1]
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            request["user"] = payload
            return await handler(request)
        except jwt.ExpiredSignatureError:
            return web.json_response({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return web.json_response({"error": "Invalid token"}, status=401)

class APIVersionMiddleware:
    def __init__(self, default_version: str = "v1"):
        self.default_version = default_version

    async def __call__(self, request: web.Request, handler: Callable[[web.Request], Awaitable[web.Response]]) -> web.Response:
        version = request.match_info.get("version", self.default_version)
        request["version"] = version
        return await handler(request)

class OpenAPIDocument:
    def __init__(self):
        self.definitions = {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            }
        }
        self.paths = {}

    def add_path(self, path: str, methods: Dict[str, Dict]) -> None:
        self.paths[path] = methods

    def generate(self) -> Dict[str, Any]:
        return {
            "openapi": "3.0.0",
            "info": {"title": "API Documentation", "version": "1.0.0"},
            "servers": [{"url": "http://localhost:8080"}],
            "paths": self.paths,
            "components": {"schemas": self.definitions}
        }

class APIRouter:
    def __init__(self, app: web.Application, version: str = "v1"):
        self.app = app
        self.version = version
        self.routes = []

    def add_route(self, method: str, path: str, handler: Callable, name: Optional[str] = None):
        route = web.Route(method, path, handler)
        self.routes.append(route)
        self.app.add_route(route)

    def add_websocket_route(self, path: str, handler: Callable):
        self.app.router.add_get(path, self.websocket_handler)
        self.app.router.add_post(path, self.websocket_handler)

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.app["websocket_connections"].add(ws)
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await self.broadcast_message(msg.data)
            elif msg.type == web.WSMsgType.CLOSE:
                self.app["websocket_connections"].remove(ws)
                break
        return ws

    async def broadcast_message(self, message: str) -> None:
        for ws in self.app["websocket_connections"]:
            await ws.send_str(message)

class UserService:
    def __init__(self, cache: CacheManager):
        self.cache = cache
        self.data = {}

    async def create_user(self, name: str, email: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "name": name,
            "email": email,
            "created_at": datetime.datetime.now().isoformat()
        }
        await self.cache.set_cache(f"user:{user_id}", user)
        return user

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = await self.cache.get_cache(f"user:{user_id}")
        if user:
            return user
        return None

    async def update_user(self, user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
        user = await self.cache.get_cache(f"user:{user_id}")
        if not user:
            return {"error": "User not found"}
        if name:
            user["name"] = name
        if email:
            user["email"] = email
        await self.cache.set_cache(f"user:{user_id}", user)
        return user

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        user = await self.cache.get_cache(f"user:{user_id}")
        if not user:
            return {"error": "User not found"}
        await self.cache.set_cache(f"user:{user_id}", None)
        return {"message": "User deleted"}

class APIHandler:
    def __init__(self, user_service: UserService, rate_limiter: RateLimiter, auth_middleware: AuthMiddleware):
        self.user_service = user_service
        self.rate_limiter = rate_limiter
        self.auth_middleware = auth_middleware
        self.openapi = OpenAPIDocument()

    async def handle_request(self, request: web.Request) -> web.Response:
        client_ip = request.remote
        if not await self.rate_limiter.check_rate_limit(client_ip):
            return web.json_response({"error": "Rate limit exceeded"}, status=429)
        
        if request.method in ["GET", "POST", "PUT", "DELETE"]:
            if request.match_info.get("version") == "v2":
                return web.json_response({"error": "Unsupported API version"}, status=400)
        
        return await self.auth_middleware(request, self._handle_api_request)

    async def _handle_api_request(self, request: web.Request) -> web.Response:
        if request.method == "GET":
            user_id = request.match_info.get("user_id")
            if user_id:
                user = await self.user_service.get_user(user_id)
                if user:
                    return web.json_response(user)
                return web.json_response({"error": "User not found"}, status=404)
            else:
                return web.json_response({"error": "Missing user ID"}, status=400)
        elif request.method == "POST":
            data = await request.json()
            name = data.get("name")
            email = data.get("email")
            if name and email:
                return web.json_response(await self.user_service.create_user(name, email))
            return web.json_response({"error": "Missing name or email"}, status=400)
        elif request.method == "PUT":
            data = await request.json()
            user_id = request.match_info.get("user_id")
            name = data.get("name")
            email = data.get("email")
            if user_id and (name or email):
                return web.json_response(await self.user_service.update_user(user_id, name, email))
            return web.json_response({"error": "Missing user ID or update data"}, status=400)
        elif request.method == "DELETE":
            user_id = request.match_info.get("user_id")
            if user_id:
                return web.json_response(await self.user_service.delete_user(user_id))
            return web.json_response({"error": "Missing user ID"}, status=400)
        else:
            return web.json_response({"error": "Method not allowed"}, status=405)

class SwaggerUIHandler:
    def __init__(self, openapi: OpenAPIDocument):
        self.openapi = openapi

    async def handle_swagger(self, request: web.Request) -> web.Response:
        openapi_spec = self.openapi.generate()
        return web.json_response(openapi_spec)

    async def handle_swagger_ui(self, request: web.Request) -> web.Response:
        with open("swagger-ui.html", "r") as f:
            return web.Response(text=f.read(), content_type="text/html")

async def main():
    app = web.Application()
    secret_key = "your-secret-key-here"
    rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
    cache = CacheManager(ttl_seconds=300)
    user_service = UserService(cache)
    auth_middleware = AuthMiddleware(secret_key)
    api_handler = APIHandler(user_service, rate_limiter, auth_middleware)
    swagger_handler = SwaggerUIHandler(api_handler.openapi)
    
    app["websocket_connections"] = set()
    
    router = APIRouter(app, version="v1")
    router.add_route("GET", "/{version}/users/{user_id}", api_handler.handle_request, name="get_user")
    router.add_route("POST", "/{version}/users", api_handler.handle_request, name="create_user")
    router.add_route("PUT", "/{version}/users/{user_id}", api_handler.handle_request, name="update_user")
    router.add_route("DELETE", "/{version}/users/{user_id}", api_handler.handle_request, name="delete_user")
    router.add_websocket_route("/{version}/ws", api_handler.handle_request)
    
    app.router.add_get("/swagger.json", swagger_handler.handle_swagger)
    app.router.add_get("/swagger", swagger_handler.handle_swagger_ui)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    await site.start()
    print("Server started on http://localhost:8080")
    await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
```