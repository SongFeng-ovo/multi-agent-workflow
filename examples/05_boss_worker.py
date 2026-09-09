"""示例 05 —— Boss/Worker 多 Agent 协作：角色分工 + 任务路由。

Boss（主管 Agent）把三名 Worker 成员「注册成可调用的工具」，
由 Boss 自主决策何时调用谁、把前一位成员的产出作为 context 传给下一位，
最终汇总成一份统一交付物。对应生产中的主管-专员 / 项目经理-干系人协作模式。

场景：为即将入职的教研专员张伟生成《入职办理材料包》。
  李娜(HR)     -> 岗位职责清单 + 入职手续要点
  培训导师     -> 基于岗位职责设计首周培训计划
  行政管家     -> 办公资源 + 系统账号开通清单
  Boss         -> 依次路由并汇总为一份完整文档

运行：python examples/05_boss_worker.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentscope.agent import ReActAgent  # noqa: E402
from agentscope.message import Msg, TextBlock  # noqa: E402
from agentscope.tool import Toolkit, ToolResponse  # noqa: E402

from common.config import load_key  # noqa: E402
from common.models import build_model, multi_formatter  # noqa: E402

load_key()

ROLE_HR = (
    "你是李娜，人力资源部的入职顾问。非常熟悉教研专员的岗位职责与公司用工流程。"
    "输出务必简洁、可执行，用 Markdown 列表呈现。"
)
ROLE_MENTOR = (
    "你是公司的资深培训导师，擅长为新员工设计循序渐进的首周培训计划。"
    "输出用 Markdown 表格，包含 时间/主题/产出 三列。"
)
ROLE_ADMIN = (
    "你是行政部的管家，负责新员工入职当天的办公资源与系统账号开通。"
    "输出用 Markdown 勾选清单（checklist）。"
)

BOSS_PROMPT = (
    "你是一个入职办理项目的主管（Boss），负责为新入职的教研专员张伟生成《入职办理材料包》。\n"
    "你有三名团队成员可以作为工具调用，请严格按照以下顺序分工协作：\n"
    "1. 先调用 invoke_hr_officer，拿到「岗位职责与入职手续要点」；\n"
    "2. 再调用 invoke_training_mentor，把 HR 的职责要点作为 context 传给培训导师，"
    "请其设计首周培训计划；\n"
    "3. 接着调用 invoke_ops_admin，请行政管家列出办公资源与账号开通清单；\n"
    "4. 最后汇总三份材料，输出一份结构完整、可直接转交 HR 落地的《入职办理材料包》。"
)


async def invoke_hr_officer(newcomer: str, position: str = "") -> ToolResponse:
    """入职 HR 顾问：给出岗位职责清单与入职手续要点。

    Args:
        newcomer: 新员工姓名
        position: 岗位名称
    """
    print("    → Boss 路由：调用 HR 顾问")
    worker = ReActAgent(
        name="HR顾问李娜",
        sys_prompt=ROLE_HR,
        model=build_model("qwen-plus"),
        formatter=multi_formatter(),
    )
    worker.set_console_output_enabled(False)
    task = f"新员工：{newcomer}（岗位：{position or '待定'}）。请给出该岗位的核心职责清单与入职手续要点。"
    msg = await worker(Msg("user", task, "user"))
    return ToolResponse(content=[TextBlock(type="text", text=msg.get_text_content())])


async def invoke_training_mentor(newcomer: str, position: str = "", context: str = "") -> ToolResponse:
    """培训导师：基于岗位职责设计首周培训计划。

    Args:
        newcomer: 新员工姓名
        position: 岗位名称
        context: 前序（HR）产出，作为设计培训计划的依据
    """
    print("    → Boss 路由：调用培训导师")
    worker = ReActAgent(
        name="培训导师",
        sys_prompt=ROLE_MENTOR,
        model=build_model("qwen-plus"),
        formatter=multi_formatter(),
    )
    worker.set_console_output_enabled(False)
    task = f"新员工：{newcomer}（岗位：{position}）。"
    if context:
        task += f"\n\n以下是 HR 提供的岗位职责要点，请据此设计首周培训计划：\n{context}"
    msg = await worker(Msg("user", task, "user"))
    return ToolResponse(content=[TextBlock(type="text", text=msg.get_text_content())])


async def invoke_ops_admin(newcomer: str, position: str = "") -> ToolResponse:
    """行政管家：列出入职当天的办公资源与账号开通清单。

    Args:
        newcomer: 新员工姓名
        position: 岗位名称
    """
    print("    → Boss 路由：调用行政管家")
    worker = ReActAgent(
        name="行政管家",
        sys_prompt=ROLE_ADMIN,
        model=build_model("qwen-plus"),
        formatter=multi_formatter(),
    )
    worker.set_console_output_enabled(False)
    task = f"新员工：{newcomer}（岗位：{position or '待定'}），预计下周一入职。请列出办公资源与系统账号开通清单。"
    msg = await worker(Msg("user", task, "user"))
    return ToolResponse(content=[TextBlock(type="text", text=msg.get_text_content())])


async def main() -> None:
    boss_toolkit = Toolkit()
    boss_toolkit.register_tool_function(invoke_hr_officer)
    boss_toolkit.register_tool_function(invoke_training_mentor)
    boss_toolkit.register_tool_function(invoke_ops_admin)

    boss = ReActAgent(
        name="项目主管Boss",
        sys_prompt=BOSS_PROMPT,
        model=build_model("qwen-plus"),
        formatter=multi_formatter(),
        toolkit=boss_toolkit,
    )
    boss.set_console_output_enabled(False)

    task = "请为新入职的教研专员张伟准备一份《入职办理材料包》。"
    print("=" * 60)
    print(f"👤 用户（向 Boss 下达任务）：{task}")
    print("=" * 60)
    final_msg = await boss(Msg("user", task, "user"))

    print("\n" + "=" * 60)
    print("📦 Boss 汇总输出《入职办理材料包》：")
    print("=" * 60)
    print(final_msg.get_text_content())


if __name__ == "__main__":
    asyncio.run(main())
