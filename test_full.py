import requests
import json

BASE = "http://localhost:8000"

# 1. 健康检查
print("1. Health check:")
r = requests.get(f"{BASE}/health")
print(r.json())

# 2. 创建Agent
print("\n2. Create agent:")
r = requests.post(f"{BASE}/api/agents", json={"name": "test", "model": "qwen3:8b"})
print(r.json())

# 3. 对话
print("\n3. Chat:")
r = requests.post(f"{BASE}/api/agents/test/think", json={"prompt": "你好，请用一句话介绍自己"})
result = r.json()
print(result.get("result", "")[:100] if "result" in result else result)

# 4. 查看历史
print("\n4. Task history:")
r = requests.get(f"{BASE}/api/tasks?limit=1")
print(f"Total tasks: {r.json().get('total', 0)}")

# 5. 查看配置
print("\n5. Config:")
r = requests.get(f"{BASE}/api/config")
print(f"Model: {r.json().get('default_model', 'N/A')}")

print("\n=== API Test Complete ===")
