import requests
BASE = "http://localhost:8001"

# Test
print("1. Health:", requests.get(f"{BASE}/health").json())
print("2. Create agent:", requests.post(f"{BASE}/api/agents", json={"name": "test", "model": "qwen3:8b"}).json())
print("3. Chat:", end=" ")
r = requests.post(f"{BASE}/api/agents/test/think", json={"prompt": "hello"})
print(r.json().get("result", "ERROR")[:50] if "result" in r.json() else r.json())
print("4. History:", requests.get(f"{BASE}/api/tasks?limit=1").json().get("total", 0), "tasks")
