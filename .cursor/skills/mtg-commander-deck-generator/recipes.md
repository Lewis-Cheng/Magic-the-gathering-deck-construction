# Theme recipes

`lands` + sum(`slots`) = **99**. Commander is extra (100th). These counts are shells. The commander and the payoff cards come from the user’s `win_condition` and that commander’s colors. A shell is not permission to import a lab deck.

Queries are hints for the Oracle index (`tag:X` = tagger). Always apply `CI ⊆ commander`.

Power filters (strip below `focused` unless `must_include`): extra-turn; fast mana (Mana Crypt, Mana Vault, Chrome Mox, Mox Diamond, Mox Opal, Jeweled Lotus, Grim Monolith, Lion's Eye Diamond); Game Changers (Rhystic Study, Smothering Tithe, The One Ring, Cyclonic Rift, Fierce Guardianship, Deflecting Swat, Deadly Rollick, Teferi's Protection, Jeska's Will, Force of Will, Force of Negation, Mana Drain, Thassa's Oracle, Underworld Breach, Consecrated Sphinx, Bolas's Citadel, Ad Nauseam, Necropotence); hard stax (Winter Orb, Static Orb, Stasis, Rule of Law, Arcane Laboratory, Drannith Magistrate, Grand Arbiter Augustin IV, Nether Void, Sphere of Resistance, Trinisphere, Thorn of Amethyst, Collector Ouphe, Null Rod).

## midrange — combat — 36 lands

ramp 10, draw 10, interaction 12, protection 4, seed 4, payoff 8, enabler 6, flex 9  
precon: no extra-turn, no stax. casual: no extra-turn.

## tokens — combat — 36 lands

ramp 8, draw 8, interaction 10, protection 4, seed 8, payoff 12, enabler 6, flex 7  
seed/payoff: token makers; enabler: anthem/populate. casual: no extra-turn, no stax.

## spellslinger — combat/combo — 34 lands

ramp 8, draw 12, interaction 10, protection 3, seed 6, payoff 10, enabler 8, flex 8  
payoff: prowess/magecraft/copy-instant. seed: cantrips. casual: no extra-turn.

## enchantress — combat — 36 lands

ramp 8, draw 10, interaction 8, protection 4, seed 10, payoff 10, enabler 6, flex 7  
seed: enchantresses; payoff: auras/enchantments that win or go wide.

## voltron — combat — 38 lands

ramp 8, draw 8, interaction 10, protection 8, seed 6, payoff 12, enabler 4, flex 5  
payoff: auras/equipment; protection heavier. lands 38.

## reanimator — combo/combat — 35 lands

ramp 8, draw 8, interaction 10, protection 3, seed 10, payoff 10, enabler 8, flex 7  
seed: mill/entomb/discard; payoff: reanimate targets; enabler: reanimate spells.

## stax — stax — 36 lands

ramp 10, draw 8, interaction 8, protection 4, seed 6, payoff 10, enabler 10, flex 7  
Only `power_level` `high` or `cedh`, or `theme: stax` explicit. Payoff: lock pieces. Do not put hard stax in casual tokens.

## aristocrats — combat — 36 lands

ramp 8, draw 8, interaction 10, protection 3, seed 10, payoff 10, enabler 8, flex 6  
seed: fodder; payoff: drains/sac outlets.

## lands — combat — 42 lands

ramp 6, draw 8, interaction 10, protection 3, seed 8, payoff 10, enabler 6, flex 6  
More lands; payoff: land-matter.

## Remaining v1 stubs (same 36 / midrange slots until specialized)

`superfriends`, `tribal`, `counters`, `mill`, `group-hug`, `combo`: use midrange counts **plus** payoff query from the theme name (planeswalkers / chosen creature type / +1/+1 / mill / pillows / combo pieces). Record `notes`: `"recipe:stub-<theme>"`.

## Land fill order

1. At least one basic per color in identity (Wastes if colorless).
2. Budget duals matching two colors in identity.
3. Shocks/fetches only if remaining budget allows and power is `high`/`cedh`.
4. Utility lands from theme query if CI + price OK.
5. Fill remainder with basics.
