"""示例 07 —— Skill：把核心工作流固化为可复用能力。

AgentScope 的 Skill 机制：注册技能后，框架把技能「描述」注入系统提示，
并提示 Agent「使用技能必须先 read 其 SKILL.md」——真正的规范正文由 Agent
通过 read_file 现场加载。因此本示例为 Agent 配备了 read_file 工具。

对比同一任务在两种状态下的表现：
  - 无 Skill：规范（流程 + 输出结构）必须每次写进用户提问，靠模型临场发挥；
  - 有 Skill：规范固化在 skills/data_report/（SKILL.md），一次注册、随取随用，
    用户只需一句简短请求，Agent 读完 SKILL.md 即按规范执行。

运行：python examples/07_skill_fixed.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentscope.agent import ReActAgent  # noqa: E402
from agentscope.message import Msg, TextBlock  # noqa: E402
from agentscope.tool import Toolkit, ToolResponse, execute_python_code as _orig_exec  # noqa: E402

from common.config import load_key  # noqa: E402
from common.models import build_model, single_formatter  # noqa: E402

load_key()

SKILL_DIR = ROOT / "skills" / "data_report"
SKILL_MD = SKILL_DIR / "SKILL.md"

SHORT_REQUEST = "请出一份本周的员工数据周报。"

VERBOSE_REQUEST = (
    "请读取 data/staff.csv，输出《员工数据周报》。要求："
    "1) 用代码输出总行数与各列缺失数；"
    "2) 按部门统计人数与占比(1位小数)；"
    "3) 校验邮箱域名是否统一为@educompany.com、工号是否唯一，并检查同名员工风险；"
    "4) 用中文 Markdown 分四节输出：数据概览/部门人数分布(表格)/数据质量与风险/给HR的结论与建议。"
    "所有数字必须用 execute_python_code 真实计算。"
)

REQUIRED_SECTIONS = ["数据概览", "人数分布", "数据质量", "建议"]

# 工具步数口径：read_file + execute_python_code 的真实调用次数
_counters = {"tools": 0}


async def read_file(file_path: str) -> ToolResponse:
    """读取指定路径的文本文件内容。

    Args:
        file_path: 文件路径
    """
    _counters["tools"] += 1
    content = Path(file_path).read_text(encoding="utf-8")
    return ToolResponse(content=[TextBlock(type="text", text=content)])


async def execute_python_code(code: str, timeout: float = 300):
    """执行给定的 Python 代码（异步包装，用于统计工具步数）。"""
    _counters["tools"] += 1
    return await _orig_exec(code=code, timeout=timeout)


def coverage(text: str) -> int:
    """规范必需的 4 个小节在最终回答中的覆盖度（0-4）。"""
    return sum(1 for s in REQUIRED_SECTIONS if s in text)


def make_agent(name: str, with_skill: bool) -> ReActAgent:
    toolkit = Toolkit()
    toolkit.register_tool_function(read_file)
    toolkit.register_tool_function(execute_python_code)
    sys_prompt = (
        "你是数据分析助手。任务完成后，必须把最终的周报正文作为你的回复输出，"
        "禁止以空回复或'任务完成'之类的话结尾。"
    )
    if with_skill:
        toolkit.register_agent_skill(str(SKILL_DIR))
        # 给 Agent 技能文件的具体路径，供其 read 后按规范执行
        sys_prompt += f"\n若任务涉及技能，请先用 read_file 读取 {SKILL_MD}，然后严格按其步骤执行。"
    agent = ReActAgent(
        name=name,
        sys_prompt=sys_prompt,
        model=build_model("qwen-plus"),
        formatter=single_formatter(),
        toolkit=toolkit,
        max_iters=12,
    )
    agent.set_console_output_enabled(False)
    return agent


async def run_until_answer(agent: ReActAgent, request: str) -> str:
    """执行任务；若模型以空回复收尾，提醒一次并让其补交正文。"""
    await agent(Msg("user", request, "user"))
    text = (await agent.memory.get_memory())[-1].get_text_content() or ""
    if not text.strip():
        nudge = "请把刚刚得到的周报正文（四个小节内容）作为最终回答完整输出，不要省略。"
        await agent(Msg("user", nudge, "user"))
        text = (await agent.memory.get_memory())[-1].get_text_content() or ""
    return text


async def main() -> None:
    print("=" * 60)
    print("🅰  无 Skill：规范每次写进提问，靠模型临场发挥")
    print("=" * 60)
    agent_a = make_agent("数据报告员_无Skill", with_skill=False)
    _counters["tools"] = 0
    final_a = await run_until_answer(agent_a, VERBOSE_REQUEST)
    steps_a, cov_a = _counters["tools"], coverage(final_a)
    print(f"   （真实工具步数 {steps_a}，覆盖 {cov_a}/4）")

    print("\n" + "=" * 60)
    print("🅱  有 Skill：规范固化复用，用户只需一句话")
    print("=" * 60)
    agent_b = make_agent("数据报告员_Skill", with_skill=True)
    _counters["tools"] = 0
    final_b = await run_until_answer(agent_b, SHORT_REQUEST)
    steps_b, cov_b = _counters["tools"], coverage(final_b)
    print(f"   （真实工具步数 {steps_b}，覆盖 {cov_b}/4）")

    print("\n" + "=" * 60)
    print("📊 A/B 对比")
    print("=" * 60)
    print(f"  真实工具步数    ：无Skill {steps_a} 步  vs  Skill {steps_b} 步")
    if steps_a and steps_b <= steps_a:
        print(f"  节省步数        ：{(steps_a - steps_b) / steps_a * 100:.0f}%")
    print(f"  规范小节覆盖    ：无Skill {cov_a}/4   vs  Skill {cov_b}/4")

    print("\n🅰  无 Skill 最终回答（节选）：")
    print("   ", " ".join(final_a.split())[:200])
    print("\n🅱  Skill 版最终回答（节选）：")
    print("   ", " ".join(final_b.split())[:200])


if __name__ == "__main__":
    asyncio.run(main())
