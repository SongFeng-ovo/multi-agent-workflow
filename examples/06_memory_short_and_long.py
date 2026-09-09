"""示例 06 —— 记忆系统：短期对话记忆 + 长期跨会话记忆。

上半场：短期记忆（InMemoryMemory）—— 会话内多轮上下文连续；
下半场：长期记忆（Mem0LongTermMemory + 向量库）——
        Agent 把重要信息沉淀进长期记忆，清空短期记忆模拟「新会话」后，
        仍能靠语义检索把上次进度捞回来（static_control 自动存取模式）。

运行：python examples/06_memory_short_and_long.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentscope.agent import ReActAgent  # noqa: E402
from agentscope.embedding import DashScopeTextEmbedding  # noqa: E402
from agentscope.formatter import DashScopeChatFormatter  # noqa: E402
from agentscope.memory import InMemoryMemory, Mem0LongTermMemory  # noqa: E402
from agentscope.message import Msg  # noqa: E402
from mem0.vector_stores.configs import VectorStoreConfig  # noqa: E402

from common.config import load_key  # noqa: E402
from common.models import build_model  # noqa: E402

load_key()
API_KEY = __import__("os").environ["DASHSCOPE_API_KEY"]


def _fmt(text: str) -> str:
    """把多行正文压成可读的单行摘录，避免刷屏。"""
    return " ".join(text.split())[:200]


async def short_term_demo() -> None:
    """上半场：InMemoryMemory 短期记忆（会话内上下文连续）。"""
    print("\n" + "=" * 60)
    print("PART 1｜短期记忆 InMemoryMemory（同一会话内连续）")
    print("=" * 60)

    agent = ReActAgent(
        name="课程写手",
        sys_prompt="你是一个课程内容编写员。",
        model=build_model("qwen-plus"),
        formatter=DashScopeChatFormatter(),
        memory=InMemoryMemory(),
    )
    agent.set_console_output_enabled(False)

    await agent(Msg("user", "记住：我们的教学风格要「严谨克制」，不使用俏皮话。", "user"))
    reply = await agent(Msg("user", "很好，那就把课程开头的欢迎语按这个风格写出来。", "user"))
    print("🤖 第二问回答（若风格被记住，则语气会偏正式克制）：")
    print("   ", _fmt(reply.get_text_content()))

    msgs = await agent.memory.get_memory()
    roles = [f"{m.name}->{m.role}" for m in msgs]
    print(f"\n📊 短期记忆已累积 {len(msgs)} 条消息：{', '.join(roles[:8])}…")
    return agent


async def long_term_demo() -> None:
    """下半场：Mem0 长期记忆（跨会话经验积累，static_control 自动存取）。"""
    print("\n" + "=" * 60)
    print("PART 2｜长期记忆 Mem0LongTermMemory（跨会话检索）")
    print("=" * 60)

    vector_store = VectorStoreConfig(config={
        "on_disk": False,           # Qdrant 本地内存向量库
        "embedding_model_dims": 1024,  # 与 text-embedding-v3 输出维度一致
    })
    ltm = Mem0LongTermMemory(
        agent_name="Writer",
        user_name="user",
        model=build_model("qwen-plus"),
        embedding_model=DashScopeTextEmbedding(
            model_name="text-embedding-v3",
            api_key=API_KEY,
            dimensions=1024,
        ),
        vector_store_config=vector_store,
    )

    agent = ReActAgent(
        name="长期记忆写手",
        sys_prompt="你是一个拥有长期记忆的课程编写员，能记住跨会话的工作进度。",
        model=build_model("qwen-plus"),
        formatter=DashScopeChatFormatter(),
        memory=InMemoryMemory(),
        long_term_memory=ltm,
        long_term_memory_mode="static_control",
    )
    agent.set_console_output_enabled(False)

    # 会话 A：写入一条重要进度
    await agent(Msg("user", "记住：我们正在写《Pandas 数据分析》课程，目前已写完初稿，正准备做审校。", "user"))
    print("📝 会话A：已把工作进度交给 Agent（将自动写入长期记忆）")

    # 模拟一次全新会话：清空短期记忆
    await agent.memory.clear()
    print("🧹 短期记忆已清空，模拟一次新的会话……")

    # 会话 B：仅凭长期记忆回答
    reply = await agent(Msg("user", "我们上次的工作进度到哪儿了？", "user"))
    print("🤖 跨会话回答（应能回忆起 Pandas 课程 & 初稿待审校）：")
    print("   ", _fmt(reply.get_text_content()))


async def main() -> None:
    await short_term_demo()
    await long_term_demo()


if __name__ == "__main__":
    asyncio.run(main())
