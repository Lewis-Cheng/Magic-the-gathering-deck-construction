"""Terra diagnostic detail: print key events for given seeds."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pod_terra import play_pod_seed

SEEDS = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [2, 3, 4]

def main():
    for seed in SEEDS:
        r = play_pod_seed(seed, 14)
        logs = r["logs"]
        winner = r["winner"]
        deck = r["deck_of"].get(winner, "-")
        print(f"\n===== seed {seed}: winner {winner} ({deck}) turn {r['win_turn']} =====")
        keys = ("P1 casts", "P1 plays land", "Trance", "chapter", "!! ", "Terra ETB",
                "fetches", "deals ", "attacker: ", "P1 draws (hand", "mulligan",
                "Eldest", "Titan", "Folly", "Leviathan", "Opalescence", "Starfield",
                "Archon", "Setessan", "Sythis", "Weaver", "Tithe", "Library",
                "Yenna", "Spark", "Mirrormade", "Neoform", "Evolution",
                "reanimate", "Wizard deals", "sacrifices")
        for ln in logs:
            if any(k in ln for k in keys):
                print("  " + ln)

if __name__ == "__main__":
    main()
