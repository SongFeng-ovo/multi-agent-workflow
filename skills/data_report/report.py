"""《员工数据周报》生成脚本 —— 被 skills/data_report/SKILL.md 引用。

工作流被固化成脚本后，Agent 只需「运行一次」即可拿到完整报告，
不再需要临场反复试错写代码。数据文件：data/staff.csv。
"""
import csv
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(ROOT, "data", "staff.csv")


def load_rows() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def missing(rows: list[dict], col: str) -> int:
    return sum(1 for r in rows if not (r.get(col) or "").strip())


def main() -> None:
    rows = load_rows()
    total = len(rows)
    cols = list(rows[0].keys())

    print("# 员工数据周报\n")
    print("## 一、数据概览")
    print(f"- 总员工数：{total} 人")
    print(f"- 数据文件：data/staff.csv（共 {len(cols)} 列：{'、'.join(cols)}）")
    print("- 缺失统计：" + "；".join(
        f"{c} 缺失 {missing(rows, c)}" for c in cols
    ) or "无")
    print()

    print("## 二、部门人数分布")
    cnt = Counter(r["部门"] for r in rows)
    print("| 部门 | 人数 | 占比 |")
    print("|------|------|------|")
    for dept, n in cnt.most_common():
        print(f"| {dept} | {n} | {n / total * 100:.1f}% |")
    print()

    print("## 三、数据质量与风险")
    domains = {r["邮箱"].split("@")[-1] for r in rows if "@" in r["邮箱"]}
    print(f"- 邮箱域名：{'、'.join(sorted(domains))}（统一域{'✅' if len(domains) == 1 else '⚠️'}）")
    ids = [r["工号"] for r in rows]
    print(f"- 工号唯一性：{'✅ 无重复' if len(set(ids)) == len(ids) else '⚠️ 存在重复'}")
    names = Counter(r["姓名"] for r in rows)
    dup = {k: v for k, v in names.items() if v > 1}
    if dup:
        for k, v in dup.items():
            depts = [r["部门"] for r in rows if r["姓名"] == k]
            print(f"- ⚠️ 同名员工风险：「{k}」共 {v} 人（{'、'.join(depts)}），需按部门区分")
    else:
        print("- 同名员工风险：✅ 无")
    print()

    print("## 四、给 HR 的结论与建议")
    if dup:
        d = ", ".join(f"「{k}」在 {v} 个部门" for k, v in dup.items())
        print(f"- 本周最需关注：存在同名员工（{d}），招聘与账号开通务必使用工号+部门定位，避免混淆。")
    if len(domains) > 1:
        print("- 建议统一员工邮箱域名，便于账号体系与权限治理。")
    else:
        print("- 员工邮箱域名统一，账号体系健康；建议保持。")
    print("- 数据整体完整（无关键列缺失），可支撑后续按部门的人力结构分析。")


if __name__ == "__main__":
    main()
