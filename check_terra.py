import sys, os
sys.path.insert(0, os.path.join("ovika", "engine"))
from oracle import Oracle
o = Oracle()
# case-insensitive index
names_lower = {}
for n in o._by_name:
    names_lower.setdefault(n.lower(), []).append(n)

def find(name):
    hits = names_lower.get(name.lower(), [])
    return hits

# fuzzy searches first
for pat in ["terra", "summon", "esper"]:
    hits = [n for n in o._by_name if pat in n.lower()]
    print("PATTERN", pat, "->", hits[:40])
print("="*60)

deck = [
"Terra, Magical Adapter // Esper Terra",
"Terra, Magical Adapter",
"Esper Terra",
"Birds of Paradise","Citanul Stalwart","Esper Sentinel","Llanowar Elves",
"Dauthi Voidwalker","Destiny Spinner","Grand Abolisher","Sanctum Weaver",
"Sythis, Harvest's Hand","Dryad of the Ilysian Grove","Enduring Vitality",
"Mesa Enchantress","Setessan Champion","Six","The Master of Keys",
"Verduran Enchantress","Victor, Valgavoth's Seneschal","Anger",
"Archon of Sun's Grace","Eidolon of Blossoms","Spark Double",
"Yenna, Redtooth Regent","Summon: Titan","Demon of Fate's Design",
"Summon: Leviathan","An Offer You Can't Refuse","Dark Ritual","Enlightened Tutor",
"Entomb","Path to Exile","Swords to Plowshares","Assassin's Trophy","Counterspell",
"Heroic Intervention","Archdruid's Charm","Reanimate","Demonic Counsel","Farseek",
"Nature's Lore","Neoform","Three Visits","Eldritch Evolution","Idyllic Tutor",
"Sevinne's Reclamation","Culling Ritual","Lotus Petal","Sol Ring","Arcane Signet",
"Fellwar Stone","Talisman of Conviction","Talisman of Creativity",
"Talisman of Dominance","Talisman of Indulgence","Land Tax","Sylvan Library",
"Amphibian Downpour","Enchantress's Presence","Mirrormade","Binding the Old Gods",
"Opalescence","Smothering Tithe","The Apprentice's Folly","Enchanted Evening",
"Starfield of Nyx","The Eldest Reborn","Ancient Tomb","Breeding Pool","Canopy Vista",
"Cinder Glade","Command Tower","Exotic Orchard","Forest","Godless Shrine","Island",
"Lumbering Falls","Marsh Flats","Mountain","Plains","Plateau","Savannah",
"Scattered Groves","Seachrome Coast","Shadowy Backstreet","Stomping Ground","Swamp",
"Taiga","Tainted Wood","Temple Garden","Watery Grave","Windswept Heath",
"Wooded Foothills","Delighted Halfling","Moonmist","Rhystic Study",
]
for name in deck:
    hits = find(name)
    status = "OK  " + hits[0] if hits else "MISSING"
    print(f"{status:60s} <- {name}")
