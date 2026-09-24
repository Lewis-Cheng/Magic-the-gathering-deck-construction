# Ovika Rules-Legal 4-Player Simulation Engine

A from-scratch Magic: The Gathering engine that plays full, sequential, rules-legal
Commander games for 4 AI players, with a PyTorch/CUDA statistical layer for the
embarrassingly-parallel parts (hand Monte Carlo, confidence intervals, sweeps).

## Data sources (merged rulebook)
- Official Comprehensive Rules, effective 2025-02-07 — `ovika/rulebook/CR.txt`
  (939 KB, 1,414 numbered rules; sourced from Wizards of the Coast).
- Card oracle text — MTGJSON `AtomicCards.json.gz` (`ovika/rulebook/data/`),
  merged with the local collection pool `ovika/ur_pool.json` + `ovika/deck_v11.py`
  (99 cards + Ovika, Enigma Goliath as commander).
- Rule digest files: `ovika/rulebook/digest_core.txt`, `digest_more.txt`,
  `deck_oracles.md`.

## Turn structure (CR 500-514)
Every player's turn runs all 5 phases / 12 steps in exactly the legal order,
with the correct active-player (AP) / non-active-player (NAP) priority timing
(117), state-based actions (704), and cleanup (514):

| # | Step          | Phase       | CR  |
|---|---------------|-------------|-----|
| 1 | Untap         | Beginning   | 502 |
| 2 | Upkeep        | Beginning   | 503 |
| 3 | Draw          | Beginning   | 504 |
| 4 | Main 1        | Precombat   | 505 |
| 5 | Begin Combat  | Combat      | 507 |
| 6 | Declare Attackers | Combat | 508 |
| 7 | Declare Blockers  | Combat | 509 |
| 8 | Combat Damage | Combat      | 510 |
| 9 | End Combat    | Combat      | 511 |
| 10| Main 2        | Postcombat  | 505 |
| 11| End Step      | Ending      | 513 |
| 12| Cleanup       | Ending      | 514 |

Priority passes around the table after each spell/ability on the stack and
at each priority window (117.3b); triggered abilities use AP/NAP ordering
(603.3b), the stack resolves LIFO (405.1, 608.2), and state-based actions
(704.5) are checked before any player receives priority.

## Rules implemented
- Turn/phase/step sequencing and priority (117, 500-514)
- Stack: LIFO resolution, responses, countering (405, 608, 701.5)
- Mana: lands, mana abilities, paying costs incl. colored pips (601-605)
- Combat: attackers/blockers, legality (flying/reach/menace), trample,
  first/double strike, damage assignment order, 508-511
- Damage, lifelink, commander damage limit 21 (120, 903.10a)
- State-based actions: lethal damage, legend rule, loss on 0 life (704)
- Triggers: "when/at/beginning of upkeep" incl. on-the-battlefield + stack
  (603); end-step triggers (513)
- Equipment/auras basics, tokens (Treasures, goblins), +1/+1 counters
- Commander rules: command zone, tax (903.8), return to zone (903.9a),
  commander damage (903.10a), 40 starting life (103.4c)
- Mulligans: London mulligan to any size (103.5), cleanup discard to 7 (514)
- Format: 4-player free-for-all, attack any number of opponents (802, 806),
  multiplayer turn order (800)

## Where the GPU is used
Full-rules games are sequential by nature, so they run on CPU (multiprocessing).
The RTX-4060-Laptop GPU (CUDA, 8 GB) is used for what is genuinely parallel:

- `batch/gpu_sim.py::hand_mc` — 1M+ opening-hand / mulligan / land-curve Monte
  Carlo with exact without-replacement sampling, fully vectorized.
- `batch/gpu_sim.py::aggregate_gpu` — Wilson score confidence interval for a
  batch's win rate, computed on GPU tensors.
- `batch/gpu_sim.py::fast_sweep` — large-N abstraction-level sensitivity sweep
  (heuristic baseline only; NOT a rules result).

## How to run
```powershell
# 1) rules conformance suite (21 checks) — CPU python
& 'C:\Users\lewis\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 -u ovika\scripts\verify_phases.py

# 2) one full 4-player game with a readable log
& 'C:\Users\lewis\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 ovika\cli.py --seed 1 --turns 12

# 3) batch: 20 rules-legal games + GPU hand MC + Wilson CI (needs .venv w/ torch-CUDA)
.\venv\Scripts\python.exe -X utf8 ovika\batch\runner.py --games 20 --seeds 1-20 --turns 14 --workers 8 --gpu --hand-mc 1000000

# 4) GPU hand Monte Carlo for the live deck (200k, CUDA RTX-4060 venv)
.\venv\Scripts\python.exe ovika\_handmc_v12.py

# 5) synergy-graph audit (networkx + matplotlib in .venv)
.\venv\Scripts\python.exe ovika\graph_analysis.py   # -> graph_deck_v12.json/.png
```

## Verified behavior (21/21 PASS, `scripts/verify_phases.py`)
1. Phase order: 96 steps over 2 turns x 4 players, exact CR schema.
2. Stack LIFO + counterspell: response resolves first, countered spell ->
   graveyard, "An Offer You Can't Refuse" makes 2 Treasures for its controller.
3. Commander tax 2 then 4 (903.8), command-zone return (903.9a),
   second cast costs 7+tax.
4. SBA: 6 damage to 6/6 -> destroyed (704.5g); two Krenkos -> legend rule (704.5j).
5. London mulligan sizes 0-7 (103.5).
6. Cleanup discard to 7 (514).


## Playing EDHREC decks (4-deck pod)
Three real decklists were pulled from EDHREC deckpreview links and converted
to engine deck modules (`ovika/decks/`):

| Deck module | Commander | Source |
|---|---|---|
| `decks/edhrec_nekusar.py` | Nekusar, the Mindrazer | moxfield.com/decks/6TkNHgp1TUuaK3rfgvjrSw |
| `decks/edhrec_kuja.py` | Kuja, Genome Sorcerer | moxfield.com/decks/-fuwGWXwgEuicZoFLj2ZTQ |
| `decks/edhrec_minstrel.py` | The Wandering Minstrel | archidekt.com/decks/22603494 |

These play in a 4-player pod against the local Ovika deck via `ovika/pod.py`.
Cards without a hand-written behavior get a generic oracle-text layer
(`engine/generic.py`): mana abilities from "{T}: Add ..." (605.1a), fetch
lands, pain lands, Blood Moon/Urborg statics, draw/wheel/tutor/ritual/counter/
destroy/mass-removal/MLD spell patterns, Nekusar/Sheoldred/Sphinx/Bowmasters
draw triggers, stax (Stasis/Winter Orb/Meekstone/Trinisphere/Smokestack), and
extra-land plays (Exploration/Azusa/Growth Spiral) + Crucible graveyard lands.

```powershell
# 4-deck pod (Ovika deck_v12 + the three EDHREC decks), deterministic seeds
# live deck = deck_v12.py (v12.1 FINAL, $533); use --deck <file> for A/B variants
<cpu-py> ovika/pod_v12.py --seeds 1-36 --turns 14 --workers 4            # final schedule (~1-2 min)
<cpu-py> ovika/pod_v12.py --deck deck_v12_1.py --seeds 1-36 --workers 4  # same-engine A/B baseline
<cpu-py> ovika/pod_v12.py --seeds 1 --turns 10 --workers 1 --log1         # one game, full rules log
# results: results_pod_v12.csv (final), results_deck_v12_2.csv (rejected experiment)
```

Anything the generic layer cannot represent is logged as "(simplified spell:
...)" instead of silently doing nothing, so fidelity is auditable per game.

### Reliability invariants (2026-09-03)
- Deterministic per seed: `Game.__init__` reseeds `random`, so a seed
  reproduces the same game; baselines must be re-run after engine changes.
- Damage routing: every damage effect (combat, burn, on-cast/ETB pings,
  activations such as Siege-Gang/Tellah) goes through `Game.deal_damage`, so
  amplifiers (City on Fire x3, Collective Inferno x2 goblin, Torbran +2) apply
  per CR 614. Opponent decks run no amplifiers, so pod balance is unchanged.
- Priority no-op detection: an action that changes no state (silent cast or
  payment failure, cast guard) is treated as a pass (CR 117). This fixed
  8-minute priority spins on large boards; keep it intact when editing
  `priority_loop`.
- Rare world-statics (Blood Moon / Urborg / Harbinger / Urza) are cached per
  board-size signature in `generic.py` (`_world_statics`) - do not restore
  the per-query full-board scans (O(board^2) hot path).
- Perf guards are disclosed abstractions: log budget (~3k lines), attacker-log
  collapse, 150 casts/turn, Mana Echoes +30/trigger cap.

## Reliability caveats
- Rules-legal for what it implements (core engine + this deck's ~100 cards),
  not every card in Magic. The engine raises on unknown/unsupported effects
  rather than silently guessing.
- AI is a heuristic pilot policy (mulligan, cast priority, combat, counters);
  every action is validated by the engine, but strategy is not optimal play.
- Combat simplification: multi-blocker damage assignment uses the first
  blocker; trample remainder is handled. Planeswalker damage, copy/clone
  permanents, and full triggered-ability coverage for every card are partial.
- `fast_sweep` is an abstraction, not a substitute for engine games.
- GPU hand MC draws without replacement per hand; the land curve is exact for
  the given shuffle model.
