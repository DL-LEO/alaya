"""Issue logging and final report generation.

Records every check result across all phases without modifying any files.
The final report is a Markdown document with per-phase tables, detailed
failure context, and actionable suggestions.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class CheckResult:
    """Single atomic check — a file verification, NL test, or script run."""
    check_id: str                     # e.g. "C-0-01", "NL-2-03"
    phase: str                        # e.g. "phase_00"
    check_type: str                   # file_exists | json_valid | nl_test | script_run | strength_check | memory_check | ...
    severity: str                     # PASS | FAIL | WARN
    category: str                     # file_integrity | script_error | retrieval_mismatch | data_inconsistency | persona_deviation | time_anomaly | performance
    target: str                       # file path or brief test description
    expected: str = ""                # what should happen
    actual: str = ""                  # what actually happened
    detail: str = ""                  # full context for debugging (paths, values, stack traces)
    suggestion: str = ""              # actionable fix recommendation (FAIL only)

    def passed(self) -> bool:
        return self.severity == "PASS"

    def failed(self) -> bool:
        return self.severity == "FAIL"

    def warn(self) -> bool:
        return self.severity == "WARN"


class IssueLog:
    """Accumulates all check results across phases.  Append-only, no mutation."""

    def __init__(self):
        self.results: list[CheckResult] = []
        self._start = datetime.now()

    def record(self, check: CheckResult) -> CheckResult:
        self.results.append(check)
        return check

    def pass_(self, check_id: str, phase: str, check_type: str, category: str, target: str,
              detail: str = "") -> CheckResult:
        return self.record(CheckResult(check_id, phase, check_type, "PASS", category, target,
                                       detail=detail))

    def fail(self, check_id: str, phase: str, check_type: str, category: str, target: str,
             expected: str = "", actual: str = "", detail: str = "", suggestion: str = "") -> CheckResult:
        return self.record(CheckResult(check_id, phase, check_type, "FAIL", category, target,
                                       expected, actual, detail, suggestion))

    def warn(self, check_id: str, phase: str, check_type: str, category: str, target: str,
             expected: str = "", actual: str = "", detail: str = "", suggestion: str = "") -> CheckResult:
        return self.record(CheckResult(check_id, phase, check_type, "WARN", category, target,
                                       expected, actual, detail, suggestion))

    def count(self, severity: str | None = None) -> int:
        if severity:
            return sum(1 for r in self.results if r.severity == severity)
        return len(self.results)

    @property
    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if r.failed()]

    @property
    def warnings(self) -> list[CheckResult]:
        return [r for r in self.results if r.warn()]

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_report(self, output_dir: str) -> str:
        """Write a Markdown report with per-phase details.  Returns file path."""
        os.makedirs(output_dir, exist_ok=True)

        passed = self.count("PASS")
        failed = self.count("FAIL")
        warned = self.count("WARN")
        total = self.count()

        lines = []
        lines.append("# Alaya 全生命周期测试报告\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**运行耗时**: {(datetime.now() - self._start).total_seconds():.0f}s\n")
        lines.append("---\n")
        lines.append("## 汇总\n")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 总检查项 | {total} |")
        lines.append(f"| [PASS] 通过 | {passed} |")
        lines.append(f"| [FAIL] 失败 | {failed} |")
        lines.append(f"| [WARN] 警告 | {warned} |")
        lines.append(f"| 失败率 | {failed / total * 100:.1f}% |" if total > 0 else "")
        lines.append("")

        if failed > 0:
            cat_breakdown: dict[str, int] = {}
            for r in self.failures:
                cat_breakdown[r.category] = cat_breakdown.get(r.category, 0) + 1
            lines.append("### 失败分类\n")
            lines.append("| 类别 | 数量 |")
            lines.append("|------|------|")
            for cat, cnt in sorted(cat_breakdown.items(), key=lambda x: -x[1]):
                lines.append(f"| {cat} | {cnt} |")
            lines.append("")

        # Per-phase breakdown
        phases = sorted(set(r.phase for r in self.results))
        lines.append("## 各阶段概览\n")
        lines.append("| 阶段 | 通过 | 失败 | 警告 | 总计 |")
        lines.append("|------|------|------|------|------|")
        for ph in phases:
            p = sum(1 for r in self.results if r.phase == ph and r.passed())
            f = sum(1 for r in self.results if r.phase == ph and r.failed())
            w = sum(1 for r in self.results if r.phase == ph and r.warn())
            lines.append(f"| {ph} | {p} | {f} | {w} | {p+f+w} |")
        lines.append("")

        # ---- Detailed phase sections ----
        for ph in phases:
            phase_results = [r for r in self.results if r.phase == ph]
            phase_fails = [r for r in phase_results if r.failed()]
            phase_warns = [r for r in phase_results if r.warn()]
            phase_passes = [r for r in phase_results if r.passed()]

            lines.append(f"---\n")
            lines.append(f"## {ph}\n")
            lines.append(f"**总数**: {len(phase_results)} | [PASS] {len(phase_passes)} | [FAIL] {len(phase_fails)} | [WARN] {len(phase_warns)}\n")

            # Failures first
            if phase_fails:
                lines.append("### [FAIL] 失败检查项\n")
                lines.append("| ID | 类型 | 检查项 | 预期 | 实际 | 说明 | 建议修复 |")
                lines.append("|----|------|--------|------|------|------|---------|")
                for r in phase_fails:
                    lines.append(f"| {r.check_id} | {r.check_type} | {r.target} | {r.expected or '—'} | {r.actual or '—'} | {r.detail or '—'} | {r.suggestion or '—'} |")
                lines.append("")

            # Warnings
            if phase_warns:
                lines.append("### [WARN] 警告（需人工复查）\n")
                for r in phase_warns:
                    lines.append(f"- **{r.check_id}** ({r.target}): {r.detail}")
                lines.append("")

            # Passes (compact list)
            if phase_passes:
                lines.append("<details>\n<summary>[PASS] 通过的检查项 ({len(phase_passes)})</summary>\n\n")
                for r in phase_passes:
                    lines.append(f"- {r.check_id} ({r.check_type}) — {r.target}")
                lines.append("\n</details>\n")

        # ---- Suggestion summary ----
        all_suggestions = [r for r in self.failures if r.suggestion]
        if all_suggestions:
            lines.append("---\n")
            lines.append("## 建议汇总\n")
            for r in all_suggestions:
                lines.append(f"- **{r.check_id}**: {r.suggestion}")
            lines.append("")

        # ---- JSON export ----
        report_path = os.path.join(output_dir, "test_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        # Also export machine-readable JSON
        json_path = os.path.join(output_dir, "results.json")
        export = {
            "generated": datetime.now().isoformat(),
            "summary": {"total": total, "passed": passed, "failed": failed, "warned": warned},
            "results": [asdict(r) for r in self.results],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export, f, ensure_ascii=False, indent=2)

        return report_path

    def print_phase_summary(self, phase_name: str) -> None:
        p = sum(1 for r in self.results if r.phase == phase_name and r.passed())
        f = sum(1 for r in self.results if r.phase == phase_name and r.failed())
        w = sum(1 for r in self.results if r.phase == phase_name and r.warn())
        t = p + f + w
        status = "[PASS]" if f == 0 else "[FAIL]"
        print(f"  [{status}] {phase_name}: {p}/{t} passed, {f} failed, {w} warnings")
        if f > 0:
            for r in self.results:
                if r.phase == phase_name and r.failed():
                    print(f"    └─ [FAIL] {r.check_id}: {r.target} — {r.detail[:120]}")
