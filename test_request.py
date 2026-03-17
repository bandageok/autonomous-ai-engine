import requests
resp = requests.get("http://localhost:8000/health")
print(f"Status: {resp.status_code}")
print(resp.json())
