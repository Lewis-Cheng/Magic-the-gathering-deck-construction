"""Synergy graph for one deck.

Atlas lesson applied here:
- Type overlap is not a link. creature / spell / artifact / enchantment
  (and aura / equipment) never create an edge by themselves.
- An edge is shared *function* (what the card does), taken from Oracle text.
  A short name list only patches cards whose text does not match the phrases.
- A second, coplay layer records when one card's text names another.
  That layer is a score only. It does not change degree and does not drive swaps.
- The report lists plan-role packages (stax, token, enchantress-draw, …),
  not type cliques and not raw connected components (bridges collapse those).
  `passed` is still "no nonland with functional degree < 3".
  `split` is two plan packages of size >= 3. It does not fail the gate.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.oracle import Oracle, Pool

# "What it is" — too broad to mean the cards belong in the same plan.
_WEAK = frozenset({
    "creature", "spell", "artifact", "enchantment", "aura", "equipment",
    "planeswalker",
})

_MIN_DEGREE = 3

# Phrase list still misses these wordings. Do not grow this into the definition.
_STAX_PATCH = frozenset({
    "Trinisphere",
    "Static Orb",
    "Vexing Bauble",
    "Dauthi Voidwalker",
})

# Functions that are a plan, not a mana/interaction shell.
# Islands and `split` use these. Shell roles still create edges.
_PLAN = frozenset({
    "stax", "token", "enchantress-draw", "constellation", "enchant-finisher",
    "enchant-ramp", "mill", "reanimate", "prowess", "anthem", "catdog", "bomb",
})


def _is_stax(text: str) -> bool:
    """Tax, lock, or resource hate from rules text. Not a type match."""
    if "more to cast" in text:
        return True
    if "can't cast more than one" in text:
        return True
    if (
        "can't untap" in text
        or "untap more than one" in text
        or "don't untap" in text
        or "doesn't untap" in text
    ):
        return True
    if "can't attack you" in text:
        return True
    if "attacking you" in text and "pay" in text:
        return True
    if "opponents can't cast" in text:
        return True
    if "unless that player pays" in text:
        return True
    if "may pay" in text and "if the player doesn't" in text:
        return True
    if "activated abilities" in text and "can't be activated" in text:
        return True
    if "can't cast" in text and ("graveyard" in text or "libraries" in text):
        return True
    if "less than three mana" in text:
        return True
    if "search" in text and "librar" in text and (
        "can't" in text or "instead" in text or "top four" in text or "while" in text
    ):
        return True
    if "graveyard" in text and "exile" in text and "instead" in text:
        return True
    tapped = (
        "enter the battlefield tapped" in text
        or "enters the battlefield tapped" in text
        or "enter tapped" in text
        or "enters tapped" in text
    )
    if tapped and (
        "opponent" in text
        or "each player" in text
        or "lands enter" in text
        or "nonbasic" in text
        or "artifacts and lands" in text
    ):
        return True
    if "produces {c} instead" in text:
        return True
    return False


def roles(card) -> set:
    """Functional tags from Oracle text, plus type tags that do not create edges."""
    text = (card.text or "").lower()
    name = card.name
    out: set[str] = set()

    if card.is_enchantment:
        out.add("enchantment")
    subtypes = {s.lower() for s in (card.subtypes or set())}
    if "aura" in subtypes:
        out.add("aura")
    if "equipment" in subtypes or name in {"Lightning Greaves", "Swiftfoot Boots", "Whispersilk Cloak"}:
        out.add("equipment")

    if name in {
        "Sythis, Harvest's Hand", "Enchantress's Presence", "Mesa Enchantress",
        "Verduran Enchantress", "Argothian Enchantress", "Satyr Enchanter",
    } or ("whenever you cast an enchantment" in text and "draw" in text):
        out.add("enchantress-draw")
    if "constellation" in text:
        out.add("constellation")
    if name in {"Opalescence", "Starfield of Nyx", "Enchanted Evening"}:
        out.add("enchant-finisher")
    if name in {"Sanctum Weaver", "Jukai Naturalist"} or (
            "number of enchantments you control" in text and "add" in text):
        out.add("enchant-ramp")
    if name.startswith("Terra,") or name == "Terra, Magical Adept":
        out.add("enchantress-draw")
        out.add("mill")

    if card.is_creature:
        out.add("creature")
    if card.is_instant or card.is_sorcery:
        out.add("spell")
    if card.is_artifact and not card.is_creature:
        out.add("artifact")
    if card.is_planeswalker:
        out.add("planeswalker")

    if "prowess" in text or "Prowess" in (card.keywords or set()):
        out.add("prowess")
    if "mill" in text:
        out.add("mill")
    if "exile" in text and ("graveyard" in text or "target" in text):
        out.add("exile")
    if (
        "{t}: add" in text
        or "add {" in text
        or "add one mana" in text
        or ("tapped for mana" in text and "add" in text)
        or "additional land" in text
        or "every basic land type" in text
        or (
            "search your library" in text
            and any(p in text for p in (
                "forest", "plains", "island", "swamp", "mountain", "basic land", "land card",
            ))
        )
        or ("less to cast" in text and "cost" in text)
    ):
        out.add("ramp")
    if "draw a card" in text or "draw two" in text or "draw cards" in text:
        out.add("draw")
    if "create " in text and "token" in text:
        out.add("token")
    if "token" in text and ("twice that many" in text or "three times" in text):
        out.add("token")
    if "whenever a creature" in text and "enters" in text and "damage" in text:
        out.add("token")
    if (
        "tokens you control get" in text
        or "you control get +" in text
        or ("other attacking" in text and "gets +" in text)
        or (
            ("creatures you control" in text or "each creature you control" in text)
            and any(p in text for p in (
                "get +", "gain trample", "gain flying", "gain vigilance",
                "gain indestructible", "gain double strike", "+1/+1",
            ))
        )
    ):
        out.add("anthem")
    subs = {s.lower() for s in (card.subtypes or set())}
    if "cat" in subs or "dog" in subs or "changeling" in text or "every creature type" in text:
        out.add("catdog")
    if card.is_creature and card.power and str(card.power).isdigit() and int(card.power) >= 5:
        out.add("bomb")
    if "counter target" in text or "destroy target" in text or "exile target" in text:
        out.add("removal")
    if "exile up to" in text and "target" in text:
        out.add("removal")
    if "search your library" in text:
        out.add("tutor")
    if "can't be countered" in text or name == "Destiny Spinner":
        out.add("protection")
    if "permanents you control gain hexproof" in text or name == "Heroic Intervention":
        out.add("protection")
    if name in {"Lightning Greaves", "Swiftfoot Boots", "Whispersilk Cloak"}:
        out.add("protection")
    if _is_stax(text) or name in _STAX_PATCH:
        out.add("stax")
    if (("return" in text or "put target" in text or "put a" in text)
            and "graveyard" in text and ("battlefield" in text or "hand" in text)):
        out.add("reanimate")
    if name == "Reanimate":
        out.add("reanimate")
    if name == "Six":
        out.add("mill")
        out.add("draw")
        out.add("reanimate")
    return out


def _strong(role_set: set) -> set:
    return role_set - _WEAK


def _functional_edge(ra: set, rb: set) -> bool:
    return bool(_strong(ra) & _strong(rb))


def _mentions(text: str, other: str) -> bool:
    """True when Oracle text names another card. Short names are skipped."""
    if len(other) < 8 or other.lower() == text:
        return False
    return re.search(rf"\b{re.escape(other.lower())}\b", text) is not None


def _components(adj: dict[str, set], names: list[str]) -> list[list[str]]:
    seen: set[str] = set()
    comps: list[list[str]] = []
    for n in names:
        if n in seen:
            continue
        stack = [n]
        seen.add(n)
        comp: list[str] = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        comps.append(sorted(comp))
    comps.sort(key=lambda c: (-len(c), c[0] if c else ""))
    return comps


def report(deck_path: str, min_degree: int | None = None) -> dict:
    oracle = Oracle()
    pool = Pool(oracle, deck_path)
    cards = [c for c in pool.decklist() if not c.is_land]
    commander = pool.commander
    by = {c.name: c for c in cards}
    by[commander.name] = commander
    names = list(by)
    role_map = {n: roles(by[n]) for n in names}
    text_map = {n: (by[n].text or "").lower() for n in names}

    functional: dict[str, set] = {n: set() for n in names}
    coplay: dict[str, set] = {n: set() for n in names}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if _functional_edge(role_map[a], role_map[b]):
                functional[a].add(b)
                functional[b].add(a)
            # Score only: one card's rules text names the other.
            if _mentions(text_map[a], b) or _mentions(text_map[b], a):
                coplay[a].add(b)
                coplay[b].add(a)

    nonlands = [n for n in names if n != commander.name]
    floor = _MIN_DEGREE if min_degree is None else min_degree
    thin = []
    for n in nonlands:
        degree = len(functional[n])
        if degree < floor:
            thin.append({
                "name": n,
                "degree": degree,
                "coplay_degree": len(coplay[n]),
                "roles": sorted(role_map[n]),
                "functions": sorted(_strong(role_map[n])),
            })
    thin.sort(key=lambda t: (t["degree"], t["name"]))

    degrees = [len(functional[n]) for n in nonlands]
    avg_deg = sum(degrees) / len(degrees) if degrees else 0.0
    min_deg = min(degrees) if degrees else 0
    # Packages are per plan-role, not raw components. Multi-role cards
    # bridge components into one blob and hide a two-plan deck.
    islands = []
    for role in sorted(_PLAN):
        members = sorted(n for n in names if role in role_map[n])
        if len(members) >= 2:
            islands.append({"label": role, "size": len(members), "names": members})
    islands.sort(key=lambda isle: (-isle["size"], isle["label"]))
    split = sum(1 for isle in islands if isle["size"] >= 3) >= 2
    components = _components(functional, names)
    return {
        "commander": commander.name,
        "nodes": len(names),
        "edges": sum(len(v) for v in functional.values()) // 2,
        "avg_degree": round(avg_deg, 2),
        "min_degree": min_deg,
        "degree_floor": floor,
        "coplay_edges": sum(len(v) for v in coplay.values()) // 2,
        "thin": thin,
        "islands": islands,
        "components": len(components),
        "split": split,
        "passed": not thin,
    }


def analyze(deck_path: str) -> None:
    data = report(deck_path)
    print("commander:", data["commander"])
    print(
        "nodes:", data["nodes"],
        "functional_edges:", data["edges"],
        "avg_degree:", data["avg_degree"],
        "coplay_edges:", data["coplay_edges"],
        "split:", data["split"],
    )
    print("functional degree under 3:")
    if not data["thin"]:
        print("  none")
    for row in data["thin"]:
        print(
            f"  {row['degree']}  coplay={row['coplay_degree']}  "
            f"{row['name']}  functions={row['functions']}"
        )
    print("plan packages:")
    if not data["islands"]:
        print("  none")
    for isle in data["islands"]:
        preview = ", ".join(isle["names"][:8])
        more = "" if isle["size"] <= 8 else f" (+{isle['size'] - 8})"
        print(f"  {isle['size']:3}  {isle['label']}  {preview}{more}")
    print("functional components:", data["components"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python simulator/graph.py DECK.py")
    analyze(sys.argv[1])
