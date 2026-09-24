# Heuristics

## H01: Treat no-op actions as priority passes
- **Rationale**: Silent cast/payment failures that re-grant priority livelock large boards (~8 min, 68 permanents) until a 5000-action guard.
- **Sensitivity**: high
- **Bounds**: State signature before/after `action.execute()`; no change ⇒ pass (CR 117). Do not replace with daemon-thread watchdogs (GIL starvation).
- **Code ref**: [src/execution/comparable_pod.py](../../src/execution/comparable_pod.py)
- **Source**: CONTEXT.md Engine reliability; REPORT.md §3 item 2; simulator skill

## H02: Route every damage source through `deal_damage`
- **Rationale**: City on Fire ×3, Collective Inferno goblin ×2, Torbran +2 must apply per CR 614; extra life-subtraction paths skip amplifiers.
- **Sensitivity**: high
- **Bounds**: Combat, burn, on-cast/ETB pings, Siege-Gang/Tellah activations. Opponent EDHREC decks run no amplifiers → pod balance unchanged when this was fixed.
- **Code ref**: [src/execution/comparable_pod.py](../../src/execution/comparable_pod.py)
- **Source**: REPORT.md §3 item 1; CONTEXT.md

## H03: Cache rare world statics on a board signature
- **Rationale**: Rescanning Blood Moon/Urborg/Harbinger/Urza per mana query is O(board²).
- **Sensitivity**: medium
- **Bounds**: Cache in `generic.py` `_world_statics`; do not restore per-query full-board scans.
- **Code ref**: [src/execution/comparable_pod.py](../../src/execution/comparable_pod.py)
- **Source**: CONTEXT.md; engine README Reliability invariants

## H04: Retain list changes only on same-engine locked pods
- **Rationale**: v12.2 connectivity/ping swap lost 9/36 → 8/36; graph outliers were velocity.
- **Sensitivity**: high
- **Bounds**: Same opponents, seeds, workers, cap, AI, engine stamp; 1-for-1 same slot by default; archive losers.
- **Code ref**: [src/execution/comparable_pod.py](../../src/execution/comparable_pod.py)
- **Source**: REPORT.md §1; CONTEXT.md v12.2; skill Optimization loop item 5

## H05: Cap pod workers at 4–5 on 4 cores
- **Rationale**: Oversubscription and daemon watchdogs stall the GIL; confirmation is ~60–90s at 4 workers.
- **Sensitivity**: medium
- **Bounds**: Diagnostic 1 worker; confirmation 4; never “more workers to go faster” as default.
- **Code ref**: [src/execution/comparable_pod.py](../../src/execution/comparable_pod.py)
- **Source**: CONTEXT.md Commands and Editing rules

## H06: Deck tuples need trailing commas; names match AtomicCards exactly
- **Rationale**: Missing comma silently merges rows into a tuple-call bug; wrong keys fail Oracle; MDFC lands use front face only; Wand of the Worldsoul is white.
- **Sensitivity**: high
- **Bounds**: Legality audit before every candidate; regenerate prices after every change.
- **Code ref**: [src/execution/comparable_pod.py](../../src/execution/comparable_pod.py)
- **Source**: CONTEXT.md Editing rules
