# Licensing checklist (E3)

Lists in this repo are **personal-lab / local-site suggestions**, not a licensed SaaS card database.

## Data sources (local)

| Source | Use in V1 |
|---|---|
| MTGJSON `AtomicCards.json.gz` via lab `Oracle` | Names, types, Oracle text, color identity, CMC |
| Local `ovika/rulebook/data/card_prices.json` | USD snapshots; missing → `null`, never `$0` |
| Dated `generator/data/ban_list.json` | Commander ban snapshot |

## Scryfall

- Optional fetch only when explicitly enabled (`GENERATOR_SCRYFALL=1`).
- Required headers: `User-Agent` and `Accept: application/json`.
- Do not bulk-mirror Scryfall or ship a paid image CDN from this repo.

## Images (V1)

- **No** Scryfall (or other) full-card scans in the UI.
- Show **card names + typed slots** only.

## Customer-facing legal copy

- Lists are suggestions; format legality is checked against a **dated** ban list (`ban_list_version`).
- Prices are a **dated** snapshot (`prices_as_of`).
- Wizards of the Coast / Magic: The Gathering names are used for identification. This is not an official Wizards product.
