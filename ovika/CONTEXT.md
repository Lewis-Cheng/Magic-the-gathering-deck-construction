# Project Context (compressed) — Ovika MTG simulator work

Last updated: 2026-09-03 (final). Read this before deep-diving; REPORT.md
holds the full final report, this file is the working-state cheat sheet.

## What the project is
4-player Commander simulation for Ovika, Enigma Goliath (UR) with an
official-CR-based engine (rulebook/CR.txt) + MTGJSON Oracle text. GPU
(RTX-4060 CUDA, .venv) runs the parallel hand-MC layer; full games are
sequential Python on CPU workers.

## Key files (ovika/)
- engine/oracle.py — CardDef from MTGJSON AtomicCards (gz); Pool loads decks.
- engine/game.py — Game: 12 steps/5 phases per turn per player, priority,
  stack, combat, mana, convoke, damage amplifiers, no-op action detection.
- engine/cards.py / generic.py — named hooks + oracle-text fallback.
- engine/ai.py — heuristic AI + name-keyed spell_score.
- deck_v12.py — LIVE deck v12.1 FINAL (99 + commander, $533.00).
- decklist_v12.md — paste-ready list + prices (regenerate: _mkdecklist.py).
- pod_v12.py — 4-deck pod; supports --deck for A/B (results CSV auto-named).
- results_pod_v12.csv — FINAL: ovika 9/36 (25%); results_deck_v12_2.csv —
  v12.2 experiment 8/36 (22%, not adopted).
- scripts/verify_phases.py — 21/21 rules checks (keep green after edits).
- _handmc_v12.py — GPU hand MC entry (200k): keep 82.1%, screw 0.359.
- REPORT.md — final v12 report (supersedes v11-era content).
- graph_analysis.py — synergy-graph audit (run: .venv python ovika/graph_analysis.py).
  Outputs graph_deck_v12.json/.png; result: 72 nodes/712 tight edges, 1 component,
  3 communities; no node <3 edges; deg-3 tail = 7 draw/velocity spells.
- decks/edhrec_{nekusar,kuja,minstrel}.py — 3 fixed opponents.
- deck_v1..v11.py — version archive (v11 = old storm baseline 9/36).

## Commands (PowerShell; python NOT on PATH)
- CPU python: C:\Users\lewis\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
- CUDA venv:  .venv\Scripts\python.exe   (hand MC: python ovika/_handmc_v12.py)
- Pod:        <cpu-py> ovika/pod_v12.py --seeds 1-36 --turns 14 --workers 4
              [--deck deck_v12_1.py]  (36 games ~60-90s on 4 workers)
- Verify:     <cpu-py> ovika/scripts/verify_phases.py
- Prices:     <cpu-py> ovika/build_convoke.py   (deck total $533.00, BUDGET OK)

## Editing rules (learned the hard way)
- Edit via node_repl JS fs (normalize CRLF->LF) or full-file Set-Content.
  JS template literals eat backslashes; keep Python regex as \\d.
- Card names must match AtomicCards keys exactly; MDFC land fronts only.
- Wand of the Worldsoul is WHITE — not UR legal. Deck rows need trailing
  commas (a missing comma silently merges rows into a tuple-call bug).
- Never rerun pods with >4-5 workers on 4 cores. Do NOT use daemon threads
  to watchdog running games (GIL starvation).

## Engine reliability state (2026-09-03)
- Deterministic per seed: Game.__init__ calls random.seed(seed).
- Damage routing: on-cast/ETB pings + Siege-Gang/Tellah go through
  game.deal_damage so City on Fire (x3), Collective Inferno (goblin x2),
  Torbran (+2) apply. Opponents run no amplifiers -> balance unchanged.
- priority_loop no-op detection: state-sig before/after action.execute();
  no change => pass (CR 117). This fixed the 8-min "hang" on big boards
  (silent cast failures used to re-grant priority until the 5000 guard).
- Perf guards (disclosed): log budget ~3000 lines, attacker-log collapse,
  150 casts/turn guard, Mana Echoes +30/trigger cap, world-static cache for
  Blood Moon/Urborg/Harbinger/Urza keyed on per-game board-size signature.
- (simplified ...) logs = unimplemented oracle effects, counted in pods.

## Deck history / decisions
- v11 (storm) baseline: 9/36 pod (25%) — old-engine numbers.
- v12.0: convoke first cut 3/36 (8%) — no burst.
- v12.1 FINAL (live): +Mana Echoes, Mana Geyser, Brightstone Ritual,
  Battle Hymn, Consider, Opt, Preordain, Thought Scour; cut Pact/Pyroblast/
  Echo of Eons/Fiery Emancipation/Urabrask/Mizzix's Mastery/Swan Song/Idol.
  9/36 (25%) on fixed engine; $533.00.
- v12.2 (tested, NOT adopted): +Guttersnipe/Coruscation Mage/Seething Song,
  -Will-Forged Golem/Thunderhead Squadron/Interdisciplinary Mascot.
  8/36 (22%); $546.04. Its discovery exposed the priority-loop no-op bug.
