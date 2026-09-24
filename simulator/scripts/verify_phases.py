"""Verification suite: the engine against the Comprehensive Rules.

1. Phase/step order per CR 500-514 for all 4 players over 2 full turns
2. Stack LIFO + counterspells (CR 405/608/701.5)
3. Commander tax (903.8) and command-zone return (903.9a)
4. State-based actions: lethal damage (704.5g), legend rule (704.5j)
5. London mulligan (103.5)
6. Cleanup discard to max hand size (514)

Usage: python simulator/scripts/verify_phases.py [--seed N] [--turns 2]
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.join(__file__, ".."))))

from engine import rules as R
from engine.oracle import Oracle, Pool
from engine.game import Game, Permanent
from engine.ai import AI

ORACLE = Oracle()  # loaded once: 35k-card DB parse is expensive
PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name} {detail}")


def make_game(seed: int = 7, turns: int = 2):
    oracle = ORACLE
    deck = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures", "sample_deck.py")
    pool = Pool(oracle, deck)
    g = Game(pool.decklist(), pool.commander, seed=seed,
             ais=[AI("A"), AI("B"), AI("C"), AI("D")],
             max_turns=turns, log_fn=None, oracle=oracle)
    return g


def test_phase_order():
    print("[1] Phase/step order (CR 500-514), 4 players, 2 turns")
    g = make_game()
    g.setup()
    g.run_game()
    got = []
    for ln in g.log_lines:
        t = ln.strip()
        m = re.match(r"^([A-Za-z]+) step \(CR (\d+)\)", t)
        if m:
            got.append(m.group(1))
            continue
        m2 = re.match(r"^\[(Main1|Main2) phase \(CR (\d+)\)\]", t)
        if m2:
            got.append(m2.group(1))
    expected = ["Untap", "Upkeep", "Draw", "Main1", "BeginCombat", "DeclareAttackers",
                "DeclareBlockers", "CombatDamage", "EndCombat", "Main2", "EndStep", "Cleanup"] * (2 * 4)
    check("exactly %d steps logged" % (2 * 4 * 12), len(got) == 2 * 4 * 12, f"got {len(got)}")
    check("step sequence matches CR schema for all players", got == expected,
          f"first mismatch: {got[:20]}")


def test_stack_lifo():
    print("[2] Stack LIFO + counterspell (CR 405.1/608.2/701.5)")
    g = make_game(turns=1)
    g.setup()
    p1, p2 = g.players[0], g.players[1]
    # give p1 a sorcery, p2 a counterspell
    sorc = next((c for c in p1.library + p1.hand
                  if c.is_sorcery and c.name in ("Song of Totentanz", "Seething Song", "Battle Hymn",
                                                 "Krenko's Command", "Dragon Fodder", "Brightstone Ritual",
                                                 "Windfall", "Empty the Warrens")), None)
    if sorc is None:
        sorc = ORACLE.require("Song of Totentanz")
    if sorc not in p1.hand:
        p1.hand.append(sorc)
    for c in list(p1.hand):
        if c is not sorc:
            p1.hand.remove(c)
    offer = next((c for c in p2.library + p2.hand if c.name == "An Offer You Can't Refuse"), None)
    if offer is None:
        offer = ORACLE.require("An Offer You Can't Refuse")
    if offer not in p2.hand:
        p2.hand.append(offer)
    # give both players mana sources
    for pp in (p1, p2):
        for name in ("Mountain", "Mountain", "Mountain", "Mountain", "Island", "Island", "Island", "Island"):
            c = next((x for x in pp.library if x.name == name), None)
            if c is None:
                c = ORACLE.require(name)
            if c in pp.library:
                pp.library.remove(c)
            pp.battlefield.append(Permanent(card=c, controller=pp, owner=pp))
    # P1 casts at sorcery speed in own main
    g.active = p1
    g.current_phase = "Main1"
    g.current_step = "Main1"
    ok1 = g.cast_spell(p1, sorc)
    check("P1 cast sorcery", ok1)
    check("sorcery on stack", len(g.stack) == 1 and g.stack[0].card is sorc)
    # P2 responds with counter (instant speed)
    ok2 = g.cast_spell(p2, offer, targets=[sorc])
    check("P2 cast counterspell in response", ok2)
    check("two objects on stack", len(g.stack) == 2)
    check("counter is on top (LIFO)", g.stack[-1].card is offer)
    g.resolve_top()
    check("counter resolved first; countered spell removed", len(g.stack) == 0)
    check("countered sorcery in graveyard", sorc in p1.graveyard)
    check("countered spell's controller got 2 Treasures", any(q.card.name == "Treasure" for q in p1.battlefield))


def test_commander_tax():
    print("[3] Commander tax (903.8) + command zone return (903.9a)")
    g = make_game(turns=1)
    g.setup()
    p1 = g.players[0]
    commander = p1.commander
    for name in ["Plains"] * 8:
        land = next((c for c in p1.library + p1.hand if c.name == name), None)
        if land is None:
            land = ORACLE.require(name)
        if land in p1.library:
            p1.library.remove(land)
        elif land in p1.hand:
            p1.hand.remove(land)
        perm = Permanent(card=land, controller=p1, owner=p1)
        p1.battlefield.append(perm)
    ok = g.cast_spell(p1, commander, from_zone="command")
    check("first commander cast from command zone", ok)
    check("tax incremented to 2 (903.8)", p1.commander_tax == 2, str(p1.commander_tax))
    g.resolve_top()
    check("commander on battlefield", any(q.card.name == commander.name for q in p1.battlefield))
    perm = next(q for q in p1.battlefield if q.card.name == commander.name)
    g.destroy(perm, "test")
    check("commander returned to command zone", commander in p1.command_zone)
    for q in p1.battlefield:
        q.tapped = False
    base = commander.mana_cost.cmc()
    cost2 = g.cost_of(p1, commander, from_zone="command")
    check("second cast costs mana value plus tax", cost2.cmc() == base + 2, f"cmc={cost2.cmc()} base={base}")
    ok2 = g.cast_spell(p1, commander, from_zone="command")
    check("second cast succeeds", ok2)
    check("tax now 4", p1.commander_tax == 4, str(p1.commander_tax))


def test_sba():
    print("[4] State-based actions: lethal damage (704.5g), legend rule (704.5j)")
    g = make_game(turns=1)
    g.setup()
    p1 = g.players[0]
    commander = p1.commander
    perm = Permanent(card=commander, controller=p1, owner=p1)
    p1.battlefield.append(perm)
    perm.damage = 2
    g.check_sba_and_triggers()
    check("lethal damage destroys the commander", perm not in p1.battlefield)
    copy = ORACLE.require(commander.name)
    a = Permanent(card=copy, controller=p1, owner=p1)
    b = Permanent(card=copy, controller=p1, owner=p1)
    p1.battlefield.append(a)
    p1.battlefield.append(b)
    g.check_sba_and_triggers()
    check("legend rule leaves one copy",
          len([q for q in p1.battlefield if q.card.name == commander.name]) == 1)


def test_mulligan():
    print("[5] London mulligan hand sizes (103.5)")
    g = make_game(turns=1)
    g.setup()
    sizes = set()
    for _ in range(12):
        gg = make_game()
        gg.setup()
        for p in gg.players:
            sizes.add(len(p.hand))
    check("hand sizes 0-7 (London 103.5)", sizes <= {0, 1, 2, 3, 4, 5, 6, 7}, str(sizes))


def test_cleanup():
    print("[6] Cleanup discard to max hand size (514)")
    g = make_game(turns=2)
    g.setup()
    p1 = g.players[0]
    p1.hand = [p1.library.pop() for _ in range(len(p1.hand))]
    for _ in range(3):
        if p1.library:
            p1.hand.append(p1.library.pop())
    g.active = p1
    g.run_step(p1, "Cleanup", "514")
    check("discarded to 7", len(p1.hand) == 7, f"hand={len(p1.hand)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--turns", type=int, default=2)
    args = ap.parse_args()
    R.MAX_TURNS = args.turns
    test_phase_order()
    test_stack_lifo()
    test_commander_tax()
    test_sba()
    test_mulligan()
    test_cleanup()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
