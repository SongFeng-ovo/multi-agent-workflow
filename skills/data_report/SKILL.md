---
name: data-report
description: |
  按公司规范自动生成《员工数据周报》。
  当用户要求出「员工数据周报 / 部门人数统计 / 人事数据报告」时使用此技能。
---

# 员工数据周报生成技能

本周报工作流**已被固化为可执行脚本**：`skills/data_report/report.py`，
它会读取 `data/staff.csv` 并一次性输出规范要求的完整周报（四节）。

## 使用方法（严格按此执行，无需自己临场写统计代码）

1. 用 `execute_python_code` 运行下面这段固定代码，即可拿到完整周报：

```python
import subprocess, sys, os
r = subprocess.run(
    [sys.executable, os.path.join("skills", "data_report", "report.py")],
    capture_output=True, text=True, encoding="utf-8",
)
print(r.stdout)
if r.returncode:
    print("[stderr]", r.stderr[-1000:])
```

2. 把脚本输出的周报内容整理成最终中文回答返回给用户：
   - 数据概览、部门人数分布表格、数据质量与风险、给 HR 的结论与建议 四个小节都要保留；
   - **只使用脚本输出的数字，禁止编造或自行估算**。

## 硬性要求

- 若脚本运行报错，把错误贴给用户并停止，不要尝试自行改写脚本；
- 所有数字以脚本输出为准。
