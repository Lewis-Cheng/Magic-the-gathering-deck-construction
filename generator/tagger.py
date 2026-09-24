"""Versioned Oracle-text tagger (v1)."""

from __future__ import annotations

import re
from typing import Iterable

VERSION = "v1"

_ADD_MANA = re.compile(r"\{t\}: add |add \{|add one mana|add two mana|add three mana", re.I)
_COUNTER = re.compile(r"counter target (spell|activated|triggered)", re.I)
_DRAW = re.compile(r"draw (a|one|two|three|four|\d+) cards?", re.I)
_TUTOR = re.compile(r"search your library for (a|an|up to)", re.I)
_LAND_TUTOR = re.compile(r"search your library for .{0,40}land", re.I)
_WIPE = re.compile(r"destroy all |exile all |each creature|all creatures", re.I)
_TOKEN = re.compile(r"create .{0,80}token", re.I)
_PROTECT = re.compile(
    r"hexproof|indestructible|shroud|protection from|can't be countered|prevent (all|the next)",
    re.I,
)
_EXTRA = re.compile(r"extra turn", re.I)
_STAX = re.compile(
    r"each opponent|players can't|can't cast|skip (your|their)|unless (you|they) pay|don't untap",
    re.I,
)
_REMOVAL = re.compile(r"destroy target |exile target (creature|permanent|artifact|enchantment)", re.I)
_AURA = re.compile(r"enchant (creature|permanent)", re.I)


def tag(name: str, text: str, types: Iterable[str], subtypes: Iterable[str] | None = None) -> list[str]:
    t = text or ""
    types_l = {x.lower() for x in types}
    subs = {x.lower() for x in (subtypes or [])}
    tags: list[str] = []

    if _ADD_MANA.search(t) or (_LAND_TUTOR.search(t) and "land" in t.lower()):
        tags.append("ramp")
    if "artifact" in types_l and "ramp" in tags:
        tags.append("rock")
    if _COUNTER.search(t):
        tags.append("counter")
    if _DRAW.search(t):
        tags.append("draw")
    if _TUTOR.search(t) and not _LAND_TUTOR.search(t):
        tags.append("tutor")
    if _WIPE.search(t):
        tags.append("wipe")
    if _TOKEN.search(t):
        tags.append("token")
    if _PROTECT.search(t):
        tags.append("protection")
    if _EXTRA.search(t):
        tags.append("extra-turn")
    if _STAX.search(t):
        tags.append("stax")
    if _REMOVAL.search(t):
        tags.append("removal")
    if "aura" in subs or _AURA.search(t):
        tags.append("aura")
    if "equipment" in subs or "equip " in t.lower():
        tags.append("equipment")
    if "enchantment" in types_l:
        tags.append("enchantment")
    if "instant" in types_l or "sorcery" in types_l:
        tags.append("spell")
    return tags


def tag_card(card) -> list[str]:
    return tag(card.name, card.text, card.types, card.subtypes)
