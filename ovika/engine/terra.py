"""Terra, Magical Adept (WUBRG enchantress) card hooks.

Card data sources:
- Local MTGJSON AtomicCards (front faces of every deck card).
- Scryfall API for the Esper Terra back face (fetched 2026-09-05):
  Legendary Enchantment Creature - Saga Wizard, 6/6 flying.
  I/II/III - token copy of a nonlegendary enchantment you control (haste,
  sacrifice at your next end step). IV - add {W}{W}{U}{U}{B}{B}{R}{R}{G}{G},
  exile Esper Terra, return it to the battlefield front face up.

These hooks fire only for Terra-deck card names; the Ovika deck and the
three fixed opponent decks are unaffected. Documented simplifications are
logged as "(simplified ...)" in game logs.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Set, Tuple

from .game import Game, Permanent, Player, StackObject, Trigger
from .oracle import CardDef, ManaCost

FRONT_NAMES = {"Terra, Magical Adept // Esper Terra", "Terra, Magical Adept"}
BACK_NAME = "Esper Terra"

SEA_TYPES = {"Kraken", "Leviathan", "Merfolk", "Octopus", "Serpent"}

# Esper Terra back face (Scryfall 2026-09-05).
ESPER_CARD = CardDef(
    name=BACK_NAME,
    mana_cost=ManaCost(), mana_cost_str="",
    types={"Creature", "Enchantment"}, supertypes={"Legendary"},
    subtypes={"Saga", "Wizard"},
    text=("I, II, III - Create a token that's a copy of target nonlegendary "
          "enchantment you control. It gains haste. If it's a Saga, put up to "
          "three lore counters on it. Sacrifice it at the beginning of your "
          "next end step. IV - Add {W}{W}, {U}{U}, {B}{B}, {R}{R}, and {G}{G}. "
          "Exile Esper Terra, then return it to the battlefield (front face up)."),
    power="6", toughness="6", keywords={"Flying"},
    colors={"B", "G", "R", "U", "W"}, color_identity={"B", "G", "R", "U", "W"},
    is_creature=True, is_enchantment=True, is_legendary=True,
)

SAGA_CHAPTERS = {
    "Summon: Titan": 3,
    "Summon: Leviathan": 3,
    "The Apprentice's Folly": 3,
    "Binding the Old Gods": 3,
    "The Eldest Reborn": 3,
    BACK_NAME: 4,
}

TALISMANS = {
    "Talisman of Conviction": ["W", "U"],
    "Talisman of Creativity": ["U", "R"],
    "Talisman of Dominance": ["U", "B"],
    "Talisman of Indulgence": ["B", "R"],
}


def _none(game, pl, perm):
    return None


def _is_front(name: str) -> bool:
    return name in FRONT_NAMES


def commander_cast_ok(game: Game, pl: Player, cost: ManaCost) -> bool:
    """First cast is free; recasts need a follow-up Trance plan."""
    tax = max(0, cost.cmc() - 3)
    if tax <= 0:
        return True
    left = game.mana_available(pl) - cost.cmc()
    copyable = sum(1 for q in pl.battlefield
                   if q.card.is_enchantment and "Aura" not in q.card.subtypes
                   and not q.card.is_legendary and not q.token)
    return left >= 5 and copyable >= 1


def _has(game: Game, pl: Player, name: str) -> bool:
    return any(q.card.name == name for q in pl.battlefield)


def _has_any(game: Game, name: str) -> bool:
    return any(q.card.name == name for p in game.players for q in p.battlefield)


def _evening(game: Game) -> bool:
    return _has_any(game, "Enchanted Evening")


def is_enchantment(game: Game, perm: Permanent) -> bool:
    return perm.card.is_enchantment or _evening(game)


def enchant_count(game: Game, pl: Player) -> int:
    return sum(1 for q in pl.battlefield if is_enchantment(game, q))


def _mill(pl: Player, n: int) -> List[CardDef]:
    out: List[CardDef] = []
    for _ in range(n):
        if not pl.library:
            break
        c = pl.library.pop()
        pl.graveyard.append(c)
        out.append(c)
    return out


def _creature_score(c: CardDef) -> int:
    p = 0
    if c.power and c.power.lstrip("-").isdigit():
        p = int(c.power)
    return p * 100 + c.mana_cost.cmc()


def _best_creature(game: Game, pl: Optional[Player], exclude: Optional[Permanent] = None,
                   opponents_of: Optional[Player] = None) -> Optional[Permanent]:
    players = game.opponents(opponents_of) if opponents_of is not None else (
        [pl] if pl is not None else list(game.players))
    best = None
    for p in players:
        for q in p.battlefield:
            if q is exclude or not q.is_creature():
                continue
            if best is None or q.power(game) > best.power(game):
                best = q
    return best


_COPY_PRIORITY = {
    "Sanctum Weaver": 12, "Serra's Sanctum": 11, "Archon of Sun's Grace": 10,
    "Smothering Tithe": 9, "Sylvan Library": 9, "Sythis, Harvest's Hand": 8,
    "Setessan Champion": 8, "Eidolon of Blossoms": 8, "Mesa Enchantress": 7,
    "Verduran Enchantress": 7, "Enchantress's Presence": 7, "Rhystic Study": 9,
    "Mirrormade": 6, "Enchanted Evening": 6, "Opalescence": 6,
    "Starfield of Nyx": 6, "Land Tax": 5, "The Apprentice's Folly": 4,
}


def _copy_priority(q: Permanent) -> int:
    return _COPY_PRIORITY.get(q.card.name, 5)


def _copy_card(card: CardDef, game: Optional[Game] = None, src: Optional[Permanent] = None,
               as_token: bool = True, keep_legendary: bool = False) -> CardDef:
    p, t = card.power, card.toughness
    if src is not None:
        p = str(max(0, src.power(game)))
        t = str(max(0, src.toughness(game)))
    return CardDef(
        name=card.name,
        mana_cost=card.mana_cost, mana_cost_str=card.mana_cost_str,
        types=set(card.types),
        supertypes=set(card.supertypes) if keep_legendary
        else {s for s in card.supertypes if s != "Legendary"},
        subtypes=set(card.subtypes), text=card.text,
        power=p, toughness=t, keywords=set(card.keywords),
        colors=set(card.colors), color_identity=set(card.color_identity),
        is_land=card.is_land, is_creature=card.is_creature,
        is_artifact=card.is_artifact, is_enchantment=card.is_enchantment,
        is_instant=card.is_instant, is_sorcery=card.is_sorcery,
        is_planeswalker=card.is_planeswalker,
        is_legendary=(card.is_legendary and keep_legendary),
        is_token=as_token,
    )


def _clone_token(game: Game, pl: Player, src: Permanent, haste: bool = False) -> Permanent:
    cd = _copy_card(src.card, game, src, as_token=True)
    tok = Permanent(card=cd, controller=pl, owner=pl, token=True,
                    token_power=int(cd.power or 0), token_toughness=int(cd.toughness or 0),
                    controlled_since_turn=game.turn_no, summon_sick=not haste)
    tok.token_creature = cd.is_creature
    if haste:
        tok.eot_haste = True
    pl.battlefield.append(tok)
    pl.tokens_created_turn = True
    return tok


# ---------------------------------------------------------------------------
# Esper Terra combo loop (bounded perf-guard model of the infinite line)
# ---------------------------------------------------------------------------

COMBO_TOKENS = 24          # hasty 6/6 flying Reflections produced per loop burst
MAX_COMBO_LOOPS = 3        # loops allowed per game (perf guard)


def _combo_enabler(game: Game, pl: Player) -> Optional[Permanent]:
    """A nonlegendary saga/enchantment that continues the Esper Terra loop."""
    for q in pl.battlefield:
        if q.card.name in ("The Apprentice's Folly", "Mirrormade"):
            return q
    return None


def _combo_loop(game: Game, pl: Player, esper: Permanent) -> int:
    """Bounded model of the Esper Terra + Folly/Mirrormade copy loop.

    Real line (edh-combos.com/combo/6575-6617): Esper Terra chapter I copies
    Folly (or Mirrormade entering as an Esper Terra copy) with lore counters;
    each Saga token's chapters recurse -> unbounded hasty nonlegendary 6/6
    flying Esper Terra copies, 10 colored mana per resolved chapter IV, and
    unbounded ETB/LTB/death triggers. The engine resolves one burst of
    COMBO_TOKENS Reflections and folds the intermediate Folly tokens, the
    repeated chapter-IV mana and the enchantress ETB triggers into this burst
    (disclosed perf guard).
    """
    made = 0
    for _ in range(COMBO_TOKENS):
        tok = _clone_token(game, pl, esper, haste=True)
        tok.counters["lore"] = 1
        tok.card.subtypes.add("Reflection")
        made += 1
    game.flags["_terra_loops"] = game.flags.get("_terra_loops", 0) + 1
    game.log(f"      (simplified: bounded Esper Terra copy loop -> {made} hasty "
             f"6/6 flying Reflections; infinite mana + ETB/death triggers folded)")
    return made


# ---------------------------------------------------------------------------
# Mana abilities (605.1a)
# ---------------------------------------------------------------------------

def mana_abilities(game: Game, perm: Permanent) -> List[Tuple[int, object, Callable]]:
    """Replacement list for Terra-specific mana permanents (empty = keep generic)."""
    n = perm.card.name
    pl = perm.controller
    if n == "Sanctum Weaver":
        return [(enchant_count(game, pl), "any", _none)]
    if n == "Serra's Sanctum":
        return [(enchant_count(game, pl), ["W"], _none)]
    if n in TALISMANS:
        def _pain(g, p, q):
            p.life -= 1
        return [(1, ["C"], _none), (1, list(TALISMANS[n]), _pain)]
    if n == "Tainted Wood":
        if any(q.card.is_land and "Swamp" in q.card.subtypes for q in pl.battlefield):
            return [(1, ["B", "G"], _none)]
        return [(1, ["C"], _none)]
    return []


# ---------------------------------------------------------------------------
# On-cast triggers (603.2)
# ---------------------------------------------------------------------------

def on_cast(game: Game, pl: Player, obj: StackObject) -> None:
    card = obj.card
    if card.name == "The Master of Keys":
        game.flags[f"{pl.name}_mok_x"] = obj.x if card.mana_cost.x else 0
    if not card.is_enchantment:
        return
    for q in list(pl.battlefield):
        qn = q.card.name
        if qn == "Sythis, Harvest's Hand":
            def _sy(g: Game, t: Trigger):
                g.draw(pl, 1)
                pl.life += 1
            game.queue_trigger(q, pl, f"Sythis: draw + gain 1 ({card.name})", _sy)
        elif qn in ("Mesa Enchantress", "Verduran Enchantress", "Enchantress's Presence"):
            def _dr(g: Game, t: Trigger, src=qn):
                g.draw(pl, 1)
            game.queue_trigger(q, pl, f"{qn}: draw ({card.name})", _dr)


# ---------------------------------------------------------------------------
# Enter-the-battlefield effects
# ---------------------------------------------------------------------------

def _terra_etb(game: Game, pl: Player) -> None:
    milled = _mill(pl, 5)
    encs = [c for c in milled if c.is_enchantment]
    if encs:
        pick = max(encs, key=lambda c: c.mana_cost.cmc())
        pl.graveyard.remove(pick)
        pl.hand.append(pick)
        game.log(f"      Terra ETB: mill 5, return {pick.name}")
    else:
        game.log("      Terra ETB: mill 5, no enchantment")


def _pegasus(game: Game, pl: Player, src: Permanent) -> None:
    game.create_token(pl, "Pegasus", 2, 2, types={"Creature", "Pegasus"},
                      abilities={"flying"}, colors={"W"})
    game.log(f"      Archon of Sun's Grace: 2/2 Pegasus ({src.card.name})")


def _victor(game: Game, pl: Player, q: Permanent) -> None:
    key = f"{pl.name}_eerie_t{game.turn_no}"
    c = game.flags.get(key, 0) + 1
    game.flags[key] = c
    if c == 1:
        _mill(pl, 1)
        game.log("      Victor eerie 1: surveil 2 (simplified: mill 1)")
    elif c == 2:
        for opp in game.opponents(pl):
            cc = opp.ai.choose_discard(game, opp)
            if cc:
                opp.discard_card(cc)
        game.log("      Victor eerie 2: each opponent discards")
    else:
        cands = [c2 for p in game.players for c2 in p.graveyard if c2.is_creature]
        if cands:
            pick = max(cands, key=_creature_score)
            owner = next(p for p in game.players if pick in p.graveyard)
            owner.graveyard.remove(pick)
            q2 = Permanent(card=pick, controller=pl, owner=owner,
                           controlled_since_turn=game.turn_no)
            pl.battlefield.append(q2)
            game.log(f"      Victor eerie 3: reanimate {pick.name}")


def _frog(game: Game, pl: Player) -> None:
    tgt = _best_creature(game, None, opponents_of=pl)
    if tgt is not None:
        game.destroy(tgt, f"Amphibian Downpour (simplified: {tgt.name} becomes a 1/1 Frog)")


def _refresh_animation(game: Game) -> None:
    opal = _has_any(game, "Opalescence")
    desired: Dict[int, Permanent] = {}
    for p in game.players:
        if not p.alive:
            continue
        star = _has(game, p, "Starfield of Nyx")
        for q in list(p.battlefield):
            if not q.card.is_enchantment or "Aura" in q.card.subtypes or q.card.is_creature:
                continue
            if opal and q.card.name != "Opalescence":
                desired[id(q)] = q
            elif star and q.card.name != "Starfield of Nyx" and enchant_count(game, p) >= 5:
                desired[id(q)] = q
    anim: Dict[int, Permanent] = game.flags.get("_terra_animated")
    if anim is None:
        anim = {}
        game.flags["_terra_animated"] = anim
    for qid in [k for k in anim if k not in desired]:
        q = anim.pop(qid)
        q.token = False
        q.token_creature = False
        q.counters["+1/+1"] = max(0, q.counters.get("+1/+1", 0) - q.card.mana_cost.cmc())
    for qid, q in desired.items():
        if qid not in anim:
            q.token = True
            q.token_creature = True
            q.counters["+1/+1"] = q.counters.get("+1/+1", 0) + q.card.mana_cost.cmc()
            anim[qid] = q
            game.log(f"      (Opalescence/Starfield: {q.name} becomes a "
                     f"{q.card.mana_cost.cmc()}/{q.card.mana_cost.cmc()} creature)")


def _prefer_combo_copy(game: Game, pl: Player, targets: List[Permanent]) -> Optional[Permanent]:
    """Combo-first copy target: Folly when an Esper Terra is transformed."""
    if not targets:
        return None
    esper = any(q.card.name == BACK_NAME and not q.token for q in pl.battlefield)
    if esper:
        folly = [q for q in targets if q.card.name == "The Apprentice's Folly"]
        if folly:
            return folly[0]
    return max(targets, key=_copy_priority)


def _enter_saga_copy(game: Game, pl: Player, perm: Permanent) -> None:
    """A copy entering as a Saga gets a lore counter and fires chapter I (714.3b)."""
    if perm.card.name in SAGA_CHAPTERS:
        perm.counters["lore"] = 1
        _chapter(game, pl, perm, 1)


def on_enter(game: Game, perm: Permanent) -> None:
    pl = perm.controller
    n = perm.card.name
    if _is_front(n):
        _terra_etb(game, pl)
    if n == "Spark Double":
        src = _best_creature(game, pl, exclude=perm)
        if src is not None and _is_front(src.card.name):
            src = None
        if src is not None:
            perm.card = _copy_card(src.card, game, src, as_token=False)
            perm.token = False
            perm.counters["+1/+1"] = perm.counters.get("+1/+1", 0) + 1
            game.log(f"      Spark Double: enters as {src.name} +1/+1")
            _enter_saga_copy(game, pl, perm)
    if n == "Mirrormade":
        targets = [q for q in pl.battlefield
                   if q is not perm and (q.card.is_artifact or q.card.is_enchantment)
                   and not q.card.is_legendary]
        if targets:
            src = _prefer_combo_copy(game, pl, targets)
            perm.card = _copy_card(src.card, game, src, as_token=False)
            perm.token = False
            game.log(f"      Mirrormade: enters as {src.name}")
            _enter_saga_copy(game, pl, perm)
    if n in ("Copy Enchantment", "Estrid's Invocation"):
        targets = [q for q in pl.battlefield
                   if q is not perm and q.card.is_enchantment and not q.card.is_legendary]
        if targets:
            src = _prefer_combo_copy(game, pl, targets)
            perm.card = _copy_card(src.card, game, src, as_token=False)
            perm.token = False
            game.log(f"      {n}: enters as {src.name}")
            if n == "Estrid's Invocation":
                game.flags.setdefault(f"{pl.name}_estrid", set()).add(id(perm))
            _enter_saga_copy(game, pl, perm)
    if n == "The Master of Keys":
        x = int(game.flags.pop(f"{pl.name}_mok_x", 0) or 0)
        if x > 0:
            perm.counters["+1/+1"] = perm.counters.get("+1/+1", 0) + x
            _mill(pl, 2 * x)
            game.log(f"      Master of Keys: {x} counters, mill {2 * x}")
    if n == "Amphibian Downpour":
        _frog(game, pl)
    # enchantment ETB triggers (Eidolon / Setessan / Archon / Victor)
    if is_enchantment(game, perm):
        for q in list(pl.battlefield):
            qn = q.card.name
            if q is perm:
                if qn == "Archon of Sun's Grace":
                    _pegasus(game, pl, q)
                continue
            if qn == "Eidolon of Blossoms":
                def _eid(g: Game, t: Trigger, src_name=n):
                    g.draw(pl, 1)
                game.queue_trigger(q, pl, f"Eidolon: draw ({n})", _eid)
            elif qn == "Setessan Champion":
                def _set(g: Game, t: Trigger):
                    q.counters["+1/+1"] = q.counters.get("+1/+1", 0) + 1
                    g.draw(pl, 1)
                game.queue_trigger(q, pl, f"Setessan Champion: +1/+1, draw ({n})", _set)
            elif qn == "Archon of Sun's Grace":
                def _peg(g: Game, t: Trigger):
                    _pegasus(g, pl, q)
                game.queue_trigger(q, pl, f"Archon: Pegasus ({n})", _peg)
            elif qn == "Victor, Valgavoth's Seneschal":
                _victor(game, pl, q)
        _refresh_animation(game)
    if n in SAGA_CHAPTERS:
        perm.counters["lore"] = 1
        _chapter(game, pl, perm, 1)


# ---------------------------------------------------------------------------
# Saga chapters (simplified: applied directly, not via stack triggers)
# ---------------------------------------------------------------------------

def _chapter(game: Game, pl: Player, perm: Permanent, n: int) -> None:
    name = perm.card.name
    if name == "Summon: Titan":
        if n == 1:
            _mill(pl, 5)
            game.log("      Summon: Titan I: mill 5")
        elif n == 2:
            lands = [c for c in list(pl.graveyard) if c.is_land]
            for c in lands:
                pl.graveyard.remove(c)
                q = Permanent(card=c, controller=pl, owner=pl,
                              controlled_since_turn=game.turn_no)
                q.tapped = True
                pl.battlefield.append(q)
            game.log(f"      Summon: Titan II: {len(lands)} lands back tapped")
        elif n == 3:
            others = [q for q in pl.battlefield if q.is_creature() and q is not perm]
            if others:
                tgt = max(others, key=lambda q: q.power(game))
                x = sum(1 for q in pl.battlefield if q.card.is_land)
                tgt.eot_power_mod += x
                tgt.eot_toughness_mod += x
                game.log(f"      Summon: Titan III: {tgt.name} +{x}/+{x} (trample simplified)")
    elif name == "Summon: Leviathan":
        if n == 1:
            for p in list(game.players):
                for q in list(p.battlefield):
                    if q.is_creature() and not (SEA_TYPES & set(q.card.subtypes)):
                        p.battlefield.remove(q)
                        q.owner.hand.append(q.card)
                        game.log(f"      Leviathan I: bounce {q.card.name}")
        elif n in (2, 3):
            game.draw(pl, 1)
            game.log("      Leviathan II/III (simplified): draw 1")
    elif name == "The Apprentice's Folly":
        if n in (1, 2):
            esper = next((q for q in pl.battlefield
                          if q.card.name == BACK_NAME and not q.token), None)
            if (esper is not None
                    and game.flags.get("_terra_loops", 0) < MAX_COMBO_LOOPS):
                _combo_loop(game, pl, esper)
                return
            src = _best_creature(game, pl, exclude=perm)
            if src is not None and _is_front(src.card.name):
                src = None
            if src is not None:
                tok = _clone_token(game, pl, src, haste=True)
                refl = game.flags.setdefault(f"{pl.name}_reflections", set())
                refl.add(id(tok))
                game.log(f"      Folly I/II: Reflection copy of {src.card.name} (haste)")
        elif n == 3:
            refl = game.flags.get(f"{pl.name}_reflections", set())
            for pid in list(refl):
                tok = next((q for q in pl.battlefield if id(q) == pid), None)
                if tok is not None:
                    game.sacrifice(pl, tok)
            refl.clear()
            game.log("      Folly III: sacrifice Reflections")
    elif name == "Binding the Old Gods":
        if n == 1:
            targets = [q for opp in game.opponents(pl) for q in opp.battlefield
                       if not q.card.is_land]
            if targets:
                tgt = max(targets, key=lambda q: q.card.mana_cost.cmc())
                game.destroy(tgt, "Binding the Old Gods I")
        elif n == 2:
            found = game.search_library(pl, lambda c: c.is_land and "Forest" in c.subtypes,
                                        1, to_hand=False)
            for f in found:
                q = next((qq for qq in pl.battlefield if qq.card is f), None)
                if q is not None:
                    q.tapped = True
            game.log("      Binding II: Forest to battlefield tapped")
        elif n == 3:
            game.log("      Binding III (simplified): deathtouch until end of turn")
    elif name == "The Eldest Reborn":
        if n == 1:
            for opp in game.opponents(pl):
                cre = [q for q in opp.battlefield if q.is_creature()]
                if cre:
                    game.sacrifice(opp, min(cre, key=lambda q: q.power(game)))
            game.log("      Eldest Reborn I: each opponent sacrifices a creature")
        elif n == 2:
            for opp in game.opponents(pl):
                c = opp.ai.choose_discard(game, opp)
                if c:
                    opp.discard_card(c)
            game.log("      Eldest Reborn II: each opponent discards")
        elif n == 3:
            cands = [c for p in game.players for c in p.graveyard if c.is_creature]
            if cands:
                pick = max(cands, key=_creature_score)
                owner = next(p for p in game.players if pick in p.graveyard)
                owner.graveyard.remove(pick)
                q = Permanent(card=pick, controller=pl, owner=owner,
                              controlled_since_turn=game.turn_no)
                pl.battlefield.append(q)
                game.log(f"      Eldest Reborn III: reanimate {pick.name}")
                from .cards import on_enter as _cards_on_enter
                _cards_on_enter(game, q)
    elif name == BACK_NAME:
        if n in (1, 2, 3):
            if perm.token:
                # Reflection tokens: their chapters are folded into the bounded
                # loop burst (their copies would only extend the same loop).
                return
            if (game.flags.get("_terra_loops", 0) < MAX_COMBO_LOOPS
                    and _combo_enabler(game, pl) is not None):
                _combo_loop(game, pl, perm)
                return
            targets = [q for q in pl.battlefield
                       if q.card.is_enchantment and not q.card.is_legendary
                       and q.card.name != BACK_NAME]
            if targets:
                src = max(targets, key=_copy_priority)
                tok = _clone_token(game, pl, src, haste=True)
                def _sac_next(g=game, tok=tok, pl=pl):
                    if tok in pl.battlefield:
                        g.sacrifice(pl, tok)
                game.end_of_turn_delayed.append(_sac_next)
                game.log(f"      Esper Terra chapter {n}: copy {src.card.name} (haste, sac next EOT)")
        elif n == 4:
            for col in ("W", "U", "B", "R", "G"):
                game.add_mana(pl, col, 2)
            if perm.token:
                if perm in pl.battlefield:
                    pl.battlefield.remove(perm)
                game.log("      Esper Terra token IV: +2 WUBRG, token exiled "
                         "(simplified: cannot return from exile)")
                return
            perm.card = pl.commander
            perm.counters["lore"] = 0
            perm.tapped = False
            perm.summon_sick = True
            game.log("      Esper Terra IV: +2 WUBRG, reverts to Terra")
            _terra_etb(game, pl)


# ---------------------------------------------------------------------------
# Draw-step triggers
# ---------------------------------------------------------------------------

def on_draw_step(game: Game, pl: Player) -> int:
    for q in list(pl.battlefield):
        if q.card.name == "Sylvan Library":
            if pl.life >= 20:
                game.draw(pl, 2)
                pl.life -= 8
                game.log("      Sylvan Library: draw 2, pay 8 life")
            elif pl.life >= 10:
                game.draw(pl, 2)
                if pl.hand:
                    worst = min(pl.hand, key=lambda c: c.mana_cost.cmc())
                    pl.hand.remove(worst)
                    pl.library.append(worst)
                pl.life -= 4
                game.log("      Sylvan Library: draw 2, keep 1, pay 4 life")
            else:
                game.draw(pl, 2)
                for _ in range(2):
                    if pl.hand:
                        worst = min(pl.hand, key=lambda c: c.mana_cost.cmc())
                        pl.hand.remove(worst)
                        pl.library.append(worst)
                game.log("      Sylvan Library: draw 2, keep 0")
    moon = game.flags.pop(f"{pl.name}_moonmist", None)
    for q in list(pl.battlefield):
        n = q.card.name
        if n not in SAGA_CHAPTERS:
            continue
        if q is moon:
            q.counters["lore"] = 1
            _chapter(game, pl, q, 1)
            continue
        if q.counters.get("lore", 0) <= 0:
            continue
        q.counters["lore"] = q.counters.get("lore", 0) + 1
        lore = q.counters["lore"]
        if n == BACK_NAME:
            if lore == 4:
                _chapter(game, pl, q, 4)
                continue
            if lore > 4:
                game.sacrifice(pl, q)
                game.log("      Esper Terra saga over -> sacrifice")
                continue
        else:
            if lore > SAGA_CHAPTERS[n]:
                game.sacrifice(pl, q)
                game.log(f"      Saga {n} completed -> sacrifice")
                continue
        _chapter(game, pl, q, lore)
    return 0


# ---------------------------------------------------------------------------
# Upkeep triggers
# ---------------------------------------------------------------------------

def upkeep(game: Game, pl: Player) -> None:
    for q in list(pl.battlefield):
        if q.card.name == "Land Tax":
            opp_lands = max((sum(1 for r in opp.battlefield if r.card.is_land)
                             for opp in game.opponents(pl)), default=0)
            mine = sum(1 for r in pl.battlefield if r.card.is_land)
            if opp_lands > mine:
                found = game.search_library(pl, lambda c: c.is_land and "Basic" in c.supertypes,
                                            3, to_hand=True)
                game.log(f"      Land Tax: {len(found)} basics to hand")
        elif q.card.name == "Starfield of Nyx":
            encs = [c for c in list(pl.graveyard) if c.is_enchantment]
            if encs:
                pick = max(encs, key=lambda c: c.mana_cost.cmc())
                pl.graveyard.remove(pick)
                qq = Permanent(card=pick, controller=pl, owner=pl,
                               controlled_since_turn=game.turn_no)
                pl.battlefield.append(qq)
                game.log(f"      Starfield upkeep: return {pick.name}")
                from .cards import on_enter as _cards_on_enter
                _cards_on_enter(game, qq)
    if _has(game, pl, "Demon of Fate's Design"):
        game.flags[f"{pl.name}_demon_lifecast"] = True
    estrid_ids = set(game.flags.get(f"{pl.name}_estrid", set()))
    for pid in list(estrid_ids):
        perm = next((q for q in pl.battlefield if id(q) == pid), None)
        if perm is None:
            estrid_ids.discard(pid)
            continue
        targets = [q for q in pl.battlefield
                   if q is not perm and q.card.is_enchantment and not q.card.is_legendary]
        src = _prefer_combo_copy(game, pl, targets)
        if src is not None:
            perm.card = _copy_card(src.card, game, src, as_token=False)
            perm.token = False
            perm.counters.clear()
            game.log(f"      Estrid's Invocation upkeep: becomes {src.name} "
                     f"(simplified: flicker without leaving battlefield)")
            _enter_saga_copy(game, pl, perm)
    if estrid_ids:
        game.flags[f"{pl.name}_estrid"] = estrid_ids


# ---------------------------------------------------------------------------
# Activated abilities (602)
# ---------------------------------------------------------------------------

def _transform(game: Game, pl: Player, perm: Permanent) -> None:
    # CR 701.28: transforming keeps the same object; the front face had to be
    # untapped to activate Trance, so it was not summoning sick.
    perm.card = _copy_card(ESPER_CARD, as_token=False, keep_legendary=True)
    perm.counters["lore"] = 1
    game.log("      Terra Trance: transforms into Esper Terra")
    _chapter(game, pl, perm, 1)


def activatable(game: Game, pl: Player) -> List[Tuple[str, Callable]]:
    acts: List[Tuple[str, Callable]] = []
    for perm in list(pl.battlefield):
        n = perm.card.name
        if perm.tapped or perm.summon_sick:
            continue
        if _is_front(n):
            combo_ready = _combo_enabler(game, pl) is not None
            combo_in_hand = any(c.name in ("The Apprentice's Folly", "Mirrormade")
                                for c in pl.hand)
            copyable = any(q.card.is_enchantment and not q.card.is_legendary
                           and q.card.name != BACK_NAME for q in pl.battlefield)
            if (combo_ready or combo_in_hand or copyable) and \
                    game.mana_available(pl) >= 7 and pl.ai.can_pay_color(
                        game, pl, ManaCost(generic=4, colored={"R": 1, "G": 1})):
                def _trance(perm=perm):
                    game.pay_mana(pl, 4, {"R": 1, "G": 1})
                    perm.tapped = True
                    _transform(game, pl, perm)
                acts.append(("Terra Trance -> Esper Terra", _trance))
        elif n == "Yenna, Redtooth Regent":
            if game.mana_available(pl) >= 2:
                targets = [q for q in pl.battlefield
                           if q.card.is_enchantment and not q.card.is_legendary and not q.token
                           and "Aura" not in q.card.subtypes
                           and sum(1 for r in pl.battlefield if r.card.name == q.card.name) == 1]
                if targets:
                    src = max(targets, key=_copy_priority)
                    def _yenna(perm=perm, src=src):
                        game.pay_mana(pl, 2, {})
                        perm.tapped = True
                        _clone_token(game, pl, src)
                        game.log(f"      Yenna: token copy of {src.card.name}")
                    acts.append((f"Yenna: copy {src.card.name}", _yenna))
    return acts


# ---------------------------------------------------------------------------
# On-death effects
# ---------------------------------------------------------------------------

def on_death(game: Game, perm: Permanent) -> None:
    pl = perm.controller if perm.controller is not None else perm.owner
    n = perm.card.name
    if n == "Enduring Vitality":
        cd = _copy_card(perm.card, as_token=True)
        cd.types = {"Enchantment"}
        cd.is_creature = False
        cd.is_enchantment = True
        cd.power = None
        cd.toughness = None
        tok = Permanent(card=cd, controller=pl, owner=perm.owner, token=True,
                        controlled_since_turn=game.turn_no)
        tok.token_creature = False
        pl.battlefield.append(tok)
        game.log("      Enduring Vitality: returns as a noncreature enchantment (simplified)")
    if perm.card.is_enchantment:
        _refresh_animation(game)


# ---------------------------------------------------------------------------
# Attack triggers
# ---------------------------------------------------------------------------

def on_attackers(game: Game, pl: Player, attackers: List[Permanent]) -> None:
    for a in attackers:
        if a.card.name == "Six":
            milled = _mill(pl, 3)
            lands = [c for c in milled if c.is_land]
            if lands:
                pick = max(lands, key=lambda c: c.mana_cost.cmc())
                pl.graveyard.remove(pick)
                pl.hand.append(pick)
                game.log("      Six: mill 3, land to hand")


# ---------------------------------------------------------------------------
# Spell resolution (608)
# ---------------------------------------------------------------------------

def _delirium(pl: Player) -> bool:
    types = set()
    for c in pl.graveyard:
        if c.is_land:
            types.add("land")
        if c.is_creature:
            types.add("creature")
        if c.is_instant:
            types.add("instant")
        if c.is_sorcery:
            types.add("sorcery")
        if c.is_enchantment:
            types.add("enchantment")
        if c.is_artifact:
            types.add("artifact")
        if c.is_planeswalker:
            types.add("planeswalker")
    return len(types) >= 4


def _put_battlefield(game: Game, pl: Player, pick: CardDef, owner: Optional[Player] = None,
                     counters: int = 0) -> None:
    q = Permanent(card=pick, controller=pl, owner=owner or pl,
                  controlled_since_turn=game.turn_no)
    if counters:
        q.counters["+1/+1"] = counters
    pl.battlefield.append(q)
    game.log(f"      -> {pick.name} to battlefield")
    from .cards import on_enter as _cards_on_enter
    _cards_on_enter(game, q)


def _sevinnes_once(game: Game, pl: Player) -> None:
    cands = [c for c in list(pl.graveyard) if not c.is_land and c.mana_cost.cmc() <= 3]
    if not cands:
        return
    pick = max(cands, key=lambda c: c.mana_cost.cmc())
    pl.graveyard.remove(pick)
    _put_battlefield(game, pl, pick)


def resolve_effect(game: Game, obj: StackObject) -> bool:
    """Handles Terra-deck instants/sorceries. Returns True when handled."""
    pl = obj.controller
    n = obj.card.name
    if n == "Idyllic Tutor":
        found = game.search_library(pl, lambda c: c.name == "The Apprentice's Folly",
                                    1, to_hand=True)
        if not found:
            found = game.search_library(pl, lambda c: c.name == "Mirrormade",
                                        1, to_hand=True)
        if not found:
            found = game.search_library(pl, lambda c: c.is_enchantment, 1, to_hand=True)
        game.log(f"      Idyllic Tutor: {'found ' + found[0].name if found else 'no target'}")
        return True
    if n == "Enlightened Tutor":
        found = game.search_library(pl, lambda c: c.name == "The Apprentice's Folly",
                                    1, to_hand=True)
        if not found:
            found = game.search_library(pl, lambda c: c.name == "Mirrormade",
                                        1, to_hand=True)
        if not found:
            found = game.search_library(pl, lambda c: c.is_artifact or c.is_enchantment,
                                        1, to_hand=True)
        game.log(f"      Enlightened Tutor: {'found ' + found[0].name if found else 'no target'}")
        return True
    if n == "Demonic Counsel":
        if _delirium(pl):
            found = game.search_library(pl, lambda c: c.name == "The Apprentice's Folly",
                                        1, to_hand=True)
            if not found:
                found = game.search_library(pl, lambda c: c.name == "Mirrormade",
                                            1, to_hand=True)
            if not found:
                found = game.search_library(pl, lambda c: True, 1, to_hand=True)
            game.log("      Demonic Counsel (delirium): combo piece or any card to hand")
        else:
            found = game.search_library(pl, lambda c: "Demon" in c.subtypes, 1, to_hand=True)
            game.log(f"      Demonic Counsel: {'found ' + found[0].name if found else 'no Demon'}")
        return True
    if n == "Moonmist":
        perm = next((q for q in pl.battlefield if _is_front(q.card.name)), None)
        if perm is not None:
            perm.card = _copy_card(ESPER_CARD, as_token=False, keep_legendary=True)
            perm.counters["lore"] = 0
            game.flags[f"{pl.name}_moonmist"] = perm
            game.log("      Moonmist: Terra transforms (simplified: lore counter "
                     "at next precombat main applied at next draw step)")
        else:
            game.log("      Moonmist: no Terra on board")
        game.flags["_moonmist_combat"] = game.turn_no
        return True
    if n == "Farseek":
        found = game.search_library(pl, lambda c: c.is_land and (
            "Plains" in c.subtypes or "Island" in c.subtypes or
            "Swamp" in c.subtypes or "Mountain" in c.subtypes), 1, to_hand=False)
        for f in found:
            q = next((qq for qq in pl.battlefield if qq.card is f), None)
            if q is not None:
                q.tapped = True
        game.log(f"      Farseek: {'found ' + found[0].name if found else 'no target'}")
        return True
    if n in ("Nature's Lore", "Three Visits"):
        found = game.search_library(pl, lambda c: c.is_land and "Forest" in c.subtypes, 1,
                                    to_hand=False)
        game.log(f"      {n}: {'found ' + found[0].name if found else 'no target'}")
        return True
    if n == "Neoform":
        cre = [q for q in pl.battlefield if q.is_creature()
               and q.card.name not in FRONT_NAMES and q.card.name != BACK_NAME]
        if not cre:
            game.log("      Neoform: no creature to sacrifice")
            return True
        sac = min(cre, key=lambda q: (q.power(game), q.card.mana_cost.cmc()))
        mv = sac.card.mana_cost.cmc()
        game.sacrifice(pl, sac)
        cands = [c for c in pl.library if c.is_creature and c.mana_cost.cmc() == mv + 1]
        if not cands:
            pl.shuffle()
            game.log("      Neoform: no valid creature in library")
            return True
        pick = max(cands, key=_creature_score)
        pl.library.remove(pick)
        pl.shuffle()
        _put_battlefield(game, pl, pick, counters=1)
        game.log(f"      Neoform: {sac.card.name} -> {pick.name} (+1/+1)")
        return True
    if n == "Eldritch Evolution":
        cre = [q for q in pl.battlefield if q.is_creature()
               and q.card.name not in FRONT_NAMES and q.card.name != BACK_NAME]
        if not cre:
            game.log("      Eldritch Evolution: no creature to sacrifice")
            return True
        sac = min(cre, key=lambda q: (q.power(game), q.card.mana_cost.cmc()))
        mv = sac.card.mana_cost.cmc()
        game.sacrifice(pl, sac)
        cands = [c for c in pl.library if c.is_creature and c.mana_cost.cmc() <= mv + 2]
        if not cands:
            pl.shuffle()
            game.log("      Eldritch Evolution: no valid creature in library")
            return True
        pick = max(cands, key=_creature_score)
        pl.library.remove(pick)
        pl.shuffle()
        _put_battlefield(game, pl, pick)
        game.log(f"      Eldritch Evolution: {sac.card.name} -> {pick.name}")
        return True
    if n == "Culling Ritual":
        destroyed = 0
        for p in list(game.players):
            for q in list(p.battlefield):
                if not q.card.is_land and q.card.mana_cost.cmc() <= 2:
                    game.destroy(q, "Culling Ritual")
                    destroyed += 1
        game.add_mana(pl, "G", destroyed)
        game.log(f"      Culling Ritual: destroyed {destroyed}, add {destroyed} G")
        return True
    if n == "Sevinne's Reclamation":
        _sevinnes_once(game, pl)
        if obj.flashback:
            _sevinnes_once(game, pl)
        else:
            fb = game.flags.setdefault(f"{pl.name}_flashback", [])
            if obj.card not in fb:
                fb.append(obj.card)
        return True
    if n == "Reanimate":
        cands = [c for p in game.players for c in p.graveyard if c.is_creature]
        if cands:
            pick = max(cands, key=_creature_score)
            owner = next(p for p in game.players if pick in p.graveyard)
            owner.graveyard.remove(pick)
            lose = min(pl.life - 1, pick.mana_cost.cmc())
            if lose > 0:
                pl.life -= lose
            _put_battlefield(game, pl, pick, owner=owner)
            game.log(f"      Reanimate: {pick.name}, lose {lose} life")
        else:
            game.log("      Reanimate: no creature in any graveyard")
        return True
    if n == "Assassin's Trophy":
        targets = [q for opp in game.opponents(pl) for q in opp.battlefield
                   if not q.card.is_land]
        if targets:
            tgt = max(targets, key=lambda q: q.card.mana_cost.cmc())
            game.destroy(tgt, "Assassin's Trophy")
            game.log("      Assassin's Trophy (simplified: no basic-land search)")
        return True
    if n == "Archdruid's Charm":
        targets = [q for opp in game.opponents(pl) for q in opp.battlefield
                   if q.card.is_artifact or q.card.is_enchantment]
        if targets:
            tgt = max(targets, key=lambda q: q.card.mana_cost.cmc())
            game.destroy(tgt, "Archdruid's Charm")
        else:
            found = game.search_library(pl, lambda c: c.is_creature or c.is_land, 1,
                                        to_hand=False)
            for f in found:
                f.tapped = f.card.is_land
            game.log("      Archdruid's Charm: tutor creature/land to battlefield")
        return True
    if n == "Heroic Intervention":
        ids = {id(q) for q in pl.battlefield}
        game.flags[f"{pl.name}_indestructible"] = ids
        def _clear():
            if game.flags.get(f"{pl.name}_indestructible") == ids:
                game.flags.pop(f"{pl.name}_indestructible", None)
        game.add_turn_effect("eot", _clear)
        game.log("      Heroic Intervention: permanents indestructible until EOT")
        return True
    return False


# ---------------------------------------------------------------------------
# Static: Anger grants haste while in the graveyard with a Mountain
# ---------------------------------------------------------------------------

def anger_haste(game: Game, pl: Player) -> bool:
    if not any(c.name == "Anger" for c in pl.graveyard):
        return False
    return any(q.card.is_land and "Mountain" in q.card.subtypes for q in pl.battlefield)


# ---------------------------------------------------------------------------
# Grave casting helpers (escape / retrace) for the AI
# ---------------------------------------------------------------------------

def grave_castable(game: Game, pl: Player) -> List[Tuple[CardDef, str]]:
    out: List[Tuple[CardDef, str]] = []
    pool = game.mana_available(pl)
    has_mok = _has(game, pl, "The Master of Keys")
    has_six = _has(game, pl, "Six")
    if has_mok:
        for c in list(pl.graveyard):
            if c.is_enchantment and not getattr(c, "is_token", False):
                cost = game.cost_of(pl, c, from_zone="grave")
                if cost.cmc() <= pool and pl.ai.can_pay_color(game, pl, cost):
                    out.append((c, "escape"))
    if has_six and game.active is pl and any(c.is_land for c in pl.hand):
        for c in list(pl.graveyard):
            if c.is_permanent and not c.is_land and not getattr(c, "is_token", False):
                cost = game.cost_of(pl, c, from_zone="grave")
                if cost.cmc() <= pool and pl.ai.can_pay_color(game, pl, cost):
                    out.append((c, "retrace"))
    return out
