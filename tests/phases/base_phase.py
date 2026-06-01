"""Base class for all test phases.

Each phase simulates a specific point in the Alaya lifecycle, building on
the state left by the previous phase.  Phases are executed sequentially by
the orchestrator.
"""

from abc import ABC, abstractmethod
from typing import Any

from lib.reporter import IssueLog, CheckResult
from lib.kb_builder import KnowledgeBase
from lib.protocol_tracer import ProtocolTracer, PostCheck


class BasePhase(ABC):
    """Abstract test phase.  Subclasses implement setup() + run_all()."""

    def __init__(self, phase_id: str, label: str, log: IssueLog, kb: KnowledgeBase):
        self.phase_id = phase_id
        self.label = label
        self.log = log
        self.kb = kb
        self.tracer = ProtocolTracer(kb.wiki_dir, kb.alaya_dir)

    @abstractmethod
    def setup(self) -> None:
        """Build the knowledge-base state for this time period."""

    @abstractmethod
    def run_all(self) -> None:
        """Run all checks and NL tests for this phase."""

    def execute(self) -> None:
        print(f"\n{'='*60}")
        print(f"  {self.phase_id}: {self.label}")
        print(f"{'='*60}")
        self.setup()
        self.run_all()
        self.log.print_phase_summary(self.phase_id)

    # ------------------------------------------------------------------
    # Convenience helpers for recording checks
    # ------------------------------------------------------------------

    def _pass(self, cid: str, ctype: str, cat: str, target: str, detail: str = "") -> CheckResult:
        return self.log.pass_(cid, self.phase_id, ctype, cat, target, detail)

    def _fail(self, cid: str, ctype: str, cat: str, target: str,
              expected: str = "", actual: str = "", detail: str = "", suggestion: str = "") -> CheckResult:
        return self.log.fail(cid, self.phase_id, ctype, cat, target, expected, actual, detail, suggestion)

    def _warn(self, cid: str, ctype: str, cat: str, target: str,
              expected: str = "", actual: str = "", detail: str = "", suggestion: str = "") -> CheckResult:
        return self.log.warn(cid, self.phase_id, ctype, cat, target, expected, actual, detail, suggestion)

    def _check_file(self, cid: str, path: str, should_exist: bool = True) -> CheckResult:
        exists = os.path.exists(path)
        if exists == should_exist:
            return self._pass(cid, "file_exists", "file_integrity", path,
                              detail=f"exists={exists}")
        if should_exist:
            return self._fail(cid, "file_exists", "file_integrity", path,
                              expected="file exists", actual="not found",
                              detail=f"Missing: {path}")
        return self._fail(cid, "file_exists", "file_integrity", path,
                          expected="file should NOT exist", actual="found",
                          detail=f"Unexpected file: {path}")

    def _check_json(self, cid: str, path: str) -> CheckResult:
        """Check a JSON file is valid."""
        if not os.path.exists(path):
            return self._fail(cid, "json_valid", "file_integrity", path,
                              expected="valid JSON", actual="file not found",
                              detail=f"Missing: {path}")
        try:
            with open(path, encoding="utf-8") as f:
                json.load(f)
            return self._pass(cid, "json_valid", "file_integrity", path)
        except json.JSONDecodeError as e:
            return self._fail(cid, "json_valid", "file_integrity", path,
                              expected="valid JSON", actual=f"parse error: {e}",
                              detail=f"File: {path}, error: {e}",
                              suggestion="Check for trailing commas, unclosed braces, or mismatched quotes")

    def _check_card_strength(self, cid: str, cat: str, card: str,
                             expected_min: float = 0.0, expected_max: float = 1.0) -> CheckResult:
        """Check a card's strength is within expected range."""
        from lib.time_machine import get_strength
        fpath = os.path.join(self.kb.wiki_dir, cat, f"{card}.md")
        s = get_strength(fpath)
        if s is None:
            return self._fail(cid, "strength_check", "data_inconsistency", f"{cat}/{card}",
                              expected=f"strength in [{expected_min}, {expected_max}]",
                              actual="no strength field",
                              detail=f"Card missing strength field: {fpath}")
        if expected_min <= s <= expected_max:
            return self._pass(cid, "strength_check", "data_inconsistency", f"{cat}/{card}",
                              detail=f"strength={s} in [{expected_min}, {expected_max}]")
        return self._fail(cid, "strength_check", "data_inconsistency", f"{cat}/{card}",
                          expected=f"strength in [{expected_min}, {expected_max}]",
                          actual=f"strength={s}",
                          detail=f"Card {fpath}: strength={s}, expected [{expected_min}, {expected_max}]")

    def _post_check(self, cid: str, post: PostCheck, cat: str = "retrieval_mismatch") -> CheckResult:
        """Record a PostCheck result."""
        if post.passed:
            return self._pass(cid, "nl_post_check", cat, post.description, detail=post.actual)
        return self._fail(cid, "nl_post_check", cat, post.description,
                          expected=post.expected, actual=post.actual,
                          detail=f"Card: {post.card_path}")


import json
import os
