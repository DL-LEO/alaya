#!/usr/bin/env python3
"""Alaya 全生命周期自动化测试 — 主编排器。

用法:
    python tests/test_orchestrator.py                         # 全链路
    python tests/test_orchestrator.py --phase phase_02        # 单阶段
    python tests/test_orchestrator.py --list                  # 列出阶段
    python tests/test_orchestrator.py --skip-phase phase_00   # 跳过某阶段
    python tests/test_orchestrator.py --fresh                 # 强制清空workdir重跑

工作流程:
  1. 从 alaya-pkg 根目录复制文件到 tests/test_workdir/
  2. 按顺序执行各阶段 (phase_00 → phase_12)
  3. 每阶段: setup() → run_all()
  4. 输出: tests/results/{timestamp}/test_report.md + results.json
"""

import argparse
import os
import shutil
import sys
import time
from datetime import datetime

# Add parent dir to path so we can import local modules
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(TESTS_DIR)
WORKDIR = os.path.join(TESTS_DIR, "test_workdir")
RESULTS_DIR = os.path.join(TESTS_DIR, "results")

# Ensure tests/ is on sys.path first
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

from lib.reporter import IssueLog
from lib.kb_builder import KnowledgeBase
from lib.time_machine import set_system_date, today_str, reset


# Phase registry
PHASES = {}
def register(cls):
    PHASES[cls.__name__.lower().replace("phase", "phase_")] = cls
    return cls

# Import phase modules and register them
from phases.phase_00_install import Phase00
register(Phase00)
from phases.phase_01_setup import Phase01
register(Phase01)
from phases.phase_02_week1 import Phase02
register(Phase02)
from phases.phase_03_month1 import Phase03
register(Phase03)
from phases.phase_04_month3 import Phase04
register(Phase04)
from phases.phase_05_month6 import Phase05
register(Phase05)
from phases.phase_12_year1 import Phase12
register(Phase12)

PHASE_ORDER = [
    "phase_00", "phase_01", "phase_02", "phase_03",
    "phase_04", "phase_05", "phase_12",
]


def prepare_workdir(fresh: bool = False):
    """Copy the alaya-pkg skeleton into the isolated test workdir.

    Preserves the original project — all mutations happen in the workdir.
    """
    if fresh or not os.path.exists(WORKDIR):
        if os.path.exists(WORKDIR):
            shutil.rmtree(WORKDIR)
        os.makedirs(WORKDIR, exist_ok=True)

        # Copy essential structure (skip .git, __pycache__, node_modules, tests/)
        skip_dirs = {".git", "__pycache__", "node_modules", "results", "test_workdir", ".claude", "tests"}
        skip_files = {".gitignore"}

        for item in os.listdir(PKG_ROOT):
            if item in skip_dirs:
                continue
            src = os.path.join(PKG_ROOT, item)
            dst = os.path.join(WORKDIR, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            elif item not in skip_files:
                shutil.copy2(src, dst)

        # Create required subdirs
        for d in ["wiki", "alaya", "alaya/memory", "alaya/manas"]:
            os.makedirs(os.path.join(WORKDIR, d), exist_ok=True)

        # Initialize an empty git repo for scripts that may check git status
        # (avoids spurious errors if a script tries git operations)
        try:
            import subprocess
            subprocess.run(["git", "init"], cwd=WORKDIR,
                           capture_output=True, timeout=5)
        except Exception:
            pass

        print(f"  Workdir prepared at: {WORKDIR}")
    else:
        print(f"  Reusing existing workdir: {WORKDIR}")

    return WORKDIR


def list_phases():
    """Print available phases and exit."""
    print("\nAvailable phases:")
    for name in PHASE_ORDER:
        doc = PHASES[name].__doc__ or ""
        summary = doc.strip().split('\n')[0] if doc else ""
        print(f"  {name:20s} {summary}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Alaya lifecycle test orchestrator")
    parser.add_argument("--phase", help="Run only this phase (e.g. phase_02)")
    parser.add_argument("--skip-phase", action="append", default=[], help="Skip a phase")
    parser.add_argument("--list", action="store_true", help="List phases")
    parser.add_argument("--fresh", action="store_true", help="Force fresh workdir")
    parser.add_argument("--keep", action="store_true", help="Keep workdir after run")
    args = parser.parse_args()

    if args.list:
        list_phases()
        return

    # Initialize
    print("=" * 60)
    print(f"  Alaya 全生命周期测试 · 开始")
    print(f"  日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    workdir = prepare_workdir(fresh=args.fresh)
    log = IssueLog()
    kb = KnowledgeBase(workdir)

    # Set system date to a fixed starting point
    set_system_date("2026-06-01")

    # Determine which phases to run
    if args.phase:
        if args.phase not in PHASES:
            print(f"  Unknown phase: {args.phase}")
            list_phases()
            sys.exit(1)
        phases_to_run = [args.phase]
    else:
        phases_to_run = [p for p in PHASE_ORDER if p not in args.skip_phase]

    # Execute phases
    total_start = time.time()
    for phase_name in phases_to_run:
        if phase_name not in PHASES:
            print(f"\n  [!] Unknown phase '{phase_name}', skipping")
            continue
        cls = PHASES[phase_name]
        instance = cls(log, kb)
        instance.execute()
        # Print separator
        print(f"  {'─' * 56}")

    elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"  测试完成 · 耗时 {elapsed:.0f}s")
    print(f"{'=' * 60}")

    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(RESULTS_DIR, timestamp)
    report_path = log.generate_report(report_dir)

    # Print summary
    total = log.count()
    passed = log.count("PASS")
    failed = log.count("FAIL")
    warned = log.count("WARN")
    print(f"\n  总检查项: {total}")
    print(f"  [PASS] Passed: {passed}")
    print(f"  [FAIL] Failed: {failed}")
    print(f"  [WARN] Warnings: {warned}")
    if failed > 0:
        print(f"\n  失败详情:")
        for r in log.failures:
            print(f"    [FAIL] {r.check_id} [{r.phase}] {r.target}")
            print(f"       预期: {r.expected[:100]}")
            print(f"       实际: {r.actual[:100]}")
            if r.suggestion:
                print(f"       建议: {r.suggestion[:150]}")
    print(f"\n  报告路径: {report_path}")
    print(f"  JSON数据: {os.path.join(report_dir, 'results.json')}")

    # Cleanup workdir unless --keep
    if not args.keep:
        print(f"\n  清理 workdir...")
        shutil.rmtree(WORKDIR, ignore_errors=True)
        print(f"  已清理: {WORKDIR}")

    # Exit non-zero if any failures
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
