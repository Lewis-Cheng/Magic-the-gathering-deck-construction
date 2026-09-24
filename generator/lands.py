"""Land base from identity + budget + power. Never copy deck_v12 UR duals."""

from __future__ import annotations

from typing import Optional

from generator.budget import effective_price, within_caps
from generator.prices import lookup

BASICS = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}

GAINLANDS = [
    ("Blossoming Sands", frozenset("GW")),
    ("Tranquil Cove", frozenset("WU")),
    ("Scoured Barrens", frozenset("WB")),
    ("Wind-Scarred Crag", frozenset("WR")),
    ("Thornwood Falls", frozenset("GU")),
    ("Jungle Hollow", frozenset("BG")),
    ("Rugged Highlands", frozenset("RG")),
    ("Dismal Backwater", frozenset("UB")),
    ("Swiftwater Cliffs", frozenset("UR")),
    ("Bloodfell Caves", frozenset("BR")),
]

GATES = [
    ("Azorius Guildgate", frozenset("WU")),
    ("Dimir Guildgate", frozenset("UB")),
    ("Rakdos Guildgate", frozenset("BR")),
    ("Gruul Guildgate", frozenset("RG")),
    ("Selesnya Guildgate", frozenset("GW")),
    ("Orzhov Guildgate", frozenset("WB")),
    ("Izzet Guildgate", frozenset("UR")),
    ("Golgari Guildgate", frozenset("BG")),
    ("Boros Guildgate", frozenset("WR")),
    ("Simic Guildgate", frozenset("GU")),
]

SHOCKS = [
    ("Hallowed Fountain", frozenset("WU")),
    ("Watery Grave", frozenset("UB")),
    ("Blood Crypt", frozenset("BR")),
    ("Stomping Ground", frozenset("RG")),
    ("Temple Garden", frozenset("GW")),
    ("Godless Shrine", frozenset("WB")),
    ("Steam Vents", frozenset("UR")),
    ("Overgrown Tomb", frozenset("BG")),
    ("Sacred Foundry", frozenset("WR")),
    ("Breeding Pool", frozenset("GU")),
]

FETCHES = [
    ("Flooded Strand", frozenset("WU")),
    ("Polluted Delta", frozenset("UB")),
    ("Bloodstained Mire", frozenset("BR")),
    ("Wooded Foothills", frozenset("RG")),
    ("Windswept Heath", frozenset("GW")),
    ("Marsh Flats", frozenset("WB")),
    ("Scalding Tarn", frozenset("UR")),
    ("Verdant Catacombs", frozenset("BG")),
    ("Arid Mesa", frozenset("WR")),
    ("Misty Rainforest", frozenset("GU")),
]

COLORLESS_BUDGET = [
    "Command Tower",
    "Path of Ancestry",
    "Exotic Orchard",
    "Evolving Wilds",
    "Terramorphic Expanse",
    "Myriad Landscape",
    "Ash Barrens",
    "Reliquary Tower",
    "Unclaimed Territory",
    "Opulent Palace",
]


def _fits_ci(land_ci: frozenset[str], cmd_ci: set[str]) -> bool:
    return set(land_ci).issubset(cmd_ci)


def _priced(name: str, owned: list[str], proxies: bool) -> Optional[float]:
    return effective_price(name, lookup(name), owned, proxies)


def build_lands(
    cmd_ci: set[str],
    count: int,
    *,
    remaining: float,
    per_card_cap: Optional[float],
    power_level: str,
    owned: list[str],
    proxies: bool,
    theme: str,
    exclude: set[str],
) -> tuple[list[str], float]:
    chosen: list[str] = []
    skip = set(exclude)

    def try_add(name: str) -> bool:
        nonlocal remaining
        if name in skip or name in chosen:
            return False
        p = _priced(name, owned, proxies)
        if not within_caps(p, remaining=remaining, per_card_cap=per_card_cap):
            return False
        chosen.append(name)
        skip.add(name)
        remaining -= float(p)
        return True

    colors = [c for c in "WUBRG" if c in cmd_ci]
    if len(colors) >= 2:
        try_add("Command Tower")
        try_add("Exotic Orchard")
        try_add("Path of Ancestry")
    try_add("Evolving Wilds")
    try_add("Terramorphic Expanse")
    try_add("Reliquary Tower")

    if theme == "voltron":
        try_add("Rogue's Passage")
    if theme == "tokens" and "R" in cmd_ci:
        try_add("Kher Keep")
    if theme == "reanimator" and "B" in cmd_ci:
        try_add("Bojuka Bog")

    for name, lci in GAINLANDS + GATES:
        if len(chosen) >= count:
            break
        if _fits_ci(lci, cmd_ci) and len(lci) == 2:
            try_add(name)

    allow_premium = power_level in {"focused", "high", "cedh"} and remaining > 20
    if allow_premium:
        for name, lci in SHOCKS + FETCHES:
            if len(chosen) >= max(0, count - max(len(colors), 1) * 3):
                break
            if _fits_ci(lci, cmd_ci):
                try_add(name)

    # Guarantee at least one basic per color, then fill remainder with basics.
    if not colors:
        while len(chosen) < count:
            chosen.append("Wastes")
        return chosen[:count], remaining

    for c in colors:
        if len(chosen) < count:
            chosen.append(BASICS[c])

    i = 0
    while len(chosen) < count:
        chosen.append(BASICS[colors[i % len(colors)]])
        i += 1

    return chosen[:count], remaining
