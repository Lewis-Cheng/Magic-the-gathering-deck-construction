# Constraints

## Boundary conditions
- **Commander family**: Numbers in this ARA are Ovika convoke (UR) unless a file is explicitly Terra. Do not compare Terra 14/36 to Ovika 9/36 as one experiment (`terra/REPORT.md` is a different engine fork date 2026-09-05).
- **Turn cap 14**: Midrange/control commanders look worse; cap-losses ≠ “cannot win.”
- **Seat order**: Source confirmation CSVs do not document seat rotation; treat as the seating encoded in those runs (skill: report `seat-0-only` if candidate never rotates).
- **Opponents**: Nekusar / Kuja / Wandering Minstrel EDHREC conversions — not a universal meta.
- **Budget**: v12.1 total $533.00 vs $1,000 cap stated in REPORT.md; v12.2 $546.04.
- **Python PATH**: `python` is not on PATH; CPU interpreter is the Codex runtime path in CONTEXT.md.

## Assumptions
- See `logic/problem.md` A1–A5.
- Prices: Scryfall cheapest non-foil USD at last `build_convoke.py` pass.
- Wand of the Worldsoul is white — not UR legal (CONTEXT editing rules).

## Known limitations
- Heuristic AI; name-keyed spell scores.
- `(simplified ...)` oracle gaps; combat multi-blocker uses first blocker.
- Planeswalker damage, copy/clone, full trigger coverage partial (engine README).
- `fast_sweep` is not a rules result.
- Graph pair rules are handwritten Ovika overlays; non-UR replacement search is invalid for other commanders (ISSUES A5).
- v11 vs v12.1 pod equality is **not** same-engine A/B.
- Wilson 95% CI is prescribed by skill v4.1 but the 2026-09-03 REPORT.md table does not quote interval endpoints — not specified in that report.

## Disclosed perf-guard abstractions
- Log budget ~3000 lines
- Attacker-log collapse
- 150 casts/turn
- Mana Echoes +30 per trigger
- World-static cache for Blood Moon / Urborg / Harbinger / Urza
