"""
完整演示项目核心功能
"""
import asyncio
import os
import sys
import random
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from agent import AgentCore, MemoryStore, MemoryItem, MemoryType
from llm.provider import OllamaLLM

MODEL = "deepseek-r1:8b"

async def demo_rag():
    """RAG 向量检索演示"""
    print(f"\n{'='*50}")
    print("演示: RAG 向量检索")
    print('='*50)
    
    from rag.vector_store import VectorStore
    
    # 创建向量存储
    store = VectorStore()
    
    # 准备文档
    docs = [
        ("Python是一门高级编程语言", {"topic": "python"}),
        ("JavaScript主要用于网页开发", {"topic": "javascript"}),
        ("Rust是一门系统级编程语言，注重安全性", {"topic": "rust"}),
        ("Go语言由Google开发，适合并发编程", {"topic": "go"}),
        ("Python的机器学习库包括TensorFlow和PyTorch", {"topic": "ml"}),
    ]
    
    # 添加文档
    random.seed(42)
    for doc_id, (text, meta) in enumerate(docs):
        vector = [random.random() for _ in range(768)]
        store.add(f"doc{doc_id}", vector, {"text": text, **meta})
    
    print(f"添加了 {len(docs)} 个文档到向量库")
    
    # 简单模拟搜索
    results = [d for d in docs if "Python" in d[0]]
    print(f"搜索'Python'找到: {len(results)} 条")
    for text, meta in results:
        print(f"  - {text}")
    
    return results

async def demo_multiagent():
    """多智能体协作演示"""
    print(f"\n{'='*50}")
    print("演示: 多智能体协作")
    print('='*50)
    
    researcher = AgentCore("researcher")
    writer = AgentCore("writer")
    reviewer = AgentCore("reviewer")
    
    provider = OllamaLLM(model=MODEL)
    researcher.set_llm_provider(provider)
    writer.set_llm_provider(provider)
    reviewer.set_llm_provider(provider)
    
    print("1. Researcher 分析问题...")
    research_result = await researcher.think("用户想要一个排序算法，分析需求")
    print(f"   完成: {research_result[:50]}...")
    
    print("2. Writer 写代码...")
    write_result = await writer.think("写一个Python快速排序算法")
    print(f"   完成: {write_result[:50]}...")
    
    print("3. Reviewer 审核...")
    review_result = await reviewer.think("简单评价一下这个排序算法")
    print(f"   完成: {review_result[:50]}...")
    
    print("[OK] 多智能体协作完成！")
    return {"research": research_result, "write": write_result, "review": review_result}

async def demo_workflow():
    """工作流演示"""
    print(f"\n{'='*50}")
    print("演示: 工作流引擎")
    print('='*50)
    
    from workflow.engine import Workflow, WorkflowStep
    
    workflow = Workflow(name="数据处理流程")
    
    step1 = WorkflowStep(name="获取数据", action=lambda: {"count": 100})
    step2 = WorkflowStep(name="处理数据", action=lambda ctx: {"processed": ctx.get("count", 0) * 2})
    step3 = WorkflowStep(name="保存结果", action=lambda ctx: {"saved": True})
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)
    
    print(f"工作流包含 {len(workflow.steps)} 个步骤:")
    for s in workflow.steps:
        print(f"  - {s.name}")
    
    print("✓ 工作流定义完成！")
    return workflow

async def main():
    print("="*50)
    print("Autonomous AI Engine 完整功能演示")
    print("="*50)
    
    await demo_rag()
    await demo_multiagent()
    await demo_workflow()
    
    print("\n" + "="*50)
    print("所有演示完成！")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
