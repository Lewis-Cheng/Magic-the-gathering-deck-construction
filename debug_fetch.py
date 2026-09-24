import sys, os
sys.path.insert(0, "ovika")
from engine.oracle import Oracle, Pool
from engine.game import Game, Permanent
from engine.ai import AI
from engine.cards import activatable, mana_abilities

oracle = Oracle()
pool = Pool(oracle, os.path.join("ovika", "deck_terra_v1.py"))
deck = pool.decklist()
game = Game(deck, pool.commander, seed=1, ais=[AI("A"), AI("B"), AI("C"), AI("D")],
            max_turns=5, oracle=oracle)
game.setup()
pl = game.players[0]
# simulate: play a fetch land manually
fetch = next(c for c in pl.hand if c.name in ("Marsh Flats", "Windswept Heath", "Wooded Foothills", "Arid Mesa"))
print("fetch in hand:", fetch.name)
pl.hand.remove(fetch)
perm = Permanent(card=fetch, controller=pl, owner=pl)
pl.battlefield.append(perm)
acts = activatable(game, pl)
print("activatable:", [a[0] for a in acts])
print("mana sources:", [(q.card.name, mana_abilities(game, q)) for q in pl.battlefield])
