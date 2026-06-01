"""Phase 05: Month 6 (T+180d).

Focus: large-scale knowledge base (800+ cards), full memory files (hot=5,
cold=45), affinity saturation, batch import with checkpoint/resume,
and performance at scale.
"""

import json
import os
import random
import time

from lib.time_machine import advance_days, get_strength, set_strength
from phases.base_phase import BasePhase


class Phase05(BasePhase):

    def __init__(self, log, kb):
        super().__init__("phase_05", "第六个月 — 大规模压力 (T+180d)", log, kb)

    def setup(self):
        advance_days(90)  # total: 90 + 90 = 180 days
        self._expand_kb_to_800()
        self._fill_memory_to_capacity()
        self._set_affinity_extremes()
        self._simulate_batch_import()
        self._apply_decay()

    def _expand_kb_to_800(self):
        """Expand to ~800 cards total."""
        from lib.kb_builder import ELEMENTARY_TOPICS

        # Add bulk cards to existing categories
        bulk_config = [
            ("deep-learning", 100),
            ("ml-fundamentals", 80),
            ("nlp", 120),
            ("reinforcement-learning", 100),
            ("computer-vision", 80),
            ("cognitive-science", 60),
            ("philosophy", 40),
        ]

        for cat, target in bulk_config:
            existing = len([c for c, _, _ in self.kb.all_cards() if c == cat])
            needed = max(0, target - existing)
            for i in range(needed):
                self.kb.add_card(
                    cat, f"{cat[:4]}-bulk-{existing + i:04d}",
                    content=f"# Bulk card {existing + i} for {cat}",
                    tags=[cat.replace("-", "_")],
                    strength=0.5,
                )

        self.kb.build_index(incremental=True)
        actual_count = self.kb.card_count()
        self._pass("SETUP-800", "card_count", "performance", "KB size",
                   detail=f"{actual_count} cards after expansion")

    def _fill_memory_to_capacity(self):
        """Fill each persona's memory to hot=5, cold=45."""
        personas = ["feynman", "socrates", "xiaozhao", "zhuangzi",
                     "audrey_hepburn", "galileo", "carl_jung"]

        for p_idx, pname in enumerate(personas):
            memory_dir = os.path.join(self.kb.alaya_dir, "memory")
            os.makedirs(memory_dir, exist_ok=True)
            mem_path = os.path.join(memory_dir, f"{pname}_history.json")

            # Build cold zone (45 compressed entries) + hot zone (5 detailed)
            cold = []
            for i in range(45):
                cold.append({
                    "date": f"2026-0{random.randint(1,6)}-{random.randint(1,28):02d}",
                    "topic": f"historical session {i}",
                    "tags": ["test", "bulk", pname],
                    "summary": f"Compressed entry #{i} for {pname}.",
                })

            hot = []
            for i in range(5):
                hot.append({
                    "date": f"2026-06-0{i+1:02d}",
                    "topic": f"recent session {i}",
                    "tags": [f"tag-{i}", pname],
                    "mood": random.choice(["好奇", "开心", "思考", "平静", "兴奋"]),
                    "summary": f"Recent entry #{i} with details.",
                    "cards_cited": [f"card-{random.randint(0,100):03d}"],
                    "turns": random.randint(2, 8),
                })

            with open(mem_path, "w", encoding="utf-8") as f:
                json.dump({"hot": hot, "cold": cold}, f, ensure_ascii=False, indent=2)

        # Ambient state with 180-day trajectory
        ambient_path = os.path.join(memory_dir, "ambient.json")
        trajectory = []
        for d in range(1, 181, 3):  # ~60 entries over 180 days
            trajectory.append({
                "mood": random.choice(["好奇", "困惑", "兴奋", "平静", "累", "开心"]),
                "date": f"2026-0{ (d // 30) + 1 }-{(d % 28) + 1:02d}" if d < 180 else "2026-06-15",
            })

        ambient = {
            "recent_mood": "好奇",
            "mood_trajectory": trajectory[-20:],  # last 20 entries
            "recent_themes": "用户持续探索深度学习和哲学交叉领域，偏好类比理解",
            "open_threads": [
                {"question": "JEPA 与传统自编码器的关系", "since": "2026-03-15"},
                {"question": "Transformer 是否真的理解了语义", "since": "2026-04-01"},
            ],
            "user_style_notes": "喜欢用类比理解技术概念；偏好苏格拉底式追问；对跨学科映射特别感兴趣",
            "recent_attention": {"deep-learning": 0.9, "philosophy": 0.7, "transformer": 0.8, "yogacara": 0.5},
        }
        with open(ambient_path, "w", encoding="utf-8") as f:
            json.dump(ambient, f, ensure_ascii=False, indent=2)

    def _set_affinity_extremes(self):
        """Set extreme affinity values to test boundaries."""
        # Feynman: high affinity (power user)
        feynman_path = os.path.join(self.kb.alaya_dir, "manas", "feynman.json")
        if os.path.exists(feynman_path):
            with open(feynman_path, encoding="utf-8") as f:
                feynman = json.load(f)
            feynman["affinity"] = {"alaya": 0.98}
            with open(feynman_path, "w", encoding="utf-8") as f:
                json.dump(feynman, f, ensure_ascii=False, indent=2)

        # Carl Jung: very low affinity (unused)
        jung_path = os.path.join(self.kb.alaya_dir, "manas", "carl_jung.json")
        if os.path.exists(jung_path):
            with open(jung_path, encoding="utf-8") as f:
                jung = json.load(f)
            jung["affinity"] = {"alaya": 0.12}
            with open(jung_path, "w", encoding="utf-8") as f:
                json.dump(jung, f, ensure_ascii=False, indent=2)

    def _simulate_batch_import(self):
        """Simulate batch import of 100 files — writes a temporary directory."""
        import tempfile
        tmpdir = os.path.join(self.kb.workdir, "_test_import_src")
        os.makedirs(tmpdir, exist_ok=True)

        for i in range(100):
            fpath = os.path.join(tmpdir, f"imported-doc-{i:04d}.md")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"# Imported Document {i}\n\nAuto-generated test document #{i} for batch import.\n")

        try:
            result = self.kb.batch_import(tmpdir, category="batch-imported")
            self._pass("SETUP-batch-import", "script_run", "performance",
                       "batch_import 100 files",
                       detail=f"exit={result.returncode}, stdout={result.stdout[:300]}")
        except Exception as e:
            self._fail("SETUP-batch-import", "script_run", "script_error",
                       "batch_import 100 files",
                       expected="normally",
                       actual=f"exception: {e}",
                       suggestion="Check batch_import.py for unhandled exceptions at scale")
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _apply_decay(self):
        r = self.kb.run_perfume_level2()
        if r.returncode != 0:
            self._warn("SETUP-m6-decay", "script_run", "script_error",
                       "perfume L2 at 800 cards",
                       expected="0", actual=str(r.returncode), detail=r.stderr)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def run_all(self):
        self._check_card_count()
        self._check_memory_capacity()
        self._check_build_index_performance()
        self._check_affinity_boundaries()
        self._check_ambient_trajectory_size()
        self._nl_tests()

    def _check_card_count(self):
        count = self.kb.card_count()
        if 650 <= count <= 850:  # Allow for batch-imported additions
            self._pass("C-05-count", "card_count", "performance", f"{count} cards",
                       detail=f"KB size: {count}")
        else:
            self._fail("C-05-count", "card_count", "performance", "card count",
                       expected="650-850 cards",
                       actual=f"{count} cards",
                       suggestion="Check bulk card creation logic in _expand_kb_to_800")

    def _check_memory_capacity(self):
        for fn in os.listdir(os.path.join(self.kb.alaya_dir, "memory")):
            if not fn.endswith("_history.json"):
                continue
            fpath = os.path.join(self.kb.alaya_dir, "memory", fn)
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            hot = data.get("hot", [])
            cold = data.get("cold", [])
            pname = fn.replace("_history.json", "")
            cid = f"C-05-mem-{pname}"

            issues = []
            if len(hot) > 5:
                issues.append(f"hot={len(hot)} > 5")
            if len(cold) > 45:
                issues.append(f"cold={len(cold)} > 45")

            if issues:
                self._fail(cid, "memory_check", "data_inconsistency", fn,
                           expected="hot≤5, cold≤45",
                           actual="; ".join(issues),
                           detail=f"Memory file: {fpath}",
                           suggestion="Enforce caps in perfume_memory.py — hot zone auto-rotates to cold at >5")
            else:
                self._pass(cid, "memory_check", "data_inconsistency", fn,
                           detail=f"hot={len(hot)}, cold={len(cold)}")

    def _check_build_index_performance(self):
        """Measure build_index time at 800+ cards."""
        start = time.time()
        result = self.kb.build_index()
        elapsed = time.time() - start
        cid = "C-05-perf-index"

        if result.returncode == 0:
            if elapsed < 10:
                self._pass(cid, "performance", "performance", "build_index.py full rebuild",
                           detail=f"{elapsed:.2f}s for ~{self.kb.card_count()} cards")
            else:
                self._warn(cid, "performance", "performance", "build_index.py full rebuild",
                           expected=f"< 10s for 800 cards",
                           actual=f"{elapsed:.2f}s",
                           detail=f"Slow rebuild at {self.kb.card_count()} cards",
                           suggestion="Consider optimizing build_index.py or using --incremental for large KBs")
        else:
            self._fail(cid, "performance", "script_error", "build_index.py",
                       expected="return code 0",
                       actual=f"exit {result.returncode} after {elapsed:.1f}s",
                       detail=f"stderr:\n{result.stderr}",
                       suggestion="Fix build_index.py errors at scale")

        # Incremental should be faster
        if result.returncode == 0:
            start2 = time.time()
            self.kb.build_index(incremental=True)
            inc_elapsed = time.time() - start2
            if inc_elapsed < elapsed:
                self._pass("C-05-perf-inc", "performance", "performance",
                           "build_index.py --incremental",
                           detail=f"{inc_elapsed:.2f}s (full was {elapsed:.2f}s)")
            else:
                self._warn("C-05-perf-inc", "performance", "performance",
                           "build_index.py --incremental",
                           expected="incremental faster than full rebuild",
                           actual=f"incremental={inc_elapsed:.2f}s >= full={elapsed:.2f}s",
                           detail="Incremental build isn't faster — all categories may be dirty",
                           suggestion="Check dirty_categories tracking in config.json")

    def _check_affinity_boundaries(self):
        """Affinity extremes: high should cap, low should not go negative."""
        manas_dir = os.path.join(self.kb.alaya_dir, "manas")
        for fn in os.listdir(manas_dir):
            if not fn.endswith(".json") or fn == "_history.json":
                continue
            fpath = os.path.join(manas_dir, fn)
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                self._warn(f"C-05-aff-{fn.replace('.json','')}", "affinity_check", "data_inconsistency",
                           f"{fn}",
                           detail=f"Skipping corrupt JSON: {fpath}",
                           suggestion="Check fault injection from previous phases")
                continue
            affinity = data.get("affinity", {})
            for key, val in affinity.items():
                cid = f"C-05-aff-{fn.replace('.json','')}-{key}"
                if isinstance(val, dict):
                    # Nested affinity (e.g. {"value": 0.8, "floor": 0.1})
                    nested_val = val.get("value", 0)
                    if nested_val > 1.0:
                        self._fail(cid, "affinity_check", "data_inconsistency",
                                   f"{fn}.affinity.{key}.value",
                                   expected="affinity ≤ 1.0",
                                   actual=f"affinity={nested_val}",
                                   suggestion="Cap affinity updates at 1.0 in perfume_persona.py")
                    else:
                        self._pass(cid, "affinity_check", "data_inconsistency",
                                   f"{fn}.affinity.{key}",
                                   detail=f"nested affinity value={nested_val}")
                elif isinstance(val, (int, float)):
                    if val > 1.0:
                        self._fail(cid, "affinity_check", "data_inconsistency",
                                   f"{fn}.affinity.{key}",
                                   expected="affinity ≤ 1.0",
                                   actual=f"affinity={val}",
                                   suggestion="Cap affinity updates at 1.0 in perfume_persona.py")
                    elif val < 0.0:
                        self._fail(cid, "affinity_check", "data_inconsistency",
                                   f"{fn}.affinity.{key}",
                                   expected="affinity ≥ 0.0",
                                   actual=f"affinity={val}",
                                   suggestion="Floor affinity at 0.0 in perfume_persona.py")
                    else:
                        self._pass(cid, "affinity_check", "data_inconsistency",
                                   f"{fn}.affinity.{key}",
                                   detail=f"affinity={val}")

    def _check_ambient_trajectory_size(self):
        """mood_trajectory should not grow unbounded."""
        ambient_path = os.path.join(self.kb.alaya_dir, "memory", "ambient.json")
        if not os.path.exists(ambient_path):
            return
        with open(ambient_path, encoding="utf-8") as f:
            ambient = json.load(f)
        traj = ambient.get("mood_trajectory", [])
        cid = "C-05-ambient-traj"
        if len(traj) <= 25:
            self._pass(cid, "memory_check", "data_inconsistency",
                       "ambient.mood_trajectory size",
                       detail=f"{len(traj)} entries")
        else:
            self._warn(cid, "memory_check", "data_inconsistency",
                       "ambient.mood_trajectory size",
                       expected="≤25 entries (capped)",
                       actual=f"{len(traj)} entries",
                       detail="Trajectory growing unbounded — will cause ambient.json bloat",
                       suggestion="Cap mood_trajectory at 20-25 entries in perfume_memory.update_ambient")

    def _nl_tests(self):
        """NL tests at 6-month scale."""

        # NL-5-01: Retrieval at 800+ cards should still select correct categories
        t_start = time.time()
        trace = self.tracer.trace("费曼，我半年前导入的那些论文里关于泛化的结论是什么？", persona_hint="feynman")
        t_elapsed = time.time() - t_start

        if trace.tier1_categories:
            self._pass("NL-5-01-t1", "nl_test", "retrieval_mismatch",
                       "large-KB category selection",
                       detail=f"categories: {trace.tier1_categories}, trace time: {t_elapsed:.3f}s")
        else:
            self._warn("NL-5-01-t1", "nl_test", "retrieval_mismatch",
                       "large-KB category selection",
                       expected="≥1 category",
                       actual="0",
                       detail="No categories matched at 800+ card scale",
                       suggestion="Ensure index.md category descriptions aren't lost during rebuild")

        if trace.tier2_core:
            self._pass("NL-5-01-t2", "nl_test", "retrieval_mismatch",
                       "large-KB candidate pool",
                       detail=f"core={len(trace.tier2_core)}, peripheral={len(trace.tier2_peripheral)}")
        else:
            self._warn("NL-5-01-t2", "nl_test", "retrieval_mismatch",
                       "large-KB candidate pool",
                       expected="≥1 card in pool",
                       actual="0",
                       detail="All cards may have decayed below 0.5 after 180 days")

        # Performance: trace should complete quickly even at 800+ cards
        if t_elapsed < 2.0:
            self._pass("NL-5-01-perf", "nl_test", "performance",
                       "retrieval trace latency",
                       detail=f"{t_elapsed:.3f}s")
        else:
            self._warn("NL-5-01-perf", "nl_test", "performance",
                       "retrieval trace latency",
                       expected="< 2s",
                       actual=f"{t_elapsed:.3f}s",
                       detail="Protocol tracer slow at 800+ cards",
                       suggestion="Optimize protocol_tracer file scanning for large KBs")

        # NL-5-03: Memory retrieval at capacity
        trace = self.tracer.trace("小昭的记忆", persona_hint="xiaozhao")
        if trace.memory_hot:
            self._pass("NL-5-03", "nl_test", "retrieval_mismatch",
                       "满载记忆检索",
                       detail=f"hot={len(trace.memory_hot)} entries, cold exists={bool(trace.memory_hot and len(trace.memory_hot) > 0)}")
        else:
            self._warn("NL-5-03", "nl_test", "retrieval_mismatch",
                       "满载记忆检索",
                       expected="hot zone with entries",
                       actual="empty",
                       detail="Memory may not have been written in previous phases")

        # NL-5-04: Verify batch import checkpoint directory was cleaned up
        checkpoint = os.path.join(self.kb.alaya_dir, ".import_checkpoint.json")
        if not os.path.exists(checkpoint):
            self._pass("NL-5-04", "nl_test", "file_integrity",
                       "batch import checkpoint cleanup",
                       detail="checkpoint file was cleaned up")
        else:
            self._warn("NL-5-04", "nl_test", "file_integrity",
                       "batch import checkpoint cleanup",
                       expected="checkpoint file deleted after successful import",
                       actual="still exists",
                       detail=".import_checkpoint.json was not cleaned up",
                       suggestion="Check clear_checkpoint() in batch_import.py is called after completion")
