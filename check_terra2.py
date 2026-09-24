import sys, os, json
sys.path.insert(0, os.path.join("ovika", "engine"))
from oracle import Oracle
o = Oracle()
names = ["Terra, Magical Adept // Esper Terra", "Summon: Titan", "Summon: Leviathan",
"Six", "The Master of Keys", "Yenna, Redtooth Regent", "Demon of Fate's Design",
"Victor, Valgavoth's Seneschal", "Enduring Vitality", "The Apprentice's Folly",
"Amphibian Downpour", "Sythis, Harvest's Hand", "Sanctum Weaver", "Anger",
"Archon of Sun's Grace", "Eidolon of Blossoms", "Spark Double", "Destiny Spinner",
"Dauthi Voidwalker", "Grand Abolisher", "Dryad of the Ilysian Grove", "Citanul Stalwart",
"Enchantress's Presence", "Mirrormade", "Binding the Old Gods", "Opalescence",
"Enchanted Evening", "Starfield of Nyx", "The Eldest Reborn", "Sevinne's Reclamation",
"Demonic Counsel", "Archdruid's Charm", "Neoform", "Eldritch Evolution", "Culling Ritual",
"Smothering Tithe", "Sylvan Library", "Land Tax", "An Offer You Can't Refuse", "Rhystic Study"]
for n in names:
    c = o.get(n)
    if c is None:
        print(f"!! MISSING: {n}"); continue
    print(f"== {c.name} | cost={c.mana_cost_str} | types={sorted(c.types)}/{sorted(c.subtypes)} | CI={sorted(c.color_identity)} | P/T={c.power}/{c.toughness} | kw={sorted(c.keywords)}")
    print("   " + (c.text or "(no text)").replace("\n", " / "))
