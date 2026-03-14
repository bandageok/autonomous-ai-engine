"""Webhooks - Webhook处理器"""
import hmac
import hashlib
import json
from typing import Dict, List, Callable
from datetime import datetime
import asyncio

class WebhookHandler:
    """Webhook处理器"""
    def __init__(self, secret: str = ""):
        self.secret = secret
        self.handlers = {}
        
    def on(self, event: str, handler: Callable):
        """注册事件处理器"""
        if event not in self.handlers:
            self.handlers[event] = []
        self.handlers[event].append(handler)
        
    def verify(self, payload: str, signature: str) -> bool:
        """验证签名"""
        if not self.secret:
            return True
        expected = hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
        
    async def handle(self, event: str, data: Dict) -> Dict:
        """处理Webhook"""
        handlers = self.handlers.get(event, [])
        results = []
        for h in handlers:
            try:
                if asyncio.iscoroutinefunction(h):
                    results.append(await h(data))
                else:
                    results.append(h(data))
            except Exception as e:
                results.append({"error": str(e)})
        return {"status": "processed", "results": results}
