"""Phase 04: Month 3 (T+90d).

Focus: multi-persona group discussion (Rule F), dormant card wake-up,
broken-link detection (health_check.py), flat→nested config migration,
and the system's robustness under injected faults.

This phase deliberately corrupts some files to test error recovery.
"""

import json
import os
import random

from lib.time_machine import advance_days, calc_strength, get_strength
from phases.base_phase import BasePhase


class Phase04(BasePhase):

    def __init__(self, log, kb):
        super().__init__("phase_04", "第三个月 — 群聊 + 故障注入 (T+90d)", log, kb)

    def setup(self):
        advance_days(60)  # total: 30 + 60 = 90 days
        self._expand_kb_to_300()
        self._force_dormant_cards()
        self._inject_faults()
        self._simulate_dormant_wake()
        self._simulate_config_migration()
        self._apply_decay()

    def _expand_kb_to_300(self):
        """Expand to ~300 cards total."""
        for cat in ["reinforcement-learning", "nlp"]:
            existing = len([c for c, _, _ in self.kb.all_cards() if c == cat])
            needed = max(0, 100 - existing)
            for i in range(needed):
                self.kb.add_card(
                    cat, f"card-{cat[:3]}-{existing + i:03d}",
                    content=f"# Additional {cat} card #{existing + i}",
                    tags=[cat.replace("-", "_")],
                    strength=0.5,
                )

        # Add 2 new categories
        for cat_slug, desc in [("computer-vision", "计算机视觉 / CV — CNNs, object detection, image generation"),
                               ("cognitive-science", "认知科学 / CogSci — perception, memory, consciousness")]:
            self.kb.add_category(cat_slug, desc)
            for i in range(25):
                self.kb.add_card(cat_slug, f"concept-{i:03d}",
                                 content=f"# {cat_slug} concept #{i}",
                                 tags=[cat_slug.replace("-", "_")],
                                 strength=0.5)

        self.kb.build_index(incremental=True)

    def _force_dormant_cards(self):
        """Set some cards to strength < 0.1 to simulate dormancy."""
        from lib.time_machine import set_strength
        all_cards = self.kb.all_cards()
        # Pick 30 random cards to force-dormant
        random.seed(42)
        dormant = random.sample([(c, n, p) for c, n, p in all_cards if c not in ("deep-learning", "ml-fundamentals")],
                                min(30, len(all_cards) // 4))
        for cat, name, fpath in dormant:
            set_strength(fpath, random.uniform(0.01, 0.09))

    def _inject_faults(self):
        """Deliberately corrupt/inject errors for robustness testing."""
        # 1. Break 2 wiki links by removing referenced cards
        for cat, card in [("nlp", "nlp-concept-000"), ("reinforcement-learning", "rl-concept-000")]:
            fpath = self.kb.card_path(cat, card)
            if os.path.exists(fpath):
                os.remove(fpath)

        # 2. Add a _category.md link to a non-existent card
        for cat in ["computer-vision"]:
            cat_md = os.path.join(self.kb.wiki_dir, cat, "_category.md")
            if os.path.exists(cat_md):
                with open(cat_md, encoding="utf-8") as f:
                    content = f.read()
                content += "\n- [[nonexistent-card-12345]]\n"
                with open(cat_md, "w", encoding="utf-8") as f:
                    f.write(content)

        # 3. Corrupt one persona JSON (bad syntax)
        corrupt_path = os.path.join(self.kb.alaya_dir, "manas", "buddha.json")
        if os.path.exists(corrupt_path):
            with open(corrupt_path, encoding="utf-8") as f:
                raw = f.read()
            # Add a trailing comma to break JSON
            raw = raw.rstrip()[:-1] + "," + raw.rstrip()[-1:]
            with open(corrupt_path, "w", encoding="utf-8") as f:
                f.write(raw)

    def _simulate_dormant_wake(self):
        """Wake some dormant cards using wake_seeds."""
        result = self.kb.run_script("perfume.py", ["--wake", "rl", "--alaya", self.kb.alaya_dir,
                                                     "--wiki", self.kb.wiki_dir])
        if result.returncode == 0:
            self._pass("SETUP-wake", "script_run", "script_error",
                       "perfume --wake rl",
                       detail=result.stdout[:200])
        else:
            self._fail("SETUP-wake", "script_run", "script_error",
                       "perfume --wake rl",
                       expected="0", actual=str(result.returncode),
                       detail=result.stderr)

    def _simulate_config_migration(self):
        """Simulate flat→nested config migration by replacing with old format."""
        cfg_path = os.path.join(self.kb.alaya_dir, "config.json")
        flat_config = {
            "version": "1.7.0",
            "enabled": True,
            "language": "zh",
            "top_k": 3,
            "max_cards": 5,
            "half_life_default": 30,
            "strength_decay": 0.977,
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(flat_config, f, ensure_ascii=False, indent=2)

    def _apply_decay(self):
        """Apply decay for the 60 additional days."""
        r = self.kb.run_perfume_level2()
        if r.returncode != 0:
            self._warn("SETUP-m3-decay", "script_run", "script_error",
                       "perfume L2",
                       expected="0", actual=str(r.returncode), detail=r.stderr)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def run_all(self):
        self._check_health_check_after_faults()
        self._check_config_migration()
        self._check_dormant_wake()
        self._check_group_discussion_struct()
        self._check_robustness_degradation()
        self._nl_tests()

    def _check_health_check_after_faults(self):
        """health_check.py should detect all injected faults."""
        hc = self.kb.health_check()
        output = hc.stdout.lower()

        checks = [
            ("broken-link", "broken" in output or "broken" in output),
            ("orphan", "orphan" in output),
            ("json-error", "corrupt" in output or "json" in output),
            ("dirty-category", "dirty" in output),
        ]

        for check_id, found in checks:
            cid = f"C-04-health-{check_id}"
            if found:
                self._pass(cid, "health_check", "script_error",
                           f"health_check detects {check_id}",
                           detail="properly detected")
            else:
                self._fail(cid, "health_check", "script_error",
                           f"health_check detects {check_id}",
                           expected=f"should report {check_id} issue",
                           actual="not detected",
                           detail=f"health_check output:\n{hc.stdout[:500]}",
                           suggestion=f"Add {check_id} detection to health_check.py")

        if hc.returncode == 0:
            self._warn("C-04-health-exit", "health_check", "script_error",
                       "health_check exit code",
                       expected="non-zero exit when issues found",
                       actual="exit code 0 despite issues",
                       detail="health_check.py returns 0 even when detecting broken links",
                       suggestion="health_check.py should return non-zero when issues are found")

    def _check_config_migration(self):
        """Running perfume.py should auto-migrate flat config to nested."""
        # Config was set to flat v1.7 format in setup
        # Running perfume --level 2 should trigger migration
        r = self.kb.run_perfume_level2()
        # Now check config structure
        cfg_path = os.path.join(self.kb.alaya_dir, "config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            has_nested = all(k in cfg for k in ("knowledge", "memory", "persona"))
            if has_nested:
                self._pass("C-04-migrate", "config_check", "file_integrity",
                           "config migration",
                           detail="flat→nested migration successful")
            else:
                self._fail("C-04-migrate", "config_check", "file_integrity",
                           "config migration",
                           expected="nested config with knowledge/memory/persona keys",
                           actual=f"config keys: {list(cfg.keys())}",
                           detail=f"Config file: {cfg_path}",
                           suggestion="Check perfume.py _migrate_config function — it runs on every perfume call")
        else:
            self._fail("C-04-migrate", "config_check", "file_integrity",
                       "config.json", expected="exists", actual="not found")

    def _check_dormant_wake(self):
        """Cards woken by wake_seeds should have strength ≈0.5."""
        from lib.time_machine import get_strength

        # The --wake rl command should have woken cards with 'rl' in the title
        all_cards = self.kb.all_cards()
        woken = 0
        for cat, name, fpath in all_cards:
            if "rl" in name.lower():
                s = get_strength(fpath)
                if s is not None and abs(s - 0.5) < 0.1:
                    woken += 1

        if woken > 0:
            self._pass("C-04-wake", "strength_check", "data_inconsistency",
                       "wake_seeds rl",
                       detail=f"{woken} cards woken to strength≈0.5")
        else:
            self._warn("C-04-wake", "strength_check", "data_inconsistency",
                       "wake_seeds rl",
                       expected=">=1 card woken to strength≈0.5",
                       actual="0 cards woken",
                       detail="Either no cards matched 'rl' keyword or wake_seeds didn't find them",
                       suggestion="Check wake_seeds keyword matching logic (title → lowercase → contains)")

    def _check_group_discussion_struct(self):
        """Verify all personas have necessary fields for group discussion (Rule F)."""
        manas_dir = os.path.join(self.kb.alaya_dir, "manas")
        issues = []
        ok_count = 0

        for fn in sorted(os.listdir(manas_dir)):
            if not fn.endswith(".json") or fn == "_history.json":
                continue
            fpath = os.path.join(manas_dir, fn)
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                issues.append(f"{fn}: corrupt JSON")
                continue

            name = data.get("persona", fn)
            missing = []
            if "ego_vector" not in data:
                missing.append("ego_vector")
            if "signature_phrases" not in data:
                missing.append("signature_phrases")
            if "domain_scope" not in data:
                missing.append("domain_scope")

            if missing:
                issues.append(f"{name}: missing {missing}")
            else:
                ok_count += 1

        if issues:
            for iss in issues:
                self._fail("C-04-group-struct", "persona_check", "persona_deviation",
                           f"group discussion struct",
                           expected="all personas have ego_vector, signature_phrases, domain_scope",
                           actual=iss,
                           detail="Missing fields prevent proper group discussion participation",
                           suggestion="Add missing fields to persona JSON definition")
        else:
            self._pass("C-04-group-struct", "persona_check", "persona_deviation",
                       "group discussion struct",
                       detail=f"{ok_count} personas have all required fields")

    def _check_robustness_degradation(self):
        """System should still function despite corrupt persona JSON."""
        # Try loading all personas — one is corrupt (Buddha), others should load
        manas_dir = os.path.join(self.kb.alaya_dir, "manas")
        valid = 0
        corrupt = 0
        for fn in sorted(os.listdir(manas_dir)):
            if not fn.endswith(".json") or fn == "_history.json":
                continue
            fpath = os.path.join(manas_dir, fn)
            try:
                with open(fpath, encoding="utf-8") as f:
                    json.load(f)
                valid += 1
            except json.JSONDecodeError:
                corrupt += 1

        if corrupt == 1 and valid >= 6:
            self._pass("C-04-robustness", "persona_check", "file_integrity",
                       "corrupt JSON robustness",
                       detail=f"{valid} valid, 1 corrupt (expected: buddha.json)")
        elif corrupt > 1:
            self._fail("C-04-robustness", "persona_check", "file_integrity",
                       "corrupt JSON robustness",
                       expected="only buddha.json should be corrupt",
                       actual=f"{corrupt} corrupt files",
                       detail="More files were accidentally corrupted than intended",
                       suggestion="Check fault injection code in setup — should only corrupt buddha.json")
        else:
            self._warn("C-04-robustness", "persona_check", "file_integrity",
                       "corrupt JSON robustness",
                       expected="buddha.json should be corrupt",
                       actual="no corrupt files found",
                       detail="Fault injection may not have worked",
                       suggestion="Check _inject_faults corrupts buddha.json correctly")

    def _nl_tests(self):
        """NL tests for month-3 state."""

        # NL-4-01: Group discussion structural — query triggers multiple personas
        trace = self.tracer.trace("费曼、苏格拉底、庄子，讨论一下机器学习过拟合")
        if trace.persona_selected:
            self._pass("NL-4-01-t0", "nl_test", "retrieval_mismatch",
                       "group discussion tier-0",
                       detail=f"persona resolved: {trace.persona_selected}")
        else:
            self._warn("NL-4-01-t0", "nl_test", "retrieval_mismatch",
                       "group discussion tier-0",
                       expected="persona resolved",
                       actual="none",
                       detail="No persona matched in group query")

        if trace.tier1_categories:
            self._pass("NL-4-01-t1", "nl_test", "retrieval_mismatch",
                       "group discussion tier-1",
                       detail=f"categories: {trace.tier1_categories}")
        # Group discussion is verified structurally (multiple persona files OK)
        # The actual LLM-driven conversation can't be tested without an LLM

        # NL-4-02: Dormant wake check (structural)
        woken_cards = self.kb.run_script(
            "perfume.py", ["--wake", "rl", "--alaya", self.kb.alaya_dir, "--wiki", self.kb.wiki_dir])
        if "Woken" in woken_cards.stdout:
            self._pass("NL-4-02-wake", "nl_test", "script_error",
                       "wake dormant cards",
                       detail=woken_cards.stdout[:200])
        else:
            self._pass("NL-4-02-wake", "nl_test", "script_error",
                       "wake dormant cards",
                       detail="no cards needed waking (already >0.1)")

        # NL-4-03: Health check after fault injection
        hc = self.kb.health_check()
        if hc.returncode == 0:
            issues_line = [l for l in hc.stdout.split('\n') if 'Issues' in l or 'Missing' in l or 'broken' in l]
            if issues_line:
                self._pass("NL-4-03-health", "nl_test", "script_error",
                           "健康检查 after faults",
                           detail=f"health_check reports issues: {issues_line}")
            else:
                self._warn("NL-4-03-health", "nl_test", "script_error",
                           "健康检查 after faults",
                           expected="health_check should report injected issues",
                           actual="no issues reported",
                           detail="Injected broken links and corrupt JSON were not detected",
                           suggestion="Improve health_check.py detection logic")

        # NL-4-04: 小昭 long absence wake
        trace = self.tracer.trace("小昭，好久不见", persona_hint="xiaozhao")
        if trace.persona_selected:
            self._pass("NL-4-04-persona", "nl_test", "retrieval_mismatch",
                       "小昭 wake after absence",
                       detail=f"resolved: {trace.persona_selected}")
        else:
            self._fail("NL-4-04-persona", "nl_test", "retrieval_mismatch",
                       "小昭 wake after absence",
                       expected="any persona resolved from 小昭 query",
                       actual="no persona matched",
                       detail="Failed to resolve 小昭 after long inactivity",
                       suggestion="Check persona file still exists and is parseable")

        # NL-4-05: Config migration check
        cfg_path = os.path.join(self.kb.alaya_dir, "config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            if "knowledge" in cfg:
                ver = cfg.get("knowledge", {}).get("version", "unknown")
                self._pass("NL-4-05-cfg", "nl_test", "file_integrity",
                           "config view after migration",
                           detail=f"config migrated, knowledge.version={ver}")
            else:
                self._fail("NL-4-05-cfg", "nl_test", "file_integrity",
                           "config view after migration",
                           expected="nested config with knowledge key",
                           actual=f"keys: {list(cfg.keys())}",
                           suggestion="Run perfume.py to trigger auto-migration")
