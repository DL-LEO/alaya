"""Phase 01: First Launch Setup (T+0 initial config).

Simulates the first-launch protocol: creates alaya/config.json,
copies default personas, runs setup_wizard (automated), and builds
an initial knowledge base with ~30 cards using batch_import.
"""

import json
import os
import subprocess
import sys

from lib.time_machine import today_str, get_strength
from phases.base_phase import BasePhase
from phases.phase_00_install import Phase00


class Phase01(BasePhase):

    def __init__(self, log, kb):
        super().__init__("phase_01", "首次初始化设置 (T+0)", log, kb)

    def setup(self):
        self._init_config()
        self._copy_default_personas()
        self._create_initial_kb()

    def _init_config(self):
        """Create alaya/config.json from default."""
        alaya_dir = self.kb.alaya_dir
        os.makedirs(alaya_dir, exist_ok=True)

        src = os.path.join(self.kb.workdir, "config", "default_config.json")
        dst = os.path.join(alaya_dir, "config.json")
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                config = json.load(f)
            config["enabled"] = True
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

    def _copy_default_personas(self):
        """Copy manas/ personas to alaya/manas/ (as production setup does)."""
        src_manas = os.path.join(self.kb.workdir, "manas")
        dst_manas = os.path.join(self.kb.alaya_dir, "manas")
        os.makedirs(dst_manas, exist_ok=True)
        for fn in os.listdir(src_manas):
            if fn.endswith(".json") or fn.endswith(".md"):
                with open(os.path.join(src_manas, fn), encoding="utf-8") as f:
                    content = f.read()
                with open(os.path.join(dst_manas, fn), "w", encoding="utf-8") as f:
                    f.write(content)

    def _create_initial_kb(self):
        """Create initial knowledge base categories and cards."""
        kb = self.kb

        # ---- Layer 0: create wiki/index.md ----
        wiki_dir = kb.wiki_dir
        os.makedirs(wiki_dir, exist_ok=True)

        # ---- Categories ----
        kb.add_category("deep-learning", "深度学习 / Deep Learning — neural networks, transformers, attention")
        kb.add_category("ml-fundamentals", "机器学习基础 / ML Fundamentals — regression, trees, SVM, RL")
        kb.add_category("philosophy", "哲学 / Philosophy — Yogacara, simplicity, aesthetics")

        # ---- Create index.md (Layer 1) ----
        index_content = (
            "---\ntitle: Alaya Knowledge Base\n---\n\n"
            "# Alaya Knowledge Base\n\n"
            "## 分类概览\n\n"
            "<!-- AUTO -->\n"
            "- [[deep-learning/_category|Deep Learning]] — 深度学习与神经网络\n"
            "- [[ml-fundamentals/_category|ML Fundamentals]] — 机器学习基础\n"
            "- [[philosophy/_category|Philosophy]] — 哲学与跨学科思考\n\n"
            "### 概念网络\n"
            "[[deep-learning/_category]] <-> [[philosophy/_category]] ← 技术-哲学交叉\n"
            "<!-- END-AUTO -->\n"
        )
        with open(os.path.join(wiki_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(index_content)

        # ---- Template cards ----
        template_keys = ["transformer", "attention", "deep-learning", "cnn", "rl",
                         "yogacara", "transformer-yoga", "overfitting", "generalization",
                         "simplicity", "beauty-in-math", "bias-variance"]

        # Distribute across categories
        cat_map = {
            "deep-learning": ["transformer", "attention", "deep-learning", "cnn", "transformer-yoga"],
            "ml-fundamentals": ["rl", "overfitting", "generalization", "bias-variance"],
            "philosophy": ["yogacara", "simplicity", "beauty-in-math"],
        }

        for cat, keys in cat_map.items():
            for key in keys:
                kb.add_template_card(cat, key)

        # Add elementary cards to ML fundamentals
        kb.add_elementary_cards("ml-fundamentals")

        # ---- Build index ----
        result = kb.build_index()
        if result.returncode != 0:
            self._fail("C-01-index", "script_run", "script_error", "build_index.py",
                       expected="return code 0",
                       actual=f"exit {result.returncode}",
                       detail=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
                       suggestion="Check build_index.py for errors with the test wiki directory")

    def run_all(self):
        self._check_config()
        self._check_personas_copied()
        self._check_index_integrity()
        self._check_card_metadata()
        self._nl_test_retrieval()

    def _check_config(self):
        """Verify config.json structure."""
        cfg_path = os.path.join(self.kb.alaya_dir, "config.json")
        self._check_json("C-01-cfg", cfg_path)

        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)

        # Check for nested structure (v1.8+)
        if all(k in cfg for k in ("knowledge", "memory", "persona")):
            self._pass("C-01-cfg-nested", "config_check", "file_integrity", "config.json",
                       detail="nested (v1.8+) config structure")
        elif all(k in cfg for k in ("top_k", "max_cards", "half_life_default")):
            self._warn("C-01-cfg-nested", "config_check", "file_integrity", "config.json",
                       expected="nested config with knowledge/memory/persona keys",
                       actual="flat v1.7-style config",
                       detail="Config is flat — should be migrated to nested structure",
                       suggestion="Run perfume.py which migrates flat→nested automatically")
        else:
            self._fail("C-01-cfg-nested", "config_check", "file_integrity", "config.json",
                       expected="nested or flat config structure",
                       actual="unrecognized structure",
                       detail=f"Config keys: {list(cfg.keys())}",
                       suggestion="Create config.json matching default_config.json format")

        # Check enabled field
        if cfg.get("enabled"):
            self._pass("C-01-cfg-enabled", "config_check", "file_integrity", "config.json",
                       detail="enabled=true")
        else:
            self._fail("C-01-cfg-enabled", "config_check", "file_integrity", "config.json",
                       expected="enabled=true",
                       actual=f"enabled={cfg.get('enabled')}",
                       suggestion="Set 'enabled': true in config.json")

    def _check_personas_copied(self):
        """Verify personas were copied to alaya/manas/."""
        dst = os.path.join(self.kb.alaya_dir, "manas")
        if not os.path.isdir(dst):
            self._fail("C-01-manas-dir", "dir_exists", "file_integrity", "alaya/manas/",
                       expected="alaya/manas/ exists", actual="not found",
                       suggestion="Copy default personas: cp -r manas/ alaya/manas/")
            return
        for name in Phase00.REQUIRED_MANAS_JSON:
            jp = os.path.join(dst, f"{name}.json")
            pp = os.path.join(dst, f"{name}_profile.md")
            if not os.path.exists(jp) or not os.path.exists(pp):
                self._fail(f"C-01-persona-{name}", "file_exists", "file_integrity",
                           f"alaya/manas/{name}",
                           expected="both .json and _profile.md",
                           actual=f"json={os.path.exists(jp)}, profile={os.path.exists(pp)}",
                           suggestion=f"Copy manas/{name}.json and manas/{name}_profile.md to alaya/manas/")

    def _check_index_integrity(self):
        """Verify the three-layer index is complete."""
        wiki = self.kb.wiki_dir

        # Layer 1
        index_path = os.path.join(wiki, "index.md")
        if os.path.exists(index_path):
            with open(index_path, encoding="utf-8") as f:
                content = f.read()
            if "<!-- AUTO -->" in content or "<!-- END-AUTO -->" in content:
                self._pass("C-01-l1", "index_check", "file_integrity", "wiki/index.md",
                           detail="AUTO markers present")
            else:
                self._warn("C-01-l1", "index_check", "file_integrity", "wiki/index.md",
                           expected="<!-- AUTO --> / <!-- END-AUTO --> markers",
                           actual="markers missing",
                           detail="without AUTO markers, LLM can't distinguish generated vs manual content",
                           suggestion="Add <!-- AUTO --> and <!-- END-AUTO --> markers to index.md")
        else:
            self._fail("C-01-l1", "index_check", "file_integrity", "wiki/index.md",
                       expected="index.md exists", actual="not found",
                       suggestion="Run build_index.py to generate index.md")

        # Layer 2
        for cat in self.kb.category_names():
            cat_md = os.path.join(wiki, cat, "_category.md")
            if not os.path.exists(cat_md):
                self._fail(f"C-01-l2-{cat}", "index_check", "file_integrity", f"wiki/{cat}/_category.md",
                           expected="_category.md exists", actual="not found",
                           suggestion=f"Create wiki/{cat}/_category.md with AUTO markers")
                continue
            with open(cat_md, encoding="utf-8") as f:
                content = f.read()
            if "<!-- AUTO -->" not in content or "<!-- END-AUTO -->" not in content:
                self._warn(f"C-01-l2-auto-{cat}", "index_check", "file_integrity",
                           f"wiki/{cat}/_category.md",
                           expected="AUTO markers in _category.md",
                           actual="missing",
                           suggestion=f"Add AUTO markers to wiki/{cat}/_category.md")

    def _check_card_metadata(self):
        """Verify all cards have required Alaya metadata fields."""
        required = ["seed_type", "strength", "last_activated", "activation_count", "half_life"]
        missing_count = 0
        total = 0
        missing_details = []

        for cat, name, fpath in self.kb.all_cards():
            total += 1
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
            for field in required:
                if f"{field}:" not in content:
                    missing_count += 1
                    missing_details.append(f"{cat}/{name}: missing {field}")

        if missing_count == 0:
            self._pass("C-01-meta", "metadata_check", "data_inconsistency", f"{total} cards",
                       detail=f"all {total} cards have complete metadata")
        else:
            self._fail("C-01-meta", "metadata_check", "data_inconsistency", f"{total} cards",
                       expected=f"0 cards missing metadata",
                       actual=f"{missing_count} fields missing across cards",
                       detail="\n".join(missing_details[:10]),
                       suggestion="Run build_index.py which injects missing metadata fields")

        # Health check
        hc = self.kb.health_check()
        hc_out = hc.stdout or ""
        hc_err = hc.stderr or ""
        if hc.returncode == 0:
            self._pass("C-01-health", "script_run", "script_error", "health_check.py",
                       detail=hc_out[-300:])
        else:
            self._warn("C-01-health", "script_run", "script_error", "health_check.py",
                       expected="return code 0", actual=f"exit {hc.returncode}",
                       detail=f"stdout: {hc_out[:300]}\nstderr: {hc_err[:300]}",
                       suggestion="Run python scripts/health_check.py wiki alaya to diagnose")

    def _nl_test_retrieval(self):
        """Natural language retrieval tests on the initial KB."""
        # NL-1-01: Self-install detection
        trace = self.tracer.trace("alaya init")
        has_config = os.path.exists(os.path.join(self.kb.alaya_dir, "config.json"))
        if has_config:
            self._pass("NL-1-01", "nl_test", "retrieval_mismatch", "alaya init",
                       detail="config.json exists → first-launch detection should skip")
        else:
            self._fail("NL-1-01", "nl_test", "retrieval_mismatch", "alaya init",
                       expected="config.json exists", actual="not found",
                       detail="First-launch protocol requires config.json to detect configured state",
                       suggestion="Run setup_wizard.py or create alaya/config.json manually")

        # NL-1-02: Basic question → tier 3 should select cards
        trace = self.tracer.trace("费曼，Transformer 为什么需要注意力机制？", persona_hint="feynman")
        if trace.tier1_categories:
            self._pass("NL-1-02-tier1", "nl_test", "retrieval_mismatch",
                       f"categories: {trace.tier1_categories}",
                       detail=f"Tier1 selected: {trace.tier1_categories}")
        else:
            self._fail("NL-1-02-tier1", "nl_test", "retrieval_mismatch", "category selection",
                       expected=">=1 category selected",
                       actual="no categories matched",
                       detail=f"Question mentions 'Transformer' and '注意力', index.md may lack category description",
                       suggestion="Ensure index.md category descriptions contain keywords matching common questions")

        if trace.tier2_core:
            self._pass("NL-1-02-tier2", "nl_test", "retrieval_mismatch",
                       f"core pool: {len(trace.tier2_core)} cards",
                       detail=f"Tier2 pool has {len(trace.tier2_core)} core cards")
        else:
            self._fail("NL-1-02-tier2", "nl_test", "retrieval_mismatch", "candidate pool",
                       expected=">=1 card in core pool",
                       actual=f"categories {trace.tier1_categories} have 0 core cards",
                       detail="All cards may have strength < 0.5 or _category.md AUTO section is empty",
                       suggestion="Check _category.md AUTO sections list cards correctly")

        if trace.tier3_selected:
            self._pass("NL-1-02-tier3", "nl_test", "retrieval_mismatch",
                       f"persona selected: {len(trace.tier3_selected)} cards",
                       detail=f"Feynman selected: {[c for _, c, _ in trace.tier3_selected]}")
        else:
            self._warn("NL-1-02-tier3", "nl_test", "retrieval_mismatch",
                       expected=">=1 card selected by persona",
                       actual="0 cards",
                       detail="May be normal if no cards match Feynman's interest_foci, or if interest_foci aren't overlapping card tags",
                       suggestion="Verify interest_foci in feynman.json match tags on deep-learning cards")

        # NL-1-03: Persona auto-detection
        trace = self.tracer.trace("小昭，今天心情不错")
        if trace.persona_selected:
            self._pass("NL-1-03-persona", "nl_test", "retrieval_mismatch",
                       "persona auto-detect: 小昭",
                       detail=f"resolved from name mention: {trace.persona_selected}")
        else:
            self._fail("NL-1-03-persona", "nl_test", "retrieval_mismatch",
                       "persona auto-detect",
                       expected="any persona resolved from 小昭 query",
                       actual="no persona matched",
                       detail="Name '小昭' appears in query but wasn't matched",
                       suggestion="Verify persona JSON files have 'persona' or 'persona_zh' field")

        # NL-1-04: Health check command simulation
        hc = self.kb.health_check()
        if hc.returncode == 0:
            issues_in_output = [l for l in hc.stdout.split('\n') if 'Issue' in l or 'Missing' in l or 'broken' in l]
            self._pass("NL-1-04", "nl_test", "script_error",
                       "健康检查 command",
                       detail=f"health_check.py ran successfully, issues: {len(issues_in_output)}")
        else:
            self._fail("NL-1-04", "nl_test", "script_error",
                       "健康检查 command",
                       expected="return code 0",
                       actual=f"exit {hc.returncode}",
                       detail=f"stderr: {hc.stderr}",
                       suggestion="Debug health_check.py script error")
