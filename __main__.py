"""CLI Entry Point - 命令行入口"""
import sys
import asyncio
import argparse
import os
from pathlib import Path

# 设置UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

from agent import AgentCore
from llm.provider import OllamaLLM
from utils.config import AppConfig, ConfigManager
from utils.logger import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="autonomous-ai-engine",
        description="Autonomous AI Engine - Self-learning AI system"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Run the AI engine")
    run_parser.add_argument("--prompt", "-p", type=str, help="Initial prompt")
    
    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port")
    
    # webui command
    webui_parser = subparsers.add_parser("webui", help="Start Web UI")
    webui_parser.add_argument("--port", type=int, default=8501, help="Port")
    webui_parser.add_argument("--api", type=str, default="http://localhost:8000", help="API base URL")
    
    # config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current config")
    
    return parser


async def run_agent(prompt: str = None):
    """运行智能体"""
    config = AppConfig.load()
    setup_logging(level=config.log_level)
    
    agent = AgentCore("main", {"max_concurrent": config.max_concurrent_tasks})
    provider = OllamaLLM(base_url=config.ollama_url, model=config.default_model)
    agent.set_llm_provider(provider)
    
    if prompt:
        result = await agent.think(prompt)
        print(f"Result: {result}")
    else:
        print("Agent ready. Use --prompt to interact.")


def start_api_server(host: str, port: int):
    """启动API服务器"""
    print(f"Starting API server on {host}:{port}...")
    try:
        import uvicorn
        from api.fastapi_server import app
        uvicorn.run(app, host=host, port=port)
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install: pip install fastapi uvicorn")


def start_webui(port: int, api_base: str):
    """启动Web UI"""
    print(f"Starting Web UI on port {port}...")
    print(f"API will connect to: {api_base}")
    os.environ["API_BASE"] = api_base
    
    try:
        import subprocess
        subprocess.run(["streamlit", "run", "webui.py", "--server.port", str(port)])
    except Exception as e:
        print(f"Error starting Streamlit: {e}")
        print("Please install: pip install streamlit")


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "run":
        await run_agent(args.prompt)
    
    elif args.command == "serve":
        start_api_server(args.host, args.port)
    
    elif args.command == "webui":
        start_webui(args.port, args.api)
    
    elif args.command == "config":
        if args.show:
            config = AppConfig.load()
            import json
            print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
