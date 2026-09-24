"""Terra diagnostic: per-seed failure taxonomy for seeds 1-10 (or given list)."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pod_terra import play_pod_seed

SEEDS = list(range(1, 11))
DECK = next((a for a in sys.argv[1:] if a.endswith(".py")), "deck_terra.py")

def main():
    rows = []
    for seed in SEEDS:
        r = play_pod_seed(seed, 14, terra_deck=DECK)
        logs = r["logs"]
        terra_seat = "P1"
        cast = [ln for ln in logs if ln.startswith(f"      [resolve] {terra_seat}: Terra,") or f"{terra_seat} casts Terra" in ln]
        trance = [ln for ln in logs if "Terra Trance" in ln]
        esper = [ln for ln in logs if "Esper Terra chapter" in ln]
        simplified = [ln for ln in logs if "(simplified" in ln]
        combo = [ln for ln in logs if "bounded Esper Terra copy loop" in ln]
        kills = [ln for ln in logs if "!! " in ln and "loses" in ln]
        winner = r["winner"]
        deck = r["deck_of"].get(winner, "-")
        life = r["life"].get(terra_seat)
        # fetch / ramp evidence
        fetches = [ln for ln in logs if "fetches" in ln]
        rows.append((seed, winner or "-", deck or "-", r["win_turn"] or 0, life, len(cast), len(trance),
                     len(esper), len(fetches), len(simplified), len(combo), len(kills)))
    print(f"{'seed':>4} {'winner':>6} {'deck':<14} {'turn':>4} {'TerraLife':>9} {'cast':>4} {'trance':>6} {'esper':>5} {'fetch':>5} {'simpl':>5} {'combo':>5} {'kills':>5}")
    for row in rows:
        print(f"{row[0]:>4} {row[1]:>6} {row[2]:<14} {row[3]:>4} {row[4]:>9} {row[5]:>4} {row[6]:>6} {row[7]:>5} {row[8]:>5} {row[9]:>5} {row[10]:>5} {row[11]:>5}")
    # detail for losses
    for row in rows:
        seed, winner, deck, wturn, life = row[0], row[1], row[2], row[3], row[4]
        if deck != "terra deck":
            r = play_pod_seed(seed, 14, terra_deck=DECK)
            logs = r["logs"]
            print(f"\n===== seed {seed} (Terra loss) =====")
            interesting = [ln for ln in logs if any(k in ln for k in
                ("[resolve] P1:", "P1 casts", "P1 plays land", "Trance", "chapter",
                 "!! ", "simplified", "P1 draws (hand", "mulligan", "Terra ETB",
                 "fetches", "attacker: P1", "deals", "loses life", "!! P1"))]
            for ln in interesting[-60:]:
                print("  " + ln)

if __name__ == "__main__":
    main()
