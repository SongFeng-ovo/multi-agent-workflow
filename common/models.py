"""模型与 Agent 工厂。

统一把「模型名 -> DashScopeChatModel 实例」收敛到这里，
既方便在 examples 里复用，也便于将来切换 qwen-plus / qwen-flash / qwen-max 做成本与效果对比。
"""
from __future__ import annotations

import os

from agentscope.formatter import DashScopeChatFormatter, DashScopeMultiAgentFormatter
from agentscope.model import DashScopeChatModel


def build_model(model_name: str = "qwen-plus", stream: bool = False) -> DashScopeChatModel:
    """根据模型名构建一个百炼对话模型实例（复用环境变量中的 Key）。"""
    return DashScopeChatModel(
        model_name=model_name,
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        stream=stream,
    )


def single_formatter() -> DashScopeChatFormatter:
    """单 Agent 场景使用的消息格式化器。"""
    return DashScopeChatFormatter()


def multi_formatter() -> DashScopeMultiAgentFormatter:
    """多 Agent 协作场景推荐使用的格式化器（保证 Agent 间通信格式兼容）。"""
    return DashScopeMultiAgentFormatter()
