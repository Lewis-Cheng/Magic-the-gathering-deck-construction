import sys, os
sys.path.insert(0, "ovika")
from engine.oracle import Oracle, Pool
from engine.game import Game, Permanent
from engine.ai import AI
from engine.generic import generic_activatable
from engine import cards

oracle = Oracle()
pool = Pool(oracle, os.path.join("ovika", "deck_terra_v1.py"))
deck = pool.decklist()
game = Game(deck, pool.commander, seed=1, ais=[AI("A"), AI("B"), AI("C"), AI("D")],
            max_turns=5, oracle=oracle)
game.setup()
pl = game.players[0]
fetch = next(c for c in pl.hand if c.name == "Arid Mesa")
pl.hand.remove(fetch)
perm = Permanent(card=fetch, controller=pl, owner=pl)
pl.battlefield.append(perm)
print("generic:", generic_activatable(game, pl))
print("cards:", cards.activatable(game, pl))
