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
    """Ovika combo pilot shared by all 4 players (mirror matches)."""

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
        # playable from exile (Jeska's Will)
        for c in game.flags.get(f"{pl.name}_playable_exile", []) or []:
            if c in pl.exile:
                cost = game.cost_of(pl, c)
                if cost.cmc() <= pool and self.can_pay_color(game, pl, cost):
                    out.append((c, 0))
        # Terra: escape (The Master of Keys) / retrace (Six) from the graveyard
        from .terra import grave_castable as terra_grave_castable
        kinds = {}
        for (gc, kind) in terra_grave_castable(game, pl):
            out.append((gc, 0))
            kinds[gc.name] = kind
        if kinds:
            game.flags[f"{pl.name}_grave_kind"] = kinds
        return out

    def decide_main(self, game: Game, pl: Player) -> Optional[Act]:
        # 1. land for turn (extra land plays from Exploration/Azusa/Growth Spiral)
        if not pl.land_played or game.land_allowance(pl) > 0:
            lands = [c for c in pl.hand if c.is_land]
            if lands:
                if pl.commander.name.startswith("Terra,"):
                    want = {"R", "G"}
                    have = set()
                    for q in pl.battlefield:
                        if q.card.is_land:
                            if "one mana of any color" in (q.card.text or "") or \
                                    q.card.name in ("Command Tower", "Exotic Orchard"):
                                have |= want
                            have |= set(q.card.color_identity)
                    def _terra_land_cover(land):
                        colors = set(land.color_identity)
                        if "one mana of any color" in (land.text or "") or \
                                land.name in ("Command Tower", "Exotic Orchard"):
                            colors |= want
                        return len(want & colors - have)
                    lands = sorted(lands, key=_terra_land_cover, reverse=True)
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
        ovika_out = any(q.card.name == "Ovika, Enigma Goliath" for q in pl.battlefield)
        cands = self.castable(game, pl)
        if not cands:
            return None
        score = {}
        for (c, x) in cands:
            s = self.spell_score(game, pl, c, x, ovika_out)
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

    def spell_score(self, game: Game, pl: Player, c: CardDef, x: int, ovika_out: bool) -> float:
        n = c.name
        if n == "Sol Ring":
            return 9
        if n in ("Arcane Signet", "Fellwar Stone", "Mind Stone", "Everflowing Chalice",
                 "Wayfarer's Bauble", "Chromatic Lantern", "Commander's Sphere", "Thran Dynamo",
                 "Pristine Talisman"):
            return 8 - c.mana_cost.cmc() * 0.3
        if n == "The Eternity Elevator":
            return 7
        if n in ("Koth, Fire of Resistance", "Saheeli, the Gifted", "The Fire Crystal"):
            return 6
        if ovika_out:
            if n in ("Mana Geyser", "Brightstone Ritual", "Battle Hymn", "Seething Song",
                     "Brass's Bounty", "Jeska's Will"):
                return 10
            if n in ("Song of Totentanz", "Empty the Warrens", "Hordeling Outburst",
                     "Krenko's Command", "Dragon Fodder", "Frantic Search"):
                return 9
            if n in ("Fact or Fiction", "Time Reversal", "Treasure Cruise", "Recurring Insight",
                     "Windfall", "Echo of Eons", "Transcendent Message", "Meeting of Minds",
                     "Unexpected Assistance", "Lunar Insight", "Travel the Overworld",
                     "Vivisurgeon's Insight", "Unfathomable Truths", "Focus the Mind",
                     "Cerebral Download", "Complete the Circuit", "Mizzix's Mastery", "Past in Flames"):
                return 8
            if n in ("City on Fire", "Collective Inferno", "Obelisk of Urd",
                     "Harmonized Crescendo", "Mana Echoes"):
                return 9
            if n in ("Stoke the Flames", "Temporal Cleansing", "Calamity of Cinders",
                     "Artistic Refusal", "The One Ring", "Rhystic Study",
                     "Mystic Remora"):
                return 8
            if n in ("Consider", "Opt", "Preordain", "Thought Scour"):
                return 7
            if n in ("Mana Geyser", "Brightstone Ritual", "Battle Hymn"):
                return 10
            if n in ("Torbran, Thane of Red Fell", "Joyful Stormsculptor",
                     "Zephyr Singer", "Chief Engineer", "Interdisciplinary Mascot",
                     "Thunderhead Squadron", "Mogg War Marshal", "Siege-Gang Commander",
                     "Goblin Rabblemaster", "Skirk Prospector", "Goblin Warchief",
                     "Veyran, Voice of Duality", "Roaming Throne", "Storm-Kiln Artist",
                     "Krenko, Mob Boss", "Guttersnipe", "Coruscation Mage"):
                return 6
            if n == "Metallurgic Summonings" or n == "Shark Typhoon":
                return 7
            if n == "Will-Forged Golem":
                return 6
            return 5
        # Terra enchantress engine (name-keyed priorities)
        if n in ("Sythis, Harvest's Hand", "Sanctum Weaver", "Serra's Sanctum"):
            return 8
        if n in ("Mesa Enchantress", "Verduran Enchantress", "Enchantress's Presence",
                 "Eidolon of Blossoms", "Setessan Champion", "Archon of Sun's Grace",
                 "Rhystic Study", "Smothering Tithe", "Sylvan Library"):
            return 7
        terra_bf = any(q.card.name in ("Terra, Magical Adept",
                                       "Terra, Magical Adept // Esper Terra",
                                       "Esper Terra") for q in pl.battlefield)
        if n in ("The Apprentice's Folly", "Mirrormade"):
            return 8 if terra_bf else 5
        if n in ("Copy Enchantment", "Estrid's Invocation"):
            return 8 if terra_bf else 4
        if n == "Moonmist":
            return 7 if terra_bf else 3
        if n in ("Ponder", "Preordain", "Brainstorm", "Opt", "Consider"):
            return 6
        if n in ("Idyllic Tutor", "Enlightened Tutor", "Demonic Counsel"):
            if n == "Demonic Counsel":
                from .terra import _delirium as _terra_delirium
                if not _terra_delirium(pl):
                    return 3
            combo_missing = terra_bf and not any(
                q.card.name in ("The Apprentice's Folly", "Mirrormade")
                for q in pl.battlefield)
            return 8 if combo_missing else 7
        if n in ("Birds of Paradise", "Llanowar Elves", "Citanul Stalwart",
                 "Delighted Halfling", "Farseek", "Nature's Lore", "Three Visits"):
            return 8
        if n == "Land Tax":
            return 6
        if n in ("Opalescence", "Starfield of Nyx", "Enchanted Evening"):
            return 6
        if n in ("The Master of Keys", "Six", "Demon of Fate's Design"):
            return 6
        if n in ("Spark Double", "Yenna, Redtooth Regent"):
            return 5
        if n in ("Summon: Titan", "The Eldest Reborn", "Binding the Old Gods"):
            return 5
        if n == "Summon: Leviathan":
            return 4
        if n == "Culling Ritual":
            return 6
        if n in ("Reanimate", "Sevinne's Reclamation", "Neoform", "Eldritch Evolution",
                 "Archdruid's Charm"):
            return 5
        if n == "Enduring Vitality":
            return 5
        if n == "Amphibian Downpour":
            return 5
        if n in ("Anger", "Destiny Spinner", "Grand Abolisher", "Dauthi Voidwalker",
                 "Dryad of the Ilysian Grove", "Esper Sentinel"):
            return 3
        if n == "Heroic Intervention":
            return 3
        # generic tag-based scoring for non-v11 decks
        if "mass" in c.tags:
            return 6
        if "wheel" in c.tags:
            return 7
        if "tutor" in c.tags or "reanimate" in c.tags:
            return 6
        if "ramp" in c.tags or "rock" in c.tags:
            return 8 - c.mana_cost.cmc() * 0.3
        if "ritual" in c.tags:
            return 5
        if "draw" in c.tags and c.mana_cost.cmc() <= 6:
            return 5
        if "removal" in c.tags or "burn" in c.tags:
            return 4
        if "token" in c.tags:
            return 5
        # v12 convoke build: pre-Ovika priorities
        if n in ("The One Ring", "Rhystic Study", "Mystic Remora", "Mana Echoes"):
            return 7
        if n in ("Consider", "Opt", "Preordain", "Thought Scour"):
            return 4
        if n in ("Mana Geyser", "Brightstone Ritual", "Battle Hymn", "Seething Song"):
            return 5
        if n in ("City on Fire", "Collective Inferno", "Obelisk of Urd",
                 "Harmonized Crescendo"):
            return 5
        if n in ("Stoke the Flames", "Calamity of Cinders", "Temporal Cleansing"):
            return 4
        if n in ("Mogg War Marshal", "Goblin Rabblemaster", "Krenko, Mob Boss",
                 "Skirk Prospector", "Goblin Warchief", "Veyran, Voice of Duality",
                 "Roaming Throne", "Storm-Kiln Artist", "Torbran, Thane of Red Fell",
                 "Chief Engineer", "Zephyr Singer", "Joyful Stormsculptor",
                 "Thunderhead Squadron", "Interdisciplinary Mascot", "Siege-Gang Commander",
                 "Urabrask", "Guttersnipe", "Coruscation Mage"):
            return 4
        if n in ("Meeting of Minds", "Unexpected Assistance", "Transcendent Message",
                 "Artistic Refusal", "Complete the Circuit"):
            return 4
        # pre-Ovika setup
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
            terra_bf = (pl.commander.name.startswith("Terra,") and any(
                q.card.name in ("Terra, Magical Adept", "Terra, Magical Adept // Esper Terra",
                                "Esper Terra") for q in pl.battlefield))
            for o in reversed(game.stack):
                if o.kind == "spell" and o.controller is not pl:
                    text = o.card.text or ""
                    removal_like = ("target creature" in text or "target permanent" in text
                                    or "target nonland permanent" in text) and (
                        "destroy" in text or "exile" in text or "gain control" in text)
                    if terra_bf and removal_like:
                        threat = o
                        break
                    if (o.card.name == pl.commander.name or o.card.mana_cost.cmc() >= 4
                            or o.card.is_creature):
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
                if mine and "Ovika" in mine[0].desc:
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
        if not pl.commander.name.startswith("Terra,"):
            return min(alive, key=lambda o: o.life)
        # Terra combo pilot: spread the Reflections to kill everyone when the
        # burst provides lethal-on-board, otherwise focus the lowest life.
        key = f"_terra_assign_{game.turn_no}"
        assign = game.flags.get(key)
        if assign is None:
            total = sum(a.power(game) for a in game.legal_attackers(pl))
            assign = {"lethal_all": total >= sum(o.life for o in alive) + 8,
                      "dmg": {o.name: 0 for o in alive}}
            game.flags[key] = assign
        if assign["lethal_all"]:
            tgt = max(alive, key=lambda o: o.life - assign["dmg"][o.name])
            assign["dmg"][tgt.name] += perm.power(game)
            return tgt
        tgt = min(alive, key=lambda o: o.life)
        assign["dmg"][tgt.name] += perm.power(game)
        return tgt

    def choose_blockers(self, game: Game, defp: Player, incoming: List[Permanent]) -> List[Tuple[Permanent, Permanent]]:
        out = []
        blockers = [q for q in defp.battlefield if q.is_creature() and not q.tapped]
        is_terra = defp.commander.name.startswith("Terra,")
        # block the biggest attacker we can survive against
        for a in sorted(incoming, key=lambda a: a.power(game), reverse=True):
            for b in blockers:
                if b in [x[0] for x in out]:
                    continue
                if is_terra and b.card.name in ("Terra, Magical Adept // Esper Terra",
                                                "Terra, Magical Adept", "Esper Terra"):
                    # do not trade the commander unless the hit is near-lethal
                    if a.power(game) >= b.toughness(game) and defp.life - a.power(game) > 3:
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
            # never feed the Ovika player card advantage unless cheap and rich
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
