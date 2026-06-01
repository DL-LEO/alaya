"""Retrieval protocol tracer — simulates Alaya's question-driven retrieval
without an LLM.  Uses keyword matching and persona interest_foci to
approximate the retrieval path, then verifies post-condition effects.

This lets us write "user says X → expect Y" tests that run deterministically.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from lib.time_machine import get_strength, get_last_activated, get_activation_count

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "的", "了", "是", "在", "有", "我", "他", "她", "它", "们",
    "这", "那", "什么", "怎么", "为什么", "如何", "可以", "能", "会",
    "要", "让", "把", "被", "和", "与", "就", "也", "都", "而", "但",
    "或", "如果", "因为", "所以", "但是", "不过", "然后", "那么",
}


@dataclass
class RetrievalTrace:
    """Full output of tracing one natural-language query through all 4 tiers."""
    user_input: str = ""
    persona_selected: str = ""
    persona_foci: dict = field(default_factory=dict)
    domain_scope: dict = field(default_factory=dict)
    memory_hot: list = field(default_factory=list)
    ambient: dict = field(default_factory=dict)
    tier1_categories: list[str] = field(default_factory=list)
    tier2_core: list[tuple[str, str, float]] = field(default_factory=list)   # (cat, card, strength)
    tier2_peripheral: list[tuple[str, str, float]] = field(default_factory=list)
    tier2_dormant: list[tuple[str, str, float]] = field(default_factory=list)
    tier3_selected: list[tuple[str, str, float]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class PostCheck:
    """A single post-condition check to run after retrieval simulation."""
    check_id: str
    description: str
    card_path: str | None = None
    expected_strength_min: float | None = None
    expected_strength_max: float | None = None
    expected_activation_increase: bool = False
    expected_date_today: bool = False
    memory_persona: str | None = None
    memory_hot_should_contain: str | None = None
    expected: str = ""
    actual: str = ""
    passed: bool = False


# ---------------------------------------------------------------------------
# Protocol Tracer
# ---------------------------------------------------------------------------

class ProtocolTracer:
    """Simulates Alaya tiered retrieval by inspecting the filesystem."""

    def __init__(self, wiki_dir: str, alaya_dir: str):
        self.wiki_dir = wiki_dir
        self.alaya_dir = alaya_dir
        self.manas_dir = os.path.join(alaya_dir, "manas")
        self.memory_dir = os.path.join(alaya_dir, "memory")

    # ---- Tier 0: Persona Resolution ---------------------------------------

    def _find_persona(self, user_input: str) -> str | None:
        """Resolve persona from user input — checks name mentions + triggers."""
        if not os.path.isdir(self.manas_dir):
            return None
        candidates = []
        for fn in sorted(os.listdir(self.manas_dir)):
            if not fn.endswith(".json") or fn == "_history.json":
                continue
            fpath = os.path.join(self.manas_dir, fn)
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                continue
            name = data.get("persona", "")
            name_zh = data.get("persona_zh", "")
            name_lower = name.lower()
            name_zh_lower = name_zh.lower()
            short = fn.replace(".json", "").lower()
            # Direct name match (check English, Chinese, and filename alias)
            user_lower = user_input.lower()
            if (name_lower in user_lower or (name_zh and name_zh_lower in user_lower)
                    or short in user_lower):
                return name
            # Trigger match
            triggers = data.get("triggers", {})
            for kw in triggers.get("active", []):
                if kw.lower() in user_input.lower():
                    candidates.append((name, 1))
            for em in triggers.get("emotions", []):
                if em.lower() in user_input.lower():
                    candidates.append((name, 0.5))
        # Return first candidate if no direct match
        if candidates:
            return candidates[0][0]
        # Fallback: first valid persona in directory
        for fn in sorted(os.listdir(self.manas_dir)):
            if not fn.endswith(".json") or fn == "_history.json":
                continue
            try:
                with open(os.path.join(self.manas_dir, fn), encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("persona", "")
            except (json.JSONDecodeError, IOError):
                continue
        return None

    def _load_persona(self, name: str) -> dict:
        """Load persona JSON by name or filename alias. Returns {} if corrupt/not found."""
        if not os.path.isdir(self.manas_dir):
            return {}
        name_lower = name.lower()
        for fn in sorted(os.listdir(self.manas_dir)):
            if not fn.endswith(".json") or fn == "_history.json":
                continue
            fpath = os.path.join(self.manas_dir, fn)
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                if (data.get("persona", "").lower() == name_lower
                        or fn.replace(".json", "").lower() == name_lower):
                    return data
            except (json.JSONDecodeError, IOError):
                continue
        return {}

    def _load_memory(self, persona: str) -> tuple[list, dict]:
        """Return (hot_entries, ambient_dict)."""
        hot = []
        mem_path = os.path.join(self.memory_dir, f"{persona}_history.json")
        if os.path.exists(mem_path):
            with open(mem_path, encoding="utf-8") as f:
                data = json.load(f)
            hot = data.get("hot", [])
        ambient = {}
        ambient_path = os.path.join(self.memory_dir, "ambient.json")
        if os.path.exists(ambient_path):
            with open(ambient_path, encoding="utf-8") as f:
                ambient = json.load(f)
        return hot, ambient

    # ---- Tier 1: Category Selection (keyword-based) -----------------------

    def _keywords(self, text: str) -> set[str]:
        """Extract meaningful keywords."""
        text = text.lower()
        # Split on non-alphanumeric (keep Chinese chars)
        tokens = re.findall(r'[a-zA-Z]+|[一-鿿]+', text)
        result = set()
        for t in tokens:
            t_clean = t.strip().lower()
            if len(t_clean) > 1 and t_clean not in STOP_WORDS:
                result.add(t_clean)
        return result

    def _select_categories(self, user_input: str) -> list[str]:
        """Match keywords against index.md category descriptions."""
        index_path = os.path.join(self.wiki_dir, "index.md")
        if not os.path.exists(index_path):
            return []
        with open(index_path, encoding="utf-8") as f:
            content = f.read()

        keywords = self._keywords(user_input)
        # Extract category lines from AUTO section
        auto_match = re.search(r'<!-- AUTO -->(.*?)<!-- END-AUTO -->', content, re.DOTALL)
        if not auto_match:
            return list(self._known_categories().keys())[:3]

        cats_scored: list[tuple[str, int]] = []
        for line in auto_match.group(1).splitlines():
            m = re.findall(r'\[\[([^/]+)/_category', line)
            if m:
                cat = m[0]
                score = sum(1 for kw in keywords if kw in line.lower())
                cats_scored.append((cat, score))

        if not cats_scored:
            return list(self._known_categories().keys())[:3]
        cats_scored.sort(key=lambda x: -x[1])
        return [c for c, s in cats_scored[:3]]

    def _known_categories(self) -> dict[str, str]:
        """Return {cat_slug: description} from _category.md files."""
        result = {}
        if not os.path.isdir(self.wiki_dir):
            return result
        for d in sorted(os.listdir(self.wiki_dir)):
            cat_path = os.path.join(self.wiki_dir, d)
            if not os.path.isdir(cat_path):
                continue
            cat_md = os.path.join(cat_path, "_category.md")
            if os.path.exists(cat_md):
                with open(cat_md, encoding="utf-8") as f:
                    result[d] = f.read()[:200]
        return result

    # ---- Tier 2: Build Candidate Pool -------------------------------------

    def _build_pool(self, categories: list[str]) -> tuple[list, list, list]:
        """Read _category.md for each category; return core/peripheral/dormant."""
        core: list[tuple[str, str, float]] = []
        peripheral: list[tuple[str, str, float]] = []
        dormant: list[tuple[str, str, float]] = []

        for cat in categories:
            cat_path = os.path.join(self.wiki_dir, cat)
            cat_md = os.path.join(cat_path, "_category.md")
            if not os.path.exists(cat_md):
                continue
            with open(cat_md, encoding="utf-8") as f:
                content = f.read()

            # Extract card links from AUTO section
            auto_match = re.search(r'<!-- AUTO -->(.*?)<!-- END-AUTO -->', content, re.DOTALL)
            if not auto_match:
                continue

            for line in auto_match.group(1).splitlines():
                m = re.findall(r'\[\[([^\]]+?)\]\]', line)
                for card_name in m:
                    card_path = os.path.join(cat_path, f"{card_name}.md")
                    strength = get_strength(card_path)
                    if strength is None:
                        continue
                    if strength >= 0.5:
                        core.append((cat, card_name, strength))
                    elif strength >= 0.1:
                        peripheral.append((cat, card_name, strength))
                    else:
                        dormant.append((cat, card_name, strength))

        core.sort(key=lambda x: -x[2])
        peripheral.sort(key=lambda x: -x[2])
        dormant.sort(key=lambda x: -x[2])

        # Supplement small core pools from peripheral
        if len(core) < 5 and peripheral:
            needed = min(5 - len(core), len(peripheral))
            core.extend(peripheral[:needed])

        return core, peripheral, dormant

    # ---- Tier 3: Persona-Driven Filtering ---------------------------------

    def _filter_by_persona(self, pool: list[tuple[str, str, float]], persona_name: str) -> list[tuple[str, str, float]]:
        """Filter candidate pool using persona interest_foci."""
        foci = self._load_persona(persona_name).get("ego_vector", {}).get("interest_foci", {})
        if not foci:
            return pool[:5]  # no foci → return top 5

        # Build a matching score for each card
        scored = []
        for cat, card, strength in pool:
            card_path = os.path.join(self.wiki_dir, cat, f"{card}.md")
            card_tags = self._card_tags(card_path)
            # Score: sum of interest_foci values where key overlaps card tags
            score = 0.0
            for focus_key, focus_val in foci.items():
                focus_words = set(focus_key.replace("_", " ").lower().split())
                card_words = set(t.lower() for t in card_tags)
                card_words.update(w.lower() for w in card.replace("-", " ").split())
                if focus_words & card_words:
                    score += focus_val.get("value", 0.7)
            scored.append((cat, card, strength, score))

        scored.sort(key=lambda x: (-x[3], -x[2]))
        return [(c, n, s) for c, n, s, _ in scored[:5]]

    def _card_tags(self, card_path: str) -> list[str]:
        if not os.path.exists(card_path):
            return []
        with open(card_path, encoding="utf-8") as f:
            raw = f.read()
        m = re.search(r'^tags:\s*(\[.*?\])\s*$', raw, re.MULTILINE)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        return []

    # ---- Main Trace -------------------------------------------------------

    def trace(self, user_input: str, persona_hint: str = "") -> RetrievalTrace:
        """Run all 4 tiers on the user input. Returns full trace."""
        trace = RetrievalTrace(user_input=user_input)

        # Tier 0
        persona_name = persona_hint or self._find_persona(user_input)
        trace.persona_selected = persona_name
        if persona_name:
            pdata = self._load_persona(persona_name)
            trace.persona_foci = pdata.get("ego_vector", {}).get("interest_foci", {})
            trace.domain_scope = pdata.get("domain_scope", {})
            trace.memory_hot, trace.ambient = self._load_memory(persona_name)

        # Tier 1
        trace.tier1_categories = self._select_categories(user_input)

        # Tier 2
        trace.tier2_core, trace.tier2_peripheral, trace.tier2_dormant = self._build_pool(trace.tier1_categories)

        # Tier 3 — only if persona resolved
        if persona_name and trace.tier2_core:
            trace.tier3_selected = self._filter_by_persona(trace.tier2_core, persona_name)

        # Validation
        if not trace.tier1_categories:
            trace.issues.append(f"Tier1: no categories matched for '{user_input}'")
        if not trace.tier2_core:
            trace.issues.append(f"Tier2: empty core pool (categories: {trace.tier1_categories})")
        if persona_name and not trace.tier3_selected:
            trace.issues.append(f"Tier3: persona '{persona_name}' selected 0 cards")

        return trace

    # ---- Post-condition verification --------------------------------------

    def verify_boost(self, card_path: str, before_strength: float, before_count: int, before_date: str) -> PostCheck:
        """Check that a card was properly boosted after retrieval."""
        check = PostCheck(
            check_id="boost",
            description=f"Card boost: {os.path.basename(card_path)}",
            card_path=card_path,
            expected=f"strength > {before_strength}, activation_count > {before_count}, date = today",
        )
        new_strength = get_strength(card_path)
        new_count = get_activation_count(card_path)
        new_date = get_last_activated(card_path)

        issues = []
        if new_strength is not None and new_strength <= before_strength:
            issues.append(f"strength {before_strength} → {new_strength} (no increase)")
        if new_count <= before_count:
            issues.append(f"activation_count {before_count} → {new_count} (no increase)")
        from lib.time_machine import today_str
        if new_date != today_str():
            issues.append(f"last_activated {new_date} ≠ today {today_str()}")

        if issues:
            check.passed = False
            check.actual = "; ".join(issues)
        else:
            check.passed = True
            check.actual = f"strength {before_strength}→{new_strength}, count {before_count}→{new_count}, date {new_date}"
        return check

    def check_memory(self, persona: str, expected_topic: str = "") -> PostCheck:
        """Check that persona memory exists and contains expected topic."""
        check = PostCheck(
            check_id="memory",
            description=f"Memory check: {persona}",
            memory_persona=persona,
            expected=f"hot zone has entry with topic involving '{expected_topic}'" if expected_topic else "hot zone has entries",
        )
        hot, _ = self._load_memory(persona)
        if not hot:
            check.passed = False
            check.actual = "no hot zone entries found"
            return check
        if expected_topic:
            found = any(expected_topic.lower() in str(e).lower() for e in hot)
            check.passed = found
            check.actual = f"hot zone entries: {len(hot)}, topic match: {found}"
        else:
            check.passed = True
            check.actual = f"hot zone has {len(hot)} entries"
        return check

    def check_ambient_updated(self) -> PostCheck:
        """Check ambient.json exists and has basic fields."""
        check = PostCheck(
            check_id="ambient",
            description="Ambient state check",
            expected="ambient.json exists with recent_mood, recent_attention, mood_trajectory",
        )
        ambient_path = os.path.join(self.memory_dir, "ambient.json")
        if not os.path.exists(ambient_path):
            check.passed = False
            check.actual = "ambient.json not found"
            return check
        with open(ambient_path, encoding="utf-8") as f:
            ambient = json.load(f)
        missing = [k for k in ["recent_mood", "recent_attention", "mood_trajectory"] if k not in ambient]
        check.passed = len(missing) == 0
        check.actual = f"fields: {list(ambient.keys())}, missing: {missing}"
        return check
