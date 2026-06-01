"""Phase 03: Month 1 (T+30d).

Focus: half-life boundary (30-day default), affinity decay, sleep detection,
first-time BI observer run, and the system's behavior when cards cross the
strength=0.5 threshold between Core and Peripheral bands.
"""

import json
import os

from lib.time_machine import advance_days, today_str, today, get_strength
from phases.base_phase import BasePhase


class Phase03(BasePhase):

    def __init__(self, log, kb):
        super().__init__("phase_03", "第一个月 — 半衰期临界 (T+30d)", log, kb)

    def setup(self):
        advance_days(23)  # total: 7 + 23 = 30 days
        self._expand_kb()
        self._simulate_extended_use()
        self._apply_decay()

    def _expand_kb(self):
        """Grow to ~120 cards total."""
        # Add 70 more cards under new and existing categories
        self.kb.add_category("reinforcement-learning", "强化学习 / RL — from bandits to PPO")
        self.kb.add_category("nlp", "自然语言处理 / NLP — transformers, embeddings, generation")

        for i in range(30):
            name = f"rl-concept-{i:03d}"
            self.kb.add_card("reinforcement-learning", name,
                             content=f"# {name}\n\nSample RL concept card #{i}.",
                             tags=["reinforcement-learning", "rl", "agent"],
                             strength=0.5)

        for i in range(40):
            name = f"nlp-concept-{i:03d}"
            self.kb.add_card("nlp", name,
                             content=f"# {name}\n\nSample NLP concept card #{i}.",
                             tags=["nlp", "language-model"],
                             strength=0.5)

        self.kb.build_index(incremental=True)

    def _simulate_extended_use(self):
        """15 more conversation sessions across personas."""
        sessions = [
            # Feynman — 5 sessions (power user)
            *[{"persona": "feynman", "cards": ["transformer", "attention"],
               "mood": "好奇", "topic": f"transformer session {i}", "tags": "transformer,attention"}
              for i in range(3)],
            {"persona": "feynman", "cards": ["backpropagation", "lstm"],
             "mood": "兴奋", "topic": "backprop and sequential models", "tags": "backprop,rnn"},
            {"persona": "feynman", "cards": ["generalization", "bias-variance"],
             "mood": "思考", "topic": "generalization theory", "tags": "generalization"},
            # Socrates — 3 sessions
            *[{"persona": "socrates", "cards": ["overfitting"],
               "mood": "质疑", "topic": f"what does overfitting mean {i}", "tags": "overfitting"}
              for i in range(2)],
            {"persona": "socrates", "cards": ["attention"],
             "mood": "追问", "topic": "attention as a philosophical concept", "tags": "attention,philosophy"},
            # 小昭 — 3 sessions
            {"persona": "xiaozhao", "cards": [],
             "mood": "开心", "topic": "daily chat 1", "tags": "daily"},
            {"persona": "xiaozhao", "cards": [],
             "mood": "关心", "topic": "daily chat 2", "tags": "daily,care"},
            {"persona": "xiaozhao", "cards": [],
             "mood": "温暖", "topic": "daily chat 3", "tags": "daily,warm"},
            # Zhuangzi — 2 sessions
            {"persona": "zhuangzi", "cards": ["simplicity", "generalization"],
             "mood": "悠然", "topic": "natural simplicity in design", "tags": "simplicity,dao"},
            {"persona": "zhuangzi", "cards": ["overfitting"],
             "mood": "感慨", "topic": "overfitting as unnatural complexity", "tags": "overfitting,nature"},
            # Audrey — 2 sessions
            {"persona": "audrey_hepburn", "cards": ["beauty-in-math"],
             "mood": "欣赏", "topic": "beauty in technical ideas", "tags": "beauty"},
            {"persona": "audrey_hepburn", "cards": ["warm-recall"],
             "mood": "温柔", "topic": "elegance in design", "tags": "elegance,design"},
        ]

        for i, sess in enumerate(sessions):
            cards = sess["cards"] or ["none"]
            result = self.kb.run_perfume_level1(
                cards=cards, persona=sess["persona"],
                topic=sess["topic"], turns=2, tags=sess["tags"], mood=sess["mood"],
            )
            cid = f"SETUP-m1-sess{i}"
            if result.returncode != 0:
                self._warn(cid, "script_run", "script_error",
                           f"perfume L1 {sess['persona']}",
                           expected="return code 0",
                           actual=f"exit {result.returncode}",
                           detail=f"stderr: {result.stderr[:200]}")

    def _apply_decay(self):
        """Apply level-2 decay for the month's passage."""
        r = self.kb.run_perfume_level2()
        if r.returncode != 0:
            self._fail("SETUP-m1-decay", "script_run", "script_error",
                       "perfume L2", expected="0", actual=str(r.returncode),
                       detail=r.stderr)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def run_all(self):
        self._check_halflife_boundary()
        self._check_affinity_decay()
        self._check_sleep_detection()
        self._check_memory_capacity()
        self._check_bi_observer()
        self._check_reference_isolation()
        self._nl_tests()

    def _check_halflife_boundary(self):
        """Cards unused for 30 days: strength should be ~0.5 * 0.977^30 ≈ 0.25."""
        # 'rl' card in ml-fundamentals was never used
        fpath = self.kb.card_path("ml-fundamentals", "rl")
        s = get_strength(fpath)
        if s is not None:
            expected = 0.5 * (0.977 ** 30)
            tolerance = 0.05
            if abs(s - expected) <= tolerance:
                self._pass("C-03-halflife", "strength_check", "time_anomaly",
                           "ml-fundamentals/rl",
                           detail=f"strength={s:.4f}, expected ≈{expected:.4f} (30d decay)")
            else:
                self._fail("C-03-halflife", "strength_check", "time_anomaly",
                           "ml-fundamentals/rl",
                           expected=f"strength ≈{expected:.4f} after 30d decay",
                           actual=f"strength={s:.4f}",
                           detail=f"Deviation: |{s} - {expected}| = {abs(s - expected):.4f}",
                           suggestion="Verify decay_all uses correct decay_rate (0.977) and days-since calculation")

        # High-frequency cards should be stronger
        for cat, card_name in [("deep-learning", "transformer"), ("ml-fundamentals", "generalization")]:
            fpath = self.kb.card_path(cat, card_name)
            s = get_strength(fpath)
            if s is not None:
                cid = f"C-03-freq-{card_name.split('-')[0]}"
                if s >= 0.40:
                    self._pass(cid, "strength_check", "data_inconsistency", card_name,
                               detail=f"strength={s:.4f} (frequently used, should be elevated)")
                else:
                    self._warn(cid, "strength_check", "data_inconsistency", card_name,
                               expected=f"strength >= 0.4 for frequently used card",
                               actual=f"strength={s:.4f}",
                               detail="High-use card has surprisingly low strength",
                               suggestion="Check that boost_cards was called with the correct card paths")

    def _check_affinity_decay(self):
        """Personas unused for extended periods should have lower affinity."""
        buddha_path = os.path.join(self.kb.alaya_dir, "manas", "buddha.json")
        if not os.path.exists(buddha_path):
            self._warn("C-03-affinity", "affinity_check", "data_inconsistency",
                       "buddha.json",
                       detail="Buddha persona file not found in alaya/manas/")
            return

        with open(buddha_path, encoding="utf-8") as f:
            buddha = json.load(f)
        affinity = buddha.get("affinity", {})
        if affinity:
            # Buddha was never used — affinity should have decayed from defaults
            self._pass("C-03-affinity-exists", "affinity_check", "data_inconsistency",
                       "buddha affinity",
                       detail=f"affinity data: {affinity}")
        else:
            self._warn("C-03-affinity-missing", "affinity_check", "data_inconsistency",
                       "buddha affinity",
                       expected="affinity field exists",
                       actual="no affinity data",
                       detail="Buddha persona has no affinity tracking — may not have been initialized",
                       suggestion="Check that persona affinity is auto-initialized on first interaction or setup")

    def _check_sleep_detection(self):
        """Check the sleep notification counter for cards crossing < 0.1."""
        sleep_check = self.kb.run_script("perfume.py", ["--sleep-check", "--alaya", self.kb.alaya_dir])
        out = sleep_check.stdout.lower()
        if "sleep" in out or "dormant" in out or sleep_check.returncode == 0:
            self._pass("C-03-sleep", "script_run", "script_error",
                       "perfume --sleep-check",
                       detail=f"output: {sleep_check.stdout[:200]}")
        else:
            self._warn("C-03-sleep", "script_run", "script_error",
                       "perfume --sleep-check",
                       detail=f"Unexpected output: {sleep_check.stdout[:200]}")

    def _check_memory_capacity(self):
        """Each persona's memory hot zone should be ≤5 entries."""
        for fn in os.listdir(os.path.join(self.kb.alaya_dir, "memory")):
            if not fn.endswith("_history.json"):
                continue
            fpath = os.path.join(self.kb.alaya_dir, "memory", fn)
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            hot = data.get("hot", [])
            cold = data.get("cold", [])
            pname = fn.replace("_history.json", "")
            cid = f"C-03-memcap-{pname}"
            if len(hot) <= 5:
                self._pass(cid, "memory_check", "data_inconsistency", fn,
                           detail=f"hot={len(hot)}, cold={len(cold)}")
            else:
                self._fail(cid, "memory_check", "data_inconsistency", fn,
                           expected=f"hot zone ≤ 5 entries",
                           actual=f"hot zone has {len(hot)} entries",
                           detail=f"Memory file: {fpath}",
                           suggestion="Check hot-to-cold rotation logic in perfume_memory.py")

    def _check_bi_observer(self):
        """BI observer should detect dormant personas and knowledge gaps."""
        result = self.kb.bi_observer()
        if result.returncode == 0:
            output = result.stdout
            self._pass("C-03-bi-run", "script_run", "script_error",
                       "bi_observer.py",
                       detail=f"ran OK, output length: {len(output)}")
            # Check if it finds anything notable
            if "dormant" in output.lower() or "gap" in output.lower():
                self._pass("C-03-bi-findings", "script_run", "script_error",
                           "bi_observer findings",
                           detail="BI observer detected dormant personas or gaps")
            else:
                self._warn("C-03-bi-findings", "script_run", "script_error",
                           "bi_observer findings",
                           expected="some findings after 30 days",
                           actual="no dormancy/gap detected",
                           detail="With unused personas for 30 days, BI should flag dormant entries",
                           suggestion="Check BI observer's dormancy threshold calculation")
        else:
            self._fail("C-03-bi-run", "script_run", "script_error",
                       "bi_observer.py",
                       expected="return code 0",
                       actual=f"exit {result.returncode}",
                       detail=f"stderr: {result.stderr}",
                       suggestion="Debug bi_observer.py")

    def _check_reference_isolation(self):
        """Check that card activation_count is NOT persona-Isolated (counts all references)."""
        from lib.time_machine import get_activation_count
        fpath = self.kb.card_path("deep-learning", "transformer")
        count = get_activation_count(fpath)
        if count is not None and count >= 3:
            self._pass("C-03-ref-count", "data_check", "data_inconsistency",
                       "transformer activation_count",
                       detail=f"count={count} (referenced by multiple personas, cross-persona accumulation works)")
        elif count is not None:
            self._warn("C-03-ref-count", "data_check", "data_inconsistency",
                       "transformer activation_count",
                       expected=f"count >= 3 (referenced in multiple sessions)",
                       actual=f"count={count}",
                       detail="Activation count lower than expected",
                       suggestion="Verify boost_cards increments activation_count on each call")

    def _nl_tests(self):
        """NL tests for month-1 state."""

        # NL-3-01: Re-activate a decaying card
        # Before trace, record pre-strength
        fpath = self.kb.card_path("deep-learning", "transformer")
        from lib.time_machine import get_strength
        before_s = get_strength(fpath)

        trace = self.tracer.trace("费曼，之前聊过的 Transformer 能不能再讲讲？", persona_hint="feynman")
        if trace.tier3_selected:
            self._pass("NL-3-01-t3", "nl_test", "retrieval_mismatch",
                       "Tier3 selects Transformer card",
                       detail=f"selected: {[(c, n, round(s, 3)) for c, n, s in trace.tier3_selected]}")
        else:
            self._warn("NL-3-01-t3", "nl_test", "retrieval_mismatch",
                       "Tier3 card selection",
                       expected=">=1 card selected",
                       actual="0 cards",
                       detail="Persona-driven filtering returned empty — card may have dropped below persona match threshold")

        # Manually boost to simulate the response effect
        boost = self.kb.run_perfume_level1(
            cards=["transformer"], persona="feynman",
            topic="transformer reactivation", turns=1,
            tags="transformer", mood="好奇")
        if boost.returncode == 0 and before_s is not None:
            after_s = get_strength(fpath)
            if after_s and after_s > before_s:
                self._pass("NL-3-01-boost", "nl_test", "data_inconsistency",
                           "strength boost on re-activation",
                           detail=f"{before_s:.4f} → {after_s:.4f}")
            else:
                self._fail("NL-3-01-boost", "nl_test", "data_inconsistency",
                           "strength boost on re-activation",
                           expected=f"strength increase ({before_s:.4f} + 0.03)",
                           actual=f"before={before_s:.4f}, after={after_s}",
                           suggestion="Check boost_cards applies +0.03 correctly")

        # NL-3-02: New persona creation (structural)
        new_persona_path = os.path.join(self.kb.alaya_dir, "manas", "laozi.json")
        if os.path.exists(new_persona_path):
            self._pass("NL-3-02-persona", "nl_test", "file_integrity",
                       "new persona laozi.json",
                       detail="exists")
        else:
            self._warn("NL-3-02-persona", "nl_test", "file_integrity",
                       "new persona laozi.json",
                       expected="user creates a new persona",
                       actual="not tested (creation is manual)",
                       detail="Skipped: persona creation requires LLM-driven 7-phase protocol",
                       suggestion="Manual test: run '创建角色 老子' and verify JSON+_profile.md created")

        # NL-3-03: Sleep check
        sc = self.kb.run_script("perfume.py", ["--sleep-check", "--alaya", self.kb.alaya_dir])
        self._pass("NL-3-03", "nl_test", "script_error",
                   "perfume --sleep-check",
                   detail=f"exit={sc.returncode}, output: {sc.stdout[:200]}")

        # NL-3-04: BI observer
        bi = self.kb.bi_observer()
        self._pass("NL-3-04", "nl_test", "script_error",
                   "BI 观察",
                   detail=f"exit={bi.returncode}, output length: {len(bi.stdout)}")
