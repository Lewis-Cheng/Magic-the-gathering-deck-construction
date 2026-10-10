# Schemas (Agent API research layer)

## Intake (required)

```json
{
  "commander": "exact English Oracle name",
  "win_condition": "user sentence",
  "budget_usd": 150,
  "power_level": "precon|casual|focused|high|cedh",
  "interaction_density": "low|medium|high",
  "stax_density": "none|light|medium|heavy"
}
```

Wait for answers. Do not invent values. Do not default `budget_usd`.

## Intake (transform / MDFC / DFC)

```json
{ "back_face_plan": "how the 99 supports the back face" }
```

## Intake (optional)

```json
{
  "per_card_cap_usd": 25,
  "collection": "pasted names",
  "new_cards_allowed": null,
  "land_count": null,
  "exclude": [],
  "must_include": [],
  "seed_list": null
}
```

`new_cards_allowed` stays `null` until the user answers after the collection-first draft.

Reject if commander does not resolve on Scryfall, `win_condition` is empty, `budget_usd <= 0`, intake skipped, or a transform commander lacks `back_face_plan`. Do not reject a commander for its colors.

## Deck JSON

- `cards`: length 99 when finished. Commander is a separate field.
- No `win_rate`.
- `price_usd`: number or `null`. `null` is not 0 in `total_usd`.
- `confidence`: always `"research-only"` in this skill.
- Stamp: `ban_list_version`, `prices_as_of`, `tagger_version`, `atlas_fetch`.
- Each card: `name`, `slot`, `source` (`collection` | `new`), `price_usd`, `reason`.
