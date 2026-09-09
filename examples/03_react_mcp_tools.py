"""示例 03 —— ReActAgent + MCP：即插即用的外部工具服务。

通过 MCP 协议接入一个本地（stdio）工具服务：
  1. StdIOStatefulClient 以子进程拉起 mcp_servers/web_search_server.py；
  2. 客户端自动向服务端做「工具发现」，把服务端暴露的工具注册进 Agent 工具箱；
  3. Agent 无需知道工具实现细节，即可调用远程服务完成任务。
生产环境可把这里的本地服务换成任意远端 MCP Server。

运行：python examples/03_react_mcp_tools.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentscope.agent import ReActAgent  # noqa: E402
from agentscope.mcp import StdIOStatefulClient  # noqa: E402
from agentscope.message import Msg  # noqa: E402
from agentscope.tool import Toolkit  # noqa: E402

from common.config import load_key  # noqa: E402
from common.models import build_model, single_formatter  # noqa: E402

load_key()

MCP_SERVER = ROOT / "mcp_servers" / "web_search_server.py"


async def main() -> None:
    # 1. 以 stdio 子进程方式启动本地 MCP 服务
    web_client = StdIOStatefulClient(
        name="web_search_service",
        command=sys.executable,
        args=[str(MCP_SERVER)],
        cwd=str(ROOT),
    )
    await web_client.connect()

    # 2. 工具发现：客户端向服务端询问"你有什么工具？"并注册进工具箱
    toolkit = Toolkit()
    await toolkit.register_mcp_client(web_client)

    # 3. 创建 ReAct Agent 并配备 MCP 工具箱
    agent = ReActAgent(
        name="资料搜集助手",
        sys_prompt=(
            "你是一个课程资料搜集助手，使用 web_search 工具搜索素材。\n"
            "规则：最多搜索 1 次即可，拿到结果就立即用中文给出整理后的要点；"
            "若结果已足够，不要重复搜索。只依据搜索结果的标题与摘要内容整理，"
            "不要补充或编造结果之外的信息（如具体论文、数据）。"
        ),
        model=build_model("qwen-plus"),
        formatter=single_formatter(),
        toolkit=toolkit,
        max_iters=10,
    )
    agent.set_console_output_enabled(False)

    question = "我正在为《多智能体系统》课程搜集素材，请搜索「多智能体」并整理其中的关键进展。"
    print("=" * 60)
    print(f"👤 用户：{question}")
    print("=" * 60)
    reply = await agent(Msg("user", question, "user"))
    print("\n🤖 回答：")
    print(reply.get_text_content())

    await web_client.close()


if __name__ == "__main__":
    asyncio.run(main())
