"""一个基于 FastMCP 的本地 MCP Server —— 模拟联网搜索。

被 examples/03_react_mcp_tools.py 以 stdio 子进程方式拉起，
演示「MCP 工具发现 + Agent 调用远程工具服务」的接入链路。
真实项目中替换成任意 MCP Server（如官方 WebSearch / 企业内部服务）即可。
"""
from datetime import datetime

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MockWebSearch")

# 模拟的搜索结果库（key 为可命中的关键词）
_MOCK_DB = {
    "大型语言模型": [
        {"title": "Qwen3 开源模型系列全面升级",
         "snippet": "阿里云通义千问发布 Qwen3，在数学推理、代码生成等方面全面超越前代。",
         "date": "2026-04-08"},
        {"title": "大语言模型在科学发现中的应用综述",
         "snippet": "Nature 综述总结了 LLM 在药物发现、材料科学等领域的最新应用。",
         "date": "2026-04-05"},
    ],
    "RAG": [
        {"title": "2026 检索增强生成实践指南",
         "snippet": "介绍句子窗口、混合检索与 Rerank 在企业知识库问答中的落地经验。",
         "date": "2026-05-12"},
    ],
    "多智能体": [
        {"title": "Multi-Agent 编排模式盘点",
         "snippet": "梳理 Boss/Worker、MoA、MsgHub 等主流多智能体协作架构的适用场景。",
         "date": "2026-06-01"},
    ],
    "MCP": [
        {"title": "MCP 协议让 Agent 无缝接入外部工具",
         "snippet": "Model Context Protocol 正在成为 LLM 应用连接数据与工具的事实标准。",
         "date": "2026-03-20"},
    ],
}


@mcp.tool()
def web_search(query: str, max_results: int = 3) -> str:
    """模拟联网搜索，根据关键词返回搜索结果。

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数量，默认为 3
    """
    results = []
    for key, items in _MOCK_DB.items():
        if key in query or query in key:
            results.extend(items)
    if not results:
        results = [{
            "title": f"关于「{query}」的搜索结果",
            "snippet": f"这是关于「{query}」的模拟结果。",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }]

    lines = [f"搜索「{query}」共找到 {len(results[:max_results])} 条结果："]
    for i, r in enumerate(results[:max_results], 1):
        lines.append(f"{i}. 【{r['title']}】\n   {r['snippet']}\n   日期: {r['date']}")
    return "\n".join(lines)


if __name__ == "__main__":
    # 以 stdio 方式启动，等待 Client 端（父进程）通过 stdin/stdout 通信
    mcp.run(transport="stdio")
