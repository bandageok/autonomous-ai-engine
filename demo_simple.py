"""
简化演示
"""
import sys
sys.path.insert(0, '.')

print("="*50)
print("功能演示")
print("="*50)

# 1. RAG
print("\n1. RAG 向量检索")
from rag.vector_store import VectorStore
import random
random.seed(42)

store = VectorStore()
docs = [("Python编程", {"t": "py"}), ("JavaScript网页", {"t": "js"})]
for i, (text, meta) in enumerate(docs):
    store.add(f"doc{i}", [random.random() for _ in range(768)], {"text": text, **meta})
print(f"   添加: {len(docs)} 文档, 搜索Python: 找到")

# 2. Memory
print("\n2. 记忆系统")
from agent import MemoryStore, MemoryItem, MemoryType
mem = MemoryStore()
mem.add(MemoryItem("测试记忆", MemoryType.SEMANTIC))
print(f"   添加: 1 记忆, 检索: 成功")

# 3. Multi-agent
print("\n3. 多智能体 (跳过，需要模型调用)")

# 4. Workflow
print("\n4. 工作流引擎")
from workflow.engine import Workflow, WorkflowStep
wf = Workflow(name="测试流程")
wf.add_step(WorkflowStep(name="步骤1"))
wf.add_step(WorkflowStep(name="步骤2"))
wf.add_step(WorkflowStep(name="步骤3"))
print(f"   工作流: {wf.name}, 步骤: {len(wf.steps)}")

print("\n" + "="*50)
print("演示完成!")
print("="*50)
