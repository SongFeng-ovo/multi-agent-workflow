# 多 Agent 智能工作流系统

面向企业场景的智能 Agent 系统，覆盖**从单 Agent 工具调用 → 任务规划 → 多 Agent 协作 → 记忆管理 → 技能固化**的完整开发生命周期。系统让 Agent 从"只会对话"升级为"可自主执行复杂任务"，并在真实运行中沉淀了可复现的对比数据。

> 📌 本项目为学习作品，基于 [AlibabaCloudDocs/aliyun_acp_learning](https://github.com/AlibabaCloudDocs/aliyun_acp_learning)（阿里云大模型 ACP 认证 · C3 构建 Agent 系统，Apache-2.0）复现并工程化。见 [LICENSE](./LICENSE) 与文末「来源与致谢」。
>
> ⚠️ C4（模型蒸馏 + LoRA 微调、多模态内容安全 & 岗位级权限过滤）依赖 GPU 与云端服务，见文末「Roadmap」。

## 核心能力（对应简历条目）

| # | 简历描述 | 实现 | 示例 | 真实运行结果 |
|---|---|---|---|---|
| 1 | 融合 **Function Calling + ReAct + MCP** 的工具调用链路 | 手写 Function Calling 主循环；AgentScope `ReActAgent`+`Toolkit`；`StdIOStatefulClient` 接入 MCP 工具服务 | [examples/01](examples/01_function_calling_raw.py) · [02](examples/02_react_local_tools.py) · [03](examples/03_react_mcp_tools.py) | 模型自主决策并**并行调用 2 个工具**；同名「张伟」按部门消歧正确；MCP 客户端自动"发现"远程工具并完成搜索 |
| 2 | **任务规划与自主决策**（分解/执行/反思修正） | `PlanNotebook` 计划状态机 + 代码解释器外部反馈 | [examples/04](examples/04_plan_and_reflect.py) | Agent 自动拆出 **5 个子任务**，实测发现 `ZeroDivisionError` → 修复 → 复验 → 总结 |
| 3 | **Boss/Worker 多 Agent 协作**（角色分工 + 任务路由） | Boss 将 Worker 成员注册为工具，自主路由并传 context 汇总 | [examples/05](examples/05_boss_worker.py) | Boss 依次路由 **HR→培训导师→行政管家**，汇总出完整《入职办理材料包》 |
| 4 | **短期 + 长期记忆**（跨会话经验积累、主动记忆管理） | `InMemoryMemory`（短期）；`Mem0LongTermMemory` + 百炼 embedding（长期，static_control 自动存取） | [examples/06](examples/06_memory_short_and_long.py) | 会话内风格跨轮保持；**清空短期记忆后**仍能回忆课程进度 |
| 5 | **Skill 固化**：核心工作流固化为可复用 Skill | `register_agent_skill()` + 固化可执行脚本 `skills/data_report/report.py` | [examples/07](examples/07_skill_fixed.py) | A/B 实测：无 Skill **12 步**（规范塞进提问、临场试错）→ 有 Skill **3 步**（读 SKILL.md → 运行固化脚本一次完成），步数 **−75%**，两版规范小节均覆盖 4/4 |

> 以上结果均为本机对 `qwen-plus` 的真实运行输出，完整日志归档在 [outputs/transcripts/](outputs/transcripts/)。

## 目录结构

```
.
├─ common/                 # 公共层：密钥/模型工厂/领域数据
│  ├─ config.py            #   Key 加载（兼容环境变量或 Key.json）
│  ├─ models.py            #   DashScopeChatModel 工厂
│  └─ data.py              #   虚构内容公司 员工/部门数据 + data/staff.csv
├─ mcp_servers/            # FastMCP 本地工具服务（stdio）
├─ skills/                 # 可复用 Skill（SKILL.md 规范目录）
├─ examples/               # 7 个可运行示例（对应简历能力逐条）
├─ outputs/transcripts/    # 真实运行日志归档（evidence）
├─ run_all.py              # 一键重跑全部示例并归档日志
├─ requirements.txt
└─ LICENSE                 # Apache-2.0
```

## 快速开始

```bash
# 1. 环境（Python 3.10+）
conda create -n maw python=3.10 -y && conda activate maw
pip install -r requirements.txt

# 2. 配置 API Key（不入库）：仓库根目录放 Key.json {"DASHSCOPE_API_KEY": "sk-..."}
#    或设置环境变量 DASHSCOPE_API_KEY

# 3. 逐个运行示例
python examples/01_function_calling_raw.py   # Function Calling
python examples/02_react_local_tools.py      # ReAct + 本地工具
python examples/03_react_mcp_tools.py        # ReAct + MCP 工具服务
python examples/04_plan_and_reflect.py       # 规划 + 反思修正
python examples/05_boss_worker.py            # Boss/Worker 协作
python examples/06_memory_short_and_long.py  # 记忆系统
python examples/07_skill_fixed.py            # Skill 固化复用

# 4. 一键全跑并归档日志
python run_all.py
```

## 设计要点（踩坑沉淀）

- **Agent 必须"用工具说话"**：仅靠系统提示不强约束时，模型会凭记忆编造（示例 02 曾把 IT 部负责人答成"李明"）。加入"每条事实必须先查工具、禁止凭记忆作答"硬约束后，输出与数据源完全一致。这既是检索/工具调用 Agent 的通用工程教训，也直接支撑简历中"幻觉率显著下降"的写法。
- **MCP 让工具"即插即用"**：Agent 侧只需 `register_mcp_client`，服务端工具自动被发现，无需改业务代码即可接入新工具服务。
- **Skill 优于"把规范塞进 prompt"**：把多步工作流**固化为可执行脚本**（`skills/data_report/report.py`）随技能目录一起复用，Agent 只需「读 SKILL.md → 运行脚本一次」即产出标准结果；不带 Skill 时模型要临场写统计代码反复试错（本机实测 12 步 vs 3 步，见示例 07 A/B）。AgentScope 的 Skill 只注入技能描述，正文需配 `read_file` 工具由 Agent 现场加载 `SKILL.md`（见 [examples/07](examples/07_skill_fixed.py)）。
- **记忆要分短期/长期**：短期记忆会随会话清空，跨会话经验须沉淀到向量化长期记忆（Mem0），检索式回忆才能跨会话生效。

## Roadmap（C4，需 GPU/云端，暂未在本仓库实现）

简历中"模型蒸馏 + LoRA 微调"与"多模态内容安全审查 + 知识库岗位级权限过滤"对应 ACP 课程 C4 章节，依赖 GPU 训练环境与云端审核服务，按 C3-only 范围暂以设计说明形式记录：

- **推理成本优化**：用 LoRA 微调 + 蒸馏把小模型（如 `qwen3-0.6b`）迁移到 Agent 高频子任务，替代部分 `qwen-plus` 调用，预估可降低 ~40% 推理成本（需标注数据集 + GPU 训练与评测闭环）。
- **安全与合规**：多模态内容安全审查（图文违规检测，可接百炼内容安全）、知识库岗位级权限过滤（检索层按员工角色做文档级 ACL + 向量级过滤），保障 Agent 输出合规上线。

## 来源与致谢

- 课程与代码蓝本：[AlibabaCloudDocs/aliyun_acp_learning](https://github.com/AlibabaCloudDocs/aliyun_acp_learning)（阿里云大模型 ACP 认证 · C3 构建 Agent 系统，**Apache-2.0**）
- 模型服务：阿里云百炼 `qwen-plus` / `text-embedding-v3`
- 框架：AgentScope（ReAct/多 Agent/Memory/Skill）、MCP、Mem0

**注意**：`Key.json` 已被 `.gitignore` 排除，切勿提交真实 API Key。
