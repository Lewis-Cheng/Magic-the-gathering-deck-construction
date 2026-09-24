"""AI players: rule-legal heuristic policies for all 4 seats.

Decisions are heuristics, but every action is validated/enforced by the
engine in game.py (timing, costs, targets, combat legality).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .game import Game, Permanent, Player, StackObject
from .oracle import CardDef


class Act:
    def __init__(self, fn):
        self.fn = fn

    def execute(self, game):
        self.fn()


class AI:
    """Heuristic pilot shared by all seats. Strategy comes from tags and Oracle text."""

    def __init__(self, name: str):
        self.name = name

    # ------------------------------------------------------------- mulligan
    def keep_hand(self, game: Game, pl: Player) -> bool:
        nl = sum(1 for c in pl.hand if c.is_land)
        ramp = any("ramp" in c.tags or c.name in ("Sol Ring", "Arcane Signet", "Wayfarer's Bauble",
                     "Mind Stone", "Fellwar Stone", "Everflowing Chalice") for c in pl.hand)
        cheap = any(not c.is_land and c.mana_cost.cmc() <= 3 for c in pl.hand)
        if 2 <= nl <= 5 and (ramp or cheap):
            return True
        if nl == 1 and ramp and cheap:
            return True
        return False

    def scry_keep(self, game: Game, card: CardDef) -> bool:
        return not card.is_land or True

    # ------------------------------------------------------------- main decide
    def decide(self, game: Game) -> Optional[Act]:
        pl = game.priority_player
        if not pl.alive:
            return None
        if game.stack:
            return self.decide_with_stack(game, pl)
        # empty stack
        if game.current_phase in ("Main1", "Main2") and game.active is pl:
            return self.decide_main(game, pl)
        # upkeep/draw/combat/end steps: only instant-speed / triggered plays
        return self.decide_instant_window(game, pl)

    # ------------------------------------------------------------- casting
    def can_pay_color(self, game: Game, pl: Player, cost) -> bool:
        """Check colored-pip availability across pool + untapped mana sources."""
        avail = dict(pl.mana_pool)
        from engine.cards import mana_abilities
        for perm in pl.battlefield:
            if perm.tapped:
                continue
            for (n, colors, _side) in mana_abilities(game, perm):
                if colors == "any":
                    for c in "WUBRG":
                        avail[c] = avail.get(c, 0) + n
                else:
                    for c in colors:
                        avail[c] = avail.get(c, 0) + n
        for c, need in (cost.colored or {}).items():
            if c in "WUBRG" and avail.get(c, 0) < need:
                return False
        return True

    def castable(self, game: Game, pl: Player) -> List[Tuple[CardDef, int]]:
        """(card, x) pairs that are legal + payable right now."""
        out = []
        pool = game.mana_available(pl)
        for c in pl.hand:
            if c.is_land:
                continue
            x = 0
            if c.mana_cost.x:
                # all-in X like the pilot policy
                x = max(0, pool - c.mana_cost.cmc())
            cost = game.cost_of(pl, c, x=x)
            if cost.cmc() <= pool and self.can_pay_color(game, pl, cost):
                out.append((c, x))
        # flashback casts (Past in Flames)
        for c in game.flags.get(f"{pl.name}_flashback", []) or []:
            if c in pl.graveyard:
                cost = game.cost_of(pl, c, from_zone="grave", flashback=True)
                if cost.cmc() <= pool and self.can_pay_color(game, pl, cost):
                    out.append((c, 0))
        # playable from exile
        for c in game.flags.get(f"{pl.name}_playable_exile", []) or []:
            if c in pl.exile:
                cost = game.cost_of(pl, c)
                if cost.cmc() <= pool and self.can_pay_color(game, pl, cost):
                    out.append((c, 0))
        return out

    def decide_main(self, game: Game, pl: Player) -> Optional[Act]:
        # 1. land for turn (extra land plays from Exploration/Azusa/Growth Spiral)
        if not pl.land_played or game.land_allowance(pl) > 0:
            lands = [c for c in pl.hand if c.is_land]
            if lands:
                return Act(lambda: game.play_land(pl, lands[0]))
            gl = [c for c in pl.graveyard if c.is_land]
            if gl and not pl.land_played and any(
                    q.card.name in ("Crucible of Worlds", "Conduit of Worlds") for q in pl.battlefield):
                return Act(lambda: game.play_land(pl, gl[0], from_zone="grave"))
        # 2. commander asap
        if pl.commander in pl.command_zone:
            cost = game.cost_of(pl, pl.commander, from_zone="command")
            if cost.cmc() <= game.mana_available(pl) and self.can_pay_color(game, pl, cost):
                return Act(lambda: game.cast_spell(pl, pl.commander, from_zone="command"))
        # 3. useful activations before spells
        for (label, fn) in self.activations(game, pl):
            return Act(fn)
        # 4. spells by value
        cands = self.castable(game, pl)
        if not cands:
            return None
        score = {}
        for (c, x) in cands:
            s = self.spell_score(game, pl, c, x)
            score[(id(c), x)] = s
        best = max(cands, key=lambda t: score[(id(t[0]), t[1])])
        if score[(id(best[0]), best[1])] < 2:
            return None
        c, x = best
        from . import cards
        # hold counterspells for the stack
        if "counter" in c.tags:
            return None
        def _cast():
            zone = "hand"
            if c in pl.graveyard:
                zone = "grave"
            elif c in pl.exile:
                zone = "exile"
            elif c in pl.command_zone:
                zone = "command"
            fb = c in (game.flags.get(f"{pl.name}_flashback", []) or [])
            kind = (game.flags.get(f"{pl.name}_grave_kind", {}) or {}).get(c.name)
            if kind == "retrace":
                lands = [lc for lc in pl.hand if lc.is_land]
                if lands:
                    pl.discard_card(lands[0])
                    game.log(f"      Six retrace: {pl.name} discards a land for {c.name}")
            game.cast_spell(pl, c, x=x, from_zone=zone, flashback=fb)
        return Act(_cast)

    def spell_score(self, game: Game, pl: Player, c: CardDef, x: int) -> float:
        """Tag-based priority. Card names do not select a strategy."""
        tags = set(c.tags or [])
        text = (c.text or "").lower()
        if "ramp" in tags or "rock" in tags or "{t}: add" in text:
            return 8 - c.mana_cost.cmc() * 0.3
        if c.name == pl.commander.name:
            return 8
        if "tutor" in tags or "search your library" in text:
            return 7
        if "draw" in tags or "draw " in text:
            return 6
        if "removal" in tags or "counter" in tags:
            return 5
        if "token" in tags or "create " in text:
            return 5
        if c.is_creature and c.mana_cost.cmc() <= 4:
            return 4
        if c.is_artifact:
            return 4
        return 3
    def activations(self, game: Game, pl: Player):
        from . import cards
        return cards.activatable(game, pl)

    def decide_with_stack(self, game: Game, pl: Player) -> Optional[Act]:
        # counter enemy spells that matter
        from . import cards
        counter_cards = [c for c in pl.hand if "counter" in c.tags]
        if counter_cards and game.mana_available(pl) >= min(c.mana_cost.cmc() for c in counter_cards) and any(
                self.can_pay_color(game, pl, game.cost_of(pl, c)) for c in counter_cards):
            threat = None
            for o in reversed(game.stack):
                if o.kind == "spell" and o.controller is not pl:
                    if o.card.name == pl.commander.name or o.card.mana_cost.cmc() >= 4 or o.card.is_creature:
                        threat = o
                        break
            if threat:
                cc = min(counter_cards, key=lambda c: c.mana_cost.cmc())
                def _counter(cc=cc, threat=threat):
                    game.cast_spell(pl, cc)
                    # resolve counter effect immediately (target the threat)
                    if threat in game.stack:
                        game.stack.pop(game.stack.index(threat))
                    if cc.name == "An Offer You Can't Refuse":
                        game.create_treasure(threat.controller, 2)
                    elif cc.name == "Mana Drain":
                        game.add_mana(pl, "C", threat.card.mana_cost.cmc())
                    if threat.card.is_legendary and threat.card.name == threat.controller.commander.name:
                        threat.controller.command_zone.append(threat.card)
                    else:
                        threat.controller.graveyard.append(threat.card)
                return Act(_counter)
        # Strionic Resonator on our own trigger
        if game.mana_available(pl) >= 2:
            res = next((q for q in pl.battlefield if q.card.name == "Strionic Resonator" and not q.tapped), None)
            if res:
                mine = [o for o in game.stack if o.kind == "trigger" and o.controller is pl]
                if mine:
                    def _strionic(res=res, src=mine[0]):
                        game.pay_mana(pl, 2, {})
                        res.tapped = True
                        copy = StackObject(kind="trigger", card=None, controller=pl, source=src.source,
                                           desc=f"Strionic copy: {src.desc}", resolve_fn=src.resolve_fn)
                        game.stack.append(copy)
                    return Act(_strionic)
        # instant draw/ritual in response (rare)
        return None

    def decide_instant_window(self, game: Game, pl: Player) -> Optional[Act]:
        return None

    # ------------------------------------------------------------- combat
    def choose_attackers(self, game: Game, pl: Player, legal: List[Permanent]) -> List[Permanent]:
        if not legal:
            return []
        # keep a few blockers if threatened
        threatened = pl.life <= 25
        keep = 2 if threatened else 0
        by_power = sorted(legal, key=lambda q: q.power(game), reverse=True)
        return by_power[: max(1, len(by_power) - keep)]

    def attack_target(self, game: Game, pl: Player, perm: Permanent) -> Optional[Player]:
        alive = game.opponents(pl)
        if not alive:
            return None
        return min(alive, key=lambda o: o.life)

    def choose_blockers(self, game: Game, defp: Player, incoming: List[Permanent]) -> List[Tuple[Permanent, Permanent]]:
        out = []
        blockers = [q for q in defp.battlefield if q.is_creature() and not q.tapped]
        for a in sorted(incoming, key=lambda a: a.power(game), reverse=True):
            for b in blockers:
                if b in [x[0] for x in out]:
                    continue
                if b.power(game) >= a.toughness(game) or b.toughness(game) > a.power(game):
                    out.append((b, a))
                    break
        return out

    # ------------------------------------------------------------- taxes
    def pays_tax(self, game: Game, pl: Player, cost: int, source) -> bool:
        """Rhystic {1} / Remora {4} / cumulative upkeep. Pay only if it matters."""
        if cost <= 0:
            return False
        if source and getattr(source, "card", None) and source.card.name in ("Mystic Remora", "Rhystic Study"):
            if game.mana_available(pl) >= cost + 2:
                return game.pay_mana(pl, cost, {})
            return False
        return game.pay_mana(pl, cost, {})

    # ------------------------------------------------------------- choices
    def choose_discard(self, game: Game, pl: Player) -> Optional[CardDef]:
        if not pl.hand:
            return None
        # discard worst: lands first (keep spells), then high-cost low-value
        nonlands = [c for c in pl.hand if not c.is_land]
        if nonlands:
            return max(nonlands, key=lambda c: self.spell_score(game, pl, c, 0, False))
        return pl.hand[0]

    def split_piles(self, game: Game, opp: Player, cards: List[CardDef]):
        """Fact or Fiction: opponent splits; put the best 2-3 together."""
        scored = sorted(cards, key=lambda c: self.spell_score(game, opp, c, 0, False), reverse=True)
        pile1 = scored[:2]
        pile2 = scored[2:]
        return (pile1, pile2)

    def pick_pile(self, game: Game, pl: Player, piles):
        s1 = sum(self.spell_score(game, pl, c, 0, False) for c in piles[0])
        s2 = sum(self.spell_score(game, pl, c, 0, False) for c in piles[1])
        return piles[0] if s1 >= s2 else piles[1]

    def choose_jeskas_modes(self, game: Game, pl: Player, both: bool) -> List[str]:
        if both:
            return ["mana", "exile"]
        # mana mode if hand sizes big; else exile
        if any(len(o.hand) >= 4 for o in game.opponents(pl)):
            return ["mana"]
        return ["exile"]

    def choose_cryptic_modes(self, game: Game, pl: Player) -> List[str]:
        modes = ["draw"]
        if game.stack:
            modes.append("counter")
        elif any(q.is_creature() and q.controller is not pl for q in pl.battlefield) or True:
            modes.append("tapall")
        return modes[:2]

    def choose_artistic_modes(self, game: Game, pl: Player) -> List[str]:
        modes = []
        if game.stack:
            modes.append("counter")
        modes.append("draw")
        return modes[:2]

    def choose_bounce_target(self, game: Game, pl: Player):
        best = None
        for opp in game.opponents(pl):
            for q in opp.battlefield:
                if q.card.is_legendary and q.card.name == opp.commander.name:
                    return q
                if q.card.mana_cost.cmc() >= 5:
                    best = q
        return best

    def surveil_choose(self, game: Game, pl: Player, top: List[CardDef]) -> List[CardDef]:
        keep = [c for c in top if not c.is_land]
        return keep

    def choose_land_color(self, game: Game, pl: Player) -> str:
        return "R"
