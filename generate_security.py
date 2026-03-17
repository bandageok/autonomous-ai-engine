import requests
import json

prompt = '''Generate a Python code security analyzer module. Include:
1. CodeSecurityAnalyzer class with AST-based detection of dangerous functions (eval, exec, subprocess, os.system)
2. VulnerabilityReport dataclass 
3. SecurityChecker class with rule-based vulnerability detection
4. At least 200 lines with type hints and docstrings'''

response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'qwen3:8b',
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.2
        }
    },
    timeout=300
)

result = response.json()
print(result.get('response', ''))
