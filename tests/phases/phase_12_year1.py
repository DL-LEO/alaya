"""Phase 12: Year 1 (T+365d).

Focus: full annual cycle — extreme decay, resurrection from near-zero,
year-long memory accumulation, complete knowledge graph lifecycle,
and holistic end-to-end verification.

This is the "graduation" phase: if the system survives a simulated year
of use with data integrity intact, the lifecycle test is considered
successful.
"""

import json
import os
import random

from lib.time_machine import (
    advance_days, get_strength, set_strength, get_activation_count,
    calc_strength,
)
from phases.base_phase import BasePhase


class Phase12(BasePhase):

    def __init__(self, log, kb):
        super().__init__("phase_12", "第十二个月 — 年度完整回检 (T+365d)", log, kb)

    def setup(self):
        advance_days(185)  # total: 180 + 185 = 365 days
        self._expand_to_1500()
        self._set_zero_strength_cards()
        self._resurrect_old_cards()
        self._apply_final_decay()
        self._build_final_index()

    def _expand_to_1500(self):
        """Expand to ~1500 cards total."""
        categories = self.kb.category_names()
        target_per_cat = max(150, 1500 // len(categories))

        for cat in categories:
            existing = len([c for c, _, _ in self.kb.all_cards() if c == cat])
            needed = max(0, target_per_cat - existing)
            for i in range(needed):
                self.kb.add_card(
                    cat, f"y1-{cat[:4]}-{existing + i:04d}",
                    content=f"# Year-1 card {existing + i} for {cat}",
                    tags=[cat.replace("-", "_")],
                    strength=random.uniform(0.3, 0.7),
                    last_activated=f"2025-{random.randint(6,12):02d}-{random.randint(1,28):02d}",
                )

    def _set_zero_strength_cards(self):
        """Simulate ~700 cards reaching near-zero strength from disuse."""
        from lib.time_machine import set_strength
        all_cards = self.kb.all_cards()
        # Pick 700 cards to have very low strength
        random.seed(365)
        candidates = [(c, n, p) for c, n, p in all_cards if "y1" not in n]
        zero_cards = random.sample(candidates, min(700, len(candidates)))
        for cat, name, fpath in zero_cards:
            s = get_strength(fpath)
            if s is not None and s > 0.1:
                set_strength(fpath, random.uniform(0.0001, 0.009))

    def _resurrect_old_cards(self):
        """Wake some cards as if user re-discovered old knowledge."""
        result = self.kb.run_script("perfume.py", [
            "--wake", "concept", "--alaya", self.kb.alaya_dir,
            "--wiki", self.kb.wiki_dir,
        ])
        if result.returncode == 0 and "Woken" in result.stdout:
            self._pass("SETUP-resurrect", "script_run", "script_error",
                       "year-1 card resurrection",
                       detail=result.stdout[:200])
        else:
            self._warn("SETUP-resurrect", "script_run", "script_error",
                       "year-1 card resurrection",
                       expected="wake_seeds finds and wakes cards",
                       actual=f"exit={result.returncode}",
                       detail=result.stdout[:300])

    def _apply_final_decay(self):
        """Apply year-long decay across all cards."""
        r = self.kb.run_perfume_level2()
        if r.returncode != 0:
            self._fail("SETUP-y1-decay", "script_run", "script_error",
                       "year-1 decay", expected="0", actual=str(r.returncode),
                       detail=f"stderr:\n{r.stderr[:500]}")

    def _build_final_index(self):
        """Final index rebuild for the year."""
        r = self.kb.build_index()
        if r.returncode != 0:
            self._fail("SETUP-y1-index", "script_run", "script_error",
                       "year-1 build_index",
                       expected="0", actual=str(r.returncode), detail=r.stderr)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def run_all(self):
        self._check_card_count()
        self._check_extreme_decay()
        self._check_resurrection()
        self._check_final_integrity()
        self._check_disk_usage()
        self._nl_tests()
        self._holistic_assessment()

    def _check_card_count(self):
        count = self.kb.card_count()
        if count >= 1400:
            self._pass("C-12-count", "card_count", "performance", f"{count} cards",
                       detail=f"Year-end KB size: {count}")
        else:
            self._warn("C-12-count", "card_count", "performance", "card count",
                       expected=">=1400 cards",
                       actual=f"{count}",
                       detail="Knowledge base didn't reach target size",
                       suggestion="Increase _expand_to_1500 target or add more categories")

    def _check_extreme_decay(self):
        """Cards unused for 365 days: strength ≈ 0.5 * 0.977^365 ≈ 0.00003."""
        from lib.time_machine import get_strength
        # Find a card that was created at T+0 with strength=0.5 and never used
        # Use the 'rl' card from ml-fundamentals which was created in phase 1
        fpath = self.kb.card_path("ml-fundamentals", "rl")
        s = get_strength(fpath)
        if s is not None:
            expected = 0.5 * (0.977 ** 365)
            if s < 0.01:
                self._pass("C-12-decay", "strength_check", "time_anomaly",
                           "ml-fundamentals/rl (365d unused)",
                           detail=f"strength={s:.6f}, theoretical ≈{expected:.6f}")
            else:
                self._fail("C-12-decay", "strength_check", "time_anomaly",
                           "ml-fundamentals/rl (365d unused)",
                           expected=f"strength < 0.01 after 365d decay",
                           actual=f"strength={s:.6f}",
                           detail=f"Expected ~{expected:.6f}, got {s:.6f}",
                           suggestion="Check decay_all applies decay *= (rate^days) correctly across multiple runs")

    def _check_resurrection(self):
        """Cards woken by wake_seeds should have strength≈0.5 despite year-long context."""
        from lib.time_machine import get_strength
        # Find cards with "concept" in name that were woken
        woken_count = 0
        for cat, name, fpath in self.kb.all_cards():
            if "concept" in name.lower():
                s = get_strength(fpath)
                if s is not None and s >= 0.4:
                    woken_count += 1

        if woken_count > 0:
            self._pass("C-12-resurrect", "strength_check", "data_inconsistency",
                       "wake_seeds resurrection",
                       detail=f"{woken_count} concept cards at strength >= 0.4")
        else:
            self._warn("C-12-resurrect", "strength_check", "data_inconsistency",
                       "wake_seeds resurrection",
                       expected=">=1 card woken to ≥0.4",
                       actual="0",
                       detail="wake_seeds may not have matched 'concept' or cards don't exist",
                       suggestion="Check wake_seeds keyword matching in perfume_knowledge.py")

    def _check_final_integrity(self):
        """Run health_check in year-1 state and report all issues."""
        hc = self.kb.health_check()
        output = hc.stdout
        issues_found = output.count("Issues found:")
        if issues_found > 0:
            # Extract issue count
            for line in output.split('\n'):
                if 'Issues found:' in line:
                    try:
                        num = int(line.split(':')[1].strip())
                        if num == 0:
                            self._pass("C-12-integrity", "health_check", "file_integrity",
                                       "year-end integrity",
                                       detail="health_check reports 0 issues")
                        else:
                            self._fail("C-12-integrity", "health_check", "file_integrity",
                                       "year-end integrity",
                                       expected="0 issues",
                                       actual=f"{num} issues found",
                                       detail=f"Health check output:\n{output[:500]}",
                                       suggestion="Review health_check report for new issues introduced over the year")
                    except ValueError:
                        pass
        else:
            self._pass("C-12-integrity", "health_check", "file_integrity",
                       "year-end integrity",
                       detail="health_check ran successfully")

    def _check_disk_usage(self):
        """Check the total size of the workdir — should not be excessive."""
        total_size = 0
        for root, dirs, files in os.walk(self.kb.workdir):
            for fn in files:
                fpath = os.path.join(root, fn)
                try:
                    total_size += os.path.getsize(fpath)
                except OSError:
                    pass

        size_mb = total_size / (1024 * 1024)
        max_mb = 100  # 1500 cards should be under 100MB
        if size_mb <= max_mb:
            self._pass("C-12-disk", "performance", "performance",
                       "workdir disk usage",
                       detail=f"{size_mb:.1f} MB for {self.kb.card_count()} cards")
        else:
            self._warn("C-12-disk", "performance", "performance",
                       "workdir disk usage",
                       expected=f"< {max_mb} MB",
                       actual=f"{size_mb:.1f} MB",
                       detail="Disk usage higher than expected for 1500 cards",
                       suggestion="Check for accumulated checkpoints, backup files, or log files")

    def _nl_tests(self):
        """Year-end natural language tests."""

        # NL-6-01: Persona memory after 365 days
        trace = self.tracer.trace("费曼，还记得我们之前讨论过的所有话题吗？", persona_hint="feynman")
        if trace.memory_hot:
            self._pass("NL-6-01-mem", "nl_test", "retrieval_mismatch",
                       "year-end persona memory",
                       detail=f"hot={len(trace.memory_hot)} entries, topics: {[e.get('topic','')[:30] for e in trace.memory_hot[:3]]}")
        else:
            self._warn("NL-6-01-mem", "nl_test", "retrieval_mismatch",
                       "year-end persona memory",
                       expected="hot zone with >=1 entry",
                       actual="empty",
                       detail="Memory may have been lost during phase transitions",
                       suggestion="Ensure memory files persist across phases (not cleared between phase setups)")

        # NL-6-02: Wake from extreme dormancy
        result = self.kb.run_script("perfume.py", [
            "--wake", "quantum", "--alaya", self.kb.alaya_dir,
            "--wiki", self.kb.wiki_dir,
        ])
        if result.returncode == 0:
            self._pass("NL-6-02-wake", "nl_test", "script_error",
                       "唤醒一年沉睡知识",
                       detail=f"exit=0, output: {result.stdout[:200]}")
        else:
            self._fail("NL-6-02-wake", "nl_test", "script_error",
                       "唤醒一年沉睡知识",
                       expected="return code 0",
                       actual=str(result.returncode),
                       detail=result.stderr)

        # NL-6-03: New persona on year-old KB
        trace = self.tracer.trace("新来的，帮我看看之前积累了哪些知识", persona_hint="feynman")
        if trace.tier3_selected:
            self._pass("NL-6-03-new", "nl_test", "retrieval_mismatch",
                       "new persona on old KB",
                       detail=f"selected {len(trace.tier3_selected)} cards from {len(trace.tier2_core)} pool")
        else:
            self._warn("NL-6-03-new", "nl_test", "retrieval_mismatch",
                       "new persona on old KB",
                       expected="Tier3 selects cards from pool",
                       actual="empty selection",
                       detail="Persona-driven filtering returned no matches after a year",
                       suggestion="Check that interest_foci values haven't decayed or been lost")

        # NL-6-04: Final health check
        hc = self.kb.health_check()
        if hc.returncode == 0:
            self._pass("NL-6-04-health", "nl_test", "script_error",
                       "年度健康检查",
                       detail=hc.stdout[:300])
        else:
            self._warn("NL-6-04-health", "nl_test", "script_error",
                       "年度健康检查",
                       expected="return code 0",
                       actual=str(hc.returncode),
                       detail=hc.stdout[:500])

    def _holistic_assessment(self):
        """Overall assessment of the year-long lifecycle."""
        all_cards = self.kb.all_cards()
        total = len(all_cards)
        strengths = []
        for _, _, fpath in all_cards:
            s = get_strength(fpath)
            if s is not None:
                strengths.append(s)

        if not strengths:
            self._fail("C-12-holistic", "holistic", "data_inconsistency",
                       "year-end assessment",
                       expected="cards with strength data",
                       actual="no strength data")
            return

        avg_s = sum(strengths) / len(strengths)
        min_s = min(strengths)
        max_s = max(strengths)
        zero_near = sum(1 for s in strengths if s < 0.01)
        strong = sum(1 for s in strengths if s >= 0.5)

        detail = (
            f"Cards: {total} | Avg strength: {avg_s:.4f} | "
            f"Range: [{min_s:.4f}, {max_s:.4f}] | "
            f"Near-zero (<0.01): {zero_near} | Strong (≥0.5): {strong}"
        )

        if avg_s > 0 and max_s <= 1.0:
            self._pass("C-12-holistic", "holistic", "data_inconsistency",
                       "year-end assessment",
                       detail=detail)
        else:
            self._fail("C-12-holistic", "holistic", "data_inconsistency",
                       "year-end assessment",
                       expected="valid strength distribution",
                       actual=f"avg={avg_s:.4f}, min={min_s:.4f}, max={max_s:.4f}",
                       detail=detail,
                       suggestion="Review full strength distribution for anomalies")

        # Memory check across all personas
        mem_files = [f for f in os.listdir(os.path.join(self.kb.alaya_dir, "memory"))
                     if f.endswith("_history.json")]
        total_hot = 0
        total_cold = 0
        for mf in mem_files:
            with open(os.path.join(self.kb.alaya_dir, "memory", mf), encoding="utf-8") as f:
                data = json.load(f)
            total_hot += len(data.get("hot", []))
            total_cold += len(data.get("cold", []))
        self._pass("C-12-holistic-mem", "holistic", "data_inconsistency",
                   "year-end memory summary",
                   detail=f"Personas: {len(mem_files)} | Total hot: {total_hot} | Total cold: {total_cold}")
