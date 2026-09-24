"""Magic Comprehensive Rules loader and engine-facing rule digest.

Loads the official Comprehensive Rules text (ovika/rulebook/CR.txt) and
exposes individual rules by number so the engine can be audited against
the rulebook. Also defines the phase/step schema from rule 500.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

CR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rulebook", "CR.txt")

_RULE_RE = re.compile(r"^(\d{3}(?:\.\d+)*[a-z]?)\.\s")


def load_cr(path: str = CR_PATH) -> Dict[str, List[str]]:
    """Parse CR.txt into {rule number: [text lines]}."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    sections: Dict[str, List[str]] = {}
    cur: str | None = None
    for ln in lines:
        m = _RULE_RE.match(ln)
        if m:
            cur = m.group(1)
            sections.setdefault(cur, []).append(ln)
        elif cur is not None and ln.strip():
            sections[cur].append(ln)
    return sections


_SECTIONS: Dict[str, List[str]] | None = None


def sections() -> Dict[str, List[str]]:
    global _SECTIONS
    if _SECTIONS is None:
        _SECTIONS = load_cr()
    return _SECTIONS


def rule(no: str) -> str:
    """Return the text of a numbered rule (e.g. '603.3b'), or '' if absent."""
    sec = sections().get(no, [])
    return "\n".join(sec)


def has_rule(no: str) -> bool:
    return no in sections()


# ---------------------------------------------------------------------------
# Game structure from rule 500 (turn) / 502-514 (steps) / 506 (combat steps)
# ---------------------------------------------------------------------------

#: (phase, CR ref, [(step, CR ref), ...])
TURN_SCHEMA: List[Tuple[str, str, List[Tuple[str, str]]]] = [
    ("Beginning", "500.1a", [
        ("Untap", "502"),      # 502.3: active player untaps; no priority (117.3a)
        ("Upkeep", "503"),     # 503.1a: beginning-of-upkeep triggers, then priority
        ("Draw", "504"),       # 504.1: active player draws
    ]),
    ("Main1", "505", []),              # precombat main phase (505.1)
    ("Combat", "506", [                # combat phase (506.1)
        ("BeginCombat", "507"),
        ("DeclareAttackers", "508"),
        ("DeclareBlockers", "509"),
        ("CombatDamage", "510"),
        ("EndCombat", "511"),
    ]),
    ("Main2", "505", []),              # postcombat main phase (505.1)
    ("Ending", "500.1e", [
        ("EndStep", "513"),
        ("Cleanup", "514"),            # 514: discard to hand size, damage/effects end
    ]),
]

# Convenience: every step in order with CR citation.
ALL_STEPS: List[Tuple[str, str]] = [
    ("Untap", "502"),
    ("Upkeep", "503"),
    ("Draw", "504"),
    ("Main1", "505"),
    ("BeginCombat", "507"),
    ("DeclareAttackers", "508"),
    ("DeclareBlockers", "509"),
    ("CombatDamage", "510"),
    ("EndCombat", "511"),
    ("Main2", "505"),
    ("EndStep", "513"),
    ("Cleanup", "514"),
]

# Step names used by card text ("beginning of your upkeep", "end step", ...)
STEP_ALIASES = {
    "beginning of combat": "BeginCombat",
    "declare attackers": "DeclareAttackers",
    "end of combat": "EndCombat",
    "end step": "EndStep",
}

# ---------------------------------------------------------------------------
# Format constants (Commander, free-for-all with attack-multiple-players)
# ---------------------------------------------------------------------------
STARTING_LIFE = 40          # 103.4c
STARTING_HAND = 7           # 103.5
COMMANDER_DAMAGE_LIMIT = 21 # 903.10a
MAX_HAND_SIZE = 7           # 514 (cleanup discard)
MAX_TURNS = 20              # simulation safety cap
