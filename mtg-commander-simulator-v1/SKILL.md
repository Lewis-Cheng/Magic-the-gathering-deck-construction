---
name: mtg-commander-simulator-v1
description: Run, verify, debug, and extend the local deterministic 4-player Commander rules engine (CR 5 phases/12 steps, priority, stack, combat, damage) plus its GPU hand-Monte-Carlo layer. Use for simulator runs, pod experiments, rules-conformance checks, engine edits, or interpreting simulation results.
---

# MTG Commander Simulator v1 (Ovika engine)

## Purpose
Operate and maintain the local from-scratch MTG Commander rules engine in `ovika/` (the "simulator"): full sequential 4-player games with CR-ordered phases/steps, priority, stack, combat, and a PyTorch/CUDA layer for the parallel statistics (hand Monte Carlo). This is the simulator section of the skill set. The companion skill `mtg-commander-deckbuilding-simulation-v4` covers building and tuning the deck that runs inside this engine; use both together for pod experiments. Use this skill when the task is to run, verify, debug, or extend the engine, or to interpret its outputs.

## Project map (paths relative to C:\Users\lewis\Documents\ChatGPT\mtg)
- `ovika/engine/game.py` — Game: 12 steps / 5 phases per turn per player, priority, stack, combat, mana, convoke, damage amplifiers, no-op detection.
- `ovika/engine/cards.py`, `ovika/engine/generic.py` — named card hooks + oracle-text fallback (generic spell patterns, world statics).
- `ovika/engine/oracle.py` — CardDef from MTGJSON AtomicCards.gz; Pool loads deck modules.
- `ovika/engine/ai.py` — heuristic pilot policy + name-keyed spell scores.
- `ovika/scripts/verify_phases.py` — 21-check rules-conformance suite.
- `ovika/cli.py` — one full game with a readable log.
- `ovika/pod_v12.py` — 4-deck pod runner (candidate vs `ovika/decks/edhrec_{nekusar,kuja,minstrel}.py`).
- `ovika/batch/gpu_sim.py`, `ovika/batch/runner.py` — GPU hand MC, Wilson CI, fast sweep + batch entry.
- `ovika/_handmc_v12.py` — live-deck GPU hand MC entry (200k hands).
- `ovika/rulebook/CR.txt` — official Comprehensive Rules text (effective 2025-02-07) + digest files.
- `ovika/deck_v12.py` — live deck (v12.1 FINAL); `deck_v1.py`..`deck_v11.py` = version archive.
- Results: `ovika/results_pod_v12.csv` (final 36-seed run), `ovika/results_deck_v12_2.csv` (rejected experiment), `ovika/results_engine.csv`.

## Runtimes
- `python` is NOT on PATH. CPU python (`<cpu-py>`): `C:\Users\lewis\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- CUDA venv: `.venv\Scripts\python.exe` (torch CUDA on the RTX-4060-Laptop 8 GB; also networkx, matplotlib, pyyaml).
- Full-rules games are sequential, so they run on CPU workers (multiprocessing). The GPU is used only for the genuinely parallel statistics layer (hand MC, Wilson CI, sweeps).
- Run all commands from `C:\Users\lewis\Documents\ChatGPT\mtg`.

## Canonical commands
| Task | Command |
|---|---|
| Rules conformance | `<cpu-py> ovika\scripts\verify_phases.py` — must stay 21/21 after any engine edit |
| One full game + log | `<cpu-py> ovika\cli.py --deck ovika\deck_v12.py --seed 1 --turns 12` (cli defaults to deck_v11.py — always pass `--deck`) |
| Pod, final schedule | `<cpu-py> ovika\pod_v12.py --seeds 1-36 --turns 14 --workers 4` (~1-2 min; default deck is deck_v12.py) |
| Pod, A/B candidate | `<cpu-py> ovika\pod_v12.py --deck deck_v12_1.py --seeds 1-36 --turns 14 --workers 4` (CSV auto-named after the deck file) |
| Single pod game + log | `<cpu-py> ovika\pod_v12.py --seeds 1 --turns 10 --workers 1 --log1` |
| GPU hand MC (live deck) | `.venv\Scripts\python.exe ovika\_handmc_v12.py` (200k hands) |
| GPU batch sweep | `.venv\Scripts\python.exe ovika\batch\runner.py --games 20 --seeds 1-20 --turns 14 --workers 8 --gpu --hand-mc 1000000 --deck ovika\deck_v12.py` (runner defaults to deck_v11.py — always pass `--deck`) |
| Decklist / price regen | `<cpu-py> ovika\_mkdecklist.py`; `<cpu-py> ovika\build_convoke.py` |

Pod conventions: diagnostic = seeds 1-10, 1 worker; confirmation = seeds 1-36, 4 workers, turn cap 14. Results CSV records the winner deck and seat for each seed. Lock the engine version and re-run baselines after engine fixes.

## Rules model (engine invariants — do not break)
- Turn schema: every player's turn runs all 5 phases / 12 steps in CR order: untap (502), upkeep (503), draw (504), precombat main (505), begin combat (507), declare attackers (508), declare blockers (509), first-strike damage (510), normal combat damage (510), end of combat (511), postcombat main (505), end step (513), cleanup (514). Magic has 5 phases; combat contains 5 steps. If a user says "6 phases", clarify with this schema (this project exposes the turn as 12 sequential steps).
- Priority per CR 117 (AP/NAP around the table after each spell/ability and at each window); triggers AP/NAP (603.3b); stack LIFO (405.1, 608.2); state-based actions (704.5) before any player receives priority.
- Combat 508-511: attack legality (haste, summoning sickness, defender, vigilance); block legality (flying/reach/menace, protection, can't-block); first/double strike as separate damage steps; simultaneous normal damage; trample after lethal (deathtouch = 1 lethal); lifelink simultaneous.
- Commander: 40 starting life (103.4c), commander damage 21 (903.10a), command zone / tax / return (903.8, 903.9a). London mulligan (103.5), cleanup discard to 7 (514). 4-player FFA attack rules (802, 806), turn order (800).
- Determinism: `Game.__init__` reseeds `random` from the seed, so the same seed reproduces the same game. Verify by replaying one seed twice. Never compare results across engine versions.
- Damage routing: every damage effect (combat, burn, on-cast/ETB pings, activations) must go through `Game.deal_damage` so amplifiers (City on Fire x3, Collective Inferno goblin x2, Torbran +2) apply per CR 614. Never add a damage path that subtracts life directly.
- Priority no-op detection: `priority_loop` compares state before/after an action; an action that changes no state (silent cast or payment failure, cast guard) is treated as a pass per CR 117. History: without it, silent cast failures re-granted priority and spun to the 5000-guard for ~8 minutes on large boards. Keep the state-signature check intact.
- World statics: `generic.py` caches rare world statics (Blood Moon / Urborg / Harbinger / Urza) in `_world_statics` keyed on a board-size signature. Do NOT restore per-query full-board scans (O(board^2) hot path).
- Unsupported effects: the engine raises or logs "(simplified ...)" — never silently do nothing. Count simplified logs in every report.

## Guardrails (learned the hard way)
- Never run more than 4-5 pod workers on 4 cores. For timeouts use separate processes — daemon-thread watchdogs starve the GIL.
- Edit files with node-repl JS fs (normalize CRLF to LF) or full-file Set-Content. JS template literals eat backslashes, so keep Python regex escaped as `\\d` when writing through JS.
- Deck rows need trailing commas (a missing comma silently merges tuples and breaks deck loading); card names must match AtomicCards keys exactly; use the front face only for modal double-faced lands.
- Perf guards are disclosed abstractions: log budget ~3k lines, attacker-log collapse, 150 casts/turn guard, Mana Echoes +30/trigger cap, world-static cache. State them in every report; do not change them silently.

## Reliability caveats (disclose in every report)
- Rules-legal for the implemented card set only — not every card in Magic. The engine raises on unknown/unsupported effects rather than guessing.
- The AI is a heuristic pilot policy (mulligan, cast priority, combat, counters). Every action is validated by the engine, but strategy is not optimal play.
- Combat simplification: multi-blocker damage assignment uses the first blocker; trample remainder is handled. Planeswalker damage, copy/clone permanents, and full triggered-ability coverage are partial.
- `fast_sweep` is an abstraction layer, never a substitute for engine games.
- GPU hand MC draws without replacement per hand; land-curve numbers are exact for the given shuffle model.

## Report standard for any simulator output
Per run: game count and exact seed list; win numerator/denominator; turn cap; engine version stamp; results CSV path; mulligan rate; win-turn distribution; unsupported ("(simplified ...)") counts; perf guards invoked; verifier status (21/21) when engine code changed. Game logs must be replayable from the seed. Reference baselines by engine version (current reference: deck_v12.1 pod 9/36 = 25%, $533 — re-run after any engine change before trusting it).
