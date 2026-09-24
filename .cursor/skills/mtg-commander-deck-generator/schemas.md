# Schemas

## Intake (required)

```json
{
  "commander": "Any exact English Oracle name the user typed",
  "win_condition": "The user's own plan, free text, not a lab deck",
  "budget_usd": 150,
  "power_level": "precon|casual|focused|high|cedh"
}
```

`win_condition` is free text from the user. It is not limited to a preset list.

## Intake (optional)

```json
{
  "per_card_cap_usd": 25,
  "collection_file": "path or upload; one Oracle name per line, optional count",
  "new_cards_allowed": null,
  "theme": "optional slot-count hint; ignored when it conflicts with win_condition",
  "land_count": null,
  "exclude": [],
  "must_include": [],
  "sim": { "enabled": false }
}
```

Reject if the commander name is not in Oracle, `win_condition` is empty, or `budget_usd <= 0`. Do not reject a commander for its colors.

`new_cards_allowed` stays `null` until the user answers. Do not default it. Each card with `source: "new"` consumes one, including the commander when `commander_owned` is false.

Collection file rows: `Name` or `Count Name` or `Name,Count`.

## Deck JSON (product)

- `cards`: length 99. Commander is a separate field, not inside `cards`.
- No `win_rate` property.
- `price_usd` is number or `null`. `null` must not be treated as 0 in `total_usd`.
- `confidence`: `generator-only` | `heuristic-baseline` | `coverage-blocked`.
- Stamp: `ban_list_version`, `prices_as_of`, `tagger_version`.

Machine schema (when code exists): `generator/schema/deck.schema.json`.
