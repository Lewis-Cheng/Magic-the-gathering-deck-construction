# Architecture

Component graph for the Ovika lab (not a general Commander generator).

```text
[MTGJSON AtomicCards.gz] --> oracle.py (CardDef / Pool.require)
[CR.txt 1414 rules]      --> game.py turn/priority/SBA semantics
[deck_v12.py + edhrec_*] --> Pool --> Game (4 players)
                                  --> ai.py heuristic pilot
                                  --> cards.py named hooks
                                  --> generic.py oracle-text fallback
Game.deal_damage <-- combat, burn, on-cast/ETB, activations (CR 614 amps)
priority_loop    <-- no-op => pass (CR 117)
pod_v12.py       --> results_*.csv
_handmc_v12.py   --> GPU tensors (openers only)
graph_analysis.py --> graph_deck_v12.json (static overlay)
verify_phases.py --> 21/21 sequencing suite
```

## oracle.py
- **Purpose**: Load Oracle-backed card definitions; refuse fabricated text.
- **Inputs**: AtomicCards keys (MDFC: front face only).
- **Outputs**: `CardDef` objects for Pool.
- **Key design**: `Oracle.require()` before benchmarks; unknown names fail closed.

## game.py
- **Purpose**: Sequential 4-player game: 5 phases / 12 steps, stack, combat, convoke, commander tax/damage.
- **Inputs**: seed, decks, turn cap, player AIs.
- **Outputs**: winner, logs, life vector, simplified-effect counts.
- **Key design**: Deterministic reseed; single `deal_damage` path; state-sig no-op detection.

## cards.py / generic.py
- **Purpose**: Named hooks for Ovika lines; pattern fallback for opponents.
- **Inputs**: Oracle text + card name.
- **Outputs**: Effect implementations or `(simplified ...)` logs.
- **Key design**: World-statics cache (`Blood Moon`/`Urborg`/`Harbinger`/`Urza`) keyed on board-size signature.

## ai.py
- **Purpose**: Heuristic mulligan, sequencing, targeting scores.
- **Inputs**: visible game state.
- **Outputs**: legal actions (engine-validated).
- **Key design**: Name-keyed `spell_score`; not optimal play; stamp as shared-pilot abstraction.

## pod_v12.py
- **Purpose**: Locked multi-seed FFA with `--deck` A/B.
- **Inputs**: seed range, workers, turn cap, optional deck module.
- **Outputs**: CSV (`seed,winner,winner_deck,win_turn,...`).
- **Key design**: Confirmation = 36 seeds, 4 workers, T14.

## _handmc_v12.py / batch/gpu_sim.py
- **Purpose**: Embarrassingly parallel opener statistics and Wilson CI tensors.
- **Inputs**: deck composition, N hands.
- **Outputs**: keep / P(2–5) / screw / T5 lands.
- **Key design**: GPU is not used to play rules-complete games.

## graph_analysis.py
- **Purpose**: Static engine-line synergy overlay for audit, not retain.
- **Inputs**: non-land names + handwritten pair rules.
- **Outputs**: 72 nodes / 712 tight edges (v12.1 report).
- **Key design**: Commander is hub; ban universal edges.
