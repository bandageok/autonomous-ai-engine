import requests
import json

prompt = '''Generate a Python code security analyzer module for an autonomous AI engine project. Create a comprehensive security module that includes:

1. A CodeSecurityAnalyzer class with methods to detect dangerous functions (eval, exec, subprocess, os.system, etc.), check for SQL injection vulnerabilities, check for command injection patterns, analyze imports for risky modules, detect path traversal vulnerabilities, check for hardcoded secrets/credentials, and analyze AST for suspicious patterns.

2. A VulnerabilityReport dataclass to store findings.

3. A SecurityChecker class with rule-based checking.

4. Include proper type hints, docstrings, and follow Python best practices.

5. Make it at least 200 lines of high-quality code.

Output only the Python code, no explanations.'''

response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'qwen3:8b',
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.3,
            'num_ctx': 32000
        }
    },
    timeout=180
)

result = response.json()
print(result.get('response', ''))
