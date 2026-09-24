"""Terra combo synergy graph: tight pair rules + strategy audit.

Edge families are engine lines only (no mass "connects to everything"):
- combo: Esper Terra <-> Folly/Mirrormade/Estrid's (the copy loop)
- tutor: the 4 tutors -> Folly/Mirrormade (combo assembly)
- ramp: mana sources -> Trance threshold (commander + enablers)
- enchantress: Sythis/3 Enchantresses/Champion/Eidolon/Presence -> enchantments
- copy-value: Yenna/Spark Double/Estrid's -> nonlegendary enchantments/creatures
- protection: Abolisher/Spinner/counters/Intervention -> commander/enablers
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.oracle import Oracle, Pool

HERE = os.path.dirname(os.path.abspath(__file__))
oracle = Oracle()
pool = Pool(oracle, os.path.join(HERE, "deck_terra.py"))
COMMANDER = pool.commander.name
DECK = [c for c in pool.decklist() if not c.is_land]
by = {c.name: c for c in DECK}
by[COMMANDER] = oracle.require(COMMANDER)
nodes = list(by.keys())

def tags(c):
    return set(c.tags or [])

ENCH = {c.name for c in DECK if c.is_enchantment}
NONLEGEND_ENCH = {c.name for c in DECK if c.is_enchantment and not c.is_legendary}
ENABLERS = {"The Apprentice's Folly", "Mirrormade", "Estrid's Invocation"}
TUTORS = {"Enlightened Tutor", "Idyllic Tutor", "Demonic Counsel", "Entomb"}
RAMP = {c.name for c in DECK if tags(c) & {"ramp", "rock"} or c.name in ("Sanctum Weaver", "Delighted Halfling")}
DRAW = {c.name for c in DECK if tags(c) & {"draw"} or c.name in ("Sylvan Library", "Rhystic Study")}
PROTECT = {"Grand Abolisher", "Destiny Spinner", "An Offer You Can't Refuse",
           "Counterspell", "Heroic Intervention"}
TRANSFORM = {"Moonmist", "Spark Double", "Dark Ritual"}
ENCHANTRESS = {"Sythis, Harvest's Hand", "Mesa Enchantress", "Verduran Enchantress",
               "Enchantress's Presence", "Setessan Champion", "Eidolon of Blossoms",
               "Archon of Sun's Grace"}

RULES = [
    ("combo-enabler", lambda a, b: (a == COMMANDER and b in ENABLERS) or (b == COMMANDER and a in ENABLERS)),
    ("tutor-enabler", lambda a, b: (a in TUTORS and b in ENABLERS) or (b in TUTORS and a in ENABLERS)),
    ("ramp-trance",   lambda a, b: (a == COMMANDER and b in RAMP) or (b == COMMANDER and a in RAMP)),
    ("enchantress",   lambda a, b: (a in ENCHANTRESS and b in ENCH) or (b in ENCHANTRESS and a in ENCH)),
    ("weaver-ench",   lambda a, b: "Sanctum Weaver" in (a, b) and ((a if b == "Sanctum Weaver" else b) in ENCH)),
    ("copy-value",    lambda a, b: (a in ("Yenna, Redtooth Regent", "Estrid's Invocation", "Mirrormade")
                                    and b in NONLEGEND_ENCH) or
                                   (b in ("Yenna, Redtooth Regent", "Estrid's Invocation", "Mirrormade")
                                    and a in NONLEGEND_ENCH)),
    ("protect",       lambda a, b: (a in PROTECT and b in (ENABLERS | {COMMANDER})) or
                                   (b in PROTECT and a in (ENABLERS | {COMMANDER}))),
    ("transform",     lambda a, b: (a == COMMANDER and b in TRANSFORM) or (b == COMMANDER and a in TRANSFORM)),
    ("velocity",      lambda a, b: (a in DRAW and b in (ENABLERS | TUTORS)) or
                                   (b in DRAW and a in (ENABLERS | TUTORS))),
]

adj = {n: set() for n in nodes}
edge_rules = collections.defaultdict(set)
for a in nodes:
    for b in nodes:
        if a >= b:
            continue
        for rname, rule in RULES:
            if rule(a, b):
                adj[a].add(b)
                adj[b].add(a)
                edge_rules[(a, b)].add(rname)

deg = {n: len(adj[n]) for n in nodes}
low = sorted(((deg[n], n) for n in nodes if deg[n] < 3), key=lambda t: (t[0], t[1]))
print("nodes:", len(nodes), "edges:", sum(len(v) for v in adj.values()) // 2)
print("components:", "1 (connected)" if all(deg[n] > 0 for n in nodes) else "disconnected; isolates listed below")
print("isolates:", [n for n in nodes if deg[n] == 0])
print("hubs (deg>=5):", sorted((n for n in nodes if deg[n] >= 5), key=lambda n: -deg[n]))
print("low-degree (<3):")
for d, n in low:
    rs = sorted({r for (a, b), rs2 in edge_rules.items() for r in rs2 if n in (a, b)})
    print("  deg %d: %-34s %s" % (d, n, rs))

import networkx as nx
nxg = nx.Graph()
nxg.add_nodes_from(nodes)
nxg.add_edges_from(edge_rules.keys())
comms = list(nx.algorithms.community.greedy_modularity_communities(nxg))
print("communities:", len(comms))
for i, cm in enumerate(comms):
    print("  C%d (%d): %s" % (i + 1, len(cm), ", ".join(sorted(cm))))

json.dump(nx.node_link_data(nxg), open(os.path.join(HERE, "graph_terra.json"), "w", encoding="utf-8"), indent=0)

os.environ.setdefault("MPLCONFIGDIR", os.path.join(HERE, ".mplcache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
cmap = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
node_c = {}
for i, cm in enumerate(comms):
    for n in cm:
        node_c[n] = cmap[i % len(cmap)]
pos = nx.spring_layout(nxg, seed=11, k=0.55, iterations=160)
fig, ax = plt.subplots(figsize=(20, 15), dpi=110)
nx.draw_networkx_edges(nxg, pos, ax=ax, width=0.4, edge_color="#cccccc", alpha=0.45)
nx.draw_networkx_nodes(nxg, pos, ax=ax,
                       node_size=[300 + 24 * deg[n] for n in nodes],
                       node_color=[node_c.get(n, "#999999") for n in nodes], alpha=0.92)
nx.draw_networkx_labels(nxg, pos, ax=ax, font_size=6.5)
ax.set_title("Terra combo graph - %d nodes / %d tight edges, colored by community (size = degree)"
             % (len(nodes), sum(len(v) for v in adj.values()) // 2))
ax.axis("off")
fig.savefig(os.path.join(HERE, "graph_terra.png"), bbox_inches="tight")
print("saved graph_terra.json + graph_terra.png")
