"""Card definitions from MTGJSON AtomicCards + the local deck/pool files."""

from __future__ import annotations

import gzip
import importlib.util
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rulebook", "data", "AtomicCards.json.gz")
POOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ur_pool.json")

_MP_RE = re.compile(r"\{([^}]*)\}")

COLORS = "WUBRG"


@dataclass
class ManaCost:
    generic: int = 0
    colored: Dict[str, int] = field(default_factory=dict)  # {U: 1, R: 1, ...}
    hybrid: List[str] = field(default_factory=list)        # e.g. ["UR", "2W"] entries
    x: bool = False
    colorless: int = 0                                     # {C} pips

    def cmc(self) -> int:
        return self.generic + self.colorless + sum(self.colored.values()) + len(self.hybrid) + (1 if self.x else 0)

    def __repr__(self) -> str:
        return f"ManaCost(g={self.generic} {self.colored} x={self.x})"


@dataclass
class CardDef:
    name: str
    mana_cost: ManaCost
    mana_cost_str: str
    types: Set[str]
    supertypes: Set[str]
    subtypes: Set[str]
    text: str
    power: Optional[str]
    toughness: Optional[str]
    keywords: Set[str]
    colors: Set[str]
    color_identity: Set[str]
    is_land: bool = False
    is_creature: bool = False
    is_artifact: bool = False
    is_enchantment: bool = False
    is_instant: bool = False
    is_sorcery: bool = False
    is_planeswalker: bool = False
    is_legendary: bool = False
    is_token: bool = False
    tags: List[str] = field(default_factory=list)   # deck-file tags (ramp, buy, ...)
    buy: bool = False

    @property
    def is_permanent(self) -> bool:
        return not (self.is_instant or self.is_sorcery)

    @property
    def is_noncreature(self) -> bool:
        return not self.is_creature

    def has_text(self, *substrs: str) -> bool:
        t = self.text.lower()
        return all(s.lower() in t for s in substrs)


def parse_mana_cost(s: Optional[str]) -> ManaCost:
    mc = ManaCost()
    if not s:
        return mc
    for token in _MP_RE.findall(s):
        if token == "":
            mc.colorless += 1
        elif token.upper() == "X":
            mc.x = True
        elif token.upper() in COLORS:
            mc.colored[token.upper()] = mc.colored.get(token.upper(), 0) + 1
        elif token.isdigit():
            mc.generic += int(token)
        elif "/" in token:
            mc.hybrid.append(token.upper())
        elif token.upper() == "C":
            mc.colorless += 1
        elif token.upper() == "S":
            mc.colored["S"] = mc.colored.get("S", 0) + 1
        else:
            mc.generic += 1
    return mc


class Oracle:
    """Access to the full MTGJSON card database."""

    def __init__(self, path: str = DATA_PATH):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)["data"]
        self._by_name: Dict[str, CardDef] = {}
        for name, printings in data.items():
            c = printings[0]
            mcost = parse_mana_cost(c.get("manaCost"))
            types = {t for t in c.get("types", [])}
            supertypes = {t for t in c.get("supertypes", [])}
            subtypes = {t for t in c.get("subtypes", [])}
            colors = {x for x in c.get("colors", [])}
            ci = {x for x in c.get("colorIdentity", [])}
            self._by_name[name] = CardDef(
                name=name,
                mana_cost=mcost,
                mana_cost_str=c.get("manaCost") or "",
                types=types,
                supertypes=supertypes,
                subtypes=subtypes,
                text=c.get("text") or "",
                power=str(c.get("power")) if c.get("power") is not None else None,
                toughness=str(c.get("toughness")) if c.get("toughness") is not None else None,
                keywords={k for k in c.get("keywords", [])},
                colors=colors,
                color_identity=ci,
                is_land="Land" in types,
                is_creature="Creature" in types,
                is_artifact="Artifact" in types,
                is_enchantment="Enchantment" in types,
                is_instant="Instant" in types,
                is_sorcery="Sorcery" in types,
                is_planeswalker="Planeswalker" in types,
                is_legendary="Legendary" in supertypes,
            )

    def get(self, name: str) -> Optional[CardDef]:
        c = self._by_name.get(name)
        if c is None:
            # MTGJSON keys modal double-faced cards as "Front // Back"
            prefix = name + " //"
            for k, v in self._by_name.items():
                if k.startswith(prefix):
                    c = v
                    if c.name.startswith(prefix):
                        c.name = name
                    break
        return c

    def require(self, name: str) -> CardDef:
        c = self.get(name)
        if c is None:
            raise KeyError(f"unknown card: {name}")
        return c


class Pool:
    """Local deck files + user pool metadata (buy flags, deck tags)."""

    def __init__(self, oracle: Oracle, deck_path: Optional[str] = None):
        self.oracle = oracle
        if deck_path is None:
            raise ValueError("deck_path is required")
        self.deck_path = deck_path
        spec = importlib.util.spec_from_file_location("deckmod", deck_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self._commander_name = getattr(mod, "COMMANDER", None)
        rows = list(getattr(mod, "DECK"))
        self.cards: List[CardDef] = []
        for r in rows:
            name, mv, kind, u, r_, tags = r[0], r[1], r[2], r[3], r[4], (r[5] if len(r) > 5 else [])
            cd = oracle.require(name)
            cd.tags = list(tags)
            cd.buy = "buy" in tags
            self.cards.append(cd)
        self._by_name = {c.name: c for c in self.cards}

    @property
    def commander(self) -> CardDef:
        return self.oracle.require(self._commander_name)

    def by_name(self, name: str) -> CardDef:
        return self._by_name[name]

    def decklist(self) -> List[CardDef]:
        return list(self.cards)
