"""Generic oracle-text behavior layer (CR-shaped approximations).

Used as a fallback for decks beyond the v11 list (EDHREC Nekusar / Kuja /
Wandering Minstrel pods). Implements, from oracle text:

- mana abilities (605.1a): lands/rocks "{T}: Add ...", pain lands, Cabal
  Coffers-style "for each Swamp", Blood Moon / Urborg statics
- spell effects (608): tutors, reanimate, wheels, mass removal / MLD,
  counters, destroy/exile, damage, rituals, draw, tokens, buffs, life
- common named triggers for the three pod decks (Nekusar, Sheoldred,
  Consecrated Sphinx, Orcish Bowmasters, Howling Mine, Puzzle Box, ...)

Effects the engine cannot represent are logged as "(simplified ...)" rather
than guessed silently.
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional, Tuple

from .game import Game, Permanent, Player, StackObject
from .oracle import CardDef

_BASICS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
_BASIC_COLORS = {"Plains": ["W"], "Island": ["U"], "Swamp": ["B"],
                 "Mountain": ["R"], "Forest": ["G"], "Wastes": ["C"]}
_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "a": 1, "an": 1}


def _side_none(game, pl, perm):
    return None


def _lowest_opponent(game: Game, pl: Player) -> Optional[Player]:
    alive = [p for p in game.opponents(pl) if p.alive]
    return min(alive, key=lambda p: p.life) if alive else None


# Cache for rare global statics (Blood Moon/Urborg/Harbinger/Urza): keyed on
# per-game board-size signature, so the common pod decks (which run none of
# these) never pay an O(boards) scan per mana query. Stale only if board
# composition changes at an identical size; self-heals on the next size change.
_WORLD_STATIC_CACHE = {}


def _world_statics(game: Game):
    sig = tuple(len(p.battlefield) for p in game.players)
    hit = _WORLD_STATIC_CACHE.get(id(game))
    if hit is not None and hit[0] == sig:
        return hit[1]
    bm = any(q.card.name == "Blood Moon" for p in game.players for q in p.battlefield)
    ub = any(q.card.name == "Urborg, Tomb of Yawgmoth" for p in game.players for q in p.battlefield)
    hb = any(q.card.name == "Harbinger of the Seas" for p in game.players for q in p.battlefield)
    ur = any(q.card.name == "Urza, Lord High Artificer" for p in game.players for q in p.battlefield)
    _WORLD_STATIC_CACHE[id(game)] = (sig, (bm, ub, hb, ur))
    return (bm, ub, hb, ur)


def _strongest_creature(game: Game, of: Optional[Player] = None) -> Optional[Permanent]:
    best = None
    for p in game.players:
        if not p.alive:
            continue
        if of is not None and p is not of:
            continue
        for q in p.battlefield:
            if q.is_creature() and (best is None or q.power(game) > best.power(game)):
                best = q
    return best


def _swamp_count(game: Game, pl: Player) -> int:
    return sum(1 for q in pl.battlefield
               if q.card.is_land and ("Swamp" in q.card.subtypes or q.card.name == "Swamp"))


def _mana_from_phrase(phrase: str):
    """Parse an 'Add ...' phrase into (n, colors | 'any')."""
    p = phrase.lower()
    if "one mana of any color" in p or "any one color" in p:
        return 1, "any"
    if "for each swamp" in p:
        return None  # handled by caller
    syms = re.findall(r"{([^}]*)}", p)
    colors = []
    for s in syms:
        u = s.upper()
        if u in "WUBRG":
            colors.append(u)
        elif u == "C":
            colors.append("C")
        elif u == "X":
            colors.append("X")
    if not colors:
        return None
    if " or " in p:
        return 1, list(dict.fromkeys(colors))
    return len(colors), colors


def generic_mana_abilities(game: Game, perm: Permanent) -> List[Tuple[int, object, Callable]]:
    """CR 605.1a fallback: parse "{T}: Add ..." from oracle text."""
    pl = perm.controller
    name = perm.card.name
    t = perm.card.text.lower()
    out: List[Tuple[int, object, Callable]] = []
    blood_moon, urborg, harbinger, _urza = _world_statics(game)

    if perm.card.is_land:
        if name in _BASIC_COLORS:
            out.append((1, _BASIC_COLORS[name], _side_none))
            if urborg:
                out.append((1, ["B"], _side_none))
            return out
        if blood_moon:
            return [(1, ["R"], _side_none)]  # nonbasic lands are Mountains
        if harbinger:
            return [(1, ["U"], _side_none)]  # nonbasic lands are Islands
        # fetch lands: no mana; activated in activatable()
        if "sacrifice" in t and "search your library" in t:
            return []
        m = re.search(r"{t}.*?: add ([^.\n]*)", t)
        if not m:
            return out
        phrase = m.group(1)
        if "for each swamp" in phrase:
            n = _swamp_count(game, pl)
            out.append((n, ["B"], _side_none))
        else:
            res = _mana_from_phrase(phrase)
            if res is None:
                return out
            n, colors = res
            side = _side_none
            if "deals 1 damage to you" in t or "pay 1 life" in t:
                side = lambda g, pl_, pm: setattr(pl_, "life", pl_.life - 1)
            elif "deals 2 damage to you" in t:
                side = lambda g, pl_, pm: setattr(pl_, "life", pl_.life - 2)
            out.append((n, colors, side))
        if urborg:
            out.append((1, ["B"], _side_none))
        # Vesuva approximation: copies a land; tap for any color
        if name == "Vesuva":
            out.append((1, "any", _side_none))
        return out

    # non-land permanents: mana rocks and friends
    m = re.search(r"{t}.*?: add ([^.\n]*)", t)
    if m:
        phrase = m.group(1)
        res = _mana_from_phrase(phrase)
        if res is not None:
            n, colors = res
            side = _side_none
            if "deals 1 damage to you" in t:
                side = lambda g, pl_, pm: setattr(pl_, "life", pl_.life - 1)
            if "sacrifice" in t and "lotus petal" in t:
                def _petal(g, pl_, pm):
                    g.sacrifice(pl_, pm)
                side = _petal
            out.append((n, colors, side))
    if not out and "mox" in name.lower() and "add one mana of any color" in t:
        out.append((1, "any", _side_none))
    if not out and name == "Chrome Mox" and "add one mana of any color" in t:
        out.append((1, "any", _side_none))
    # Urza, Lord High Artificer: artifacts you control are mana artifacts
    if perm.card.is_artifact and any(
            q.card.name == "Urza, Lord High Artificer" for q in pl.battlefield):
        out.append((1, ["U"], _side_none))
    return out


# ---------------------------------------------------------------------------
# Enter-the-battlefield + static entry effects
# ---------------------------------------------------------------------------

def generic_on_enter(game: Game, perm: Permanent) -> None:
    pl = perm.controller
    n = perm.card.name
    t = perm.card.text.lower()
    if perm.card.is_land:
        if "enters the battlefield tapped" in t or "enters tapped" in t:
            perm.tapped = True
        if pl.commander.name == "The Wandering Minstrel" and perm.card.name != pl.commander.name:
            perm.tapped = False  # lands you control enter untapped
    if n == "Orcish Bowmasters":
        opp = _lowest_opponent(game, pl)
        if opp:
            game.deal_damage(perm, opp, 1)
        game.create_token(pl, "Orc Army", 1, 1, types={"Creature", "Orc", "Army"}, colors={"B"})
    if n == "Keldon Firebombers":
        for p in game.players:
            lands = [q for q in p.battlefield if q.card.is_land]
            for q in lands[3:]:
                game.destroy(q, "Keldon Firebombers")
        game.log("      Keldon Firebombers: everyone keeps 3 lands")
    if n == "The One Ring":
        perm.counters["burden"] = perm.counters.get("burden", 0) + 1
        game.log("      The One Ring ETB (burden 1)")
    if n in ("Dack Fayden", "Narset, Parter of Veils", "Tezzeret, Master of the Bridge"):
        perm.counters["loyalty"] = perm.counters.get("loyalty", 0) + (4 if n == "Dack Fayden" else 5)
    if n == "Roaming Throne":
        perm.chosen_type = perm.chosen_type or "Shaman"
    if n == "Jin-Gitaxias, Core Augur":
        for opp in game.opponents(pl):
            game.flags[f"{opp.name}_max_hand_0"] = True
    if n == "Lumra, Bellow of the Woods":
        lands = [c for c in pl.graveyard if c.is_land][:5]
        for c in lands:
            pl.graveyard.remove(c)
            pl.battlefield.append(Permanent(card=c, controller=pl, owner=pl))
        game.log(f"      Lumra: {len(lands)} lands back from graveyard")
    if n == "Platinum Angel":
        pass  # static "you can't lose" not modeled


# ---------------------------------------------------------------------------
# On-cast triggers (603.2)
# ---------------------------------------------------------------------------

def generic_on_cast(game: Game, pl: Player, obj: StackObject) -> None:
    card = obj.card
    for q in list(pl.battlefield):
        n = q.card.name
        if n == "Guttersnipe" and (card.is_instant or card.is_sorcery):
            for opp in game.opponents(pl):
                game.deal_damage(q, opp, 2)
        elif n == "Coruscation Mage" and (card.is_instant or card.is_sorcery):
            opp = _lowest_opponent(game, pl)
            if opp:
                game.deal_damage(q, opp, 1)
        elif n == "Aetherflux Reservoir":
            pl.life += 1
        elif n == "Birgi, God of Storytelling":
            pl.mana_pool["R"] += 1
        elif n == "Urabrask" and (card.is_instant or card.is_sorcery):
            pl.mana_pool["R"] += 1
            opp = _lowest_opponent(game, pl)
            if opp:
                game.deal_damage(q, opp, 1)
        elif n == "Wizard" and q.token and not card.is_creature:
            # Kuja's token: whenever you cast a noncreature spell, 1 to each opponent
            for opp in game.opponents(pl):
                game.deal_damage(q, opp, 1)
        elif n == "Joyful Stormsculptor" and "Convoke" in card.keywords:
            for opp in game.opponents(pl):
                game.deal_damage(q, opp, 1)
    # Jin-Gitaxias, Progress Tyrant: copy your instants and sorceries
    if (card.is_instant or card.is_sorcery) and any(
            q.card.name == "Jin-Gitaxias, Progress Tyrant" for q in pl.battlefield):
        copy = StackObject(kind="spell", card=card, controller=pl, x=obj.x,
                           targets=list(obj.targets), modes=list(obj.modes),
                           desc=f"Progress Tyrant copy of {card.name}")
        copy._is_copy = True
        game.stack.append(copy)
        game.log(f"      Progress Tyrant copies {card.name}")
    # Nether Void: counter unless caster pays 3
    for q in game.players:
        for v in list(q.battlefield):
            if v.card.name == "Nether Void" and v.controller is not pl:
                if not pl.ai.pays_tax(game, pl, 3, v):
                    if obj in game.stack:
                        game.stack.remove(obj)
                        if card.is_legendary and card.name == pl.commander.name:
                            pl.command_zone.append(card)
                        else:
                            pl.graveyard.append(card)
                        game.log(f"      Nether Void counters {card.name}")
    # Price of Glory: instant/sorcery -> destroy a land of the caster
    if card.is_instant or card.is_sorcery:
        for q in game.players:
            for v in list(q.battlefield):
                if v.card.name == "Price of Glory" and v.controller is not pl:
                    lands = [r for r in pl.battlefield if r.card.is_land]
                    if lands:
                        game.destroy(lands[0], "Price of Glory")


# ---------------------------------------------------------------------------
# Draw triggers (603.2h) -- Nekusar & friends
# ---------------------------------------------------------------------------

def on_draw(game: Game, pl: Player, n: int) -> None:
    key = "draw_chain"
    game.flags[key] = game.flags.get(key, 0) + n
    if game.flags[key] > 200:
        game.flags[key] = max(0, game.flags[key] - n)
        return
    try:
        for p in list(game.players):
            if not p.alive:
                continue
            for q in list(p.battlefield):
                nm = q.card.name
                if nm == "Nekusar, the Mindrazer" and p is not pl:
                    pl.life -= n
                    game.log(f"      Nekusar: {pl.name} loses {n} life")
                elif nm == "Sheoldred, the Apocalypse":
                    if p is pl:
                        pl.life += 2 * n
                        game.log(f"      Sheoldred: {pl.name} gains {2*n} life")
                    else:
                        pl.life -= 2 * n
                        game.log(f"      Sheoldred: {pl.name} loses {2*n} life")
                elif nm == "Orcish Bowmasters" and p is not pl:
                    pl.life -= n
                    game.log(f"      Orcish Bowmasters: {pl.name} loses {n} life")
                elif nm == "Niv-Mizzet, Parun" and p is pl:
                    opp = _lowest_opponent(game, pl)
                    if opp:
                        opp.life -= n
                        game.log(f"      Niv-Mizzet: {opp.name} loses {n} life")
                elif nm == "Consecrated Sphinx" and p is not pl:
                    game.draw(p, 2 * n)
                    game.log(f"      Consecrated Sphinx: {p.name} draws {2*n}")
        # Smothering Tithe: whenever an opponent draws, they pay {2} or we Treasure
        for opp in list(game.players):
            if opp is pl or not opp.alive:
                continue
            for q in list(opp.battlefield):
                if q.card.name == "Smothering Tithe":
                    if opp.ai.pays_tax(game, pl, 2, q):
                        continue
                    game.create_treasure(opp, n)
    finally:
        game.flags[key] = max(0, game.flags[key] - n)


def on_draw_step(game: Game, pl: Player) -> int:
    """Draw-step triggers (503/504): Nekusar, Howling Mine, Puzzle Box."""
    extra = 0
    for q in pl.battlefield:
        if q.card.name == "Nekusar, the Mindrazer":
            extra += 1
        elif q.card.name == "Howling Mine" and not q.tapped:
            extra += 1
    if any(q.card.name == "Teferi's Puzzle Box" for q in pl.battlefield):
        for c in list(pl.hand):
            pl.hand.remove(c)
            pl.library.append(c)
        for c in list(pl.graveyard):
            pl.graveyard.remove(c)
            pl.library.append(c)
        pl.shuffle()
        extra += 7
        game.log("      Teferi's Puzzle Box: shuffle, draw 7")
    from .terra import on_draw_step as terra_on_draw_step
    extra += terra_on_draw_step(game, pl)
    return extra


def on_begin_combat(game: Game, pl: Player) -> None:
    """507: beginning of combat triggers (Minstrel's Ballad)."""
    if pl.commander.name == "The Wandering Minstrel" and any(
            q.card.name == "The Wandering Minstrel" for q in pl.battlefield):
        towns = sum(1 for q in pl.battlefield if "Town" in q.card.subtypes)
        if towns >= 5:
            game.create_token(pl, "Elemental", 2, 2,
                              types={"Creature", "Elemental"}, colors={"W", "U", "B", "R", "G"})
            game.log("      Minstrel's Ballad: 2/2 Elemental")


def on_end_step(game: Game, pl: Player) -> None:
    """End-step triggers (513): Kuja token, Jin-Gitaxias, Sire of Insanity."""
    if pl.commander.name == "Kuja, Genome Sorcerer" and any(
            q.card.name == "Kuja, Genome Sorcerer" for q in pl.battlefield):
        perm = game.create_token(pl, "Wizard", 0, 1, types={"Creature", "Wizard"}, colors={"B"})
        perm.tapped = True
        game.log("      Kuja: tapped 0/1 Wizard token")
    for q in pl.battlefield:
        if q.card.name == "Jin-Gitaxias, Core Augur":
            game.draw(pl, 7)
            for opp in game.opponents(pl):
                game.flags[f"{opp.name}_max_hand_0"] = True
            game.log("      Jin-Gitaxias: draw 7")
        elif q.card.name == "Sire of Insanity":
            for p in game.players:
                for c in list(p.hand):
                    p.discard_card(c)
            game.log("      Sire of Insanity: everyone discards their hand")
        elif q.card.name == "Undergrowth Recon":
            best = _strongest_creature(game, of=pl)
            if best is not None and best.power(game) >= 4:
                lands = [c for c in pl.graveyard if c.is_land]
                if lands:
                    c = max(lands, key=lambda c: c.mana_cost.cmc())
                    pl.graveyard.remove(c)
                    pl.battlefield.append(Permanent(card=c, controller=pl, owner=pl))
                    game.log("      Undergrowth Recon: land back")


def generic_upkeep(game: Game, pl: Player) -> None:
    for q in pl.battlefield:
        n = q.card.name
        if n == "The One Ring":
            game.draw(pl, 1)
            pl.life -= 1
            game.log("      The One Ring: draw 1, lose 1")
        elif n == "Necropotence":
            pass
        elif n == "Slaughter Pact":
            pass  # upkeep payment simplified away
        elif n == "Smokestack":
            soot = q.counters.get("soot", 0) + 1
            q.counters["soot"] = soot
            for p in game.players:
                for _ in range(min(soot, 4)):
                    cs = [r for r in p.battlefield if r.is_creature()]
                    if cs:
                        game.sacrifice(p, min(cs, key=lambda r: r.power(game)))
                    elif [r for r in p.battlefield if r.card.is_land]:
                        game.sacrifice(p, [r for r in p.battlefield if r.card.is_land][0])
            game.log(f"      Smokestack: {soot} sacrifices each")
        elif n == "Impending Disaster":
            q.counters["age"] = q.counters.get("age", 0) + 1
            if q.counters["age"] >= 7:
                for p in game.players:
                    for r in list(p.battlefield):
                        if r.card.is_land:
                            game.destroy(r, "Impending Disaster")


# ---------------------------------------------------------------------------
# Death triggers
# ---------------------------------------------------------------------------

def generic_on_death(game: Game, perm: Permanent) -> None:
    if perm.card.is_land:
        for p in game.players:
            if any(q.card.name == "Dingus Egg" for q in p.battlefield):
                perm.controller.life -= 2
                game.log("      Dingus Egg: 2 to land's controller")
                break


# ---------------------------------------------------------------------------
# Activated abilities for the AI (602) -- fetch lands, Minstrel ballad
# ---------------------------------------------------------------------------

def generic_activatable(game: Game, pl: Player) -> List[Tuple[str, Callable]]:
    acts = []
    for perm in pl.battlefield:
        if perm.tapped:
            continue
        n = perm.card.name
        t = perm.card.text.lower()
        if perm.card.is_land and "sacrifice" in t and "search your library" in t:
            m = re.search(r"search your library for (?:a |an |up to two |up to three )?([a-z ]+?)(?: card| cards)", t)
            if m:
                want = m.group(1).strip()
                enters_tapped = "onto the battlefield tapped" in t
                def _fetch(perm=perm, want=want, enters_tapped=enters_tapped):
                    game.sacrifice(pl, perm)
                    pl.life -= 1
                    parts = [w for w in want.split() if w not in ("basic", "land", "or", "and")]
                    def pred(c):
                        if not c.is_land:
                            return False
                        if not parts:
                            return "Basic" in c.supertypes
                        return any(w.capitalize() in (c.subtypes | {c.name}) for w in parts)
                    found = game.search_library(pl, pred, 1, to_hand=False)
                    if found:
                        found[0].tapped = enters_tapped
                        game.log(f"      {pl.name} fetches {found[0].name} with {perm.card.name}")
                acts.append((f"Fetch with {n}", _fetch))
                def _fetch(perm=perm, want=want):
                    game.sacrifice(pl, perm)
                    pl.life -= 1
                    parts = [w for w in want.split() if w != "basic"]
                    def pred(c):
                        if not c.is_land:
                            return False
                        if not parts:
                            return "Basic" in c.supertypes
                        return any(w.capitalize() in (c.subtypes | {c.name}) for w in parts)
                    found = game.search_library(pl, pred, 1, to_hand=False)
                    if found:
                        found[0].tapped = True
                        game.log(f"      {pl.name} fetches {found[0].name} with {perm.card.name}")
                acts.append((f"Fetch with {n}", _fetch))
        if n == "The Wandering Minstrel" and game.mana_available(pl) >= 9:
            towns = sum(1 for q in pl.battlefield if "Town" in q.card.subtypes)
            if towns > 0:
                def _ballad(perm=perm, towns=towns):
                    game.pay_mana(pl, 9, {})
                    for q in pl.battlefield:
                        if q.is_creature() and q is not perm:
                            q.counters["+1/+1"] += towns
                    game.log(f"      Minstrel ballad: +{towns}/+{towns} to other creatures")
                acts.append(("Minstrel: ballad", _ballad))
    return acts


# ---------------------------------------------------------------------------
# Static cost modifiers
# ---------------------------------------------------------------------------

def cost_mods(game: Game, pl: Player, card: CardDef, from_zone: str):
    """Return (free, min_total, reduction) from statics."""
    free = False
    min_total = None
    red = 0
    if from_zone == "hand" and not card.is_land and any(
            q.card.name == "Omniscience" for q in pl.battlefield):
        free = True
    if any(q.card.name == "Trinisphere" for p in game.players for q in p.battlefield):
        min_total = 3
    if "Red" in card.colors and any(q.card.name == "Ruby Medallion" for q in pl.battlefield):
        red += 1
    return free, min_total, red


# ---------------------------------------------------------------------------
# Spell resolution (608) -- generic oracle-text patterns
# ---------------------------------------------------------------------------

def _exile_perm(game: Game, perm: Permanent) -> None:
    pl = perm.controller
    if perm not in pl.battlefield:
        return
    pl.battlefield.remove(perm)
    if perm.card.is_legendary and perm.card.name == pl.commander.name:
        pl.command_zone.append(perm.card)
    else:
        pl.exile.append(perm.card)
    game.log(f"      {perm.name} exiled")


def _pick_target(game: Game, pl: Player, what: str) -> Optional[Permanent]:
    if what == "creature":
        return _strongest_creature(game, of=None) if _strongest_creature(game, of=None) else None
    if what == "land":
        for p in game.opponents(pl):
            best = None
            for q in p.battlefield:
                if not q.card.is_land:
                    continue
                if q.card.name in _BASIC_COLORS:
                    continue
                if best is None or len(q.card.color_identity) > len(best.card.color_identity):
                    best = q
            if best:
                return best
        for p in game.opponents(pl):
            for q in p.battlefield:
                if q.card.is_land:
                    return q
        return None
    if what in ("artifact", "enchantment", "planeswalker"):
        for p in game.opponents(pl):
            for q in p.battlefield:
                if what == "artifact" and q.card.is_artifact:
                    return q
                if what == "enchantment" and q.card.is_enchantment:
                    return q
                if what == "planeswalker" and q.card.is_planeswalker:
                    return q
    return None


def _generic_tutor(game: Game, obj: StackObject, t: str) -> bool:
    pl = obj.controller
    if "onto the battlefield" in t:
        to_zone = "battlefield"
    elif "into your graveyard" in t or "put it into your graveyard" in t:
        to_zone = "graveyard"
    else:
        to_zone = "hand"
    pred = None
    if "basic land card" in t:
        pred = lambda c: c.is_land and "Basic" in c.supertypes
    elif "creature card" in t and "instant or sorcery" not in t:
        pred = lambda c: c.is_creature
    elif "instant or sorcery card" in t:
        pred = lambda c: c.is_instant or c.is_sorcery
    elif "artifact card" in t:
        pred = lambda c: c.is_artifact
    elif "land card" in t:
        pred = lambda c: c.is_land
    cands = [c for c in pl.library if pred(c)] if pred else list(pl.library)
    if not cands:
        pl.shuffle()
        return True
    def score(c):
        return (500 if not c.is_land else 0) + c.mana_cost.cmc() * 10 + (5 if c.is_creature else 0)
    pick = max(cands, key=score)
    pl.library.remove(pick)
    if to_zone == "hand":
        pl.hand.append(pick)
    elif to_zone == "battlefield":
        pl.battlefield.append(Permanent(card=pick, controller=pl, owner=pl))
    else:
        pl.graveyard.append(pick)
    pl.shuffle()
    game.log(f"      Tutor: {pick.name} -> {to_zone}")
    if "at random" in t and to_zone == "hand" and pl.hand:
        pl.discard_card(pl.hand[game.rng.randrange(len(pl.hand))])
    return True


def _reanimate(game: Game, pl: Player) -> None:
    cands = [c for c in pl.graveyard if c.is_creature]
    if not cands:
        return
    pick = max(cands, key=lambda c: int(c.power) if c.power and c.power.isdigit() else 0)
    pl.graveyard.remove(pick)
    pl.battlefield.append(Permanent(card=pick, controller=pl, owner=pl))
    game.log(f"      Reanimate: {pick.name}")


def _wheel(game: Game, pl: Player, t: str) -> None:
    discards = []
    for p in game.players:
        if not p.alive:
            continue
        discards.append(len(p.hand))
        for c in list(p.hand):
            p.discard_card(c)
    n = 7
    if "draws that many cards" in t:
        n = max(discards) if discards else 7
    for p in game.players:
        if p.alive:
            game.draw(p, n)
    game.log(f"      Wheel: everyone discards and draws {n}")


def _mass_removal(game: Game, pl: Player, t: str, x: int) -> bool:
    # Splendid Reclamation
    if "return all land cards from your graveyard to the battlefield" in t:
        for c in list(pl.graveyard):
            if c.is_land:
                pl.graveyard.remove(c)
                pl.battlefield.append(Permanent(card=c, controller=pl, owner=pl))
        game.log("      Splendid Reclamation: all lands back")
        return True
    # Sunder
    if "return all lands to their owners' hands" in t:
        for p in game.players:
            for q in list(p.battlefield):
                if q.card.is_land:
                    p.battlefield.remove(q)
                    p.hand.append(q.card)
        game.log("      Sunder: all lands to hand")
        return True
    # Death Cloud
    if "each player loses x life" in t or "each player loses x life, discards" in t:
        for p in game.players:
            if p.alive:
                p.life -= x
        game.log(f"      Death Cloud: each player loses {x} life")
        return True
    # Wildfire
    if "deals 4 damage to each creature" in t and "sacrifices four lands" in t:
        for p in game.players:
            for q in p.battlefield:
                if q.is_creature():
                    q.damage += 4
            lands = [q for q in p.battlefield if q.card.is_land]
            for q in lands[:4]:
                game.destroy(q, "Wildfire")
        game.log("      Wildfire: 4 to each creature, sac 4 lands")
        return True
    # Cataclysm: keep best creature + best land
    if "chooses from the permanents they control an artifact, a creature, an enchantment, and a land" in t:
        for p in game.players:
            keep = set()
            best_c = _strongest_creature(game, of=p)
            if best_c:
                keep.add(id(best_c))
            lands = [q for q in p.battlefield if q.card.is_land]
            if lands:
                keep.add(id(max(lands, key=lambda q: q.card.mana_cost.cmc())))
            for q in list(p.battlefield):
                if id(q) not in keep and (q.is_creature() or q.card.is_land):
                    game.destroy(q, "Cataclysm")
        game.log("      Cataclysm")
        return True
    # Bend or Break: destroy about half of each player's lands
    if "separates their lands into two piles" in t:
        for p in game.players:
            lands = [q for q in p.battlefield if q.card.is_land]
            for q in lands[:len(lands) // 2]:
                game.destroy(q, "Bend or Break")
        game.log("      Bend or Break: half of each player's lands")
        return True
    # Tectonic Break: each player sacrifices X lands
    if "each player sacrifices x lands" in t:
        for p in game.players:
            lands = [q for q in p.battlefield if q.card.is_land]
            for q in lands[:x]:
                game.destroy(q, "Tectonic Break")
        game.log(f"      Tectonic Break: sac {x} lands each")
        return True
    # Global Ruin / Thoughts of Ruin / Ruination: nonbasic lands
    if ("nonbasic lands" in t or "sacrifices the rest" in t) and ("destroy" in t or "sacrifice" in t):
        for p in game.players:
            for q in list(p.battlefield):
                if q.card.is_land and q.card.name not in _BASIC_COLORS:
                    game.destroy(q, "mass land")
        game.log("      Nonbasic lands destroyed")
        return True
    # Boil / Acid Rain: lands of a color
    m = re.search(r"destroy all (islands|forests|mountains|plains|swamps)", t)
    if m:
        target_color = {"islands": "U", "forests": "G", "mountains": "R",
                        "plains": "W", "swamps": "B"}[m.group(1)]
        for p in game.players:
            for q in list(p.battlefield):
                if q.card.is_land and target_color in q.card.color_identity:
                    game.destroy(q, "color land destruction")
        game.log(f"      All {m.group(1)} destroyed")
        return True
    # category flags
    destroy_land = ("all lands" in t or "all lands you control" in t or "all lands they control" in t) and                    any(w in t for w in ("destroy", "exile", "sacrifices"))
    destroy_creature = ("all creatures" in t or "destroy all creatures" in t or "all creatures and planeswalkers" in t) and                        any(w in t for w in ("destroy", "exile"))
    destroy_artifact = "all artifacts" in t and any(w in t for w in ("destroy", "exile"))
    destroy_ench = "all enchantments" in t and any(w in t for w in ("destroy", "exile"))
    if "each player sacrifices all lands" in t:
        destroy_land = True
    if "all artifacts, creatures, enchantments, and lands" in t:
        destroy_land = destroy_creature = destroy_artifact = destroy_ench = True
    if not (destroy_land or destroy_creature or destroy_artifact or destroy_ench):
        return False
    opponents_only = "you don't control" in t
    for p in game.players:
        for q in list(p.battlefield):
            if opponents_only and q.controller is pl:
                continue
            if destroy_land and q.card.is_land:
                game.destroy(q, "mass land")
            elif destroy_creature and q.is_creature():
                game.destroy(q, "mass creatures")
            elif destroy_artifact and q.card.is_artifact:
                game.destroy(q, "mass artifacts")
            elif destroy_ench and q.card.is_enchantment:
                game.destroy(q, "mass enchantments")
    game.log("      Mass removal executed")
    return True


def _token_create(game: Game, pl: Player, t: str, x: int) -> bool:
    m = re.search(r"create (?:a |an |(?:up to )?)([a-z]+) (?:(\d+)/(\d+) )?(?:black |white |blue |red |green |colorless |all colors )?([a-z ]+?) (?:creature )?token", t)
    if not m:
        return False
    num = _NUM.get(m.group(1), 1)
    if m.group(1) == "x":
        num = x
    p = int(m.group(2) or 1)
    q = int(m.group(3) or 1)
    kinds = m.group(4).split()
    if kinds and kinds[0] == "treasure":
        game.create_treasure(pl, num)
        return True
    name = " ".join(w.capitalize() for w in kinds)
    game.create_token(pl, name, p, q, types={"Creature"} | {k.capitalize() for k in kinds},
                      colors=set())
    game.log(f"      Tokens: {num}x {name} {p}/{q}")
    return True


def generic_spell_resolution(game: Game, obj: StackObject) -> None:
    pl = obj.controller
    card = obj.card
    t = card.text.lower()
    x = obj.x
    handled = False

    # --- tutors / search (Entomb, Demonic/Vampiric/Mystical/Grim/Diabolic Tutor, Gamble, Reach the Horizon)
    if "search your library" in t:
        if "up to two basic land cards" in t or "up to three basic land cards" in t:
            n = 2 if "two" in t else 3
            found = game.search_library(pl, lambda c: c.is_land and "Basic" in c.supertypes, n, to_hand=False)
            for f in found:
                f.tapped = True
            game.log(f"      Land search: {len(found)} basics")
            handled = True
        else:
            handled = _generic_tutor(game, obj, t)

    # --- reanimate
    if not handled and re.search(r"return target creature card from (?:your|a) graveyard", t) and "battlefield" in t:
        _reanimate(game, pl)
        handled = True

    # --- wheels
    if not handled and "discard their hand" in t:
        _wheel(game, pl, t)
        handled = True
    if not handled and "discard your hand" in t:
        pl.hand = []
        if "draw" in t:
            game.draw(pl, 7)
        handled = True

    # --- shuffle-wheel (Molten Psyche)
    if not handled and "shuffles their hand and graveyard" in t:
        for p in game.players:
            if not p.alive:
                continue
            for c in list(p.hand):
                p.hand.remove(c)
                p.library.append(c)
            for c in list(p.graveyard):
                p.graveyard.remove(c)
                p.library.append(c)
            p.shuffle()
            game.draw(p, 7)
        m = re.search(r"deals (\d+) damage to each opponent", t)
        if m:
            for opp in game.opponents(pl):
                opp.life -= int(m.group(1))
        handled = True

    # --- mass removal / MLD
    if not handled and _mass_removal(game, pl, t, x):
        handled = True

    # --- counters
    if not handled and "counter target" in t:
        targets = [o for o in reversed(game.stack) if o.kind == "spell" and o.controller is not pl]
        if targets:
            countered = targets[0]
            game.stack.remove(countered)
            if countered.card.is_legendary and countered.card.name == countered.controller.commander.name:
                countered.controller.command_zone.append(countered.card)
            else:
                countered.controller.graveyard.append(countered.card)
            game.log(f"      {card.name} counters {countered.card.name}")
            if re.search(r": add {c}", t):
                game.add_mana(pl, "C", countered.card.mana_cost.cmc())
        handled = True

    # --- destroy / exile target
    if not handled:
        m = re.search(r"(destroy|exile) target (nonblack |nonbasic |nontoken |target )?(creature|land|artifact|enchantment|planeswalker)", t)
        if m:
            tgt = _pick_target(game, pl, m.group(3))
            if tgt:
                if m.group(1) == "destroy":
                    game.destroy(tgt, card.name)
                else:
                    _exile_perm(game, tgt)
            mg = re.search(r"you gain (\d+) life", t)
            if mg:
                pl.life += int(mg.group(1))
            handled = True

    # --- damage to any target
    if not handled:
        m = re.search(r"deals (?:x|(\d+)) damage to any target", t)
        if m:
            dmg = x if m.group(1) is None else int(m.group(1))
            opp = _lowest_opponent(game, pl)
            if opp:
                opp.life -= dmg
                game.log(f"      {card.name}: {dmg} to {opp.name}")
            handled = True
    if not handled:
        m = re.search(r"deals (\d+) damage to each opponent", t)
        if m:
            for opp in game.opponents(pl):
                opp.life -= int(m.group(1))
            handled = True
    if not handled:
        m = re.search(r"deals (\d+) damage to each untapped creature", t)
        if m:
            for p in game.players:
                for q in p.battlefield:
                    if q.is_creature() and not q.tapped:
                        q.damage += int(m.group(1))
            game.log(f"      Calamity of Cinders: {m.group(1)} to untapped creatures")
            handled = True
    if not handled:
        m = re.search(r"deals (\d+) damage to each creature", t)
        if m:
            for p in game.players:
                for q in p.battlefield:
                    if q.is_creature():
                        q.damage += int(m.group(1))
            handled = True

    # --- rituals
    if not handled and (card.is_instant or card.is_sorcery) and "add" in t:
        phrases = re.findall(r"add ([^.\n]*)", t)
        for phrase in phrases:
            if "for each card named rite of flame" in phrase:
                n = 2 + sum(1 for c in pl.graveyard if c.name == "Rite of Flame")
                game.add_mana(pl, "R", min(n, 6))
                handled = True
                continue
            res = _mana_from_phrase(phrase)
            if res is None:
                continue
            n, colors = res
            if colors == "any":
                pl.mana_pool["*"] += n
            else:
                game.add_mana(pl, colors[0], n)
            handled = True

    # --- convoke payoffs (2026 build)
    if not handled and card.name == "Harmonized Crescendo":
        goblins = sum(1 for q in pl.battlefield
                      if "Goblin" in q.card.types or "Goblin" in q.card.subtypes)
        game.draw(pl, max(1, goblins))
        game.log(f"      Harmonized Crescendo: draw {max(1, goblins)} (goblins)")
        handled = True

    # --- draw
    if not handled and "draw" in t:
        if "draw cards equal to the number of cards in their library" in t:
            opp = _lowest_opponent(game, pl)
            if opp:
                game.draw(opp, len(opp.library))
                opp.life -= (opp.life + 1) // 2
                game.log(f"      Peer into the Abyss on {opp.name}")
            handled = True
        elif "draw cards equal to your hand size" in t:
            game.draw(pl, max(1, len(pl.hand)))
            if pl.hand:
                c = pl.ai.choose_discard(game, pl)
                if c:
                    pl.hand.remove(c)
                    pl.library.append(c)
            handled = True
        else:
            m = re.search(r"draw (?:a card|(?:up to )?((?:two|three|four|five|six|seven|eight|nine|ten|\d+)) cards?)", t)
            if m:
                g1 = m.group(1)
                n = _NUM.get(g1, 1) if g1 else 1
                if g1 and g1.isdigit():
                    n = int(g1)
                game.draw(pl, n)
                if "play an additional land" in t:
                    pl.extra_land_allowance += 1
                if "discard" in t:
                    m2 = re.search(r"discard (?:a card|((?:two|three|four|five|six|seven|\d+)) cards?)", t)
                    dn = _NUM.get(m2.group(1), 1) if m2 and m2.group(1) else 1
                    if m2 and m2.group(1) and m2.group(1).isdigit():
                        dn = int(m2.group(1))
                    for _ in range(dn):
                        c = pl.ai.choose_discard(game, pl)
                        if c:
                            pl.discard_card(c)
                if "create" in t and "token" in t:
                    _token_create(game, pl, t, x)
                game.log(f"      {card.name}: draw {n}")
                handled = True
            else:
                game.log(f"      (simplified draw: {card.name})")
                handled = True

    # --- tokens
    if not handled and "create" in t and "token" in t:
        handled = _token_create(game, pl, t, x)

    # --- buff
    if not handled:
        m = re.search(r"target creature gets +(\d+)/+(\d+) until end of turn", t)
        if m:
            tgt = _strongest_creature(game, of=pl) or _strongest_creature(game)
            if tgt:
                tgt.eot_power_mod += int(m.group(1))
                tgt.eot_toughness_mod += int(m.group(2))
                game.log(f"      {card.name}: +{m.group(1)}/+{m.group(2)} to {tgt.name}")
            handled = True

    # --- life totals
    if not handled:
        m = re.search(r"each opponent loses (\d+) life", t)
        if m:
            for opp in game.opponents(pl):
                opp.life -= int(m.group(1))
            handled = True
    if not handled:
        m = re.search(r"target (?:player|opponent) loses (\d+) life", t)
        if m:
            opp = _lowest_opponent(game, pl)
            if opp:
                opp.life -= int(m.group(1))
            handled = True
    if not handled:
        m = re.search(r"you gain (\d+) life", t)
        if m:
            pl.life += int(m.group(1))
            handled = True

    # --- Show and Tell
    if not handled and "put an artifact, creature, enchantment, or land card from their hand onto the battlefield" in t:
        for p in game.players:
            if not p.alive:
                continue
            cands = [c for c in p.hand if c.is_permanent]
            if cands:
                pick = max(cands, key=lambda c: c.mana_cost.cmc())
                p.hand.remove(pick)
                p.battlefield.append(Permanent(card=pick, controller=p, owner=p))
                game.log(f"      Show and Tell: {p.name} puts {pick.name}")
        handled = True

    # --- Temporal Cleansing: tuck target nonland permanent
    if not handled and card.name == "Temporal Cleansing":
        tgt = _pick_target(game, pl, "creature")
        if tgt is None:
            tgt = _pick_target(game, pl, "artifact") or _pick_target(game, pl, "enchantment")
        if tgt is not None:
            owner = tgt.owner
            tgt.controller.battlefield.remove(tgt)
            owner.library.insert(0, tgt.card)
            game.log(f"      Temporal Cleansing: tucks {tgt.name}")
        handled = True

    # --- land destruction of one land (Stone Rain / Sinkhole)
    if not handled and re.search(r"(destroy|exile) target land", t):
        tgt = _pick_target(game, pl, "land")
        if tgt:
            game.destroy(tgt, card.name)
        handled = True

    # --- Yawgmoth's Will: cast from graveyard until end of turn
    if not handled and card.name == "Yawgmoth's Will":
        game.flags[f"{pl.name}_flashback"] = [c for c in pl.graveyard if not c.is_land]
        game.add_turn_effect("eot", lambda: game.flags.pop(f"{pl.name}_flashback", None))
        handled = True

    if not handled:
        game.log(f"      (simplified spell: {card.name})")
