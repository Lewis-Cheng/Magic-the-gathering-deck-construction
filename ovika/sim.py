# sim.py v2 - heuristic baseline 4-player EDH simulator for Ovika 30-creature win (skill v3)
# Disclosed abstractions (heuristic baseline): abstracted opponents (wipe p=0.12/turn, Ovika removal p=0.20/turn,
# ward/greaves factored), attrition = 30% per creature per turn (user model), win = >=30 creatures at end of our turn.
import random, argparse, importlib.util

TURN_CAP = 10
WIN_N = 30
DIE_P = 0.30
WIPE_P = 0.12
REMOVE_P = 0.20
WARD_SAVE = 0.30
COUNTER_SAVE = 0.60
BREACH_HIT = 0.60
TRIAD_HIT = 0.60

COMMANDER = ("Ovika, Enigma Goliath", 7, "creature", 1, 1, ["ovika"])

def load_deck(path):
    spec = importlib.util.spec_from_file_location("d", path)
    d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
    return getattr(d, "DECK", getattr(d, "BASELINE", []))

class Card:
    __slots__ = ("name","mv","kind","u","r","tags","buy")
    def __init__(self, t):
        self.name, self.mv, self.kind, self.u, self.r, self.tags = t[:6]
        self.buy = "buy" in (t[5] if len(t) > 5 else [])
    def has(self, tag): return tag in self.tags
    def __repr__(self): return self.name

class Game:
    def __init__(self, seed, deck):
        self.rng = random.Random(seed)
        self.seed = seed
        self.deck_src = deck
        self.library = [Card(t) for t in deck]
        self.rng.shuffle(self.library)
        self.hand = []
        self.lands = []
        self.rocks = []
        self.creatures = []
        self.rooms = []
        self.perm_mvs = []
        self.grave = []
        self.ovika = False
        self.ovika_tax = 0
        self.turn = 0
        self.won = False
        self.win_turn = None
        self.max_board = 0
        self.reached30 = False
        self.mulligans = 0
        self.opening = []
        self.flags = set()
        self.spent = 0
        self.cast_this_turn = 0
        self.treasure_mana = 0
        self.geyser_mana = 0
        self.ritual_mana = 0
        self.bounty_mana = 0
        self.strionic_used = False
        self.saheeli_used = False
        self.krenko_used = False
        self.complete_pending = False
        self.stats = {"spells_cast":0,"mana_used":0,"tokens_created":0,"cards_drawn":0,
                      "ovika_casts":0,"ovika_removed":0,"wipes":0,"skullclamps":0,"free_casts":0}

    # ---------- mana ----------
    def has_flag(self, f): return f in self.flags
    def set_flag(self, f): self.flags.add(f)

    def land_mana(self):
        n = len(self.lands)
        return n + (4 if self.has_flag("cataracts") and n >= 6 else 0)

    def rock_mana(self):
        m = 0
        for c in self.rocks:
            if c.has("+2"): m += 2
            elif c.has("+3"): m += 3
            elif c.has("+1"): m += 1
        return m

    def mana_available(self):
        return (self.land_mana() + self.rock_mana() + self.treasure_mana +
                self.geyser_mana + self.ritual_mana + self.bounty_mana - self.spent)

    def sources(self):
        u = r = 0
        for ls in self.lands:
            if "u" in ls or "any" in ls: u += 1
            if "r" in ls or "any" in ls: r += 1
        if self.has_flag("cataracts") and len(self.lands) >= 6: u += 1; r += 1
        for c in self.rocks:
            if c.has("anycolor"): u += 1; r += 1
        if self.has_flag("koth"): r += 1
        return u, r

    def cost_of(self, card):
        c = card.mv
        if card.name == "Travel the Overworld":
            c = max(1, 7 - sum(1 for ls in self.lands if "town" in ls))
        if card.has("focus") and self.cast_this_turn > 0: c -= 2
        if card.has("redcost") and card.r > 0 and self.has_flag("firecrystal"): c -= 1
        if card.mv >= 5 and self.has_flag("thryx"): c -= 1
        if card.has("is") and self.has_flag("electromancer"): c -= 1
        if self.has_flag("saheeli") and self.cast_this_turn == 0: c -= 2
        if card.has("xspell"):
            return max(1, self.mana_available())
        if card.has("goblin") and self.has_flag("warchief"): c -= 1
        if card.has("cruise"):
            c = max(1, 8 - min(5, len(self.grave)))
        if card.has("convoke") and not card.has("xspell"):
            c = max(1, c - min(max(0, c - 1), len(self.creatures)))
        return max(0, c)

    def can_pay(self, card, cost):
        u, r = self.sources()
        return cost <= self.mana_available() and card.u <= u and card.r <= r

    def draw(self, n=1, silent=False):
        got = 0
        for _ in range(n):
            if not self.library: break
            self.hand.append(self.library.pop())
            got += 1
        self.stats["cards_drawn"] += got
        return got

    def tutor(self, pred, n=1):
        found = []
        for c in list(self.library):
            if pred(c):
                self.library.remove(c); self.hand.append(c); found.append(c.name)
                if len(found) >= n: break
        return found

    def play_land(self, card=None):
        if card is None:
            cands = [c for c in self.hand if c.kind == "land"]
            if not cands: return False
            card = min(cands, key=lambda c: (0 if any(x in c.tags for x in ("u","r","any")) else 1, c.name != "Mountain"))
        self.hand.remove(card)
        self.lands.append(frozenset(card.tags))
        if card.has("cataracts"): self.set_flag("cataracts")
        if card.has("fetcher"):
            for c in list(self.library):
                if c.name == "Mountain":
                    self.library.remove(c)
                    self.lands.append(frozenset(c.tags))
                    break
        if card.has("myriad"):
            for want in ("Island", "Mountain"):
                for c in list(self.library):
                    if c.name == want:
                        self.library.remove(c)
                        self.lands.append(frozenset(c.tags))
                        break
        return True

    # ---------- board ----------
    def add_creature(self, name, token=True, ephemeral=False):
        self.creatures.append({"name": name, "token": token, "ephemeral": ephemeral})
        if not ephemeral:
            if len(self.creatures) > self.max_board: self.max_board = len(self.creatures)
            if len(self.creatures) >= WIN_N: self.reached30 = True

    def goblin_count(self):
        names = ("Phyrexian Goblin","Goblin token","Warrior token","Hero token","Goblin")
        return sum(1 for c in self.creatures if c["token"] and any(n in c["name"] for n in names))

    # ---------- ovika trigger ----------
    def ovika_trigger(self, mv, spell_card=None):
        n = mv
        if spell_card is not None:
            if spell_card.has("is") and self.has_flag("veyran"):
                n *= 2
            if self.has_flag("strionic") and not self.strionic_used:
                self.strionic_used = True
                n *= 2
        if self.has_flag("throne"):
            n *= 2
        for _ in range(n):
            self.add_creature("Phyrexian Goblin", token=True)
        self.stats["tokens_created"] += n
        # Shark Typhoon: one X/X shark per noncreature spell
        if self.has_flag("shark") and spell_card is not None:
            self.add_creature("Shark", token=True)
        # Metallurgic Summonings: construct per instant/sorcery
        if self.has_flag("metallurgic") and spell_card is not None and spell_card.has("is"):
            self.add_creature("Construct", token=True)
        # Tellah: hero token per noncreature spell
        if self.has_flag("tellah") and spell_card is not None:
            self.add_creature("Hero token", token=True)
            if spell_card.mv >= 4: self.draw(2)
            if spell_card.mv >= 8:
                self.creatures = [c for c in self.creatures if c["name"] != "Tellah, Great Sage"]
        if self.has_flag("stormkiln") and spell_card is not None and spell_card.has("is"):
            self.treasure_mana += 1

    # ---------- mulligan ----------
    def mulligan(self):
        for attempt in range(3):
            self.hand = []
            for _ in range(7 - attempt): self.draw(1, silent=True)
            if attempt == 0: self.opening = [c.name for c in self.hand]
            nl = sum(1 for c in self.hand if c.kind == "land")
            ok = (2 <= nl <= 5 and (any(c.has("ramp") for c in self.hand) or any(c.kind != "land" and c.mv <= 3 for c in self.hand))) or (nl == 1 and any(c.has("ramp") for c in self.hand) and any(c.kind != "land" and c.mv <= 3 for c in self.hand))
            if ok: break
            self.mulligans += 1
            if self.hand:
                self.library.append(self.hand.pop())
        return self.opening

    # ---------- casting ----------
    def cast_spell(self, card, cost, free=False):
        if card.name == "Ovika, Enigma Goliath":
            self.ovika = True
            self.ovika_casts = self.stats["ovika_casts"] + 1
            self.stats["ovika_casts"] += 1
            self.stats["mana_used"] += cost
            self.spent += cost
            self.cast_this_turn += 1
            self.perm_mvs.append(7)
            self.stats["spells_cast"] += 1
            return
        if not free:
            self.hand.remove(card)
            self.spent += cost
            self.stats["mana_used"] += cost
        self.cast_this_turn += 1
        self.stats["spells_cast"] += 1
        as_mv = cost if card.has("xspell") else card.mv
        if card.has("xspell") and card.has("convoke"):
            as_mv = cost + min(len(self.creatures), 12)
        if self.ovika:
            self.ovika_trigger(as_mv, card)
        if card.has("song") and card.has("xspell"):
            for _ in range(as_mv - 1):
                self.add_creature("Rat", token=True)
        self.resolve(card)
        if card.kind == "creature":
            self.add_creature(card.name, token=False)
        if self.has_flag("echoes"):
            self.treasure_mana += min(18, self.goblin_count())

    def free_cast(self, card):
        # cast without mana cost (Mizzix/Breaching/Triple Triad)
        self.stats["free_casts"] += 1
        self.cast_this_turn += 1
        self.stats["spells_cast"] += 1
        if self.ovika:
            self.ovika_trigger(card.mv, card)
        self.resolve(card)
        if card.kind == "creature":
            self.add_creature(card.name, token=False)

    def resolve(self, card):
        n = card.name
        mult = 1
        if self.complete_pending and card.has("is") and card.name != "Complete the Circuit":
            mult = 3
            self.complete_pending = False
        if card.has("rock"):
            self.rocks.append(card); self.perm_mvs.append(card.mv)
        if card.has("bauble") and self.mana_available() >= 2:
            self.spent += 2; self.stats["mana_used"] += 2
            for want in ("Island", "Mountain"):
                for c in list(self.library):
                    if c.name == want:
                        self.library.remove(c)
                        self.lands.append(frozenset(c.tags))
                        break
                else:
                    continue
                break
        if card.has("koth"):
            self.set_flag("koth"); self.tutor(lambda c: c.name == "Mountain", 1)
        if card.has("firecrystal"): self.set_flag("firecrystal")
        if card.has("thryx"): self.set_flag("thryx")
        if card.has("tellah"): self.set_flag("tellah")
        if card.has("clamp"): self.set_flag("clamp")
        if card.has("rabble"): self.set_flag("rabble")
        if card.has("mobilize"): self.set_flag("mobilize")
        if card.has("forge"): self.set_flag("forge")
        if card.has("triad"): self.set_flag("triad")
        if card.has("pupu"): self.set_flag("pupu")
        if card.has("terrain"): self.set_flag("terrain")
        if card.has("grimoire"): self.set_flag("grimoire")
        if card.has("veyran"): self.set_flag("veyran")
        if card.has("electromancer"): self.set_flag("electromancer")
        if card.has("stormkiln"): self.set_flag("stormkiln")
        if card.has("shark"): self.set_flag("shark")
        if card.has("metallurgic"): self.set_flag("metallurgic")
        if card.has("strionic"): self.set_flag("strionic")
        if card.has("greaves"): self.set_flag("greaves")
        if card.has("remora"): self.set_flag("remora")
        if card.has("rhystic"): self.set_flag("rhystic")
        if card.has("throne"): self.set_flag("throne")
        if card.has("assault"): self.set_flag("assault")
        if card.has("idol"): self.set_flag("idol")
        if card.has("warchief"): self.set_flag("warchief")
        if card.has("echoes"): self.set_flag("echoes")
        if card.has("saheeli"):
            self.set_flag("saheeli"); self.add_creature("Servo", token=True)
        if card.has("krenko"): self.set_flag("krenko")
        if card.has("skirk"): self.set_flag("skirk")
        if card.has("hart"):
            if self.mana_available() >= 3:
                self.spent += 3; self.stats["mana_used"] += 3
                for _ in range(2):
                    got = self.tutor(lambda c: c.name == "Mountain", 1)
                    if got:
                        c = self.hand.pop()
                        self.lands.append(frozenset(c.tags))
        if card.has("trinket"):
            self.tutor(lambda c: (c.has("ramp") and c.mv <= 1) or c.name == "Skullclamp", 1)
        if card.has("micromancer"):
            self.tutor(lambda c: c.kind == "spell" and c.mv == 1 and any(t in c.tags for t in ("removal","counter","draw1","body")), 1)
        if card.has("draw1"): self.draw(1 * mult)
        if card.has("draw2"): self.draw(2 * mult)
        if card.has("draw3"): self.draw(3 * mult)
        if card.has("draw4"): self.draw(4 * mult)
        if card.has("draw5"): self.draw(5 * mult)
        if card.has("message"): self.draw(max(0, card.mv - 4) * mult)
        if card.has("lunar"):
            mvs = set(self.perm_mvs + ([7] if self.ovika else []))
            self.draw(max(1, len(mvs)))
        if card.has("windfall"): self.draw(6)
        if card.has("cruise"): self.draw(3)
        if card.has("recurring"): self.draw(6)
        if card.has("echo"): self.draw(7)
        if card.has("sacdraw"): self.draw(1)
        if card.has("body") or card.has("body2") or card.has("body3"):
            k = (1 if card.has("body") else 2 if card.has("body2") else 3) * mult
            for _ in range(k):
                self.add_creature("Token", token=True)
        if card.has("circuit"):
            self.complete_pending = True
        if card.has("frantic"):
            self.draw(2)
            if len(self.hand) > 2:
                self.hand = self.hand[:-2]
            self.ritual_mana += 3
        if card.has("warrens"):
            for _ in range(2 * max(0, self.cast_this_turn - 1)):
                self.add_creature("Storm Goblin", token=True)
        if card.has("past"):
            cands = [c for c in self.grave if c.has("is")]
            for _ in range(2):
                if not cands: break
                best = max(cands, key=lambda c: (5 if c.has("draw") else 0, c.mv))
                if best in self.grave:
                    self.grave.remove(best)
                    self.free_cast(best)
        if card.has("hymn"):
            self.ritual_mana += min(25, len(self.creatures))
        if card.has("seething"):
            self.ritual_mana += 5
        if card.has("jeskas"):
            self.ritual_mana += min(10, len(self.hand))
            for _ in range(2):
                top = [c for c in self.library if c.kind != "land" and c.mv <= 8]
                if not top: break
                c = self.library.pop(self.library.index(top[0]))
                self.free_cast(c)
        if card.has("room"):
            self.rooms.append({"name": n, "unlocked": []})
            self.perm_mvs.append(card.mv)
            if card.has("ticket"): self.add_creature("Manifest", token=True)
            if card.has("elevator"): self.tutor(lambda c: c.has("room"), 1)
            for tag, (cost, eff) in {"meat":(5,"d3"), "smoky":(4,"spirit"), "ticket":(6,None), "elevator":(3,None)}.items():
                if card.has(tag) and self.mana_available() >= cost:
                    self.spent += cost; self.stats["mana_used"] += cost
                    self.rooms[-1]["unlocked"].append(tag)
                    if eff == "d3": self.draw(3)
                    elif eff == "spirit":
                        self.add_creature("Spirit", token=True)
                    break
        if card.has("breach") and self.rng.random() < BREACH_HIT:
            top = [c for c in self.library if c.kind != "land"]
            if top:
                c = self.library.pop(self.library.index(top[0]))
                if c.mv <= 8: self.free_cast(c)
                else: self.hand.append(c)
        if card.has("random"):
            for _ in range(4):
                if not self.library: break
                c = self.library.pop()
                if c.kind == "creature":
                    self.add_creature(c.name, token=False, ephemeral=True)
        if card.has("mizzix"):
            cands = [c for c in self.grave if c.has("is")]
            if cands:
                best = max(cands, key=lambda c: (5 if c.has("draw") else 0, c.mv))
                self.free_cast(best)
        if card.has("message"):
            self.draw(max(0, card.mv - 4))
        if card.has("geyser"):
            self.geyser_mana += self.rng.randint(8, 14)
        if card.has("brightstone"):
            self.ritual_mana += min(20, self.goblin_count())
        if card.has("bounty"):
            self.bounty_mana += min(12, len(self.lands))

    # ---------- turns ----------
    def upkeep(self):
        if self.has_flag("koth"): self.tutor(lambda c: c.name == "Mountain", 1)
        if self.has_flag("idol"):
            self.draw(1)
        if self.has_flag("remora") and self.rng.random() < 0.6: self.draw(1)
        if self.has_flag("rhystic") and self.rng.random() < 0.6: self.draw(1)
        if self.has_flag("grimoire") and any(c.name == "Pristine Talisman" for c in self.rocks): self.draw(1)
        if self.has_flag("saheeli"): self.add_creature("Servo", token=True)
        if self.has_flag("assault"):
            self.add_creature("Goblin token", token=True)
        if self.has_flag("triad") and self.rng.random() < TRIAD_HIT:
            top = [c for c in self.library if c.kind != "land" and c.mv <= 6]
            if top:
                c = self.library.pop(self.library.index(top[0]))
                self.free_cast(c)

    def combat_bodies(self):
        if self.has_flag("rabble"): self.add_creature("Goblin token", token=True)
        if self.has_flag("mobilize"): self.add_creature("Warrior token", token=True)
        if self.has_flag("forge"): self.add_creature("Forge Horror", token=True, ephemeral=True)
        if self.has_flag("krenko") and not self.krenko_used and self.goblin_count() > 0:
            self.krenko_used = True
            k = self.goblin_count()
            for _ in range(k): self.add_creature("Goblin token", token=True)

    def end_step(self):
        if self.has_flag("clamp") and self.mana_available() >= 1:
            toks = [c for c in self.creatures if c["token"]]
            if toks:
                self.spent += 1
                self.creatures.remove(toks[0])
                self.stats["skullclamps"] += 1
                self.draw(2)
        self.creatures = [c for c in self.creatures if not c["ephemeral"]]
        survivors = []
        for c in self.creatures:
            if c["name"] == "Ovika, Enigma Goliath":
                if self.rng.random() < DIE_P:
                    self.ovika = False
                    self.ovika_tax += 1
                    self.stats["ovika_removed"] += 1
                    continue
            elif self.rng.random() < DIE_P:
                continue
            survivors.append(c)
        self.creatures = survivors
        if len(self.creatures) >= WIN_N:
            self.won = True
            self.win_turn = self.turn

    def opponent_cycle(self):
        counters = [c for c in self.hand if c.has("counter")]
        if self.rng.random() < WIPE_P:
            if counters and self.rng.random() < COUNTER_SAVE:
                c = max(counters, key=lambda c: c.mv)
                self.hand.remove(c); self.grave.append(c)
            else:
                self.creatures = []
                self.stats["wipes"] += 1
                if self.ovika:
                    self.ovika = False; self.ovika_tax += 1
        counters = [c for c in self.hand if c.has("counter")]
        if self.ovika and self.rng.random() < REMOVE_P:
            saved = False
            if self.has_flag("greaves"):
                saved = self.rng.random() < 0.9
            elif self.rng.random() < WARD_SAVE:
                saved = True
            if not saved and counters and self.rng.random() < COUNTER_SAVE:
                c = max(counters, key=lambda c: c.mv)
                self.hand.remove(c); self.grave.append(c)
                saved = True
            if not saved:
                self.ovika = False
                self.ovika_tax += 1
                self.stats["ovika_removed"] += 1

    # ---------- policy ----------
    def skirk_mana(self, needed):
        if not self.has_flag("skirk"): return 0
        toks = self.goblin_count()
        if toks < 5: return 0
        take = min(needed, toks - 5, 8)
        if take <= 0: return 0
        removed = 0
        new = []
        for c in self.creatures:
            if removed < take and c["token"]:
                removed += 1
            else:
                new.append(c)
        self.creatures = new
        return take

    def pick_next(self):
        if not self.ovika:
            ovika_cost = 7 + 2 * self.ovika_tax
            if self.mana_available() >= ovika_cost and self.sources()[0] >= 1 and self.sources()[1] >= 1:
                return (Card(COMMANDER), ovika_cost)
            cands = [c for c in self.hand if c.kind != "land"]
            def score(c):
                if c.has("ramp"): return 300 - c.mv
                if c.name in ("Tellah, Great Sage", "Thryx, the Sudden Storm"): return 280 - c.mv
                if c.has("draw"): return 220 - c.mv
                if c.has("room"): return 120 - c.mv
                if c.name in ("Saheeli, the Gifted", "Shark Typhoon", "Metallurgic Summonings", "Strionic Resonator", "Krenko, Mob Boss", "Veyran, Voice of Duality"): return 260 - c.mv
                return 60 - c.mv
            cands.sort(key=score, reverse=True)
            for c in cands:
                cost = self.cost_of(c)
                if self.can_pay(c, cost): return (c, cost)
            return None
        counters = [c for c in self.hand if c.has("counter")]
        reserved = max(counters, key=lambda c: c.mv) if counters else None
        cands = [c for c in self.hand if c.kind != "land" and c is not reserved]
        def score(c):
            if c.has("big"): return 400 + c.mv * 3
            if c.has("draw") or c.has("draw1") or c.has("draw2") or c.has("draw3") or c.has("draw4") or c.has("draw5") or c.has("windfall") or c.has("echo"): return 350 + c.mv * 2
            if c.has("room"): return 300 + c.mv * 2
            if c.name in ("Tellah, Great Sage", "Krenko, Mob Boss", "Veyran, Voice of Duality", "Shark Typhoon", "Metallurgic Summonings", "Strionic Resonator", "Goblin Electromancer", "Storm-Kiln Artist", "Saheeli, the Gifted", "Goblin Rabblemaster"):
                return (500 + c.mv) if len(self.hand) >= 4 else (150 + c.mv)
            if c.kind == "creature": return 250 + c.mv
            if c.has("counter"): return 200 + c.mv
            if c.has("removal"): return 180 + c.mv
            if c.has("ramp"): return 150 - c.mv
            return 100 + c.mv
        cands.sort(key=score, reverse=True)
        for c in cands:
            cost = self.cost_of(c)
            if self.can_pay(c, cost): return (c, cost)
        # skirk: sac goblins to afford the best remaining card
        if self.has_flag("skirk"):
            best = None
            for c in cands:
                cost = self.cost_of(c)
                need = cost - self.mana_available()
                if need > 0 and self.skirk_mana(need) > 0 and self.can_pay(c, cost):
                    best = (c, cost); break
            if best: return best
        return None

    def take_turn(self):
        self.turn += 1
        self.spent = 0
        self.cast_this_turn = 0
        self.treasure_mana = 0
        self.geyser_mana = 0
        self.ritual_mana = 0
        self.bounty_mana = 0
        self.strionic_used = False
        self.krenko_used = False
        self.complete_pending = False
        self.saheeli_used = False
        self.draw(1)
        self.upkeep()
        if any(c.kind == "land" for c in self.hand): self.play_land()
        if self.has_flag("pupu") and any(c.kind == "land" for c in self.hand): self.play_land()
        if self.has_flag("terrain") and self.mana_available() >= 2 and any(c.name == "Mountain" for c in self.hand):
            self.spent += 2
            self.play_land(next(c for c in self.hand if c.name == "Mountain"))
        guard = 0
        while guard < 60:
            guard += 1
            nxt = self.pick_next()
            if nxt is None: break
            card, cost = nxt
            self.cast_spell(card, cost)
        self.combat_bodies()
        self.end_step()
        if not self.won:
            self.opponent_cycle()

    def run(self, detail=False):
        self.mulligan()
        turns_log = []
        for _ in range(TURN_CAP):
            if self.won: break
            before = len(self.creatures)
            self.take_turn()
            if detail:
                turns_log.append({
                    "t": self.turn, "lands": len(self.lands), "mana": self.land_mana() + self.rock_mana(),
                    "board_before": before, "board_after": len(self.creatures), "ovika": self.ovika,
                    "hand": len(self.hand), "max": self.max_board,
                })
        if self.reached30 and not self.won and self.max_board >= 30:
            fail = "attrition"
        elif self.stats["ovika_casts"] == 0:
            fail = "ovika_never_cast"
        elif self.stats["spells_cast"] < 18:
            fail = "fuel_short"
        elif self.max_board < 30:
            fail = "mana_or_board_short"
        else:
            fail = "attrition"
        return {
            "seed": self.seed, "won": self.won, "win_turn": self.win_turn,
            "board": len(self.creatures), "max_board": self.max_board, "reached30": self.reached30,
            "mulligans": self.mulligans, "spells_cast": self.stats["spells_cast"],
            "mana_used": self.stats["mana_used"], "tokens_created": self.stats["tokens_created"],
            "cards_drawn": self.stats["cards_drawn"], "ovika_casts": self.stats["ovika_casts"],
            "ovika_removed": self.stats["ovika_removed"], "wipes": self.stats["wipes"],
            "skullclamps": self.stats["skullclamps"], "free_casts": self.stats["free_casts"],
            "failure": fail, "opening": self.opening, "detail": turns_log,
        }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default=r"C:\Users\lewis\Documents\ChatGPT\mtg\ovika\deck_v2.py")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--seeds", type=str, default="")
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args()
    deck = load_deck(args.deck)
    seeds = [int(x) for x in args.seeds.split(",")] if args.seeds else list(range(1, args.games + 1))
    wins = 0
    import collections
    fails = collections.Counter()
    for s in seeds:
        g = Game(s, deck)
        r = g.run(detail=args.detail)
        wins += 1 if r["won"] else 0
        fails[r["failure"]] += 1
        print(f"seed {s:>3}: {'WIN' if r['won'] else 'LOSS'} t{r['win_turn'] or '-'}  board={r['board']:>2} max={r['max_board']:>2} reach30={'Y' if r['reached30'] else 'n'} mull={r['mulligans']} spells={r['spells_cast']:>2} tokens={r['tokens_created']:>3} draw={r['cards_drawn']:>2} ovika={r['ovika_casts']} rem={r['ovika_removed']} wipes={r['wipes']} fail={r['failure']}")
        if args.detail:
            for t in r["detail"]:
                print("    ", t)
    print(f"\n{wins}/{len(seeds)} wins (cap {TURN_CAP}, win = {WIN_N}+ creatures end of turn, die p={DIE_P})")
    print("failure taxonomy:", dict(fails))

if __name__ == "__main__":
    main()
