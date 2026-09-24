# Ovika Convoke Engine — v12 Final Report

Date: 2026-09-03. Supersedes the v11-era report. Deck: `ovika/deck_v12.py`
(99 cards + commander), paste-ready list in `ovika/decklist_v12.md`.

## 1. Result summary

| Metric | v11 (storm, old engine) | v12.1 FINAL (convoke) | v12.2 (pinger variant) |
|---|---|---|---|
| Pod wins (36 games, seeds 1–36, 4 decks, T14 cap) | 9/36 (25%) | **9/36 (25%)** | 8/36 (22%) |
| Total price (99 + commander) | — | **$533.00** | $546.04 |
| GPU hand MC (200k, CUDA) keep rate | 79.0% | **82.1%** | — |
| P(2–5 lands opener) | 0.592 | **0.640** | — |
| Mana screw rate | 0.406 | **0.359** | — |
| Lands by turn 5 (mean) | 3.16 | **3.39** | — |

v12.1 is the adopted build: it matches v11's win share at a fraction of the
storm variance, with better openers and a strict $1,000 budget (uses $533).
v12.2 (added Guttersnipe, Coruscation Mage, Seething Song; cut the three
slow 6–8 MV convoke creatures) measured 22% — no improvement, not adopted.

Pod opponents (fixed 3): EDHREC-derived Nekusar, Kuja, Wandering Minstrel.
Final engine run: ovika 9/36 (25%), nekusar 6/36 (17%), kuja 7/36 (19%),
minstrel 3/36 (8%), 11 no-winner (31%). Results: `results_pod_v12.csv`;
v12.2 experiment: `results_deck_v12_2.csv`.

## 2. How the simulation works

- `engine/game.py` — full sequential 4-player Commander game. Every turn
  runs the CR 500–514 structure: untap (502) → upkeep (503) → draw (504) →
  precombat main (505) → begin combat/attackers/blockers/combat damage/end
  combat (507–511) → postcombat main (505) → end step (513) → cleanup (514).
  (Magic has 5 phases / 12 steps; combat is one phase containing 5 steps.)
- Priority (CR 117) is passed around the table after every action; stack
  resolves LIFO (405/608); triggers use AP/NAP order (603); state-based
  actions run before each priority pass (704); London mulligan (103.5);
  commander tax/damage (903).
- `engine/oracle.py` — card rules text from MTGJSON AtomicCards (local gz);
  `engine/cards.py` + `engine/generic.py` implement named-card hooks and an
  oracle-text fallback for the opponent decks. Unsupported effects are
  logged as "(simplified ...)" instead of being silently guessed.
- Rules source merged into the project: official Comprehensive Rules
  (`rulebook/CR.txt`, 1,414 rules) plus rule digests and Oracle text.

## 3. Reliability

- **Deterministic**: each Game reseeds `random` from its seed in
  `Game.__init__`, so a seed reproduces the same game (verified: seed 1 run
  twice → identical winner/timing).
- **Rules checks**: `scripts/verify_phases.py` — 21/21 passing after every
  engine change (phase order, priority windows, SBA, mulligan, cleanup).
- **Perf guards (disclosed abstractions)**: log budget (~3k lines), attacker
  log collapse, 150-casts-per-turn guard, Mana Echoes capped +30 per trigger,
  world-static cache for Blood Moon/Urborg/Harbinger/Urza. None change card
  behavior in the pod decks; they bound pathological token chains.
- **Fixed this session (code review + refinement)**:
  1. On-cast/ETB damage (Guttersnipe, Coruscation Mage, Urabrask, Kuja Wizard
     token, Joyful Stormsculptor, Orcish Bowmasters, Siege-Gang, Tellah) now
     routes through `game.deal_damage`, so City on Fire / Torbran amplifiers
     apply per CR 614. Opponent decks run no amplifiers, so pod balance is
     unchanged; Ovika's own amplifiers now work on every damage source.
  2. No-op action detection in `priority_loop`: a decision that changes no
     state (silent cast/payment failure, cast guard) now counts as a pass
     (CR 117) instead of re-granting priority and spinning for minutes —
     this was the v12.2 "hang" (8+ min games on a 68-permanent board).
  3. `pod_v12.py --deck <file>` for same-engine A/B benchmarks.
- **Known approximations**: AI pilots are heuristic (name-keyed spell
  scoring); a few oracle effects log "(simplified)"; GPU is used only for
  the parallel hand-MC layer — full rules games are sequential Python and
  run on CPU workers (4-way multiprocessing).

## 4. Deck strategy (convoke engine)

Every noncreature spell with Ovika on board creates X Phyrexian Goblins
(X = mana value). Goblins then convoke-pay the next spell
(Meeting of Minds, Temporal Cleansing, City on Fire, Obelisk of Urd, ...),
which creates more goblins → chain acceleration. Finishers: goblin horde
under City on Fire / Collective Inferno / Torbran amplification, Obelisk
anthem, Jeska's Will + Mana Geyser + ritual bursts, Rhystic/Mystic Remora
card advantage.

Build shape (99 + commander, $533.00): 28 lands · 11 ramp · 10 draw ·
12 convoke payoffs · 15 creatures/convoke bodies · 6 token spells ·
9 burst/velocity · 5 protection · 3 utility.

GPU hand-MC (200k, RTX-4060 CUDA): keep rate 82.1%, P(2–5 lands) 0.640,
screw 0.359, mean lands by T5 3.39.

## 5. Files

- `deck_v12.py` (live), `decklist_v12.md` (list + prices),
  `build_convoke.py` (validate + price), `_handmc_v12.py` (GPU MC),
  `pod_v12.py` (pod benchmark), `results_pod_v12.csv`,
  `results_deck_v12_2.csv`, `CONTEXT.md` (working notes).
