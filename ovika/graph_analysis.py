"""Ovika v12 synergy graph v2 - tight pair rules + engine-hooked replacement search."""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.oracle import Oracle, Pool

HERE = os.path.dirname(os.path.abspath(__file__))
oracle = Oracle()
pool = Pool(oracle, os.path.join(HERE, "deck_v12.py"))
COMMANDER = pool.commander.name
DECK = [c for c in pool.decklist() if not c.is_land]
by = {c.name: c for c in DECK}
by[COMMANDER] = oracle.require(COMMANDER)
nodes = list(by.keys())

def tags(c): return set(c.tags or [])
TOKEN = {c.name for c in DECK if c.is_creature and "Goblin" in c.subtypes and c.name in (
    "Krenko, Mob Boss", "Goblin Rabblemaster", "Mogg War Marshal", "Siege-Gang Commander")}
TOKEN |= {c.name for c in DECK if not c.is_creature and (
    "create" in (c.text or "").lower() or bool(tags(c) & {"body2", "body3", "warrens", "assault", "song"}))}
GOBLIN_CRE = {c.name for c in DECK if c.is_creature and "Goblin" in c.subtypes}
GOBLIN_TOK = {n for n in TOKEN if n not in ("Song of Totentanz", "Shark Typhoon")}
CONVOKE = {c.name for c in DECK if "Convoke" in c.keywords}
AMPL = {"City on Fire", "Collective Inferno", "Torbran, Thane of Red Fell"}
RITUAL = {"Mana Geyser", "Brightstone Ritual", "Battle Hymn", "Jeska's Will"}
ROCKS = {c.name for c in DECK if tags(c) & {"ramp", "rock"} and not c.is_land}
COUNTER = {c.name for c in DECK if "counter" in tags(c)}
CRITICAL = {"Ovika, Enigma Goliath", "Mana Echoes", "City on Fire", "Collective Inferno",
            "Torbran, Thane of Red Fell", "Roaming Throne", "Veyran, Voice of Duality",
            "Rhystic Study", "Mystic Remora", "The One Ring", "Storm-Kiln Artist",
            "Krenko, Mob Boss", "Goblin Rabblemaster", "Obelisk of Urd", "Siege-Gang Commander"}
KEY_CRE = {"Ovika, Enigma Goliath", "Krenko, Mob Boss", "Goblin Rabblemaster",
           "Siege-Gang Commander", "Veyran, Voice of Duality", "Torbran, Thane of Red Fell",
           "Roaming Throne", "Storm-Kiln Artist", "Goblin Warchief"}
DOUBLER = {"Veyran, Voice of Duality", "Roaming Throne"}
DOUBLER_T = {"Ovika, Enigma Goliath", "Krenko, Mob Boss", "Goblin Rabblemaster",
             "Siege-Gang Commander", "Storm-Kiln Artist", "Goblin Assault",
             "Mogg War Marshal", "Joyful Stormsculptor", "Mana Echoes"}
DAMAGE = {"Stoke the Flames", "Siege-Gang Commander"}
INST_SORC = {c.name for c in DECK if c.is_instant or c.is_sorcery}
SAC = {"Skirk Prospector", "Siege-Gang Commander"}
FUEL = {c.name for c in DECK if not c.is_creature and not c.is_land}
ARTIFACTS = {c.name for c in DECK if c.is_artifact}

RULES = [
    ("convoke-fuel",   lambda a, b: (a in CONVOKE and b in TOKEN) or (b in CONVOKE and a in TOKEN)),
    ("echoes",         lambda a, b: "Mana Echoes" in (a, b) and ((a if b == "Mana Echoes" else b) in TOKEN)),
    ("clamp",          lambda a, b: "Skullclamp" in (a, b) and ((a if b == "Skullclamp" else b) in TOKEN)),
    ("sac-fodder",     lambda a, b: (a in SAC and b in GOBLIN_TOK) or (b in SAC and a in GOBLIN_TOK)),
    ("amp-token",      lambda a, b: (a in AMPL and b in TOKEN) or (b in AMPL and a in TOKEN)),
    ("amp-damage",     lambda a, b: (a in AMPL and b in DAMAGE) or (b in AMPL and a in DAMAGE)),
    ("anthem",         lambda a, b: "Obelisk of Urd" in (a, b) and ((a if b == "Obelisk of Urd" else b) in (GOBLIN_CRE | GOBLIN_TOK))),
    ("doubler",        lambda a, b: (a in DOUBLER and b in DOUBLER_T) or (b in DOUBLER and a in DOUBLER_T)),
    ("ritual-convoke", lambda a, b: (a in RITUAL and b in CONVOKE) or (b in RITUAL and a in CONVOKE)),
    ("rock-top",       lambda a, b: ((a in ROCKS and b in FUEL and by[b].mana_cost.cmc() >= 5) or
                                     (b in ROCKS and a in FUEL and by[a].mana_cost.cmc() >= 5))),
    ("protect",        lambda a, b: (a in COUNTER and b in CRITICAL) or (b in COUNTER and a in CRITICAL)),
    ("greaves",        lambda a, b: "Lightning Greaves" in (a, b) and ((a if b == "Lightning Greaves" else b) in KEY_CRE)),
    ("warchief",       lambda a, b: "Goblin Warchief" in (a, b) and ((a if b == "Goblin Warchief" else b) in GOBLIN_CRE)),
    ("skirk",          lambda a, b: "Skirk Prospector" in (a, b) and ((a if b == "Skirk Prospector" else b) in GOBLIN_CRE)),
    ("flashback",      lambda a, b: "Past in Flames" in (a, b) and ((a if b == "Past in Flames" else b) in INST_SORC)),
    ("joyful-convoke", lambda a, b: "Joyful Stormsculptor" in (a, b) and ((a if b == "Joyful Stormsculptor" else b) in CONVOKE)),
    ("chief-artifact", lambda a, b: "Chief Engineer" in (a, b) and ((a if b == "Chief Engineer" else b) in ARTIFACTS)),
    ("fuel",           lambda a, b: "Ovika, Enigma Goliath" in (a, b) and ((a if b == "Ovika, Enigma Goliath" else b) in FUEL)),
    ("stormkiln-cast", lambda a, b: "Storm-Kiln Artist" in (a, b) and ((a if b == "Storm-Kiln Artist" else b) in INST_SORC)),
]
adj = {n: set() for n in nodes}
edge_rules = {}
for i, a in enumerate(nodes):
    for b in nodes[i + 1:]:
        hits = [r for r, f in RULES if f(a, b)]
        if hits:
            adj[a].add(b); adj[b].add(a)
            edge_rules[(a, b)] = hits

deg = {n: len(adj[n]) for n in nodes}
import networkx as nx
nxg = nx.Graph()
nxg.add_nodes_from(nodes)
for (a, b), rs in edge_rules.items():
    nxg.add_edge(a, b, rules=",".join(rs))

print("nodes:", len(nodes), "| tight edges:", len(edge_rules),
      "| avg degree: %.1f" % (2 * len(edge_rules) / len(nodes)))
comps = list(nx.connected_components(nxg))
print("connected components:", len(comps), [len(c) for c in sorted(comps, key=len, reverse=True)])
comms = list(nx.community.greedy_modularity_communities(nxg))
print("greedy communities:", len(comms), "sizes:", sorted((len(c) for c in comms), reverse=True))
for i, cm in enumerate(comms):
    top = sorted(cm, key=lambda n: -deg[n])
    print("  community %d preview: %s" % (i + 1, ", ".join(top[:10])))

low = sorted([(d, n) for n, d in deg.items() if n != COMMANDER and d < 3])
print("\n-- nodes with degree < 3 (user criterion) --")
for d, n in low:
    rs = sorted({r for (a, b), rs2 in edge_rules.items() for r in rs2 if n in (a, b)})
    print("  deg %d: %-28s %s" % (d, n, rs))
if not low:
    print("  none -> community is connected enough at the 3-edge threshold")
tail = sorted([(d, n) for n, d in deg.items() if n != COMMANDER and d <= 3])
if tail and not low:
    low = tail
    print("\n-- weakest tail (degree == 3) used for replacement search --")
    for d, n in tail:
        rs = sorted({r for (a, b), rs2 in edge_rules.items() for r in rs2 if n in (a, b)})
        print("  deg %d: %-28s %s" % (d, n, rs))

json.dump(nx.node_link_data(nxg), open(os.path.join(HERE, "graph_deck_v12.json"), "w", encoding="utf-8"), indent=0)

# ---- replacement search: engine-hooked UR candidates, curated roles ----
engine_text = ""
for f in ("engine/cards.py", "engine/generic.py", "engine/ai.py"):
    engine_text += open(os.path.join(HERE, f), encoding="utf-8").read()
price_db = json.load(open(os.path.join(HERE, "rulebook/data/card_prices.json"), encoding="utf-8"))

# curated roles for engine-hooked candidates (from earlier engine-support audit)
CURATED = {
    "Seething Song": {"ritual", "instsorc"}, "Rite of Flame": {"ritual", "instsorc"},
    "Brass's Bounty": {"instsorc"}, "Time Reversal": {"instsorc"}, "Echo of Eons": {"instsorc"},
    "Mizzix's Mastery": {"instsorc"}, "Cerebral Download": {"instsorc"}, "Lunar Insight": {"instsorc"},
    "Unfathomable Truths": {"instsorc"}, "Focus the Mind": {"instsorc"},
    "Travel the Overworld": {"instsorc"}, "Vivisurgeon's Insight": {"instsorc"},
    "Guttersnipe": {"creature", "pinger"}, "Coruscation Mage": {"creature", "pinger"},
    "Urabrask": {"creature", "pinger"}, "Niv-Mizzet, Parun": {"creature", "pinger"},
    "Idol of Oblivion": {"token", "artifact"}, "Chrome Mox": {"rock", "artifact"},
    "Ruby Medallion": {"reducer", "artifact"}, "Strionic Resonator": {"doubler2", "artifact"},
    "Metallurgic Summonings": {"eng"}, "Saheeli, the Gifted": {"eng"},
    "Birgi, God of Storytelling": {"mana", "creature"}, "Howling Mine": {"draw", "artifact"},
    "Aetherflux Reservoir": {"artifact"},
}

def added_edges(name, roles, ignore=None):
    cnt = collections.Counter()
    if "ritual" in roles:
        cnt["ritual-convoke"] = len(CONVOKE - {ignore})
    if "token" in roles:
        cnt["convoke-fuel"] = len(CONVOKE - {ignore})
        cnt["echoes"] = 1 if "Mana Echoes" not in {ignore} else 0
        cnt["clamp"] = 1 if "Skullclamp" not in {ignore} else 0
        cnt["amp-token"] = len(AMPL - {ignore})
        cnt["anthem"] = 1 if "Obelisk of Urd" not in {ignore} else 0
        cnt["sac-fodder"] = 1 if ("Skirk Prospector" in nodes and "Skirk Prospector" != ignore) else 0
    if "rock" in roles:
        cnt["rock-top"] = sum(1 for n in FUEL - {ignore} if by[n].mana_cost.cmc() >= 5)
        cnt["fuel"] = 1
        cnt["chief-artifact"] = 1 if "Chief Engineer" not in {ignore} else 0
    if "instsorc" in roles:
        cnt["fuel"] = 1
        cnt["flashback"] = 1 if "Past in Flames" not in {ignore} else 0
    if "pinger" in roles:
        cnt["amp-damage"] = len(AMPL - {ignore})
        cnt["pinger-spells"] = len(INST_SORC)  # dynamic engine value: pings every instant/sorcery
    if "counter" in roles:
        cnt["protect"] = len(CRITICAL - {ignore})
    if "reducer" in roles:
        cnt["reducer-red"] = sum(1 for n in nodes if n != ignore and "R" in (by[n].colors or set()) and n != COMMANDER)
    if "draw" in roles:
        cnt["fuel"] = 1
    return cnt

if low:
    print("\n-- replacements for thin nodes (engine-hooked UR candidates; +edges = new graph edges) --")
    for d, thin in low:
        best = []
        for cname, roles in CURATED.items():
            if cname in nodes or cname == thin:
                continue
            try:
                cd = oracle.require(cname)
            except KeyError:
                continue
            if cd.is_land or (cd.color_identity - {"U", "R"}):
                continue
            gained = sum(added_edges(cname, roles, ignore=thin).values())
            if gained <= d:
                continue
            best.append((gained, cname, roles, price_db.get(cname)))
        best.sort(key=lambda t: (-t[0], float(t[3] or 999)))
        print("\n  %s (deg %d):" % (thin, d))
        for g, cn, roles, pr in best[:4]:
            print("    +%-3d edges (net %+d)  %-30s $%-7s roles=%s" % (g, g - d, cn, pr if pr else "?", sorted(roles)))

# render community-colored PNG
import os as _os
_os.environ["MPLCONFIGDIR"] = _os.path.join(HERE, ".mplcache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
cmap = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
node_c = {}
for i, cm in enumerate(comms):
    for n in cm:
        node_c[n] = cmap[i % len(cmap)]
pos = nx.spring_layout(nxg, seed=11, k=0.5, iterations=150)
fig, ax = plt.subplots(figsize=(22, 16), dpi=110)
nx.draw_networkx_edges(nxg, pos, ax=ax, width=0.4, edge_color="#cccccc", alpha=0.45)
nx.draw_networkx_nodes(nxg, pos, ax=ax,
                       node_size=[300 + 26 * deg[n] for n in nodes],
                       node_color=[node_c[n] for n in nodes], alpha=0.92)
nx.draw_networkx_labels(nxg, pos, ax=ax, font_size=6.5)
ax.set_title("Ovika convoke v12 - synergy graph, %d nodes / %d tight edges, colored by detected community (size = degree)"
             % (len(nodes), len(edge_rules)), fontsize=13)
ax.axis("off")
fig.savefig(os.path.join(HERE, "graph_deck_v12.png"), bbox_inches="tight")
print("\nsaved graph_deck_v12.json + graph_deck_v12.png")
