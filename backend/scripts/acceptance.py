import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).resolve().parent.parent
SCRIPTS = BACKEND / "scripts"

STEPS = [
    ("单元测试（pytest 全量）", ["python", "-m", "pytest", "tests", "-q", "--no-header"], BACKEND),
    ("阶段3 冒烟（登录/权限/领用归还/记录）", ["python", str(SCRIPTS / "phase3_smoke.py")], BACKEND),
    ("阶段4 冒烟（附件/导出/高级查询/AI）", ["python", str(SCRIPTS / "phase4_smoke.py")], BACKEND),
    ("阶段5 冒烟（提示词/项目RAG/Skills/工作流）", ["python", str(SCRIPTS / "phase5_smoke.py")], BACKEND),
]

summary = []
for title, command, cwd in STEPS:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = (result.stdout or "") + (result.stderr or "")
    tail = "\n".join(output.strip().splitlines()[-8:])
    print(tail)
    ok = result.returncode == 0
    summary.append((ok, title))

print(f"\n{'=' * 60}\n验收汇总\n{'=' * 60}")
for ok, title in summary:
    print(("通过  " if ok else "失败  ") + title)
failed = [t for ok, t in summary if not ok]
print(f"\n共 {len(summary)} 项，通过 {len(summary) - len(failed)} 项，失败 {len(failed)} 项")
sys.exit(1 if failed else 0)
