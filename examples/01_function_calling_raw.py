"""示例 01 —— 手写 Function Calling 链路（不依赖 Agent 框架）。

演示 Agent 从「只会对话」到「能自主执行」的第一步：
  1. 把业务函数写成 JSON Schema 工具描述，随请求交给模型；
  2. 模型自主决策是否调用工具、并给出结构化的参数；
  3. 我们执行真实函数，把结果回填给模型；
  4. 模型基于工具结果生成最终答复。

运行：python examples/01_function_calling_raw.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from common import data  # noqa: E402
from common.config import load_key  # noqa: E402
from openai import OpenAI  # noqa: E402

load_key()

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ---- 1. 真实业务函数（Tool 的执行端） ----
def query_employee(name: str, dept: str = "") -> str:
    """查员工信息；同名时按 dept 消歧。"""
    return data.find_employee(name, dept)


def query_department(dept: str) -> str:
    """查部门负责人与职责。"""
    return data.department_summary(dept)


# ---- 2. 函数 -> OpenAI 风格 JSON Schema 工具描述 ----
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_employee",
            "description": "在员工库中查询某位员工的部门/岗位/工号/工位/邮箱。存在同名员工时须传入部门(dept)精确查询。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "员工姓名"},
                    "dept": {"type": "string", "description": "员工所在部门（同名时必填）"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_department",
            "description": "查询某部门的分管负责人及其核心职责。",
            "parameters": {
                "type": "object",
                "properties": {
                    "dept": {"type": "string", "description": "部门名称"},
                },
                "required": ["dept"],
            },
        },
    },
]

# 工具名 -> 真实函数 的映射表（调度器）
DISPATCHER = {"query_employee": query_employee, "query_department": query_department}


def run_tool_call(tool_call) -> str:
    """执行一次模型发起的工具调用，返回结果字符串。"""
    fn = tool_call.function
    name, args = fn.name, json.loads(fn.arguments or "{}")
    print(f"    → 模型决定调用 `{name}`，参数 {args}")
    result = DISPATCHER[name](**args)
    print(f"    → 工具返回：{result[:120]}")
    return result


# ---- 3. 主链路：决策 -> 执行 -> 回填 -> 生成 ----
USER_MSG = "教研部的张伟邮箱是什么？另外行政部主要负责哪些工作？"

messages = [
    {"role": "system", "content": "你是一个企业智能助手。需要查数据时调用工具，最后用中文给出简洁、准确的答复。"},
    {"role": "user", "content": USER_MSG},
]

print("=" * 60)
print(f"👤 用户：{USER_MSG}")
print("=" * 60)

# 第一轮：模型决策
resp = client.chat.completions.create(model="qwen-plus", messages=messages, tools=TOOLS, tool_choice="auto")
msg = resp.choices[0].message

round_no = 0
while msg.tool_calls and round_no < 5:
    round_no += 1
    print(f"\n--- 第 {round_no} 轮工具调用 ---")
    messages.append(msg)  # 把带 tool_calls 的助手消息放回对话
    for tc in msg.tool_calls:
        messages.append({
            "tool_call_id": tc.id,
            "role": "tool",
            "name": tc.function.name,
            "content": run_tool_call(tc),
        })
    resp = client.chat.completions.create(model="qwen-plus", messages=messages, tools=TOOLS, tool_choice="auto")
    msg = resp.choices[0].message

print("\n" + "=" * 60)
print(f"🤖 最终回答：{msg.content}")
print("=" * 60)
