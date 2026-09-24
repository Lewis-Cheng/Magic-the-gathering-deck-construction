# EDH generator (product)

JSON in / JSON out. Does **not** import `Pool`, does **not** read `deck_v12.py` as a template, and does **not** call `pod_v12.py` to pick cards.

Pinned Python: `C:\Users\lewis\Documents\ChatGPT\mtg\.venv\Scripts\python.exe`

## Run API + web (Windows PowerShell)

From the repo root `C:\Users\lewis\Documents\ChatGPT\mtg`:

```powershell
$py = "C:\Users\lewis\Documents\ChatGPT\mtg\.venv\Scripts\python.exe"
cd C:\Users\lewis\Documents\ChatGPT\mtg
$env:PYTHONPATH = "C:\Users\lewis\Documents\ChatGPT\mtg"
& $py -m uvicorn generator.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd C:\Users\lewis\Documents\ChatGPT\mtg\web
npm install
npm run dev
```

Open `http://localhost:5173`. Generate stays disabled until commander, theme, and budget are set. No default commander or $1000.

## Tests

```powershell
$py = "C:\Users\lewis\Documents\ChatGPT\mtg\.venv\Scripts\python.exe"
$env:PYTHONPATH = "C:\Users\lewis\Documents\ChatGPT\mtg"
& $py -m pytest generator/tests -q
```

## Endpoints

| Method | Path | Role |
|---|---|---|
| GET | `/v1/health` | liveness |
| GET | `/v1/commanders?q=` | legendary typeahead |
| POST | `/v1/decks` | generate list (`confidence: generator-only`) |
| POST | `/v1/swap` | same-slot cheaper candidates |
| POST | `/v1/sim` | stub: `coverage-blocked` |

## Data

- Oracle: lab `ovika/engine/oracle.py` `Oracle()` via `oracle_bridge.py` (never `Pool`)
- Prices: `ovika/rulebook/data/card_prices.json` (`None` if missing)
- Ban list: `generator/data/ban_list.json` (`ban_list_version`)
