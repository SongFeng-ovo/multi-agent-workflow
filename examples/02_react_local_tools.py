"""示例 02 —— AgentScope ReActAgent + 本地工具（自主规划执行链）。

把上一步「手写的 Function Calling 主循环」交给框架：
ReActAgent 内部自动完成 思考 -> 调用工具 -> 观察结果 -> 再思考 的循环，
我们只负责注册工具与提问。

运行：python examples/02_react_local_tools.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentscope.agent import ReActAgent  # noqa: E402
from agentscope.message import Msg, TextBlock  # noqa: E402
from agentscope.tool import Toolkit, ToolResponse  # noqa: E402

from common import data  # noqa: E402
from common.config import load_key  # noqa: E402
from common.models import build_model, single_formatter  # noqa: E402

load_key()


def query_employee(name: str, dept: str = "") -> ToolResponse:
    """查员工信息；同名员工须传部门消歧。

    Args:
        name: 员工姓名
        dept: 员工所在部门（同名时必填）
    """
    return ToolResponse(content=[TextBlock(type="text", text=data.find_employee(name, dept))])


def query_department(dept: str) -> ToolResponse:
    """查部门分管负责人与核心职责。

    Args:
        dept: 部门名称
    """
    return ToolResponse(content=[TextBlock(type="text", text=data.department_summary(dept))])


async def main() -> None:
    toolkit = Toolkit()
    toolkit.register_tool_function(query_employee)
    toolkit.register_tool_function(query_department)

    agent = ReActAgent(
        name="企业助手",
        sys_prompt=(
            "你是一个企业智能助手。用户会问员工或部门信息。\n"
            "硬性要求：每一条需要的事实都必须先调用对应工具查询，"
            "只依据工具返回内容作答，禁止凭记忆编造。回答用中文，简洁准确。"
        ),
        model=build_model("qwen-plus"),
        formatter=single_formatter(),
        toolkit=toolkit,
    )
    agent.set_console_output_enabled(False)

    question = "教研部张伟的工位和 IT 部负责人的姓名分别是什么？"
    print("=" * 60)
    print(f"👤 用户：{question}")
    print("=" * 60)
    reply = await agent(Msg("user", question, "user"))
    print("\n🤖 回答：")
    print(reply.get_text_content())


if __name__ == "__main__":
    asyncio.run(main())
