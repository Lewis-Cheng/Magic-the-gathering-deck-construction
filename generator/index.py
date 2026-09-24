"""In-memory Oracle index: CI, types, text, tagger roles. Empty search returns []."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from generator.legal import banned_names
from generator.oracle_bridge import get_oracle
from generator.tagger import tag_card

SKIP_TYPES = {"conspiracy", "phenomenon", "plane", "scheme", "vanguard", "dungeon"}


@dataclass
class IndexedCard:
    name: str
    color_identity: frozenset[str]
    types: frozenset[str]
    subtypes: frozenset[str]
    text: str
    keywords: frozenset[str]
    roles: tuple[str, ...]
    is_land: bool
    is_creature: bool
    cmc: int
    is_legendary: bool
    spell_front_mdfc: bool


@dataclass
class CardIndex:
    cards: list[IndexedCard] = field(default_factory=list)
    by_name: dict[str, IndexedCard] = field(default_factory=dict)

    def search(self, ci: set[str], slot: str, query: str, limit: int = 80) -> list[IndexedCard]:
        ci_f = set(ci)
        hits: list[IndexedCard] = []
        for c in self.cards:
            if c.is_land:
                continue
            if not set(c.color_identity).issubset(ci_f):
                continue
            if not _matches(c, query, slot):
                continue
            hits.append(c)
            if len(hits) >= limit:
                break
        return hits


def _matches(c: IndexedCard, query: str, slot: str) -> bool:
    if not query or query.strip() == "*":
        return True
    clauses = [p.strip() for p in query.split(" OR ") if p.strip()]
    return any(_clause(c, cl, slot) for cl in clauses)


def _clause(c: IndexedCard, clause: str, slot: str) -> bool:
    text = c.text.lower()
    name = c.name.lower()
    types = {t.lower() for t in c.types} | {t.lower() for t in c.subtypes}
    roles = set(c.roles)
    tokens = clause.split()
    for tok in tokens:
        low = tok.lower()
        if low.startswith("type:"):
            want = low.split(":", 1)[1]
            if want not in types:
                return False
        elif low.startswith("tag:"):
            want = low.split(":", 1)[1]
            if want not in roles:
                return False
        elif low.startswith("slot:"):
            if low.split(":", 1)[1] != slot:
                return False
        else:
            word = tok.strip('"').lower()
            if word not in text and word not in name and word not in types:
                return False
    return True


@lru_cache(maxsize=1)
def get_index() -> CardIndex:
    oracle = get_oracle()
    bans = banned_names()
    idx = CardIndex()
    for name, card in oracle._by_name.items():
        types_l = {t.lower() for t in card.types}
        if types_l & SKIP_TYPES:
            continue
        if card.is_token:
            continue
        if name in bans:
            continue
        display = name.split(" // ", 1)[0] if " // " in name else name
        if display in idx.by_name:
            continue
        roles = tuple(tag_card(card))
        spell_front = (" // " in name) and bool(card.is_instant or card.is_sorcery) and not card.is_land
        ic = IndexedCard(
            name=display,
            color_identity=frozenset(card.color_identity),
            types=frozenset(card.types),
            subtypes=frozenset(card.subtypes),
            text=card.text or "",
            keywords=frozenset(card.keywords),
            roles=roles,
            is_land=card.is_land,
            is_creature=card.is_creature,
            cmc=card.mana_cost.cmc(),
            is_legendary=card.is_legendary,
            spell_front_mdfc=spell_front,
        )
        idx.cards.append(ic)
        idx.by_name[display] = ic
    return idx


def commanders_matching(q: str, limit: int = 20) -> list[dict]:
    qn = (q or "").strip().lower()
    if len(qn) < 2:
        return []
    out = []
    for c in get_index().cards:
        if not c.is_legendary:
            continue
        if not (c.is_creature or "Planeswalker" in c.types):
            continue
        if qn not in c.name.lower():
            continue
        out.append(
            {
                "name": c.name,
                "color_identity": sorted(c.color_identity),
            }
        )
        if len(out) >= limit:
            break
    return out
