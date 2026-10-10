# Theme recipes

`lands` + sum(`slots`) = **99**. Commander is extra. Shells are not permission to copy a staple list.

Queries filter the Lantern neighbor pool. Always `CI ⊆ commander`. Discovery order: Deckmates, then What it does, then Combos.

Power filters (strip below `focused` unless `must_include`): extra-turn; fast mana (Mana Crypt, Mana Vault, Chrome Mox, Mox Diamond, Mox Opal, Jeweled Lotus, Grim Monolith, Lion's Eye Diamond); Game Changers (Rhystic Study, Smothering Tithe, The One Ring, Cyclonic Rift, Fierce Guardianship, Deflecting Swat, Deadly Rollick, Teferi's Protection, Jeska's Will, Force of Will, Force of Negation, Mana Drain, Thassa's Oracle, Underworld Breach, Consecrated Sphinx, Bolas's Citadel, Ad Nauseam, Necropotence); hard stax (Winter Orb, Static Orb, Stasis, Rule of Law, Arcane Laboratory, Drannith Magistrate, Grand Arbiter Augustin IV, Nether Void, Sphere of Resistance, Trinisphere, Thorn of Amethyst, Collector Ouphe, Null Rod).

## midrange — combat — 36 lands

ramp 10, draw 10, interaction 12, protection 4, seed 4, payoff 8, enabler 6, flex 9  
precon: no extra-turn, no stax. casual: no extra-turn.

## tokens — combat — 36 lands

ramp 8, draw 8, interaction 10, protection 4, seed 8, payoff 12, enabler 6, flex 7  
seed/payoff: token makers; enabler: anthem/populate.

## spellslinger — combat/combo — 34 lands

ramp 8, draw 12, interaction 10, protection 3, seed 6, payoff 10, enabler 8, flex 8  
payoff: prowess/magecraft/copy-instant. seed: cantrips.

## enchantress — combat — 36 lands

ramp 8, draw 10, interaction 8, protection 4, seed 10, payoff 10, enabler 6, flex 7

## voltron — combat — 38 lands

ramp 8, draw 8, interaction 10, protection 8, seed 6, payoff 12, enabler 4, flex 5

## reanimator — combo/combat — 35 lands

ramp 8, draw 8, interaction 10, protection 3, seed 10, payoff 10, enabler 8, flex 7

## stax — stax — 36 lands

ramp 10, draw 8, interaction 8, protection 4, seed 6, payoff 10, enabler 10, flex 7  
Only `power_level` `high` or `cedh`, or win_condition names stax. Do not put hard stax in casual tokens.

## aristocrats — combat — 36 lands

ramp 8, draw 8, interaction 10, protection 3, seed 10, payoff 10, enabler 8, flex 6

## lands — combat — 42 lands

ramp 6, draw 8, interaction 10, protection 3, seed 8, payoff 10, enabler 6, flex 6

## Stubs

`superfriends`, `tribal`, `counters`, `mill`, `group-hug`, `combo`: midrange counts plus a payoff query from the theme. Record `notes`: `"recipe:stub-<theme>"`.

## Land fill order

1. One basic per color (Wastes if colorless).
2. Budget duals in identity.
3. Shocks/fetches only if budget and power is `high`/`cedh`.
4. Utility lands if CI + price OK.
5. Fill with basics.

Collection-first: lands only from the paste, up to owned counts.

## Density modifiers

Steal from `flex` first, then `enabler`, never from `must_include`. Keep `lands` unless `land_count` is set.

**interaction_density:** low = interaction −2 → flex; medium = no change; high = interaction +4, protection +1 ← flex/enabler. Instants and flash count. Do not meet high with only sorcery removal.

**stax_density:** none = strip hard stax unless must_include; light = ≤3 soft tax/pillow; medium = stax/protection +4 ← flex; heavy = stax shell bias, stax/protection +6 ← flex/payoff.

If `win_condition` says stax and density is `none`, follow `win_condition` and confirm once.
