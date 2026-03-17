"""
工作流演示
"""
import sys
sys.path.insert(0, '.')

from workflow.engine import Workflow, WorkflowStep

workflow = Workflow(id="wf1", name="数据处理流程")

step1 = WorkflowStep(id="s1", name="获取数据", action=lambda: {"count": 100})
step2 = WorkflowStep(id="s2", name="处理数据", action=lambda ctx: {"processed": ctx.get("count", 0) * 2})
step3 = WorkflowStep(id="s3", name="保存结果", action=lambda ctx: {"saved": True})

workflow.add_step(step1)
workflow.add_step(step2)
workflow.add_step(step3)

print(f"Workflow: {workflow.name}")
print(f"Steps: {len(workflow.steps)}")
for s in workflow.steps:
    print(f"  - {s.name}")
print("OK")
