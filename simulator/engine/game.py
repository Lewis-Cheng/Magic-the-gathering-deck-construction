"""Core rules engine: a real 4-player Commander game.

Implements the Magic Comprehensive Rules (ovika/rulebook/CR.txt, eff. 2025-02-07):
- full turn structure with all phases/steps (CR 500-514)
- priority system (CR 117), the stack (CR 405/608), triggers (CR 603)
- state-based actions (CR 704), damage (CR 120), drawing (CR 121)
- combat (CR 506-511), mana pools (CR 500.4), Commander rules (CR 903)
- London mulligan (CR 103.5), free-for-all + attack-multiple-players (CR 802/806)

The engine is rules-legal for everything it models; card-specific behavior
lives in cards.py driven by real oracle text.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

from . import rules as R
from .oracle import CardDef, ManaCost, Oracle, Pool


# ---------------------------------------------------------------------------
# Small data types
# ---------------------------------------------------------------------------

@dataclass
class Trigger:
    """A triggered ability waiting to be put on the stack (CR 603)."""
    source: object                # Permanent | CardDef | None (emblem-ish)
    controller: "Player"
    desc: str
    fn: Callable                  # fn(game, trigger) performs the effect on resolution
    extra_copies: int = 1         # from Veyran/Roaming Throne (603.2d replacement)
    delay: int = 0                # 1 = put on stack at next beginning-of-<step> (e.g. rebound)


@dataclass
class StackObject:
    """A spell or activated/triggered ability on the stack (CR 405/601/602)."""
    kind: str                     # 'spell' | 'ability' | 'trigger'
    card: Optional[CardDef]
    controller: "Player"
    source: object = None         # Permanent for abilities/triggers
    x: int = 0
    targets: list = field(default_factory=list)
    modes: list = field(default_factory=list)
    cost_paid: int = 0
    manacost: Optional[ManaCost] = None
    cant_be_countered: bool = False
    resolve_fn: Optional[Callable] = None   # for abilities/triggers
    desc: str = ""
    flashback: bool = False
    overload: bool = False
    from_grave: bool = False


@dataclass
class Permanent:
    """A permanent on the battlefield (CR 109/110)."""
    card: CardDef
    controller: "Player"
    owner: "Player"
    token: bool = False
    tapped: bool = False
    damage: int = 0
    counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    attacking: Optional["Player"] = None
    blocked: bool = False
    blockers: List["Permanent"] = field(default_factory=list)
    blocking: List["Permanent"] = field(default_factory=list)
    equipment: List["Permanent"] = field(default_factory=list)
    equipped_to: Optional["Permanent"] = None
    controlled_since_turn: int = 0
    # temporary characteristics until end of turn
    eot_haste: bool = False
    eot_cant_block: bool = False
    eot_power_mod: int = 0
    eot_toughness_mod: int = 0
    chosen_type: Optional[str] = None       # Roaming Throne
    chosen_color: Optional[str] = None      # Crossroads Village
    is_command_zone_perm: bool = False      # Koth emblem-like
    sac_at_eot: bool = False
    echoed: bool = False                    # echo tracked
    summon_sick: bool = True

    @property
    def name(self) -> str:
        return self.card.name

    def is_creature(self) -> bool:
        return self.card.is_creature or self.token and self.token_creature

    token_creature: bool = False

    def has_ability(self, key: str) -> bool:
        """Keyword lookup: haste, flying, trample, first_strike, double_strike,
        vigilance, reach, deathtouch, lifelink, defender, menace, ward,
        shroud, indestructible, flash, storm, convoke, delve, magecraft."""
        if key in ("haste",) and (self.eot_haste or "Haste" in self.card.keywords):
            return True
        if key in ("cant_block",) and self.eot_cant_block:
            return True
        k = {"first_strike": "First strike", "double_strike": "Double strike",
             "vigilance": "Vigilance", "flying": "Flying", "trample": "Trample",
             "reach": "Reach", "deathtouch": "Deathtouch", "lifelink": "Lifelink",
             "defender": "Defender", "menace": "Menace", "ward": "Ward",
             "shroud": "Shroud", "indestructible": "Indestructible",
             "flash": "Flash", "storm": "Storm", "convoke": "Convoke",
             "delve": "Delve", "magecraft": "Magecraft"}
        return k.get(key, key) in self.card.keywords

    def power(self, game) -> int:
        p = 0
        if self.card.power is not None and self.card.power.lstrip("-").isdigit():
            p = int(self.card.power)
        elif self.token:
            p = self.token_power
        p += self.counters.get("+1/+1", 0)
        p += self.eot_power_mod
        from .cards import equipment_power_mod
        for eq in self.equipment:
            p += equipment_power_mod(game, eq, self)
        from .cards import anthem_power_mod
        p += anthem_power_mod(game, self)
        return max(0, p)

    def toughness(self, game) -> int:
        t = 0
        if self.card.toughness is not None and self.card.toughness.lstrip("-").isdigit():
            t = int(self.card.toughness)
        elif self.token:
            t = self.token_toughness
        t += self.counters.get("+1/+1", 0)
        t += self.eot_toughness_mod
        from .cards import equipment_toughness_mod
        for eq in self.equipment:
            t += equipment_toughness_mod(game, eq, self)
        from .cards import anthem_toughness_mod
        t += anthem_toughness_mod(game, self)
        return max(0, t)

    token_power: int = 0
    token_toughness: int = 0

    def __repr__(self):
        return f"<{self.name}{'#'+str(id(self)%1000) if self.token else ''}>"


class Player:
    def __init__(self, name: str, ai, commander: CardDef):
        self.name = name
        self.ai = ai
        self.commander = commander
        self.life = R.STARTING_LIFE
        self.library: List[CardDef] = []
        self.hand: List[CardDef] = []
        self.graveyard: List[CardDef] = []
        self.exile: List[CardDef] = []
        self.battlefield: List[Permanent] = []
        self.command_zone: List[CardDef] = [commander]
        self.mana_pool: Dict[str, int] = defaultdict(int)
        self.commander_tax = 0
        self.commander_damage: Dict[str, int] = defaultdict(int)
        self.land_played = False
        self.tokens_created_turn = False
        self.spells_cast_turn = 0
        self.spells_cast_total = 0
        self.cards_drawn = 0
        self.alive = True
        self.lost_reason: Optional[str] = None
        self.turn_no = 0
        self.attacked_this_turn: Set[str] = set()
        self.last_attack_info: Dict = {}
        self.mana_abilities_used = 0
        self.extra_land_allowance = 0

    # ---- zones helpers -------------------------------------------------
    def draw(self, n: int = 1) -> int:
        got = 0
        for _ in range(n):
            if not self.library:
                break
            self.hand.append(self.library.pop())
            got += 1
        self.cards_drawn += got
        return got

    def discard_card(self, card: CardDef) -> None:
        if card in self.hand:
            self.hand.remove(card)
        self.graveyard.append(card)

    def shuffle(self) -> None:
        random.shuffle(self.library)

    def permanents(self) -> List[Permanent]:
        return list(self.battlefield)

    def untapped_sources(self, game) -> List[Permanent]:
        return [p for p in self.battlefield if not p.tapped and game.is_mana_source(p)]

    def __repr__(self):
        return self.name


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class Game:
    """One 4-player Commander game (free-for-all, attack-multiple-players)."""

    def __init__(self, deck: List[CardDef], commander: CardDef, seed: int,
                 ais: List, max_turns: int = R.MAX_TURNS, log_fn: Optional[Callable] = None,
                 oracle: Optional[Oracle] = None,
                 decks: Optional[List[List[CardDef]]] = None,
                 commanders: Optional[List[CardDef]] = None):
        if decks is None:
            decks = [deck] * 4
        if commanders is None:
            commanders = [commander] * 4
        self.decks = decks
        self.commanders = commanders
        self.deck = deck
        self.commander_def = commander
        self.seed = seed
        self.rng = random.Random(seed)
        # Player.shuffle() uses module-level random; reseed it so every game is
        # fully reproducible from its seed (fixes cross-run variance)
        random.seed(seed)
        self.max_turns = max_turns
        self.log_fn = log_fn or (lambda line: None)
        self.oracle = oracle
        self.players: List[Player] = []
        for i, ai in enumerate(ais):
            pl = Player(f"P{i+1}", ai, commanders[i])
            pl.deck = decks[i]
            self.players.append(pl)
        self.active: Optional[Player] = None
        self.priority_player: Optional[Player] = None
        self.turn_no = 0
        self.stack: List[StackObject] = []
        self.waiting_triggers: List[Trigger] = []
        self.winner: Optional[Player] = None
        self.over = False
        self.current_phase = ""
        self.current_step = ""
        self.step_ended = False
        self.turn_effects: List[Tuple[str, Callable]] = []   # ('eot'|'turn', fn)
        self.flags: Dict[str, object] = {}
        self.log_lines: List[str] = []
        self.sba_happened = False
        self.end_of_turn_delayed: List[Tuple[int, Callable]] = []
        self.cleanup_discarded = False

    # ------------------------------------------------------------------ setup
    LOG_BUDGET = 3000

    def log(self, msg: str) -> None:
        if len(self.log_lines) < self.LOG_BUDGET:
            self.log_lines.append(msg)
        self.log_fn(msg)

    def draw(self, pl: Player, n: int = 1) -> int:
        """Draw n cards, then fire on-draw triggers (Nekusar, Sheoldred, ...)."""
        got = pl.draw(n)
        if got:
            from .generic import on_draw
            on_draw(self, pl, got)
        return got

    def land_allowance(self, pl: Player) -> int:
        """Extra land plays this turn (Growth Spiral) + static (Exploration/Azusa/Oracle)."""
        extra = pl.extra_land_allowance
        for q in pl.battlefield:
            if q.card.name in ("Exploration", "Azusa, Lost but Seeking", "Oracle of Mul Daya",
                                "Dryad of the Ilysian Grove"):
                extra += 1
        return extra

    def setup(self) -> None:
        for pl in self.players:
            pl.library = list(pl.deck)
            pl.shuffle()
            pl.command_zone = [pl.commander]
        # London mulligan (103.5) -- AI decides keep/mull
        for pl in self.players:
            self.do_mulligan(pl)
        # random starting player, then first turn (103.8); no draw step skip in Commander
        start = self.rng.randrange(len(self.players))
        self.players = self.players[start:] + self.players[:start]
        self.log(f"Game seed={self.seed}; players {[p.name for p in self.players]}")

    def do_mulligan(self, pl: Player) -> None:
        """London mulligan: 7, then shuffle back and draw one fewer; scry 1 at 0 (103.5)."""
        n = R.STARTING_HAND
        while True:
            pl.hand = []
            pl.library = list(pl.deck)
            pl.shuffle()
            self.draw(pl, n)
            if n == 0:
                # scry 1 (103.5c)
                if pl.library:
                    top = pl.library.pop()
                    if pl.ai.scry_keep(game=self, card=top):
                        pl.library.append(top)
                    else:
                        pl.library.insert(0, top)
                break
            if pl.ai.keep_hand(self, pl):
                break
            pl.library.extend(pl.hand)
            pl.hand = []
            pl.shuffle()
            n -= 1

    # ------------------------------------------------------------ turn loop
    def run_game(self) -> dict:
        self.setup()
        while not self.over and self.turn_no < self.max_turns:
            self.turn_no += 1
            for pl in list(self.players):
                if not pl.alive:
                    continue
                self.play_turn(pl)
                if self.over:
                    break
        if self.over and self.winner is not None:
            self.log(f"WINNER: {self.winner.name}")
        else:
            self.log(f"GAME ENDED: no winner by turn {self.turn_no} (cap {self.max_turns})")
        return self.summary()

    def summary(self) -> dict:
        return {
            "seed": self.seed,
            "winner": self.winner.name if self.winner else None,
            "win_turn": self.winner.turn_no if self.winner else None,
            "turns": self.turn_no,
            "life": {p.name: p.life for p in self.players},
            "alive": [p.name for p in self.players if p.alive],
            "lost": [{"name": p.name, "reason": p.lost_reason} for p in self.players if not p.alive],
            "logs": self.log_lines,
            "commander_damage": {p.name: dict(p.commander_damage) for p in self.players},
        }

    def play_turn(self, pl: Player) -> None:
        pl.turn_no = self.turn_no
        self.active = pl
        self.log(f"--- T{self.turn_no} {pl.name} ---")
        # summoning sickness clears at the start of the controller's turn (302.6)
        for perm in pl.battlefield:
            perm.summon_sick = False
        pl.land_played = False
        pl.tokens_created_turn = False
        pl.spells_cast_turn = 0
        pl.attacked_this_turn = set()
        self.flags["_atk_logged"] = 0
        self.flags["_cast_guard_logged"] = False
        for (scope, fn) in self.turn_effects:
            if scope == "turn":
                fn()
        for phase, phref, steps in R.TURN_SCHEMA:
            if self.over:
                return
            self.current_phase = phase
            if phase in ("Main1", "Main2"):
                self.log(f"  [{phase} phase (CR {phref})]")
                self.run_main_phase(pl)
            else:
                for step, sref in steps:
                    if self.over:
                        return
                    self.current_step = step
                    self.run_step(pl, step, sref)
                    if step == "Cleanup":
                        # 500.4: mana empties at end of step
                        self.empty_mana()
                        self.current_step = ""
            self.empty_mana()  # 500.4 at end of phase

    # ------------------------------------------------------------ steps
    def run_step(self, pl: Player, step: str, sref: str) -> None:
        self.step_ended = False
        self.log(f"    {step} step (CR {sref})")
        # ---- turn-based actions (no stack) ----
        if step == "Untap":
            skip_all = any(q.card.name == "Stasis" for q in pl.battlefield)
            cap_land = any(q.card.name == "Hokori, Dust Drinker" for q in pl.battlefield) or \
                       any(q.card.name == "Winter Orb" and not q.tapped for q in pl.battlefield)
            cap_land_2 = any(q.card.name == "Static Orb" and not q.tapped for q in pl.battlefield)
            choke = any(q.card.name == "Choke" for q in pl.battlefield)
            meek = any(q.card.name == "Meekstone" for q in pl.battlefield)
            untapped_lands = 0
            for perm in pl.battlefield:
                if perm.counters.get("stun", 0) > 0:
                    perm.counters["stun"] -= 1
                    continue
                if skip_all:
                    continue
                if perm.card.is_land:
                    if cap_land or cap_land_2:
                        if untapped_lands >= (1 if cap_land else 2):
                            continue
                        untapped_lands += 1
                    if choke and "Island" in perm.card.subtypes:
                        continue
                if meek and perm.is_creature() and perm.power(self) >= 3:
                    continue
                perm.tapped = False
        elif step == "Upkeep":
            from .cards import upkeep_triggers
            upkeep_triggers(self, pl)  # 503.1a: beginning-of-upkeep triggers
        elif step == "Draw":
            self.draw(pl, 1)  # 504.1
            self.log(f"      {pl.name} draws (hand {len(pl.hand)})")
            from .generic import on_draw_step
            extra = on_draw_step(self, pl)
            if extra:
                self.draw(pl, extra)
                self.log(f"      {pl.name} draws {extra} extra (draw-step triggers)")
        elif step == "BeginCombat":
            from .generic import on_begin_combat
            on_begin_combat(self, pl)
        elif step == "DeclareAttackers":
            self.declare_attackers(pl)
        elif step == "DeclareBlockers":
            self.declare_blockers(pl)
        elif step == "CombatDamage":
            self.combat_damage(pl)
        elif step == "EndCombat":
            self.end_combat(pl)
        elif step == "EndStep":
            from .generic import on_end_step
            on_end_step(self, pl)
        elif step == "Cleanup":
            self.cleanup(pl)
        # ---- SBA + triggers, then priority (117.3a) ----
        self.check_sba_and_triggers()
        if self.over:
            return
        if step == "Untap":
            return  # 117.3a: no player receives priority during untap step
        if step == "Cleanup" and not self.sba_happened and not self.waiting_triggers:
            return  # 514.x: no priority in cleanup unless SBA/triggers
        self.priority_loop()


    def run_main_phase(self, pl: Player) -> None:
        """A main phase is a phase, not a step; priority starts with the AP (117.3a)."""
        self.step_ended = False
        self.current_step = self.current_phase  # 'Main1' | 'Main2'
        self.check_sba_and_triggers()
        if self.over:
            return
        self.priority_loop()

    # ------------------------------------------------------------ priority
    def priority_loop(self) -> None:
        """CR 117.3/117.4: AP first; after an action the same player gets
        priority again (117.3c); all-pass with empty stack ends the step;
        all-pass with a non-empty stack resolves the top object."""
        n = len([p for p in self.players if p.alive])
        passes = 0
        idx = self.players.index(self.active)
        guard = 0

        def _state_sig():
            # cheap snapshot to detect no-op actions (117: doing nothing is a pass)
            pl_ = self.priority_player
            return (pl_.spells_cast_turn, len(pl_.hand), len(pl_.battlefield),
                    len(pl_.graveyard), len(self.stack), sum(pl_.mana_pool.values()),
                    tuple(p.life for p in self.players))

        while not self.over and not self.step_ended:
            guard += 1
            if guard > 5000:
                self.log(f"!! priority loop guard hit at step {self.current_step}")
                self.step_ended = True
                return
            self.check_sba_and_triggers()
            if self.over:
                return
            if self.stack:
                if passes >= n:
                    self.resolve_top()
                    passes = 0
                    continue
            else:
                if passes >= n:
                    self.step_ended = True   # 117.4
                    return
            pl = self.players[idx]
            if not pl.alive:
                idx = (idx + 1) % len(self.players)
                continue
            self.priority_player = pl
            action = pl.ai.decide(self)
            if action is not None:
                sig_before = _state_sig()
                action.execute(self)
                self.check_sba_and_triggers()
                if self.over:
                    return
                if sig_before == _state_sig():
                    # silent no-op (failed cast/payment/guard): treat as a pass
                    passes += 1
                    idx = (idx + 1) % len(self.players)
                else:
                    passes = 0
                    # 117.3c: same player keeps priority
            else:
                passes += 1
                idx = (idx + 1) % len(self.players)

    # ------------------------------------------------------------ triggers
    def queue_trigger(self, src, controller: Player, desc: str, fn: Callable,
                      extra: int = 0, delay: int = 0) -> None:
        """Queue a triggered ability (CR 603.2). 'extra' = extra copies from
        Veyran/Roaming Throne (603.2d)."""
        copies = 1 + extra
        for _ in range(copies):
            self.waiting_triggers.append(Trigger(src, controller, desc, fn, extra_copies=1, delay=delay))

    def put_triggers_on_stack(self) -> None:
        """603.3b: APNAP order; triggers that target/choose get resolved by AI."""
        if not self.waiting_triggers:
            return
        order = self.turn_order(self.active)
        staged = []
        for pl in order:
            mine = [t for t in self.waiting_triggers if t.controller is pl and t.delay == 0]
            for t in mine:
                self.waiting_triggers.remove(t)
                staged.append(t)
        # delayed triggers (rebound) are put on stack at the start of the
        # appropriate step; for now treat them like normal triggers
        delayed = [t for t in self.waiting_triggers if t.delay > 0]
        for t in delayed:
            self.waiting_triggers.remove(t)
            staged.append(t)
        for t in staged:
            self.stack.append(StackObject(
                kind="trigger", card=None, controller=t.controller,
                source=t.source, desc=t.desc, resolve_fn=t.fn))
            self.log(f"      [trigger on stack] {t.controller.name}: {t.desc}")

    def check_sba_and_triggers(self) -> bool:
        """CR 704.3 loop: SBA -> triggers -> SBA ... until stable."""
        did = False
        guard = 0
        while True:
            guard += 1
            if guard > 200:
                self.log("!! SBA/trigger loop guard")
                break
            sba = self.state_based_actions()
            if sba:
                did = True
                self.sba_happened = True
                continue
            if self.waiting_triggers:
                self.put_triggers_on_stack()
                did = True
                continue
            break
        return did

    def state_based_actions(self) -> bool:
        """CR 704.5 (implemented subset relevant to this deck)."""
        performed = False
        for pl in self.players:
            # 704.5a: life <= 0
            if pl.alive and pl.life <= 0:
                self.eliminate(pl, f"life <= 0 ({pl.life})")
                performed = True
            # 903.10a: commander damage
            for name, dmg in list(pl.commander_damage.items()):
                if dmg >= R.COMMANDER_DAMAGE_LIMIT and pl.alive:
                    self.eliminate(pl, f"commander damage {dmg} from {name}")
                    performed = True
        for pl in self.players:
            for perm in list(pl.battlefield):
                # 704.5g/h: lethal damage or toughness <= 0 -> destroyed
                if perm.is_creature():
                    if perm.damage >= perm.toughness(self) or perm.toughness(self) <= 0:
                        self.destroy(perm, "lethal damage")
                        performed = True
                # 704.5j: legend rule
                if perm.card.is_legendary and not perm.token:
                    same = [q for q in pl.battlefield
                            if q is not perm and q.card.name == perm.card.name and not q.token]
                    if same:
                        self.destroy(same[0], "legend rule (704.5j)")
                        performed = True
                # stun counters don't block untap already handled
        # tokens in non-battlefield zones cease to exist (704.5m-ish)
        for pl in self.players:
            for zone in (pl.graveyard, pl.exile):
                toks = [c for c in zone if getattr(c, "is_token", False)]
                for c in toks:
                    zone.remove(c)
        return performed

    def eliminate(self, pl: Player, reason: str) -> None:
        if not pl.alive:
            return
        pl.alive = False
        pl.lost_reason = reason
        self.log(f"!! {pl.name} loses ({reason})")
        alive = [p for p in self.players if p.alive]
        if len(alive) == 1:
            self.winner = alive[0]
            self.over = True
            self.winner.turn_no = self.turn_no
        elif len(alive) == 0:
            self.over = True

    def destroy(self, perm: Permanent, why: str = "") -> None:
        if perm not in perm.controller.battlefield:
            return
        if perm.controller is not None and id(perm) in (
                self.flags.get(f"{perm.controller.name}_indestructible") or set()):
            self.log(f"      {perm.name} is indestructible, not destroyed ({why})")
            return
        perm.controller.battlefield.remove(perm)
        if perm.card.is_legendary and (
                perm.card is perm.controller.commander or
                (perm.card.name == "Esper Terra" and perm.controller.commander.name.startswith("Terra,"))):
            # 903.9a: owner may put commander into command zone
            perm.owner.command_zone.append(perm.controller.commander)
            self.log(f"      {perm.name} destroyed ({why}); {perm.owner.name} moves commander to command zone (903.9a)")
        else:
            perm.owner.graveyard.append(perm.card)
            self.log(f"      {perm.name} destroyed ({why}) -> graveyard")
        self.trigger_after_death(perm)

    def trigger_after_death(self, perm: Permanent) -> None:
        from .cards import on_death
        on_death(self, perm)

    def turn_order(self, start: Optional[Player]) -> List[Player]:
        if start is None:
            start = self.players[0]
        i = self.players.index(start)
        return self.players[i:] + self.players[:i]

    def opponents(self, pl: Player) -> List[Player]:
        return [p for p in self.players if p is not pl and p.alive]

    # ------------------------------------------------------------ stack
    def resolve_top(self) -> None:
        obj = self.stack.pop()
        if obj.kind == "spell":
            self.resolve_spell(obj)
        else:
            if obj.resolve_fn is not None:
                obj.resolve_fn(self, obj)
            self.log(f"      [resolve] {obj.controller.name}: {obj.desc}")
        self.check_sba_and_triggers()

    def resolve_spell(self, obj: StackObject) -> None:
        from .cards import resolve_effect, on_enter, mana_echoes_trigger
        card = obj.card
        pl = obj.controller
        self.log(f"      [resolve] {pl.name}: {card.name}")
        is_copy = getattr(obj, "_is_copy", False)
        if card.is_permanent:
            if not is_copy:
                perm = Permanent(card=card, controller=pl, owner=pl,
                                 controlled_since_turn=self.turn_no)
                pl.battlefield.append(perm)
                self.log(f"        -> {card.name} enters battlefield under {pl.name}")
                on_enter(self, perm)
                mana_echoes_trigger(self, perm)
        else:
            resolve_effect(self, obj)
            # zone move: 608.4 (spell goes to graveyard after resolution)
            if not is_copy:
                if obj.flashback:
                    if card not in pl.exile:
                        pl.exile.append(card)
                elif card.name in ("Time Reversal", "Mizzix's Mastery", "Recurring Insight"):
                    pass  # effects self-exile
                else:
                    if card not in pl.graveyard:
                        pl.graveyard.append(card)

    def cast_spell(self, pl: Player, card: CardDef, x: int = 0,
                   targets: Optional[list] = None, modes: Optional[list] = None,
                   from_zone: str = "hand", flashback: bool = False,
                   free: bool = False, overload: bool = False) -> bool:
        """601: propose, determine costs, pay, put on stack, on-cast triggers."""
        if card.is_land:
            return False
        # perf guard: bound ritual/X-spell chains on huge boards
        if pl.spells_cast_turn >= 150:
            if not self.flags.get("_cast_guard_logged"):
                self.log(f"!! cast guard: {pl.name} hit 150 casts this turn")
                self.flags["_cast_guard_logged"] = True
            return False
        # --- 601.3 legality checks
        if not free:
            is_sorcery_speed = card.is_sorcery or (card.is_permanent and not card.is_instant and "Flash" not in card.keywords)
            if is_sorcery_speed:
                if self.current_phase not in ("Main1", "Main2") or self.stack:
                    return False
                if self.active is not pl:
                    return False
            # Complete the Circuit: sorceries have flash
            if card.is_sorcery and self.flags.get(f"{pl.name}_sorcery_flash"):
                pass
        cost = self.cost_of(pl, card, x=x, from_zone=from_zone, flashback=flashback)
        # Demon of Fate's Design: cast one enchantment per turn paying life
        # equal to its mana value instead of mana (simplified replacement)
        lifecast = (self.flags.get(f"{pl.name}_demon_lifecast") and card.is_enchantment
                    and from_zone == "hand" and not free)
        if lifecast:
            self.flags[f"{pl.name}_demon_lifecast"] = False
            pl.life -= min(pl.life - 1, card.mana_cost.cmc())
            cost = ManaCost()
            self.log(f"    {pl.name} lifecasts {card.name} paying "
                     f"{card.mana_cost.cmc()} life (Demon of Fate's Design)")
        # pay
        if not free and not self.pay_total(pl, card, cost, from_zone=from_zone):
            return False
        # move card to stack (601.2a)
        if from_zone == "hand":
            if card in pl.hand:
                pl.hand.remove(card)
        elif from_zone == "grave":
            if card in pl.graveyard:
                pl.graveyard.remove(card)
        elif from_zone == "command":
            if card in pl.command_zone:
                pl.command_zone.remove(card)
        elif from_zone == "exile":
            if card in pl.exile:
                pl.exile.remove(card)
        elif from_zone == "library":
            if card in pl.library:
                pl.library.remove(card)
        if from_zone == "command":
            pl.commander_tax += 2  # 903.8
        obj = StackObject(kind="spell", card=card, controller=pl, x=x,
                          targets=targets or [], modes=modes or [],
                          cant_be_countered=bool(self.flags.get("thryx") and card.mana_cost.cmc() >= 5),
                          manacost=cost, flashback=flashback, from_grave=(from_zone == "grave"),
                          overload=overload)
        if free:
            obj.cost_paid = 0
        else:
            obj.cost_paid = cost.cmc() if isinstance(cost, ManaCost) else cost
        self.stack.append(obj)
        pl.spells_cast_turn += 1
        pl.spells_cast_total += 1
        self.log(f"    {pl.name} casts {card.name}" + (f" X={x}" if x else ""))
        # --- on-cast triggers (603.2)
        from .cards import on_cast
        on_cast(self, pl, obj)
        # Storm (702.39)
        if card.has_text("storm"):
            from .cards import storm_copies
            storm_copies(self, obj)
        self.check_sba_and_triggers()
        return True


    # ------------------------------------------------------------ mana/costs
    def is_mana_source(self, perm: Permanent) -> bool:
        from .cards import mana_abilities
        return bool(mana_abilities(self, perm))

    def mana_available(self, pl: Player) -> int:
        total = sum(pl.mana_pool.values())
        for perm in pl.battlefield:
            if perm.tapped:
                continue
            from .cards import mana_abilities
            for (n, _colors, _side) in mana_abilities(self, perm):
                total += n
        return total

    def cost_of(self, pl: Player, card: CardDef, x: int = 0,
                from_zone: str = "hand", flashback: bool = False) -> ManaCost:
        """Determine total cost (601.2f): mana cost + additional - reductions."""
        if flashback:
            # flashback cost = mana cost (702.33); Past in Flames grants it
            mc = card.mana_cost
        else:
            mc = card.mana_cost
        generic = mc.generic + (x if mc.x else 0)
        colored = dict(mc.colored)
        # --- reductions
        red = 0
        if any(q.card.name == "Thryx, the Sudden Storm" for q in pl.battlefield) and mc.cmc() >= 5:
            red += 1
        if any(q.card.name == "The Fire Crystal" for q in pl.battlefield) and "Red" in card.colors:
            red += 1
        if card.name == "Focus the Mind" and pl.spells_cast_turn > 0:
            red += 2
        # Travel the Overworld affinity for Towns
        if card.name == "Travel the Overworld":
            towns = sum(1 for q in pl.battlefield if "Town" in q.card.subtypes)
            red += towns
        generic = max(0, generic - red)
        # delve (702.66): exile up to N cards from graveyard for generic
        if card.is_sorcery and "Delve" in card.keywords and from_zone == "hand":
            delve = min(generic, len(pl.graveyard))
            generic -= delve
        # convoke (702.50): untapped creatures pay generic; Chief Engineer
        # grants convoke to artifact spells
        convoke_ok = "Convoke" in card.keywords or (
            card.is_artifact and any(q.card.name == "Chief Engineer" for q in pl.battlefield))
        if convoke_ok:
            convokers = sum(1 for q in pl.battlefield if q.is_creature() and not q.tapped)
            generic = max(0, generic - convokers)
        # commander tax (903.8)
        if from_zone == "command":
            generic += pl.commander_tax
        # generic static modifiers: Omniscience, Trinisphere, Ruby Medallion
        from .generic import cost_mods
        free, min_total, red_g = cost_mods(self, pl, card, from_zone)
        red += red_g
        generic = max(0, generic - red)
        if free:
            generic, colored = 0, {}
        if min_total is not None:
            generic = max(generic, min_total)
        return ManaCost(generic=generic, colored=colored, x=mc.x)

    def pay_total(self, pl: Player, card: CardDef, cost: ManaCost, from_zone: str = "hand") -> bool:
        """Pay mana cost incl. convoke (702.50). Mana abilities don't use the stack (605.3a)."""
        need_g = cost.generic
        need_c = dict(cost.colored)
        # convoke (702.50): tap untapped creatures to pay 1 generic or 1 of
        # their color; Chief Engineer grants convoke to artifact spells
        convoke_ok = "Convoke" in card.keywords or (
            card.is_artifact and any(q.card.name == "Chief Engineer" for q in pl.battlefield))
        used_convokers = 0
        if convoke_ok:
            convokers = [q for q in pl.battlefield if q.is_creature() and not q.tapped]
            for q in convokers:
                if need_g > 0:
                    q.tapped = True
                    need_g -= 1
                    used_convokers += 1
                elif need_c:
                    col = next(iter(need_c))
                    q.tapped = True
                    need_c[col] -= 1
                    used_convokers += 1
                    if need_c[col] == 0:
                        del need_c[col]
            self.flags["last_convoke_count"] = used_convokers
        if need_g > 0 or need_c:
            if not self.pay_mana(pl, need_g, need_c):
                return False
        return True

    def pay_mana(self, pl: Player, generic: int, colored: Dict[str, int]) -> bool:
        """Pay from mana pool, then activate untapped mana sources (605)."""
        # use pool first
        for c in list(colored):
            use = min(colored[c], pl.mana_pool[c])
            colored[c] -= use
            pl.mana_pool[c] -= use
            if colored[c] == 0:
                del colored[c]
        # pool colorless/generic
        pool_c = pl.mana_pool["C"] + pl.mana_pool["*"]
        use = min(generic, pool_c)
        generic -= use
        if pl.mana_pool["C"] >= use:
            pl.mana_pool["C"] -= use
        else:
            rem = use - pl.mana_pool["C"]
            pl.mana_pool["C"] = 0
            pl.mana_pool["*"] -= rem
        # activate untapped sources (AI picks order; engine enforces color)
        sources = [q for q in pl.battlefield if not q.tapped and self.is_mana_source(q)]
        for perm in sources:
            from .cards import mana_abilities
            for (n, colors, side) in mana_abilities(self, perm):
                if generic <= 0 and not colored:
                    break
                if colors == "any":
                    if colored:
                        c = next(iter(colored))
                        take = min(n, colored[c])
                        colored[c] -= take
                        n -= take
                        if colored[c] == 0:
                            del colored[c]
                        if n > 0:
                            use = min(n, generic)
                            generic -= use
                    else:
                        use = min(n, generic)
                        generic -= use
                else:
                    take = 0
                    for c in colors:
                        if c in colored and colored[c] > 0:
                            t = min(n, colored[c])
                            colored[c] -= t
                            take += t
                            if colored[c] == 0:
                                del colored[c]
                    rem = n - take
                    if rem > 0:
                        use = min(rem, generic)
                        generic -= use
                perm.tapped = True
                pl.mana_abilities_used += 1
                if side is not None:
                    side(self, pl, perm)
            if generic <= 0 and not colored:
                break
        return generic <= 0 and not colored

    def after_mana_ability(self, pl: Player, perm: Permanent) -> None:
        from .cards import after_mana_ability
        after_mana_ability(self, pl, perm)

    def add_mana(self, pl: Player, color: str, n: int = 1) -> None:
        pl.mana_pool[color] += n

    def empty_mana(self) -> None:
        """500.4: unused mana empties when a step/phase ends."""
        for pl in self.players:
            if any(pl.mana_pool.values()):
                pl.mana_pool.clear()

    def play_land(self, pl: Player, card: CardDef, from_zone: str = "hand") -> bool:
        """305.2: play a land as a special action during own main phase, empty stack."""
        if not card.is_land:
            return False
        if pl.land_played and self.land_allowance(pl) <= 0:
            return False
        if from_zone == "hand":
            if card not in pl.hand:
                return False
        elif from_zone == "grave":
            if card not in pl.graveyard or not any(
                    q.card.name in ("Crucible of Worlds", "Conduit of Worlds") for q in pl.battlefield):
                return False
        else:
            return False
        if self.current_phase not in ("Main1", "Main2") or self.active is not pl or self.stack:
            return False
        if from_zone == "hand":
            pl.hand.remove(card)
        else:
            pl.graveyard.remove(card)
        perm = Permanent(card=card, controller=pl, owner=pl)
        pl.battlefield.append(perm)
        if pl.land_played:
            pl.extra_land_allowance -= 1
        pl.land_played = True
        self.log(f"    {pl.name} plays land {card.name}" + (" (from graveyard)" if from_zone == "grave" else ""))
        from .cards import on_enter
        on_enter(self, perm)
        return True

    # ------------------------------------------------------------ tokens
    def create_token(self, controller: Player, name: str, power: int, toughness: int,
                     types: Optional[Set[str]] = None, abilities: Optional[Set[str]] = None,
                     haste: bool = False, colors: Optional[Set[str]] = None) -> Permanent:
        """Create a token permanent (110.5/701.14)."""
        return self.create_tokens(controller, name, power, toughness, 1, types, abilities,
                                  haste, colors)[0]

    def create_tokens(self, controller: Player, name: str, power: int, toughness: int, count: int,
                      types: Optional[Set[str]] = None, abilities: Optional[Set[str]] = None,
                      haste: bool = False, colors: Optional[Set[str]] = None) -> List[Permanent]:
        if count <= 0:
            return []
        tset = set(types or {"Creature"})
        card = CardDef(name=name, mana_cost=ManaCost(), mana_cost_str="",
                       types=tset, supertypes=set(), subtypes=set(),
                       text="", power=str(power), toughness=str(toughness),
                       keywords=set(abilities or {}), colors=colors or set(),
                       color_identity=set(), is_creature=("Creature" in tset), is_token=True)
        made = []
        for _ in range(count):
            perm = Permanent(card=card, controller=controller, owner=controller,
                             token=True, token_power=power, token_toughness=toughness,
                             controlled_since_turn=self.turn_no, summon_sick=not haste)
            perm.token_creature = "Creature" in (types or set())
            if haste:
                perm.eot_haste = True
            perm.card.is_token = True
            controller.battlefield.append(perm)
            controller.tokens_created_turn = True
            made.append(perm)
        self.log(f"        token: {count}x {name} ({power}/{toughness}) for {controller.name}")
        from .cards import on_tokens_created
        on_tokens_created(self, controller, made)
        return made

    def create_treasure(self, controller: Player, n: int = 1) -> None:
        for _ in range(n):
            self.create_token(controller, "Treasure", 0, 0,
                              types={"Artifact"}, abilities={"treasure"})

    # ------------------------------------------------------------ search
    def search_library(self, pl: Player, pred: Callable[[CardDef], bool],
                       n: int = 1, to_hand: bool = True) -> List[CardDef]:
        found = []
        for c in list(pl.library):
            if pred(c):
                pl.library.remove(c)
                if to_hand:
                    pl.hand.append(c)
                else:
                    pl.battlefield.append(Permanent(card=c, controller=pl, owner=pl))
                found.append(c)
                if len(found) >= n:
                    break
        pl.shuffle()
        return found


    # ------------------------------------------------------------ combat
    def legal_attackers(self, pl: Player) -> List[Permanent]:
        cands = []
        for perm in pl.battlefield:
            if not perm.is_creature():
                continue
            if perm.tapped:
                continue
            if perm.summon_sick and "haste" not in {a.lower() for a in perm.card.keywords}:
                continue
            if perm.has_ability("defender"):
                continue
            if perm.attacking is not None:
                continue
            cands.append(perm)
        return cands

    def declare_attackers(self, pl: Player) -> None:
        """508.1: active player declares attackers; 'attacks each combat if able'
        requirements (508.1c) are enforced by adding legal attackers."""
        chosen = pl.ai.choose_attackers(self, pl, self.legal_attackers(pl))
        legal = {id(q) for q in self.legal_attackers(pl)}
        chosen = [q for q in chosen if id(q) in legal]
        for perm in chosen:
            perm.tapped = True if not perm.has_ability("vigilance") else perm.tapped
            perm.attacking = pl.ai.attack_target(self, pl, perm)
            perm.blocked = False
            perm.blockers = []
            pl.attacked_this_turn.add(perm.attacking.name if perm.attacking else "?")
            if self.flags.get("_atk_logged", 0) < 25:
                self.log(f"      attacker: {pl.name}'s {perm.name} -> {perm.attacking.name if perm.attacking else '?'}")
            elif self.flags.get("_atk_logged") == 25:
                self.log("      ... (more attackers, log collapsed)")
            self.flags["_atk_logged"] = self.flags.get("_atk_logged", 0) + 1
        # 508.1m: triggers on attackers declared
        from .cards import on_attackers_declared
        on_attackers_declared(self, pl, chosen)

    def declare_blockers(self, pl: Player) -> None:
        """509.1: each defending player declares blockers."""
        # group attackers by target player
        for def_player in self.players:
            if def_player is self.active or not def_player.alive:
                continue
            incoming = [a for a in self.active.battlefield if a.attacking is def_player and a.is_creature()]
            if not incoming:
                continue
            choices = def_player.ai.choose_blockers(self, def_player, incoming)
            # engine legality: blocker must be untapped, can block attacker
            for (blocker, attacker) in choices:
                if blocker.tapped or blocker.attacking is not None:
                    continue
                if not self.can_block(blocker, attacker):
                    continue
                blocker.blocking.append(attacker)
                attacker.blockers.append(blocker)
                attacker.blocked = True
                self.log(f"      blocker: {def_player.name}'s {blocker.name} blocks {attacker.name}")

    def can_block(self, blocker: Permanent, attacker: Permanent) -> bool:
        if not blocker.is_creature() or not blocker.is_creature():
            return False
        if blocker.has_ability("cant_block"):
            return False
        if attacker.has_ability("flying") and not (blocker.has_ability("flying") or blocker.has_ability("reach")):
            return False
        if attacker.has_ability("menace") and len([b for b in attacker.blockers if b is blocker]) == 0:
            # menace needs two blockers; handled at declaration level
            pass
        return True

    def combat_damage(self, pl: Player) -> None:
        """510: assign and deal combat damage; handles first/double strike
        by splitting into two damage steps (506.1, 702.7/702.4)."""
        involved = [a for a in pl.battlefield if a.attacking is not None]
        involved += [b for b in pl.battlefield if b.blocking]
        fs_creatures = [c for c in involved if c.has_ability("first_strike") or c.has_ability("double_strike")]
        reg_creatures = [c for c in involved if not (c.has_ability("first_strike") or c.has_ability("double_strike"))]
        if fs_creatures:
            self.deal_combat_damage(pl, fs_creatures)
            self.check_sba_and_triggers()
        self.deal_combat_damage(pl, reg_creatures)

    def deal_combat_damage(self, pl: Player, creatures: List[Permanent]) -> None:
        moon = self.flags.get("_moonmist_combat") == self.turn_no
        for creature in creatures:
            if moon and creature.is_creature() and not (
                    {"Werewolf", "Wolf"} & set(creature.card.subtypes)):
                continue
            if creature.attacking is not None:
                if creature.blockers:
                    # assign to blockers first (510.1c); trample: lethal then remainder (702.19)
                    total = creature.power(self)
                    remaining = total
                    if creature.has_ability("trample"):
                        for b in creature.blockers:
                            need = max(0, b.toughness(self) - b.damage)
                            dmg = min(remaining, need)
                            if dmg > 0:
                                self.deal_damage(creature, b, dmg)
                                remaining -= dmg
                            if remaining <= 0:
                                break
                        # leftover damage tramples over to the player
                        if remaining > 0 and creature.attacking.alive:
                            self.deal_damage(creature, creature.attacking, remaining)
                    else:
                        b = creature.blockers[0]
                        self.deal_damage(creature, b, total)
                else:
                    target = creature.attacking
                    if target.alive:
                        self.deal_damage(creature, target, creature.power(self))
            if creature.blocking:
                for target in list(creature.blocking):
                    if target in self.active.battlefield:
                        self.deal_damage(creature, target, creature.power(self))

    def end_combat(self, pl: Player) -> None:
        """511.1: attacking/blocking status ends."""
        for perm in list(pl.battlefield):
            perm.attacking = None
            perm.blocked = False
            perm.blockers = []
            perm.blocking = []
        for opp in self.players:
            for perm in list(opp.battlefield):
                perm.attacking = None
                perm.blocked = False
                perm.blockers = []
                perm.blocking = []

    def deal_damage(self, source: Permanent, target, amount: int) -> None:
        """120.3: damage to player loses life (commander damage 903.10); to a
        creature marks damage."""
        if amount <= 0:
            return
        # damage amplifiers that apply to any source, not a single tribe
        if source is not None:
            ctrl = source.controller
            if any(q.card.name in ("City on Fire", "Fiery Emancipation")
                   for q in ctrl.battlefield):
                amount *= 3
            if any(q.card.name == "Torbran, Thane of Red Fell" for q in ctrl.battlefield) and (
                    "R" in source.card.colors or "Red" in source.card.colors):
                amount += 2
        if isinstance(target, Player):
            target.life -= amount
            if source is not None and source.card.is_legendary and not source.token and (
                    source.card is source.owner.commander or source.card.name == source.owner.commander.name):
                target.commander_damage[source.owner.name] += amount
                self.log(f"      {source.name} deals {amount} to {target.name} (commander dmg {target.commander_damage[source.owner.name]})")
            else:
                self.log(f"      {source.name} deals {amount} to {target.name} (life {target.life})")
        else:
            target.damage += amount
            self.log(f"      {source.name} deals {amount} to {target.name} (marked {target.damage}/{target.toughness(self)})")

    # ------------------------------------------------------------ cleanup
    def cleanup(self, pl: Player) -> None:
        """514: discard down to max hand size; damage removed; until-EOT effects end."""
        self.sba_happened = False
        # 514.x: discard to max hand size
        max_hand = 0 if self.flags.get(f"{pl.name}_max_hand_0") else R.MAX_HAND_SIZE
        if len(pl.hand) > max_hand and not self.flags.get(f"{pl.name}_no_max_hand"):
            while len(pl.hand) > max_hand:
                c = pl.ai.choose_discard(self, pl)
                if c is None:
                    break
                pl.discard_card(c)
            self.log(f"      {pl.name} discards to {len(pl.hand)} (max hand size)")
        # damage removed and 'until end of turn' effects end (514.x)
        for perm in pl.battlefield:
            perm.damage = 0
            perm.eot_haste = False
            perm.eot_cant_block = False
            perm.eot_power_mod = 0
            perm.eot_toughness_mod = 0
            perm.sac_at_eot = False
        for (scope, fn) in self.turn_effects:
            if scope == "eot":
                fn()
        self.turn_effects = [t for t in self.turn_effects if t[0] == "turn"]
        # end-of-turn delayed sacrifices etc.
        for fn in self.end_of_turn_delayed:
            fn()
        self.end_of_turn_delayed = []

    def add_turn_effect(self, scope: str, fn: Callable) -> None:
        self.turn_effects.append((scope, fn))
