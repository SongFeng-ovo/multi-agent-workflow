"""多 Agent 智能工作流系统 —— 公共配置与密钥加载。

密钥读取顺序：环境变量 ``DASHSCOPE_API_KEY`` -> 仓库根目录 ``Key.json``。
``Key.json`` 已被 .gitignore 排除，切勿提交到 GitHub。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import dashscope

ROOT = Path(__file__).resolve().parent.parent
KEY_FILE = ROOT / "Key.json"


def load_key() -> str:
    """返回并设置百炼（DashScope）API Key，未找到则给出可操作提示。"""
    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not key and KEY_FILE.exists():
        try:
            key = json.loads(KEY_FILE.read_text(encoding="utf-8")).get(
                "DASHSCOPE_API_KEY", ""
            ).strip()
        except Exception:
            key = ""
    if not key:
        raise RuntimeError(
            "未找到 DASHSCOPE_API_KEY。请二选一：\n"
            "  1) 设置环境变量 DASHSCOPE_API_KEY=sk-xxx\n"
            "  2) 在仓库根目录创建 Key.json：{\"DASHSCOPE_API_KEY\": \"sk-xxx\"}"
        )
    os.environ["DASHSCOPE_API_KEY"] = key
    # dashscope 同时依赖模块级 api_key 属性，须显式赋值
    dashscope.api_key = key
    return key
