"""CLI Entry Point - 命令行入口"""
import sys
import asyncio
import argparse
from pathlib import Path

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
    run_parser.add_argument("--config", "-c", type=str, help="Config file path")
    run_parser.add_argument("--prompt", "-p", type=str, help="Initial prompt")
    
    # agent command
    agent_parser = subparsers.add_parser("agent", help="Manage agents")
    agent_parser.add_argument("--name", "-n", type=str, required=True, help="Agent name")
    agent_parser.add_argument("--action", "-a", choices=["create", "list", "delete"], required=True)
    
    # config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current config")
    config_parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set config value")
    
    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port")
    
    return parser


async def run_agent(config: AppConfig, prompt: str = None):
    """运行智能体"""
    # Setup logging
    setup_logging(level=config.log_level)
    
    # Create agent
    agent = AgentCore("main", {"max_concurrent": config.max_concurrent_tasks})
    
    # Set up LLM provider
    provider = OllamaLLM(
        base_url=config.ollama_url,
        model=config.default_model
    )
    agent.set_llm_provider(provider)
    
    # Run
    if prompt:
        result = await agent.think(prompt)
        print(f"Result: {result}")
    else:
        print("Agent ready. Use --prompt to interact.")


def list_agents():
    """列出智能体"""
    print("Agents: (storage not implemented yet)")


def create_agent(name: str):
    """创建智能体"""
    print(f"Creating agent: {name}")


def show_config(config_manager: ConfigManager):
    """显示配置"""
    import json
    print(json.dumps(config_manager.config.to_dict(), indent=2))


def set_config(config_manager: ConfigManager, key: str, value: str):
    """设置配置"""
    config_manager.set(key, value)
    config_manager.save()
    print(f"Set {key} = {value}")


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load config
    config_manager = ConfigManager()
    config = config_manager.config
    
    if args.command == "run":
        await run_agent(config, args.prompt)
    
    elif args.command == "agent":
        if args.action == "list":
            list_agents()
        elif args.action == "create":
            create_agent(args.name)
        elif args.action == "delete":
            print(f"Delete agent: {args.name}")
    
    elif args.command == "config":
        if args.show:
            show_config(config_manager)
        elif args.set:
            set_config(config_manager, args.set[0], args.set[1])
    
    elif args.command == "serve":
        try:
            from api.server import APIServer
            server = APIServer(host=args.host, port=args.port)
            print(f"Starting server on {args.host}:{args.port}")
            await server.start()
        except ImportError:
            print("API server not available. Install fastapi/uvicorn.")


if __name__ == "__main__":
    asyncio.run(main())
