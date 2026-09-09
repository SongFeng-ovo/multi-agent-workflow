"""一键串行运行全部示例，并把每个脚本的控制台输出存到 outputs/transcripts/。

用法：
    python run_all.py            # 跑全部
    python run_all.py 03         # 只跑 examples/03_*.py
"""
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
EXAMPLES = sorted((ROOT / "examples").glob("[0-9][0-9]_*.py"))
OUT_DIR = ROOT / "outputs" / "transcripts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = sys.argv[1] if len(sys.argv) > 1 else ""


def main() -> None:
    targets = [p for p in EXAMPLES if TARGET in p.name] if TARGET else EXAMPLES
    for script in targets:
        log = OUT_DIR / f"{script.name.replace('.py', '')}.txt"
        print(f"▶ 运行 {script.name} ...", flush=True)
        try:
            cp = subprocess.run(
                [sys.executable, str(script)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=900,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            body = cp.stdout + ("\n[stderr]\n" + cp.stderr if cp.stderr else "")
            # 过滤框架/日志噪音，保留模型与业务输出，方便阅读
            kept = [
                ln for ln in body.splitlines()
                if not any(t in ln for t in (" INFO ", " PostHog", "server.py:", "Processing request of type"))
                and "Warning" not in ln and "warn" not in ln.lower()
            ]
            log.write_text("\n".join(kept) + "\n", encoding="utf-8")
            tail = [l for l in body.splitlines() if l.strip()][-3:]
            print(f"   ✅ 退出码 {cp.returncode} → {log.name}")
            for l in tail:
                print(f"      … {l[:120]}")
        except subprocess.TimeoutExpired:
            print(f"   ⏰ 超时：{script.name}")


if __name__ == "__main__":
    main()
