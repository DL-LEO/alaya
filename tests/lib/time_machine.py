"""Time simulation: controls date context for lifecycle testing.

Alaya uses date-based decay (strength = strength * decay^days). Rather than
waiting real time, we override the system date context and manipulate card
dates directly. All decay formulas match the production code exactly.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
import os
import re
from typing import Optional

_OVERRIDE_DATE: Optional[date] = None


def set_system_date(date_str: str) -> None:
    """Set the test's 'today' to YYYY-MM-DD."""
    global _OVERRIDE_DATE
    _OVERRIDE_DATE = datetime.strptime(date_str, "%Y-%m-%d").date()


def advance_days(n: int) -> None:
    """Advance the override date by N days."""
    global _OVERRIDE_DATE
    if _OVERRIDE_DATE is None:
        _OVERRIDE_DATE = date.today() + timedelta(days=n)
    else:
        _OVERRIDE_DATE += timedelta(days=n)


def advance_months(n: int) -> None:
    """Advance by N months (30-day units)."""
    advance_days(n * 30)


def today() -> date:
    """Return the current test date (or real today if unset)."""
    if _OVERRIDE_DATE is not None:
        return _OVERRIDE_DATE
    return date.today()


def today_str() -> str:
    return today().strftime("%Y-%m-%d")


def reset() -> None:
    global _OVERRIDE_DATE
    _OVERRIDE_DATE = None


# ---------------------------------------------------------------------------
# Pure decay functions — mirrors perfume_knowledge.decay_all exact formula
# ---------------------------------------------------------------------------

def calc_strength(initial: float, days_since_use: int, decay_rate: float = 0.977) -> float:
    """strength after N idle days.  Default rate matches Alaya v1.7+."""
    if days_since_use <= 0:
        return initial
    return round(initial * (decay_rate ** days_since_use), 4)


def calc_affinity(initial: float, days_since_interaction: int, decay_rate: float = 0.992) -> float:
    """affinity after N days without persona interaction."""
    if days_since_interaction <= 0:
        return initial
    return round(initial * (decay_rate ** days_since_interaction), 4)


# ---------------------------------------------------------------------------
# Card-level date helpers
# ---------------------------------------------------------------------------

YAML_FIELD_RE = re.compile(r'^(last_activated|strength|activation_count):\s*(.+?)\s*$', re.MULTILINE)


def _read_card(path: str) -> tuple[str, str] | None:
    """Return (yaml_frontmatter, body) or None."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if not raw.startswith("---"):
        return None
    end = raw.find("---", 3)
    if end < 0:
        return None
    return raw[3:end], raw[end + 3:]


def _write_card(path: str, yaml_str: str, body: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("---" + yaml_str + "---" + body)


def backdate_card(card_path: str, days_ago: int) -> None:
    """Set last_activated to N days before test-today."""
    data = _read_card(card_path)
    if data is None:
        return
    yaml_str, body = data
    target = (today() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    if "last_activated:" in yaml_str:
        yaml_str = re.sub(r'^last_activated:\s*.*$', f"last_activated: {target}", yaml_str, flags=re.MULTILINE)
    else:
        yaml_str = yaml_str.rstrip() + f"\nlast_activated: {target}\n"
    _write_card(card_path, yaml_str, body)


def set_strength(card_path: str, value: float) -> None:
    data = _read_card(card_path)
    if data is None:
        return
    yaml_str, body = data
    if "strength:" in yaml_str:
        yaml_str = re.sub(r'^strength:\s*.*$', f"strength: {value:.4f}", yaml_str, flags=re.MULTILINE)
    else:
        yaml_str = yaml_str.rstrip() + f"\nstrength: {value:.4f}\n"
    _write_card(card_path, yaml_str, body)


def get_strength(card_path: str) -> float | None:
    data = _read_card(card_path)
    if data is None:
        return None
    yaml_str, _ = data
    m = re.search(r'^strength:\s*([0-9.]+)', yaml_str, re.MULTILINE)
    return float(m.group(1)) if m else None


def get_activation_count(card_path: str) -> int:
    data = _read_card(card_path)
    if data is None:
        return 0
    yaml_str, _ = data
    m = re.search(r'^activation_count:\s*(\d+)', yaml_str, re.MULTILINE)
    return int(m.group(1)) if m else 0


def get_last_activated(card_path: str) -> str | None:
    data = _read_card(card_path)
    if data is None:
        return None
    yaml_str, _ = data
    m = re.search(r'^last_activated:\s*(.+?)\s*$', yaml_str, re.MULTILINE)
    return m.group(1).strip() if m else None
