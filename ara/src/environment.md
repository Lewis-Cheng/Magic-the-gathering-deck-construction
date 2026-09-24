# Environment
- **Python**: Not specified as a version pin in REPORT.md; CPU interpreter path in CONTEXT.md: `C:\Users\lewis\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. CUDA games use repo `.venv\Scripts\python.exe`. `python` is not on PATH.
- **Framework**: Sequential rules games = stdlib + project engine. GPU layer = PyTorch/CUDA (engine README). Graph audit = networkx + matplotlib in `.venv`.
- **Hardware**: CPU multiprocessing for full games (4 workers). GPU: RTX-4060-Laptop, CUDA, 8 GB — hand MC / Wilson tensors / `fast_sweep` only.
- **Key dependencies**: Local `ovika/rulebook/CR.txt`; `ovika/rulebook/data/AtomicCards.json.gz`; `card_prices.json`; torch in `.venv` (CUDA). Exact package versions: Not specified in paper.
- **Random seeds**: Confirmation seeds 1–36. `Game.__init__` calls `random.seed(seed)`. Seed 1 replayed twice → identical winner/timing (REPORT.md §3).
