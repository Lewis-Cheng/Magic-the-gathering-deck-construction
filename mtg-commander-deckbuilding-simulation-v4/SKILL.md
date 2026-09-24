---
name: mtg-commander-deckbuilding-simulation-v4
description: Build, validate, and optimize a Commander deck with source-backed card data, a deterministic 4-player rules engine, GPU hand Monte Carlo, and synergy-graph audits. Use for Commander construction, testing, tuning, or matchup analysis.
---

# Commander Deckbuilding & Simulation v4

## Purpose
Build a legal 100-card Commander deck, then test it without presenting a heuristic estimate as a rules-complete result. The deckbuilder is responsible for card legality, source-backed card data, transparent assumptions, game logs, and recursive tuning. This version is updated for the Ovika convoke project (2026-09-03): deterministic engines, verified phase suites, budget builds, and graph-audited iteration.

## Non-negotiable principles
1. **Truthful labels:** Call a result `rules-complete` only if every material card effect and decision path in the game is implemented. Otherwise call it `heuristic baseline`.
2. **No fabricated card text:** Obtain card properties from Oracle data (local MTGJSON AtomicCards or Scryfall). Do not infer mana cost, types, keywords, Oracle text, color identity, or token stats from a card name.
3. **No silent omissions:** An unsupported card must be `blocked`, `irrelevant`, or `abstracted`, with a reason recorded. Unsupported effects are logged as "(simplified ...)".
4. **Comparable experiments:** Every candidate version uses the same opponents, seeds, game count, turn cap, mulligan policy, pilot policy version, engine version, and win definition. Re-run baselines after engine fixes; stale numbers mislead.
5. **Determinism:** Each game must reseed the RNG from its seed (`Game.__init__` calls `random.seed(seed)`); same seed => same game. Verify by replaying a seed twice.
6. **Actionable iteration:** Do not stop at a low win rate. Identify the observable bottleneck, make a 1-for-1 same-slot change, retest, and retain only improvements. Never optimize from a single lucky game.
7. **Graph audits are one lens:** Synergy connectivity measures static pairwise value. Draw/velocity cards (cantrips, wheels) are structurally thin but carry dynamic consistency value. If a connectivity-driven swap contradicts a measured pod result, trust the measurement.

## Required intake
Collect before building: commander (exact English name + Oracle text), color identity (both faces, rules text), target/casual level, budget (per-card and total cap), existing list or NONE, win preference, opponents (exact lists preferred; otherwise disclose the abstraction), test objective, constraints (land cap, bans, proxies, flavor).

## Source data & prices
- Card definitions: local `rulebook/data/AtomicCards.json.gz` (MTGJSON) via `engine/oracle.py`; verify every deck name with `Oracle.require()` before benchmarking. Modal double-faced lands: use the front face key only. Spell-front MDFCs resolve as instants in this engine -> avoid.
- Prices: local `rulebook/data/card_prices.json` (Scryfall cheapest non-foil USD). When a card is missing, fetch Scryfall `cards/named?exact=...` with BOTH `User-Agent` and `Accept: application/json` headers (Scryfall 400s otherwise). Budget checks must be re-run after every change (`build_convoke.py`).
- Legality traps seen in the wild: color-identity errors (e.g. Wand of the Worldsoul is white, not UR), cards not in the Oracle DB, duplicate rows, and deck rows missing trailing commas (silently merges tuples -> tuple-call bug).

## Deck legality audit
Before every candidate is tested, verify: exactly 100 cards incl. commander; singleton (basic lands exempt); commander color-identity legality; current format legality; land count per user constraint; every add has a same-slot cut. Keep a versioned deck module (e.g. `deck_v12.py`) and an archive per rejected experiment so any benchmark is reproducible.

## Rules engine baseline
A credible engine must process every turn in CR order: Untap (502), Upkeep (503), Draw (504), Precombat main (505), Begin combat (507), Declare attackers (508), Declare blockers (509), First-strike damage (510), Normal combat damage (510), End of combat (511), Postcombat main (505), End step (513), Cleanup (514). (Magic has 5 phases; combat contains 5 steps. When a user says "6 phases", clarify with this schema.)

### Mandatory state
Per player: life, poison, commander damage by commander object, library, hand, graveyard, exile, command zone, mana pool, land plays, commander tax, elimination. Per permanent: controller, owner, types/subtypes, base+modified P/T, tapped, summoning sickness, damage marked, counters, attachments, token status, copy source, keywords, attacking/blocking, entered-turn identity.

### Mandatory combat & damage
Attack legality (haste/sickness/defender/restrictions/vigilance), block legality (flying/reach/menace/protection/can't-block), first/double strike as separate damage steps, simultaneous normal damage, trample after lethal (deathtouch => 1 lethal), lifelink simultaneous, indestructible handling, SBAs after each resolution, commander damage only from the physical commander object, loss at 0 life / 10 poison / 21 commander damage. Life loss is not damage; damage, life loss, and life gain are distinct events.

### Stack & priority
LIFO stack, legal targets, trigger collection/order, priority passes among living players (AP first, same player keeps priority after an action, all-pass with empty stack ends the step), countering/fizzles, SBAs after each resolution.

### Engine reliability invariants (hard-won)
- **No-op actions are passes:** if an AI action changes no game state (silent cast/payment failure, per-turn cast guard), the priority loop must treat it as a pass, not re-grant priority. Without this, big boards spin for minutes.
- **Damage routing:** all damage-dealing effects (combat, burn, on-cast/ETB pings, activated abilities) go through one `deal_damage` path so amplifiers (City on Fire x3, Collective Inferno x2 goblin, Torbran +2) apply per CR 614.
- **Rare world-statics** (Blood Moon/Urborg/Harbinger/Urza) must not be rescanned per mana query (O(board^2)); cache on a board signature.
- **Perf guards are disclosed abstractions:** log budget (~3k lines), attacker-log collapse, 150 casts/turn, Mana Echoes +30/trigger cap. State them in every report.
- **Rules suite must stay green:** `scripts/verify_phases.py` (21 checks: phase order, priority, stack, commander tax, SBAs, London mulligan, cleanup) after every engine change.
- Daemon-thread watchdogs starve the GIL; use separate processes for timeouts. Never run >4-5 pod workers on 4 cores.

## Pilot policy
Versioned and identical across candidates: mulligan (2-4 lands or fast-mana equivalent, early play, commander mana plan by target turn, one engine seed/draw/interaction; official multiplayer London mulligan, log all mulligans/bottoms), sequencing (mana development -> low-risk filtering -> commander when a seed+follow-up is likely -> engine/protected win -> interaction held for the biggest threat), multiplayer targeting by an explicit score, never random.

## Simulation modes
- **Rules-complete:** only when all material cards/rules are implemented; report wins/losses/draws, win turn, elimination order, commander damage, interaction events, unsupported=0, replayable logs.
- **Heuristic baseline:** for triage; must state abstractions, never be called a real MTG win rate, use fixed seeds + identical opponent abstraction, report low confidence and excluded mechanics.

## Required simulation output
Per candidate version: game count + deterministic seed list; win rate numerator/denominator; turn distribution; mean/median win turn (wins only); commander cast rate + mean cast turn; mulligan rate; opponent life profile (above 30 / at or below 30 / at or below 10 / eliminated); damage profile (combat vs noncombat); engine profile (seed found, commander active, payoff cast); failure taxonomy (mana, no seed, commander removed, interaction, insufficient clock, unsupported effect); confidence label. For pod runs, record winner deck and seat per seed in CSV.

### Pod conventions (this project)
- 4-player pod: candidate deck + 3 fixed opponent decks (`ovika/decks/edhrec_*.py`).
- Diagnostic: seeds 1-10, one worker. Confirmation: seeds 1-36, 4 workers, turn cap 14 (about 1-2 min). Lock the engine version; re-run baselines after engine fixes.
- GPU hand Monte Carlo (CUDA venv): 200k hands -> keep rate, P(2-5 lands), screw rate, lands by turn 5. Report beside pod results.

## Optimization loop
1. Run 10 diagnostic games; classify failure causes (stalls with everyone >30 life => add finishers/reach; commander rarely cast => ramp/curve; tokens can't convert => haste/anthem/sac outlet).
2. One temporary candidate per dominant cause; 1-for-1 same-slot swaps.
3. Same 10 seeds; retain only if wins improve (or ties with a predeclared secondary metric).
4. Confirm on the locked 36-seed schedule + GPU hand MC.
5. Reject and archive candidates that lose (example: v12.2 pinger swap scored higher connectivity but lost 25% -> 22%; the graph's "outliers" were the velocity layer that made v12.1 consistent).

## Synergy graph audit
Build a graph over non-land cards (commander included as the engine hub) with explicit, documented pair rules - engine lines only, no mass "connects to everything" rules. Useful rule families: convoke x token creators; Mana Echoes/Skullclamp/sac outlets x token creators; damage amplifiers x damage/token swarm; anthem x goblins; trigger doublers x trigger permanents; rituals x convoke; rocks x MV>=5 noncreature; counterspells x critical permanents; Greaves x key creatures; Past in Flames x instants/sorceries.
Report: node/edge counts, connected components (expect 1), community structure (greedy modularity), nodes with degree < 3 (user criterion) plus the weakest tail, hubs. For each thin node, score engine-hooked UR replacements by edges added (net of the cut), show price, and note role shift. State the caveat: static connectivity under-weights per-cast dynamic value, so validate any swap with the pod before adopting.
Project implementation: `ovika/graph_analysis.py` -> `graph_deck_v12.json` + `graph_deck_v12.png` (`.venv` python, needs networkx + matplotlib).

## Final deliverables
1. Paste-ready decklist: MTGO plain-text file AND markdown table (card, cost, price).
2. Legality + budget audit (total price <= cap, re-verified).
3. Adds/cuts table with exact reasons and version history (keep rejected variants archived).
4. Commander seed test (first legal seed card + earliest line).
5. Aggregate simulation table + failure taxonomy + confidence label (engine version stamped).
6. Synergy-graph summary (components, thin nodes, recommended swaps and their measured outcome if tested).
7. Optimization history: retained/rejected candidates and next recommended change.

## Prohibited claims
Do not claim "fully rules accurate", "real win rate", "all cards modeled", "infinite combo verified", or "legal deck" unless the corresponding cache, rule handlers, validation, and test logs exist.
