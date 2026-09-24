# Training / run hyperparameters

These are experiment-protocol knobs, not neural training.

## Confirmation seed list
- **Value**: 1–36 inclusive
- **Rationale**: Locked A/B schedule in CONTEXT.md / REPORT.md
- **Search range**: Diagnostic 1–10; confirmation 1–36
- **Sensitivity**: high
- **Source**: CONTEXT.md Commands; REPORT.md §1

## Turn cap
- **Value**: 14
- **Rationale**: Fast-deck measurement; 36 games ~60–90s at 4 workers
- **Search range**: Single-game logs use 10–12; batch README examples use 14
- **Sensitivity**: high
- **Source**: REPORT.md §1; CONTEXT.md Pod command

## Worker processes
- **Value**: 4 (confirmation); 1 (diagnostic / `--log1`)
- **Rationale**: 4 cores; >4–5 workers oversubscribe
- **Search range**: 1–5
- **Sensitivity**: medium
- **Source**: CONTEXT.md Editing rules

## Hand Monte Carlo N
- **Value**: 200000 (live-deck report)
- **Rationale**: GPU opener stats in REPORT.md §1
- **Search range**: README also documents 1000000 in `batch/runner.py` examples
- **Sensitivity**: medium
- **Source**: REPORT.md §1; CONTEXT.md `_handmc_v12.py`

## Starting life
- **Value**: 40
- **Rationale**: CR 103.4c Commander
- **Search range**: Not specified in paper as swept
- **Sensitivity**: low
- **Source**: engine README Commander rules

## Commander damage loss
- **Value**: 21
- **Rationale**: CR 903.10a
- **Search range**: Not specified as swept
- **Sensitivity**: low
- **Source**: engine README
