"""示例领域数据：一家虚构教育内容公司的员工与部门信息。

数据层只返回普通字符串；真正注册给 Agent 的工具函数在各 examples 中
用 ToolResponse 包装（见 examples/02_react_local_tools.py），
以便演示「函数定义 -> 工具注册 -> 被大模型调用」的完整链路。
同时导出 data/staff.csv，供代码解释器/规划类示例做真实的数据分析。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAFF_CSV = ROOT / "data" / "staff.csv"

# 注意：两名同名员工「张伟」（教研部 / IT 部）用来演示同名消歧
STAFF: list[dict] = [
    {"name": "张伟",  "dept": "教研部",     "role": "教研专员",     "emp_id": "001", "seat": "A101", "email": "zhangwei@educompany.com"},
    {"name": "张伟",  "dept": "IT部",       "role": "网络工程师",   "emp_id": "101", "seat": "C102", "email": "it.zhangwei@educompany.com"},
    {"name": "秦飞",  "dept": "行政部",     "role": "行政专员",     "emp_id": "007", "seat": "B203", "email": "qinfei@educompany.com"},
    {"name": "邓琪",  "dept": "评估部",     "role": "评估专员（内容质检岗位）", "emp_id": "009", "seat": "C301", "email": "dengqi@educompany.com"},
    {"name": "李娜",  "dept": "人力资源部", "role": "HRBP",         "emp_id": "015", "seat": "D105", "email": "lina@educompany.com"},
    {"name": "王强",  "dept": "市场部",     "role": "市场专员",     "emp_id": "021", "seat": "E207", "email": "wangqiang@educompany.com"},
    {"name": "陈曦",  "dept": "课程开发部", "role": "课程策划",     "emp_id": "018", "seat": "D208", "email": "chenxi@educompany.com"},
    {"name": "赵敏",  "dept": "内容开发部", "role": "内容开发工程师", "emp_id": "032", "seat": "E110", "email": "zhaomin@educompany.com"},
    {"name": "孙悦",  "dept": "财务部",     "role": "会计",         "emp_id": "040", "seat": "F115", "email": "sunyue@educompany.com"},
]

DEPARTMENTS: dict[str, dict] = {
    "教研部": {"manager": "刘敏", "responsibility": "课程内容与教学研究，制定教学大纲与学习目标，组织教研活动"},
    "IT部":   {"manager": "周凯", "responsibility": "公司网络与硬件设备运维、系统监控、技术支持与工具培训"},
    "行政部": {"manager": "蔡静", "responsibility": "办公资源管理、考勤与行政事务、办公环境保障"},
    "评估部": {"manager": "杨帆", "responsibility": "内容质量审核、质检标准制定、课程评测与质量报告"},
    "人力资源部": {"manager": "高琳", "responsibility": "招聘、员工职业发展、培训规划、人事政策执行"},
    "市场部": {"manager": "陈浩", "responsibility": "市场竞品分析、行业动态收集、销售目标与策略协助、市场研究报告"},
    "课程开发部": {"manager": "徐丽", "responsibility": "课程体系规划、课程策划与开发项目管理"},
    "内容开发部": {"manager": "郑爽", "responsibility": "课程内容创作、多媒体课件制作、内容上线与更新"},
    "财务部": {"manager": "吴军", "responsibility": "财务核算、预算管理、成本控制、财务报表"},
}


def _fmt_staff(row: dict) -> str:
    return (f"{row['name']}｜{row['dept']}｜{row['role']}｜"
            f"工号 {row['emp_id']}｜工位 {row['seat']}｜{row['email']}")


def find_employee(name: str, dept: str = "") -> str:
    """按姓名（可加部门）查员工。同名时返回全部候选，供上层消歧。"""
    hits = [s for s in STAFF if s["name"] == name]
    if dept:
        hits = [s for s in hits if s["dept"] == dept]
    if not hits:
        return f"未找到员工：{name}{f'（部门 {dept}）' if dept else ''}"
    if len(hits) == 1:
        return _fmt_staff(hits[0])
    # 同名员工：返回候选列表，要求按部门/工号进一步区分
    lines = [f"「{name}」存在 {len(hits)} 位同名员工，请提供部门以精确查询："]
    lines += [f"- {_fmt_staff(s)}" for s in hits]
    return "\n".join(lines)


def department_summary(dept: str) -> str:
    """查部门负责人与核心职责。"""
    d = DEPARTMENTS.get(dept)
    if not d:
        avail = "、".join(DEPARTMENTS)
        return f"未找到部门：{dept}。现有部门：{avail}"
    return f"{dept}｜负责人：{d['manager']}｜职责：{d['responsibility']}"
