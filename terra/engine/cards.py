"""Card behaviors for the v11 deck, implemented from real oracle text
(see ovika/rulebook/deck_oracles.md). Each function is rules-shaped: mana
abilities (605), triggered abilities (603), spell effects (608), and
activated abilities (602) are resolved by the engine in game.py.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Set, Tuple

from .game import Game, Permanent, Player, StackObject, Trigger
from .oracle import CardDef, ManaCost


# ---------------------------------------------------------------------------
# Mana abilities (605) -- (amount, colors, side_effect)
# colors: list like ['U','R'] or 'any'
# ---------------------------------------------------------------------------

def _side_none(game, pl, perm):
    return None


def mana_abilities(game: Game, perm: Permanent) -> List[Tuple[int, object, Callable]]:
    n = perm.card.name
    out = []
    if perm.card.is_land:
        if n == "Mountain":
            out.append((1, ["R"], _side_none))
        elif n == "Island":
            out.append((1, ["U"], _side_none))
        elif n in ("Command Tower", "Path of Ancestry", "Command Bridge"):
            out.append((1, "any", _side_none))
        elif n == "Exotic Orchard":
            colors = set()
            for opp in game.opponents(perm.controller):
                for p in opp.battlefield:
                    if p.card.is_land:
                        colors |= set(_land_colors(p.card.name))
            out.append((1, list(colors) or ["C"], _side_none))
        elif n in ("Baron, Airship Kingdom", "Peculiar Lighthouse", "Swiftwater Cliffs"):
            out.append((1, ["U", "R"], _side_none))
        elif n == "Shivan Reef":
            out.append((1, ["U", "R"], lambda g, pl, perm: (g.deal_damage(perm, pl, 1), pl.life)))
        elif n == "Jidoor, Aristocratic Capital // Overture":
            out.append((1, ["U"], _side_none))
        elif n == "Crossroads Village":
            out.append((1, [perm.chosen_color or "R"], _side_none))
        elif n in ("Cascading Cataracts", "Adventurer's Inn", "Mirrorpool", "Terrain Generator", "Myriad Landscape"):
            out.append((1, ["C"], _side_none))
        elif n == "Power Depot":
            out.append((1, ["C"], _side_none))
        elif n == "The Autonomous Furnace":
            out.append((1, ["R"], _side_none))
        # Chromatic Lantern: lands you control tap for any color (static)
        for q in perm.controller.battlefield:
            if q.card.name == "Chromatic Lantern" and q.card.is_artifact:
                out = [(amt, "any", side) for (amt, colors, side) in out]
    elif perm.card.is_artifact:
        if n == "Sol Ring":
            out.append((2, ["C"], _side_none))
        elif n == "Arcane Signet":
            out.append((1, "any", _side_none))
        elif n == "Everflowing Chalice":
            out.append((perm.counters.get("charge", 0), ["C"], _side_none))
        elif n == "Pristine Talisman":
            out.append((1, ["C"], lambda g, pl, perm: setattr(pl, "life", pl.life + 1)))
        elif n == "The Eternity Elevator":
            out.append((3, ["C"], _side_none))
        elif n == "Chromatic Lantern":
            out.append((1, "any", _side_none))
        elif n == "Fellwar Stone":
            colors = set()
            for opp in game.opponents(perm.controller):
                for p in opp.battlefield:
                    if p.card.is_land:
                        colors |= set(_land_colors(p.card.name))
            out.append((1, list(colors) or ["C"], _side_none))
        elif n == "Mind Stone":
            out.append((1, ["C"], _side_none))
        elif n == "Thran Dynamo":
            out.append((3, ["C"], _side_none))
        elif n == "Commander's Sphere":
            out.append((1, "any", _side_none))
        elif n == "Skirk Prospector" and perm.card.is_creature:
            # Sacrifice a Goblin: Add {R} -- mana ability (605.1b)
            if any(q.card.name == "Skirk Prospector" and q is not perm for q in perm.controller.battlefield):
                pass
            out.append((1, ["R"], lambda g, pl, perm: None))
    # Skirk Prospector is a creature; handle via its own entry
    if perm.card.name == "Skirk Prospector":
        out.append((1, ["R"], lambda g, pl, perm: None))
    from .terra import mana_abilities as terra_mana_abilities
    terra_own = terra_mana_abilities(game, perm)
    if terra_own:
        out = list(terra_own)
    if not out:
        from .generic import generic_mana_abilities
        out = generic_mana_abilities(game, perm)
    # Enduring Vitality: creatures you control have "{T}: Add one mana of any color"
    if perm.is_creature() and not out and any(
            q.card.name == "Enduring Vitality" for q in perm.controller.battlefield):
        out.append((1, "any", _side_none))
    # Dryad of the Ilysian Grove: lands you control tap for any color (simplified static)
    if perm.card.is_land and any(
            q.card.name == "Dryad of the Ilysian Grove" for q in perm.controller.battlefield):
        out = [(amt, "any", side) for (amt, colors, side) in out]
    return out


def _land_colors(name: str) -> List[str]:
    if name == "Mountain":
        return ["R"]
    if name == "Island":
        return ["U"]
    if name in ("Command Tower", "Path of Ancestry", "Command Bridge"):
        return ["U", "R"]
    if name in ("Baron, Airship Kingdom", "Peculiar Lighthouse", "Swiftwater Cliffs", "Shivan Reef", "Crossroads Village"):
        return ["U", "R"]
    if name == "Jidoor, Aristocratic Capital // Overture":
        return ["U"]
    return ["C"]


def after_mana_ability(game: Game, pl: Player, perm: Permanent) -> None:
    """Side effects of mana abilities (Shivan Reef pain handled inline)."""
    if perm.card.name == "Skirk Prospector":
        goblins = [q for q in pl.battlefield if q.is_creature() and q is not perm
                   and ("Goblin" in q.card.subtypes or "Goblin" in q.card.name or "Phyrexian Goblin" in q.card.name)]
        # sacrifice a goblin (other than itself if possible)
        if goblins:
            game.sacrifice(pl, goblins[0])
        elif perm in pl.battlefield:
            game.sacrifice(pl, perm)


def game_sacrifice_patch():
    """Add Game.sacrifice if missing."""
    if not hasattr(Game, "sacrifice"):
        def sacrifice(self, pl: Player, perm: Permanent):
            if perm not in pl.battlefield:
                return
            pl.battlefield.remove(perm)
            self.log(f"      {pl.name} sacrifices {perm.name}")
            self.trigger_after_death(perm)
            if perm.card.is_legendary and (
                    perm.card is pl.commander or
                    (perm.card.name == "Esper Terra" and pl.commander.name.startswith("Terra,"))):
                pl.command_zone.append(pl.commander)
            else:
                pl.graveyard.append(perm.card)
        Game.sacrifice = sacrifice


game_sacrifice_patch()


# ---------------------------------------------------------------------------
# On-cast triggers (603.2) -- Ovika engine, Veyran, Throne, Shark, etc.
# ---------------------------------------------------------------------------

def spell_mv(obj: StackObject) -> int:
    """Mana value of a spell as cast (including X as paid; CR 202.3e)."""
    mc = obj.card.mana_cost
    base = mc.cmc()
    if mc.x:
        return base - 1 + obj.x
    return base


def on_cast(game: Game, pl: Player, obj: StackObject) -> None:
    card = obj.card
    # ---- Ovika: whenever you cast a noncreature spell ----
    ovika = next((q for q in pl.battlefield if q.card.name == "Ovika, Enigma Goliath"), None)
    if ovika is not None and not card.is_creature:
        mv = spell_mv(obj)
        extra = 0
        # Veyran: inst/sorc cast triggers trigger an additional time
        veyran = any(q.card.name == "Veyran, Voice of Duality" for q in pl.battlefield)
        if veyran and (card.is_instant or card.is_sorcery):
            extra += 1
        # Roaming Throne (choose Phyrexian): Ovika triggers an additional time
        for q in pl.battlefield:
            if q.card.name == "Roaming Throne" and q.chosen_type == "Phyrexian":
                extra += 1
        def _ovika(game_: Game, t: Trigger):
            for _ in range(mv):
                game_.create_token(pl, "Phyrexian Goblin", 1, 1,
                                   types={"Creature", "Goblin"}, abilities=set(), haste=True,
                                   colors={"R"})
        game.queue_trigger(ovika, pl, f"Ovika: {mv} Phyrexian Goblins ({card.name})",
                           _ovika, extra=extra)
    # ---- Shark Typhoon: shark per noncreature spell ----
    if any(q.card.name == "Shark Typhoon" for q in pl.battlefield) and not card.is_creature:
        mv = spell_mv(obj)
        def _shark(game_: Game, t: Trigger):
            game_.create_token(pl, "Shark", mv, mv,
                               types={"Creature", "Shark"}, abilities={"flying"}, colors={"U"})
        game.queue_trigger(None, pl, f"Shark Typhoon: {mv}/{mv} Shark", _shark)
    # ---- Metallurgic Summonings: construct per instant/sorcery ----
    if any(q.card.name == "Metallurgic Summonings" for q in pl.battlefield) and (card.is_instant or card.is_sorcery):
        mv = spell_mv(obj)
        def _construct(game_: Game, t: Trigger):
            game_.create_token(pl, "Construct", mv, mv,
                               types={"Artifact", "Creature", "Construct"}, colors=set())
        game.queue_trigger(None, pl, f"Metallurgic Summonings: {mv}/{mv} Construct", _construct)
    # ---- Storm-Kiln Artist: treasure per magecraft ----
    if any(q.card.name == "Storm-Kiln Artist" for q in pl.battlefield) and (card.is_instant or card.is_sorcery):
        def _treasure(game_: Game, t: Trigger):
            game_.create_treasure(pl, 1)
        game.queue_trigger(None, pl, "Storm-Kiln Artist: Treasure", _treasure)
    # ---- Veyran magecraft: +1/+1 ----
    for q in pl.battlefield:
        if q.card.name == "Veyran, Voice of Duality" and (card.is_instant or card.is_sorcery):
            q.eot_power_mod += 1
    # ---- Tellah ----
    tellah = next((q for q in pl.battlefield if q.card.name == "Tellah, Great Sage"), None)
    if tellah is not None and not card.is_creature:
        mv = spell_mv(obj)
        spent = obj.cost_paid
        def _tellah(game_: Game, t: Trigger):
            game_.create_token(pl, "Hero", 1, 1, types={"Creature", "Hero"}, colors=set())
            if spent >= 4:
                game.draw(pl, 2)
            if spent >= 8:
                game.sacrifice(pl, tellah)
                for opp in game.opponents(pl):
                    game_.deal_damage(tellah, opp, spent)
        game.queue_trigger(tellah, pl, f"Tellah: Hero token (spent {spent})", _tellah)
    # ---- Rhystic Study / Mystic Remora ----
    for q in pl.battlefield:
        if q.card.name == "Rhystic Study":
            def _rhystic(game_: Game, t: Trigger):
                for opp in list(game.opponents(pl)):
                    if opp.ai.pays_tax(game, opp, 1, q):
                        continue
                    game.draw(pl, 1)
            game.queue_trigger(q, pl, "Rhystic Study: draw", _rhystic)
        if q.card.name == "Mystic Remora" and not card.is_creature:
            def _remora(game_: Game, t: Trigger):
                for opp in list(game.opponents(pl)):
                    if opp.ai.pays_tax(game, opp, 4, q):
                        continue
                    game.draw(pl, 1)
            game.queue_trigger(q, pl, "Mystic Remora: draw", _remora)
    # ---- Complete the Circuit: copy next instant/sorcery twice ----
    if card.is_instant or card.is_sorcery:
        flag = f"{pl.name}_circuit"
        if game.flags.get(flag):
            del game.flags[flag]
            for _ in range(2):
                copy = StackObject(kind="spell", card=card, controller=pl, x=obj.x,
                                   targets=list(obj.targets), modes=list(obj.modes),
                                   desc=f"Circuit copy of {card.name}")
                copy._is_copy = True
                game.stack.append(copy)
            game.log(f"      Complete the Circuit copies {card.name} twice")

    from .terra import on_cast as terra_on_cast
    terra_on_cast(game, pl, obj)
    from .generic import generic_on_cast
    generic_on_cast(game, pl, obj)

# storm handled in game.cast_spell


# ---------------------------------------------------------------------------
# Enter-the-battlefield triggers and land ETB effects
# ---------------------------------------------------------------------------

def on_enter(game: Game, perm: Permanent) -> None:
    n = perm.card.name
    pl = perm.controller
    if n in ("Swiftwater Cliffs", "Adventurer's Inn"):
        pl.life += 1 if n == "Swiftwater Cliffs" else 2
        game.log(f"        {n}: {pl.name} gains life")
    if n in ("Path of Ancestry", "Baron, Airship Kingdom", "Jidoor, Aristocratic Capital // Overture",
             "Crossroads Village", "Command Bridge", "Power Depot", "The Autonomous Furnace",
             "Mirrorpool", "Myriad Landscape", "Swiftwater Cliffs"):
        perm.tapped = True
    if n == "Command Bridge":
        # sacrifice unless you tap an untapped permanent you control
        untapped = [q for q in pl.battlefield if q is not perm and not q.tapped]
        if untapped:
            untapped[0].tapped = True
        else:
            game.sacrifice(pl, perm)
    if n == "Crossroads Village":
        perm.chosen_color = pl.ai.choose_land_color(game, pl) or "R"
    if n == "Roaming Throne":
        perm.chosen_type = "Phyrexian"  # for Ovika
    if n == "Everflowing Chalice":
        perm.counters["charge"] = perm.counters.get("charge", 0)
    if n == "Mogg War Marshal":
        perm.echo_pending = True
        game.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"}, colors={"R"})
    if n == "Joyful Stormsculptor":
        game.create_token(pl, "Elemental", 1, 1, types={"Creature", "Elemental"}, colors={"U", "R"})
        game.create_token(pl, "Elemental", 1, 1, types={"Creature", "Elemental"}, colors={"U", "R"})
        game.log("        Joyful Stormsculptor: 2 Elemental tokens")
    if n == "Interdisciplinary Mascot":
        game.draw(pl, 1)
        game.log("        Interdisciplinary Mascot: look at top 4, draw 1")
    if n == "Obelisk of Urd":
        perm.chosen_type = "Goblin"
    if n == "Siege-Gang Commander":
        for _ in range(3):
            game.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"}, colors={"R"})
    if n == "Trinket Mage":
        found = game.search_library(pl, lambda c: c.is_artifact and c.mana_cost.cmc() <= 1, 1)
        if found:
            game.log(f"        Trinket Mage finds {found[0].name}")
    if n == "Marina Vendrell's Grimoire":
        game.draw(pl, 5)
        game.flags[f"{pl.name}_no_max_hand"] = True
    if n == "Koth, Fire of Resistance":
        perm.counters["loyalty"] = perm.counters.get("loyalty", 0) + 4
    if n == "Saheeli, the Gifted":
        perm.counters["loyalty"] = perm.counters.get("loyalty", 0) + 4
    if n == "The Fire Crystal":
        pass
    if n == "Meat Locker // Drowned Diner":
        # room: unlock trigger taps a creature with 2 stun counters
        targets = [q2 for q in game.opponents(pl) for q2 in q.battlefield if q2.is_creature() and not q2.tapped]
        if targets:
            tgt = targets[0]
            tgt.tapped = True
            tgt.counters["stun"] += 2
            game.log(f"        Meat Locker taps {tgt.name} (2 stun)")
    if n == "Ovika, Enigma Goliath":
        perm.summon_sick = True
    from .generic import generic_on_enter
    generic_on_enter(game, perm)
    from .terra import on_enter as terra_on_enter
    terra_on_enter(game, perm)


def on_death(game: Game, perm: Permanent) -> None:
    pl = perm.controller if perm.controller else perm.owner
    # Skullclamp: whenever equipped creature dies, draw two cards
    if perm.equipment:
        for eq in perm.equipment:
            if eq.card.name == "Skullclamp":
                game.draw(pl, 2)
                game.log(f"      Skullclamp: {pl.name} draws 2")
                eq.equipped_to = None
    if perm.card.name == "Mogg War Marshal":
        game.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"}, colors={"R"})
        game.log("      Mogg War Marshal death trigger: Goblin")
    from .generic import generic_on_death
    generic_on_death(game, perm)
    from .terra import on_death as terra_on_death
    terra_on_death(game, perm)


def on_attackers_declared(game: Game, pl: Player, attackers: List[Permanent]) -> None:
    for a in attackers:
        if a.card.name == "Goblin Rabblemaster":
            n = sum(1 for q in attackers if q is not a and "Goblin" in (q.card.subtypes | {q.card.name}))
            a.eot_power_mod += n
            game.log(f"      Rabblemaster +{n}/+0")
    from .terra import on_attackers as terra_on_attackers
    terra_on_attackers(game, pl, attackers)


def on_token_created(game: Game, perm: Permanent) -> None:
    mana_echoes_trigger(game, perm, 1)


def on_tokens_created(game: Game, controller, made: list) -> None:
    if not made:
        return
    mana_echoes_trigger(game, made[0], len(made))


def mana_echoes_trigger(game: Game, perm: Permanent, count: int = 1) -> None:
    """Mana Echoes: whenever a creature enters, may add C equal to # creatures
    you control that share a creature type with it (605.1b, mana ability)."""
    for q in game.players:
        if not any(e.card.name == "Mana Echoes" and e.controller is q for e in q.battlefield):
            continue
        if perm.controller is not q or not perm.is_creature():
            continue
        share = 0
        if perm.card.subtypes:
            share = sum(1 for o in q.battlefield if o.is_creature() and (o.card.subtypes & perm.card.subtypes))
        if share == 0 and "Goblin" in perm.card.name:
            share = sum(1 for o in q.battlefield if o.is_creature() and "Goblin" in o.card.name)
        if share > 0:
            added = min(share * count, 30)  # perf guard; disclosed abstraction
            q.mana_pool["C"] += added
            game.log(f"      Mana Echoes: {q.name} adds {added} C")


def storm_copies(game: Game, obj: StackObject) -> None:
    """Storm (702.39): copy this spell for each spell cast before it this turn."""
    pl = obj.controller
    n = max(0, pl.spells_cast_turn - 1)
    if n == 0:
        return
    for _ in range(n):
        copy = StackObject(kind="spell", card=obj.card, controller=pl, x=obj.x,
                           targets=[], modes=[], desc=f"Storm copy of {obj.card.name}")
        copy._is_copy = True
        copy.card = obj.card
        game.stack.append(copy)
    game.log(f"      Storm: {n} copies of {obj.card.name}")


# ---------------------------------------------------------------------------
# Spell resolution (608) -- instant/sorcery effects from oracle text
# ---------------------------------------------------------------------------

def resolve_effect(game: Game, obj: StackObject) -> None:
    pl = obj.controller
    n = obj.card.name
    x = obj.x
    if n == "Song of Totentanz":
        for _ in range(x):
            game.create_token(pl, "Rat", 1, 1, types={"Creature", "Rat"},
                              abilities={"cant_block"}, colors={"B"})
        for q in pl.battlefield:
            if q.is_creature():
                q.eot_haste = True
    elif n in ("Krenko's Command", "Dragon Fodder"):
        for _ in range(2):
            game.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"}, colors={"R"})
    elif n == "Hordeling Outburst":
        for _ in range(3):
            game.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"}, colors={"R"})
    elif n == "Empty the Warrens":
        for _ in range(2):
            game.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"}, colors={"R"})
    elif n == "Frantic Search":
        game.draw(pl, 2)
        for _ in range(2):
            c = pl.ai.choose_discard(game, pl)
            if c:
                pl.discard_card(c)
        lands = [q for q in pl.battlefield if q.card.is_land and q.tapped][:3]
        for q in lands:
            q.tapped = False
    elif n == "Battle Hymn":
        game.add_mana(pl, "R", sum(1 for q in pl.battlefield if q.is_creature()))
    elif n == "Brightstone Ritual":
        gobs = sum(1 for q in pl.battlefield if q.is_creature() and "Goblin" in (q.card.subtypes | {q.card.name}))
        game.add_mana(pl, "R", gobs)
    elif n == "Seething Song":
        game.add_mana(pl, "R", 5)
    elif n == "Mana Geyser":
        tapped = sum(1 for opp in game.opponents(pl) for q in opp.battlefield if q.card.is_land and q.tapped)
        game.add_mana(pl, "R", tapped)
    elif n == "Brass's Bounty":
        nlands = sum(1 for q in pl.battlefield if q.card.is_land)
        game.create_treasure(pl, nlands)
    elif n == "Windfall":
        discards = []
        for p in game.turn_order(pl):
            discards.append(len(p.hand))
            for c in list(p.hand):
                p.discard_card(c)
        top = max(discards) if discards else 0
        for p in game.turn_order(pl):
            p.draw(top)
    elif n in ("Time Reversal", "Echo of Eons"):
        for p in game.turn_order(pl):
            for c in list(p.hand):
                p.hand.remove(c)
                p.library.append(c)
            for c in list(p.graveyard):
                p.graveyard.remove(c)
                p.library.append(c)
            p.shuffle()
            p.draw(7)
        if n == "Time Reversal":
            pl.exile.append(obj.card)
        # Echo of Eons flashback handled in resolve_spell
    elif n == "Fact or Fiction":
        top5 = pl.library[-5:][::-1] if len(pl.library) >= 5 else list(pl.library)[::-1]
        for c in top5:
            pl.library.remove(c)
        opp = game.opponents(pl)[0]
        piles = opp.ai.split_piles(game, opp, top5)
        pick = pl.ai.pick_pile(game, pl, piles)
        for c in pick:
            pl.hand.append(c)
        for c in piles[1] if piles[0] is pick else piles[0]:
            pl.graveyard.append(c)
    elif n == "Treasure Cruise":
        game.draw(pl, 3)
    elif n == "Recurring Insight":
        target = max(game.opponents(pl), key=lambda o: len(o.hand))
        game.draw(pl, len(target.hand))
        # rebound: exile, cast free at next upkeep (702.94)
        pl.exile.append(obj.card)
        game.flags[f"{pl.name}_rebound"] = obj.card
    elif n == "Jeska's Will":
        both = pl.commander in [q.card.name for q in pl.battlefield if q.card.name == pl.commander.name] or \
               any(q.card.name == "Ovika, Enigma Goliath" for q in pl.battlefield)
        modes = pl.ai.choose_jeskas_modes(game, pl, both)
        if "mana" in modes:
            target = max(game.opponents(pl), key=lambda o: len(o.hand))
            game.add_mana(pl, "R", len(target.hand))
        if "exile" in modes:
            top3 = pl.library[-3:][::-1] if len(pl.library) >= 3 else list(pl.library)[::-1]
            for c in top3:
                pl.library.remove(c)
                pl.exile.append(c)
            game.flags[f"{pl.name}_playable_exile"] = list(top3)
            game.add_turn_effect("turn", lambda: game.flags.pop(f"{pl.name}_playable_exile", None))
    elif n == "Past in Flames":
        grave_isc = [c for c in pl.graveyard if c.is_instant or c.is_sorcery]
        game.flags[f"{pl.name}_flashback"] = grave_isc
        game.add_turn_effect("turn", lambda: game.flags.pop(f"{pl.name}_flashback", None))
    elif n == "Mizzix's Mastery":
        if obj.overload:
            for c in list(pl.graveyard):
                if c.is_instant or c.is_sorcery:
                    pl.graveyard.remove(c)
                    game.cast_spell(pl, c, free=True, from_zone="grave", flashback=True)
        else:
            targets = [c for c in pl.graveyard if c.is_instant or c.is_sorcery]
            if targets:
                c = targets[0]
                pl.graveyard.remove(c)
                game.cast_spell(pl, c, free=True, from_zone="grave", flashback=True)
        pl.exile.append(obj.card)
    elif n == "Transcendent Message":
        game.draw(pl, x)
    elif n == "Meeting of Minds":
        game.draw(pl, 2)
    elif n == "Unexpected Assistance":
        game.draw(pl, 3)
        c = pl.ai.choose_discard(game, pl)
        if c:
            pl.discard_card(c)
    elif n == "Complete the Circuit":
        game.flags[f"{pl.name}_sorcery_flash"] = True
        game.add_turn_effect("turn", lambda: game.flags.pop(f"{pl.name}_sorcery_flash", None))
        game.flags[f"{pl.name}_circuit"] = True
    elif n == "Artistic Refusal":
        modes = pl.ai.choose_artistic_modes(game, pl)
        if "counter" in modes and game.stack:
            # counter target spell (topmost opposing spell)
            idx = next((i for i, o in enumerate(game.stack) if o.kind == "spell" and o.controller is not pl), None)
            if idx is not None:
                countered = game.stack.pop(idx)
                if countered.card.is_legendary and countered.card.name == countered.controller.commander.name:
                    countered.controller.command_zone.append(countered.card)
                else:
                    countered.controller.graveyard.append(countered.card)
                game.log(f"      Artistic Refusal counters {countered.card.name}")
        if "draw" in modes:
            game.draw(pl, 2)
            c = pl.ai.choose_discard(game, pl)
            if c:
                pl.discard_card(c)
    elif n == "An Offer You Can't Refuse":
        idx = next((i for i, o in enumerate(game.stack) if o.kind == "spell" and o.controller is not pl and not o.card.is_creature), None)
        if idx is not None:
            countered = game.stack.pop(idx)
            if countered.card.is_legendary and countered.card.name == countered.controller.commander.name:
                countered.controller.command_zone.append(countered.card)
            else:
                countered.controller.graveyard.append(countered.card)
            game.create_treasure(countered.controller, 2)
            game.log(f"      An Offer counters {countered.card.name} (2 Treasures)")
    elif n == "Cryptic Command":
        modes = pl.ai.choose_cryptic_modes(game, pl)
        if "counter" in modes and game.stack:
            idx = next((i for i, o in enumerate(game.stack) if o.kind == "spell" and o.controller is not pl), None)
            if idx is not None:
                countered = game.stack.pop(idx)
                if countered.card.is_legendary and countered.card.name == countered.controller.commander.name:
                    countered.controller.command_zone.append(countered.card)
                else:
                    countered.controller.graveyard.append(countered.card)
                game.log(f"      Cryptic Command counters {countered.card.name}")
        if "bounce" in modes:
            tgt = pl.ai.choose_bounce_target(game, pl)
            if tgt:
                tgt.controller.battlefield.remove(tgt)
                tgt.controller.hand.append(tgt.card)
                game.log(f"      Cryptic Command bounces {tgt.name}")
        if "tapall" in modes:
            for opp in game.opponents(pl):
                for q in opp.battlefield:
                    if q.is_creature():
                        q.tapped = True
        if "draw" in modes:
            game.draw(pl, 1)
    elif n == "Lunar Insight":
        mvs = set()
        for q in pl.battlefield:
            if not q.card.is_land:
                mvs.add(q.card.mana_cost.cmc())
        game.draw(pl, len(mvs))
    elif n == "Travel the Overworld":
        game.draw(pl, 4)
    elif n == "Vivisurgeon's Insight":
        game.draw(pl, 3)
        for q in pl.battlefield:
            for kind in list(q.counters):
                if kind in ("charge", "+1/+1", "loyalty", "stun"):
                    q.counters[kind] += 1
    elif n == "Unfathomable Truths":
        game.draw(pl, 3)
        game.create_token(pl, "Eldrazi Spawn", 0, 1, types={"Creature", "Eldrazi", "Spawn"},
                          abilities={"sac_c"}, colors=set())
    elif n == "Focus the Mind":
        game.draw(pl, 3)
        c = pl.ai.choose_discard(game, pl)
        if c:
            pl.discard_card(c)
    elif n == "Cerebral Download":
        x = sum(1 for q in pl.battlefield if q.card.is_artifact)
        top = pl.library[-x:][::-1] if x > 0 and len(pl.library) >= x else []
        for c in top:
            pl.library.remove(c)
        keep = pl.ai.surveil_choose(game, pl, top)
        for c in keep:
            pl.library.append(c)
        game.draw(pl, 3)
    else:
        from .terra import resolve_effect as terra_resolve_effect
        if not terra_resolve_effect(game, obj):
            from .generic import generic_spell_resolution
            generic_spell_resolution(game, obj)


# ---------------------------------------------------------------------------
# Upkeep triggers (503.1)
# ---------------------------------------------------------------------------

def upkeep_triggers(game: Game, pl: Player) -> None:
    """Called at the beginning of upkeep before priority (503.1a)."""
    for perm in list(pl.battlefield):
        n = perm.card.name
        if n == "Goblin Assault":
            def _ga(game_: Game, t: Trigger):
                game_.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"},
                                   colors={"R"}, haste=True)
            game.queue_trigger(perm, pl, "Goblin Assault: Goblin token", _ga)
        if n == "Mystic Remora":
            # cumulative upkeep {1}: add age counter, pay {1}xage or sacrifice
            perm.counters["age"] += 1
            cost = perm.counters["age"]
            if pl.ai.pays_tax(game, pl, cost, perm):
                game.pay_mana(pl, cost, {})
            else:
                game.sacrifice(pl, perm)
                game.log(f"      {pl.name} sacrifices Mystic Remora (cumulative upkeep)")
        if n == "Mogg War Marshal" and getattr(perm, "echo_pending", False):
            # echo {1}{R} (702.29): pay or sacrifice
            if game.mana_available(pl) >= 2:
                game.pay_mana(pl, 1, {"R": 1})
                perm.echo_pending = False
                game.log(f"      {pl.name} pays Mogg War Marshal echo")
            else:
                game.sacrifice(pl, perm)
    # rebound: cast exiled card free (702.94)
    rb = game.flags.pop(f"{pl.name}_rebound", None)
    if rb is not None:
        if rb in pl.exile:
            pl.exile.remove(rb)
        game.cast_spell(pl, rb, free=True, from_zone="exile")


    from .generic import generic_upkeep
    generic_upkeep(game, pl)
    from .terra import upkeep as terra_upkeep
    terra_upkeep(game, pl)


# ---------------------------------------------------------------------------
# Activated abilities (602) exposed to the AI
# ---------------------------------------------------------------------------

def activatable(game: Game, pl: Player) -> List[Tuple[str, Callable]]:
    """Return (label, activation callable) for abilities the AI may use now."""
    acts = []
    for perm in pl.battlefield:
        n = perm.card.name
        if perm.tapped:
            continue
        if n == "Krenko, Mob Boss":
            gobs = sum(1 for q in pl.battlefield if q.is_creature() and "Goblin" in (q.card.subtypes | {q.card.name}))
            if gobs > 0:
                def _krenko(perm=perm, gobs=gobs):
                    perm.tapped = True
                    for _ in range(gobs):
                        game.create_token(pl, "Goblin", 1, 1, types={"Creature", "Goblin"}, colors={"R"})
                acts.append((f"Krenko: {gobs} Goblins", _krenko))
        if n == "Lightning Greaves" and not perm.equipped_to:
            targets = [q for q in pl.battlefield if q.is_creature() and q is not perm and not q.equipment]
            if targets:
                def _greaves(perm=perm, tgt=targets[0]):
                    perm.equipped_to = tgt
                    tgt.equipment.append(perm)
                    game.log(f"      {pl.name} equips Lightning Greaves to {tgt.name}")
                acts.append(("Equip Greaves", _greaves))
        if n == "Skullclamp" and not perm.equipped_to:
            targets = [q for q in pl.battlefield if q.is_creature() and q is not perm and not q.equipment]
            if targets and game.mana_available(pl) >= 1:
                def _clamp(perm=perm, tgt=targets[0]):
                    game.pay_mana(pl, 1, {})
                    perm.equipped_to = tgt
                    tgt.equipment.append(perm)
                    game.log(f"      {pl.name} equips Skullclamp to {tgt.name}")
                acts.append(("Equip Skullclamp", _clamp))
        if n == "Strionic Resonator" and game.mana_available(pl) >= 2:
            mine = [o for o in game.stack if o.kind == "trigger" and o.controller is pl]
            if mine:
                def _strionic(perm=perm, src=mine[0]):
                    game.pay_mana(pl, 2, {})
                    perm.tapped = True
                    copy = StackObject(kind="trigger", card=None, controller=pl,
                                       source=src.source, desc=f"Strionic copy: {src.desc}",
                                       resolve_fn=src.resolve_fn)
                    game.stack.append(copy)
                    game.log(f"      Strionic Resonator copies {src.desc}")
                acts.append(("Strionic: copy trigger", _strionic))
        if n == "Kher Keep" and game.mana_available(pl) >= 2:
            def _kher(perm=perm):
                game.pay_mana(pl, 1, {"R": 1})
                perm.tapped = True
                game.create_token(pl, "Kobold", 1, 1, types={"Creature", "Kobold"}, colors={"R"})
                game.log("      Kher Keep: 1/1 Kobold")
            acts.append(("Kher Keep: Kobold", _kher))
        if n == "Mind Stone" and game.mana_available(pl) >= 1:
            def _mind(perm=perm):
                game.pay_mana(pl, 1, {})
                game.sacrifice(pl, perm)
                game.draw(pl, 1)
            acts.append(("Mind Stone: sac, draw", _mind))
        if n == "Commander's Sphere":
            def _sphere(perm=perm):
                game.sacrifice(pl, perm)
                game.draw(pl, 1)
            acts.append(("Sphere: sac, draw", _sphere))
        if n == "Wayfarer's Bauble" and game.mana_available(pl) >= 2:
            def _bauble(perm=perm):
                game.pay_mana(pl, 2, {})
                game.sacrifice(pl, perm)
                found = game.search_library(pl, lambda c: c.is_land and "Basic" in c.supertypes, 1, to_hand=False)
                if found:
                    found[0].tapped = True
            acts.append(("Bauble: fetch basic", _bauble))
        if n == "Terramorphic Expanse":
            def _expanse(perm=perm):
                game.sacrifice(pl, perm)
                found = game.search_library(pl, lambda c: c.is_land and "Basic" in c.supertypes, 1, to_hand=False)
                if found:
                    found[0].tapped = True
            acts.append(("Expanse: fetch basic", _expanse))
        if n == "Myriad Landscape" and game.mana_available(pl) >= 2:
            def _myriad(perm=perm):
                game.pay_mana(pl, 2, {})
                game.sacrifice(pl, perm)
                found = game.search_library(pl, lambda c: c.is_land and "Basic" in c.supertypes, 2, to_hand=False)
                for f in found:
                    f.tapped = True
            acts.append(("Myriad: fetch 2 basics", _myriad))
        if n == "The Autonomous Furnace" and game.mana_available(pl) >= 2:
            def _furnace(perm=perm):
                game.pay_mana(pl, 1, {"R": 1})
                game.sacrifice(pl, perm)
                game.draw(pl, 1)
            acts.append(("Furnace: sac, draw", _furnace))
        if n == "Terrain Generator" and game.mana_available(pl) >= 2:
            basics = [c for c in pl.hand if c.is_land and "Basic" in c.supertypes]
            if basics:
                def _terrain(perm=perm, c=basics[0]):
                    game.pay_mana(pl, 2, {})
                    perm.tapped = True
                    pl.hand.remove(c)
                    pl.battlefield.append(Permanent(card=c, controller=pl, owner=pl))
                acts.append(("Terrain Generator: land", _terrain))
        if n == "Idol of Oblivion" and pl.tokens_created_turn:
            def _idol(perm=perm):
                perm.tapped = True
                game.draw(pl, 1)
            acts.append(("Idol: draw", _idol))
        if n == "Idol of Oblivion" and game.mana_available(pl) >= 8:
            def _eldrazi(perm=perm):
                game.pay_mana(pl, 8, {})
                game.sacrifice(pl, perm)
                game.create_token(pl, "Eldrazi", 10, 10, types={"Creature", "Eldrazi"},
                                  abilities={"annihilator"}, colors=set())
            acts.append(("Idol: Eldrazi", _eldrazi))
        if n == "Siege-Gang Commander" and game.mana_available(pl) >= 2:
            gobs = [q for q in pl.battlefield if q.is_creature() and q is not perm and "Goblin" in q.card.name]
            if gobs:
                def _sgc(perm=perm, g=gobs[0]):
                    game.pay_mana(pl, 1, {"R": 1})
                    game.sacrifice(pl, g)
                    # 2 damage to any target: prefer a player
                    tgt = min(game.opponents(pl), key=lambda o: o.life)
                    game.deal_damage(perm, tgt, 2)
                acts.append(("Siege-Gang: 2 dmg", _sgc))
        if n == "Koth, Fire of Resistance" and perm.counters.get("loyalty", 0) >= 2:
            def _koth_plus(perm=perm):
                perm.counters["loyalty"] -= 2
                game.search_library(pl, lambda c: c.name == "Mountain", 1)
            acts.append(("Koth +2: Mountain", _koth_plus))
        if n == "Saheeli, the Gifted" and perm.counters.get("loyalty", 0) >= 1:
            def _saheeli_servo(perm=perm):
                perm.counters["loyalty"] -= 1
                game.create_token(pl, "Servo", 1, 1, types={"Artifact", "Creature", "Servo"}, colors=set())
            acts.append(("Saheeli +1: Servo", _saheeli_servo))
            def _saheeli_affinity(perm=perm):
                perm.counters["loyalty"] -= 1
                n_art = sum(1 for q in pl.battlefield if q.card.is_artifact)
                game.flags[f"{pl.name}_affinity_next"] = n_art
                game.add_turn_effect("turn", lambda: game.flags.pop(f"{pl.name}_affinity_next", None))
            acts.append(("Saheeli +1: affinity", _saheeli_affinity))
        if n == "The Fire Crystal" and game.mana_available(pl) >= 6:
            targets = [q for q in pl.battlefield if q.is_creature() and q is not perm]
            if targets:
                def _firecrystal(perm=perm, tgt=targets[0]):
                    game.pay_mana(pl, 4, {"R": 2})
                    perm.tapped = True
                    tok = game.create_token(pl, f"Copy of {tgt.name}", tgt.power(game), tgt.toughness(game),
                                      types=set(tgt.card.types), abilities=set(tgt.card.keywords),
                                      colors=set(tgt.card.colors))
                    tok.sac_at_eot = True
                    game.end_of_turn_delayed.append(lambda tok=tok: game.sacrifice(pl, tok))
                acts.append(("Fire Crystal: copy", _firecrystal))
        if n == "Skirk Prospector":
            gobs = [q for q in pl.battlefield if q.is_creature() and q is not perm and "Goblin" in q.card.name]
            if gobs:
                def _skirk(perm=perm, g=gobs[0]):
                    game.sacrifice(pl, g)
                    game.add_mana(pl, "R", 1)
                acts.append(("Skirk: sac goblin, R", _skirk))
    from .generic import generic_activatable
    acts += generic_activatable(game, pl)
    from .terra import activatable as terra_activatable
    acts += terra_activatable(game, pl)
    return acts


# ---------------------------------------------------------------------------
# Equipment modifiers
# ---------------------------------------------------------------------------

def anthem_power_mod(game: Game, perm: Permanent) -> int:
    """Obelisk of Urd: +2/+2 to chosen-type (Goblin) creatures."""
    if "Goblin" not in perm.card.types and "Goblin" not in perm.card.subtypes:
        return 0
    n = sum(1 for q in perm.controller.battlefield if q.card.name == "Obelisk of Urd")
    return 2 * n


def anthem_toughness_mod(game: Game, perm: Permanent) -> int:
    if "Goblin" not in perm.card.types and "Goblin" not in perm.card.subtypes:
        return 0
    n = sum(1 for q in perm.controller.battlefield if q.card.name == "Obelisk of Urd")
    return 2 * n


def equipment_power_mod(game: Game, eq: Permanent, bearer: Permanent) -> int:
    if eq.card.name == "Skullclamp":
        return 1
    return 0


def equipment_toughness_mod(game: Game, eq: Permanent, bearer: Permanent) -> int:
    if eq.card.name == "Skullclamp":
        return -1
    return 0
