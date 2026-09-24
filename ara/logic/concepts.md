# Concepts

## Heuristic baseline
- **Notation**: \(\text{label} \in \{\text{rules-complete},\ \text{heuristic baseline},\ \text{coverage-blocked},\ \text{stale}\}\)
- **Definition**: A simulation report whose engine implements a disclosed subset of card effects and a heuristic pilot policy. It may quote win numerators on a locked schedule but must not be called a real Magic win rate.
- **Boundary conditions**: Applies whenever any material card is `simplified`/`unimplemented` or AI is non-optimal. `rules-complete` requires every material effect and decision path implemented and unsupported = 0.
- **Related concepts**: Coverage gate, pod share, confidence label

## Locked-schedule pod share
- **Notation**: \(w/n\) with factor tuple \((L, O, C, \pi, P, \sigma, T, E)\)
- **Definition**: Wins \(w\) for the candidate deck in \(n\) games given list \(L\), Oracle defs \(O\), coverage \(C\), pilot \(\pi\), opponent set \(P\), seating/seeds \(\sigma\), turn cap \(T\), engine stamp \(E\).
- **Boundary conditions**: Changing any factor invalidates comparison. v11 9/36 is not the same experiment as v12.1 9/36 if \(E\) differs.
- **Related concepts**: Confirmation schedule, seat-0-only, turn cap honesty

## Confirmation schedule
- **Notation**: seeds \(1..36\), workers \(4\), \(T=14\)
- **Definition**: The locked Ovika A/B protocol in CONTEXT.md / REPORT.md used for retain/reject of list versions.
- **Boundary conditions**: Diagnostic is seeds 1–10, one worker. Do not retain from a single lucky game. Never >4–5 workers on 4 cores.
- **Related concepts**: Locked-schedule pod share, same-slot swap

## Same-slot 1-for-1 swap
- **Notation**: replace card \(c\) in slot \(s\) by \(c'\) with \(|\Delta \text{slot counts}|=0\)
- **Definition**: Default optimization step: one add, one cut, same primary slot (land, ramp, draw/filter, interaction, protection, seed/engine, payoff/finisher, enabler/synergy, flex).
- **Boundary conditions**: Slot-mix changes are allowed only when failure taxonomy says the mix is wrong, and must be a single documented step.
- **Related concepts**: Failure taxonomy, retain rule

## Synergy graph (engine-line overlay)
- **Notation**: undirected graph \(G=(V,E)\) over non-land cards plus commander hub
- **Definition**: Pairwise edges from documented engine-line rules (convoke×tokens, amplifiers×damage, etc.). Audit reports node/edge counts, components, communities, degree tails.
- **Boundary conditions**: No mass “connects to everything” rules. Connectivity is not a pod result. Pair rules in `graph_analysis.py` are Ovika-shaped unless rewritten.
- **Related concepts**: Thin node, velocity layer

## Velocity layer
- **Notation**: draw/filter/cantrip/wheel/ritual set \(V_{\text{vel}}\)
- **Definition**: Cards that look poorly connected in a static synergy graph but supply consistency (finding seeds, chaining spells). CONTEXT identifies the deg-3 tail as 7 draw/velocity spells; v12.2 cut slow convoke bodies in favor of pingers and lost measured wins.
- **Boundary conditions**: Dynamic value is validated only by pods, not by degree.
- **Related concepts**: Synergy graph, same-slot 1-for-1 swap

## Coverage gate
- **Notation**: classification of each nonland as named-hook | generic-pattern | simplified | unimplemented
- **Definition**: Before confirmation, report hooks/99 and simplified-log rate on a 10-seed diagnostic. Unimplemented win-condition cards must not enter confirmation (`coverage-blocked`).
- **Boundary conditions**: Verifier 21/21 tests sequencing/priority/SBA/mulligan/cleanup, not full-card coverage.
- **Related concepts**: Heuristic baseline, `(simplified ...)` log

## Priority no-op pass
- **Notation**: if \(\text{sig}(s)=\text{sig}(\text{execute}(a,s))\) then \(a\) is a pass
- **Definition**: CR 117-aligned treatment of silent cast/payment failure: do not re-grant priority; count as passing priority.
- **Boundary conditions**: Required for large token boards; without it the 5000-guard livelock appears. Daemon-thread watchdogs are not a substitute (GIL starvation).
- **Related concepts**: Perf guards, deal_damage routing
