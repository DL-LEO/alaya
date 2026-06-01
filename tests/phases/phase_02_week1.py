"""Phase 02: Week 1 of active use (T+7d).

Simulates ~5 real conversational sessions, each referencing specific wiki cards.
Runs perfume level-1 (strength boost) after each session, then level-2 (decay)
to simulate the passage of 7 days.  Verifies card strengths, memory files,
and ambient state evolve correctly.
"""

import json
import os

from lib.time_machine import (
    advance_days, today_str, today, get_strength,
    get_activation_count, get_last_activated,
)
from lib.protocol_tracer import PostCheck
from phases.base_phase import BasePhase


class Phase02(BasePhase):

    def __init__(self, log, kb):
        super().__init__("phase_02", "第一周使用模拟 (T+7d)", log, kb)

    def setup(self):
        # Advance date by 7 days from start
        advance_days(7)
        self._add_new_cards()
        self._simulate_conversations()
        self._run_level2_decay()
        self._run_level3_backfill()

    def _add_new_cards(self):
        """Add 20 more cards across categories for week-1 expansion."""
        # Template cards for known template keys (skip if already exist)
        for cat, keys in {
            "deep-learning": ["deep-learning"],
            "ml-fundamentals": ["rl", "overfitting", "generalization", "bias-variance"],
        }.items():
            for key in keys:
                fpath = os.path.join(self.kb.wiki_dir, cat, f"{key}.md")
                if not os.path.exists(fpath):
                    self.kb.add_template_card(cat, key)

        # Generic cards for topics without templates (skip if already exist)
        for cat, name, tags in [
            ("deep-learning", "lstm", ["deep-learning", "rnn", "nlp"]),
            ("deep-learning", "gan", ["deep-learning", "generative"]),
            ("deep-learning", "embedding", ["nlp", "representation-learning"]),
            ("ml-fundamentals", "python-basics", ["programming", "python"]),
            ("ml-fundamentals", "data-structures", ["computer-science", "algorithms"]),
            ("ml-fundamentals", "linear-regression", ["machine-learning", "statistics"]),
            ("ml-fundamentals", "decision-trees", ["machine-learning", "algorithms"]),
            ("ml-fundamentals", "svm", ["machine-learning", "algorithms"]),
            ("ml-fundamentals", "entropy", ["information-theory", "mathematics"]),
            ("ml-fundamentals", "backpropagation", ["deep-learning", "optimization"]),
        ]:
            fpath = os.path.join(self.kb.wiki_dir, cat, f"{name}.md")
            if not os.path.exists(fpath):
                self.kb.add_card(cat, name,
                                 content=f"# {name.replace('-', ' ').title()}\n\nContent about {name}.",
                                 tags=tags, strength=0.5)

        # Build index for new cards
        self.kb.build_index(incremental=True)

    def _simulate_conversations(self):
        """Simulate 5 NL conversations, each boosting relevant cards."""

        session_defs = [
            # Session 1: Feynman discusses Transformer
            {
                "persona": "feynman",
                "cards": ["transformer", "attention"],
                "mood": "好奇",
                "topic": "transformer architecture",
                "tags": "transformer,attention,deep-learning",
            },
            # Session 2: Socrates probes attention
            {
                "persona": "socrates",
                "cards": ["attention", "transformer"],
                "mood": "质疑",
                "topic": "what does attention really mean",
                "tags": "attention,philosophy",
            },
            # Session 3: 小昭 daily chat
            {
                "persona": "xiaozhao",
                "cards": [],
                "mood": "开心",
                "topic": "daily check-in",
                "tags": "daily",
            },
            # Session 4: Zhuangzi
            {
                "persona": "zhuangzi",
                "cards": ["generalization", "overfitting"],
                "mood": "悠然",
                "topic": "overfitting and natural simplicity",
                "tags": "generalization,nature",
            },
            # Session 5: Audrey on beauty in math
            {
                "persona": "audrey_hepburn",
                "cards": ["beauty-in-math", "simplicity"],
                "mood": "欣赏",
                "topic": "beauty and elegance in technical ideas",
                "tags": "beauty,elegance",
            },
        ]

        session_results = []
        for i, sess in enumerate(session_defs):
            cards_str = ",".join(sess["cards"]) if sess["cards"] else "none"
            result = self.kb.run_perfume_level1(
                cards=sess["cards"] or ["none"],
                persona=sess["persona"],
                topic=sess["topic"],
                turns=3,
                tags=sess["tags"],
                mood=sess["mood"],
            )
            session_results.append({
                "index": i,
                "persona": sess["persona"],
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            })

        # Record session results
        for sr in session_results:
            cid = f"SETUP-session{sr['index']}"
            if sr["returncode"] == 0:
                self._pass(cid, "script_run", "script_error",
                           f"perfume.py --level1 {sr['persona']}",
                           detail=f"OK: {sr['stdout'][:200]}")
            else:
                self._fail(cid, "script_run", "script_error",
                           f"perfume.py --level1 {sr['persona']}",
                           expected="return code 0",
                           actual=f"exit {sr['returncode']}",
                           detail=f"stderr:\n{sr['stderr']}",
                           suggestion="Check perfume.py argument parsing or card path resolution")

    def _run_level2_decay(self):
        """Run level-2 (decay all) to simulate 7 days passing."""
        result = self.kb.run_perfume_level2()
        if result.returncode != 0:
            self._fail("SETUP-decay", "script_run", "script_error",
                       "perfume.py --level2",
                       expected="return code 0",
                       actual=f"exit {result.returncode}",
                       detail=f"stderr:\n{result.stderr}",
                       suggestion="Check perfume_knowledge.decay_all for errors")

    def _run_level3_backfill(self):
        """Run level-3 backfill check."""
        result = self.kb.run_perfume_level3()
        if result.returncode != 0:
            self._warn("SETUP-backfill", "script_run", "script_error",
                       "perfume.py --level3",
                       expected="return code 0",
                       actual=f"exit {result.returncode}",
                       detail=f"stderr:\n{result.stderr}",
                       suggestion="Check perfume.py --level3 implementation")

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def run_all(self):
        self._check_card_boosts()
        self._check_memory_isolation()
        self._check_ambient_state()
        self._check_unused_cards_decayed()
        self._nl_tests()

    def _check_card_boosts(self):
        """Cards referenced during conversations should have boosted strength."""
        # Transformer and Attention were referenced twice — check
        for cat, card in [("deep-learning", "transformer"),
                          ("deep-learning", "attention")]:
            fpath = self.kb.card_path(cat, card)
            s = get_strength(fpath)
            count = get_activation_count(fpath)
            last = get_last_activated(fpath)
            cid = f"C-02-boost-{card}"

            if s is None:
                self._fail(cid, "strength_check", "data_inconsistency", f"{cat}/{card}",
                           expected="strength field exists", actual="not found")
                continue

            # After 2 boosts (each +0.03) + 7 days decay (0.977^7 ≈ 0.85)
            # base=0.5, boosted to 0.56, decayed: 0.56*0.977^7 ≈ 0.56*0.852 ≈ 0.477
            expected_min = 0.44
            expected_max = 0.60
            if expected_min <= s <= expected_max:
                self._pass(cid, "strength_check", "data_inconsistency", f"{cat}/{card}",
                           detail=f"strength={s:.4f}, count={count}, last={last}")
            else:
                self._fail(cid, "strength_check", "data_inconsistency", f"{cat}/{card}",
                           expected=f"strength in [{expected_min}, {expected_max}] after 2 boosts + 7d decay",
                           actual=f"strength={s:.4f}",
                           detail=f"Card: {fpath}, count={count}, last={last}",
                           suggestion="Check perfume_knowledge.boost_cards and decay_all formulas")

        # Beauty-In-Mathematics was referenced once
        fpath = self.kb.card_path("philosophy", "beauty-in-math")
        s = get_strength(fpath)
        if s is not None:
            # base=0.5, boosted to 0.53, decayed: 0.53*0.977^7 ≈ 0.452
            if 0.40 <= s <= 0.55:
                self._pass("C-02-boost-Beauty", "strength_check", "data_inconsistency",
                           "philosophy/Beauty-In-Mathematics",
                           detail=f"strength={s:.4f}")
            else:
                self._warn("C-02-boost-Beauty", "strength_check", "data_inconsistency",
                           "philosophy/Beauty-In-Mathematics",
                           expected=f"strength ≈0.45 (1 boost + 7d decay)",
                           actual=f"strength={s:.4f}",
                           detail="Single-boost card deviates from expected range",
                           suggestion="Verify boost_cards uses +0.03 per call")

    def _check_memory_isolation(self):
        """Each persona should have its own history file with correct hot zone."""
        for pname in ["feynman", "socrates", "xiaozhao", "zhuangzi", "audrey_hepburn"]:
            mem_path = os.path.join(self.kb.alaya_dir, "memory", f"{pname}_history.json")
            cid = f"C-02-mem-{pname}"

            if not os.path.exists(mem_path):
                self._fail(cid, "memory_check", "data_inconsistency", mem_path,
                           expected=f"{pname}_history.json created",
                           actual="not found",
                           suggestion="Check perfume.py --level1 creates memory directory and history files")
                continue

            with open(mem_path, encoding="utf-8") as f:
                data = json.load(f)

            hot = data.get("hot", [])
            cold = data.get("cold", [])

            if len(hot) > 0:
                self._pass(cid, "memory_check", "data_inconsistency", f"{pname} memory",
                           detail=f"hot={len(hot)}, cold={len(cold)}")
            else:
                self._fail(cid, "memory_check", "data_inconsistency", f"{pname} memory",
                           expected="hot zone has >=1 entry",
                           actual=f"hot zone empty",
                           detail=f"Memory file at {mem_path} has empty hot zone")

        # Cross-check: Feynman's memory should NOT contain 小昭's interaction
        feynman_mem = os.path.join(self.kb.alaya_dir, "memory", "feynman_history.json")
        xiaozhao_mem = os.path.join(self.kb.alaya_dir, "memory", "xiaozhao_history.json")
        if os.path.exists(feynman_mem) and os.path.exists(xiaozhao_mem):
            with open(feynman_mem, encoding="utf-8") as f:
                feynman_data = json.load(f)
            with open(xiaozhao_mem, encoding="utf-8") as f:
                xiaozhao_data = json.load(f)
            feynman_topics = [e.get("topic", "") for e in feynman_data.get("hot", [])]
            xiaozhao_topics = [e.get("topic", "") for e in xiaozhao_data.get("hot", [])]
            # Feynman should NOT have daily-checkin (xiaozhao's session)
            if any("daily" in t.lower() for t in feynman_topics):
                self._fail("C-02-mem-isolation", "memory_check", "data_inconsistency",
                           "memory isolation",
                           expected="Feynman memory does NOT contain 小昭's topics",
                           actual=f"Feynman hot topics: {feynman_topics}",
                           suggestion="Check that memory files are keyed by persona name, not shared")
            else:
                self._pass("C-02-mem-isolation", "memory_check", "data_inconsistency",
                           "memory isolation",
                           detail="Feynman and 小昭 have separate memory files")

    def _check_ambient_state(self):
        """Verify ambient.json reflects shared state."""
        post = self.tracer.check_ambient_updated()
        self._post_check("C-02-ambient", post)

        ambient_path = os.path.join(self.kb.alaya_dir, "memory", "ambient.json")
        if os.path.exists(ambient_path):
            with open(ambient_path, encoding="utf-8") as f:
                ambient = json.load(f)
            mood = ambient.get("recent_mood", "")
            attention = ambient.get("recent_attention", {})
            if mood:
                self._pass("C-02-ambient-mood", "memory_check", "data_inconsistency",
                           "ambient.recent_mood",
                           detail=f"mood='{mood}'")
            else:
                self._warn("C-02-ambient-mood", "memory_check", "data_inconsistency",
                           "ambient.recent_mood",
                           expected="non-empty recent_mood",
                           actual="empty or missing",
                           suggestion="Check perfume_memory.update_ambient sets recent_mood")
            if attention:
                self._pass("C-02-ambient-attn", "memory_check", "data_inconsistency",
                           "ambient.recent_attention",
                           detail=f"attention keys: {list(attention.keys())}")
            else:
                self._warn("C-02-ambient-attn", "memory_check", "data_inconsistency",
                           "ambient.recent_attention",
                           expected="non-empty recent_attention",
                           actual="empty or missing",
                           suggestion="Check that perfume level-1 tag parameter populates recent_attention")

    def _check_unused_cards_decayed(self):
        """Cards that were NOT referenced should have decayed."""
        # 'rl' card in ml-fundamentals was never referenced
        fpath = self.kb.card_path("ml-fundamentals", "rl")
        s = get_strength(fpath)
        if s is not None:
            # 7 days decay from 0.5: 0.5 * 0.977^7 ≈ 0.426
            if s < 0.48:
                self._pass("C-02-decay-unused", "strength_check", "time_anomaly",
                           "ml-fundamentals/rl",
                           detail=f"decayed to {s:.4f} (expected ≈0.43)")
            else:
                self._fail("C-02-decay-unused", "strength_check", "time_anomaly",
                           "ml-fundamentals/rl",
                           expected=f"strength < 0.48 after 7d decay",
                           actual=f"strength={s:.4f}",
                           detail="Unused card didn't decay as expected",
                           suggestion="Check decay_all formula: strength * (decay_rate ** days_since_activation)")

    def _nl_tests(self):
        """Natural language tests for week-1 state."""

        # NL-2-01: Feynman on Transformer (should still retrieve despite decay)
        trace = self.tracer.trace("费曼，Transformer 为什么需要注意力机制？", persona_hint="feynman")
        if "deep-learning" in trace.tier1_categories:
            self._pass("NL-2-01-cat", "nl_test", "retrieval_mismatch",
                       "category: deep-learning",
                       detail=f"Tier1 categories: {trace.tier1_categories}")
        else:
            self._fail("NL-2-01-cat", "nl_test", "retrieval_mismatch",
                       "category: deep-learning",
                       expected="deep-learning in category selection",
                       actual=f"categories: {trace.tier1_categories}",
                       detail="Transformer question didn't select deep-learning category",
                       suggestion="Ensure index.md descriptions include keywords like 'transformer', 'attention', 'deep learning'")

        if any(c in ("transformer", "attention") for _, c, _ in trace.tier2_core):
            self._pass("NL-2-01-pool", "nl_test", "retrieval_mismatch",
                       "pool has Transformer or Attention",
                       detail=f"core pool: {[(c, round(s, 3)) for _, c, s in trace.tier2_core[:5]]}")
        else:
            self._warn("NL-2-01-pool", "nl_test", "retrieval_mismatch",
                       "pool has Transformer or Attention",
                       expected="Transformer or Attention cards in core pool",
                       actual="not found",
                       detail="Cards may have dropped below strength=0.5 threshold after decay")

        # NL-2-02: Socrates memory check
        post = self.tracer.check_memory("socrates", "attention")
        self._post_check("NL-2-02-mem", post)

        # NL-2-03: 小昭 ambient awareness
        trace = self.tracer.trace("小昭，今天有什么新发现？", persona_hint="xiaozhao")
        if trace.persona_selected:
            self._pass("NL-2-03-persona", "nl_test", "retrieval_mismatch",
                       "persona auto-detect: 小昭",
                       detail=f"resolved: {trace.persona_selected}")
        else:
            self._fail("NL-2-03-persona", "nl_test", "retrieval_mismatch",
                       "persona auto-detect",
                       expected="any persona resolved from 小昭 query",
                       actual="no persona matched",
                       detail="Name '小昭' in query failed persona resolution",
                       suggestion="Ensure 小昭's JSON has persona:'小昭' or persona_zh:'小昭'")

        # NL-2-04: Group discussion structural check
        trace = self.tracer.trace("各位大佬，讨论一下泛化能力", persona_hint="zhuangzi")
        if trace.tier1_categories:
            self._pass("NL-2-04-group", "nl_test", "retrieval_mismatch",
                       "group discussion retrieval",
                       detail=f"categories: {trace.tier1_categories}, persona: {trace.persona_selected}")
        else:
            self._warn("NL-2-04-group", "nl_test", "retrieval_mismatch",
                       "group discussion",
                       expected="retrieval works for general query",
                       actual="no categories matched",
                       detail="'泛化能力' keyword may not match any category description",
                       suggestion="Add '泛化', 'generalization' keywords to relevant category descriptions")
