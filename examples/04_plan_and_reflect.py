"""示例 04 —— 任务规划 + 执行 + 反思修正（PlanNotebook & 代码解释器）。

展示 Agent 面对复杂任务时的完整闭环：
  1. 用 create_plan 把任务分解为子任务（PlanNotebook 记录计划状态机）；
  2. 逐步执行，用 execute_python_code 运行真实代码获得外部反馈；
  3. 发现错误后反思、修复并重新执行（本示例让 Agent 修复一个空列表会崩溃的函数）；
  4. 通过 finish_subtask / finish_plan 提交进度，产出最终报告。
我们用钩子函数捕获计划快照，运行结束后打印「计划 -> 子任务」执行情况。

运行：python examples/04_plan_and_reflect.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentscope.agent import ReActAgent  # noqa: E402
from agentscope.message import Msg  # noqa: E402
from agentscope.plan import PlanNotebook  # noqa: E402
from agentscope.tool import Toolkit, execute_python_code  # noqa: E402

from common.config import load_key  # noqa: E402
from common.models import build_model, single_formatter  # noqa: E402

load_key()

# 用于记录计划变化的钩子
plan_snapshots = []


def capture_plan_snapshot(notebook, plan):  # noqa: ANN001
    if plan:
        plan_snapshots.append({
            "name": plan.name,
            "description": plan.description,
            "state": plan.state,
            "subtasks": [{
                "name": st.name,
                "state": st.state,
                "outcome": (str(st.outcome)[:80] if st.outcome else ""),
            } for st in plan.subtasks],
        })


async def main() -> None:
    plan_notebook = PlanNotebook()
    plan_notebook.register_plan_change_hook("capture", capture_plan_snapshot)

    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)

    agent = ReActAgent(
        name="代码工程师",
        sys_prompt=(
            "你是一名严谨的代码工程师。遇到复杂任务时请：\n"
            "1. 先用 create_plan 把任务拆解成清晰的子任务；\n"
            "2. 逐步执行子任务，涉及代码务必用 execute_python_code 真实运行验证；\n"
            "3. 代码运行报错时，阅读错误信息反思原因、修复后再执行，不要带着错误继续；\n"
            "4. 每个子任务完成后用 finish_subtask 提交，全部完成用 finish_plan 结束，"
            "最后用中文输出结论。"
        ),
        model=build_model("qwen-plus"),
        formatter=single_formatter(),
        toolkit=toolkit,
        plan_notebook=plan_notebook,
    )
    agent.set_console_output_enabled(False)

    task = (
        "这是同事写的一个计算平均分的函数：\n\n"
        "def avg_score(scores):\n"
        "    return sum(scores) / len(scores)\n\n"
        "请先用 execute_python_code 对它做几组测试（包括空列表、正常列表），"
        "找出它会崩溃的场景，然后修复它并重新运行验证，"
        "最后用中文说明：发现了什么问题、你如何修复、修复前后对比。"
    )
    print("=" * 60)
    print(f"👤 用户：{task}")
    print("=" * 60)

    reply = await agent(Msg("user", task, "user"))

    print("\n🤖 Agent 结论：")
    print(reply.get_text_content())

    # 汇总执行时的计划状态机
    print("\n" + "=" * 60)
    print("📊 计划执行快照（PlanNotebook 钩子捕获）")
    print("=" * 60)
    if plan_snapshots:
        final = plan_snapshots[-1]
        DONE = {"finished", "done", "completed"}
        finished = sum(1 for st in final["subtasks"] if st["state"] in DONE)
        print(f"计划：{final['name']}｜计划状态：{final['state']}｜"
              f"子任务完成 {finished}/{len(final['subtasks'])}")
        for i, st in enumerate(final["subtasks"], 1):
            icon = "✅" if st["state"] in DONE else "⏳"
            print(f"  {icon} {i}. {st['name']}  [{st['state']}]")
            if st["outcome"]:
                print(f"       ↳ {st['outcome']}")
    else:
        print("（未捕获到计划，Agent 未使用 create_plan 显式拆解任务）")


if __name__ == "__main__":
    asyncio.run(main())
