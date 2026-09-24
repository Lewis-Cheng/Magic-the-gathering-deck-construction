# deck_v2.py - Ovika v2: collection + targeted upgrades (cards marked "buy" are not in collection)
# tag guide: ramp, rock, drawN, counter, removal, big, room, body, clamp, is (instant/sorcery), etc.
DECK = [
    # --- Lands (25) ---
    ("Mountain", 0, "land", 0, 0, ["basic", "r", "mountain"]),
    ("Mountain", 0, "land", 0, 0, ["basic", "r", "mountain"]),
    ("Mountain", 0, "land", 0, 0, ["basic", "r", "mountain"]),
    ("Mountain", 0, "land", 0, 0, ["basic", "r", "mountain"]),
    ("Mountain", 0, "land", 0, 0, ["basic", "r", "mountain"]),
    ("Command Tower", 0, "land", 0, 0, ["any"]),
    ("Exotic Orchard", 0, "land", 0, 0, ["any"]),
    ("Path of Ancestry", 0, "land", 0, 0, ["any"]),
    ("Baron, Airship Kingdom", 0, "land", 0, 0, ["u", "r"]),
    ("Peculiar Lighthouse", 0, "land", 0, 0, ["u", "r"]),
    ("Jidoor, Aristocratic Capital // Overture", 0, "land", 0, 0, ["u", "town"]),
    ("Crossroads Village", 0, "land", 0, 0, ["u", "r", "town"]),
    ("Command Bridge", 0, "land", 0, 0, ["any"]),
    ("Cascading Cataracts", 0, "land", 0, 0, ["cataracts"]),
    ("Power Depot", 0, "land", 0, 0, ["any"]),
    ("Terramorphic Expanse", 0, "land", 0, 0, ["fetcher"]),
    ("The Autonomous Furnace", 0, "land", 0, 0, ["r"]),
    ("The Monumental Facade", 0, "land", 0, 0, []),
    ("Adventurer's Inn", 0, "land", 0, 0, ["town"]),
    ("Eden, Seat of the Sanctum", 0, "land", 0, 0, []),
    ("Animal Sanctuary", 0, "land", 0, 0, []),
    ("Inventors' Fair", 0, "land", 0, 0, []),
    ("Mirrorpool", 0, "land", 0, 0, []),
    ("Mystifying Maze", 0, "land", 0, 0, []),
    ("Terrain Generator", 0, "land", 0, 0, ["terrain"]),
    # --- Ramp (13) ---
    ("Sol Ring", 1, "spell", 0, 0, ["ramp", "rock", "+2"]),
    ("Arcane Signet", 2, "spell", 0, 0, ["ramp", "rock", "+1", "anycolor"]),
    ("Everflowing Chalice", 2, "spell", 0, 0, ["ramp", "rock", "+2"]),
    ("Pristine Talisman", 3, "spell", 0, 0, ["ramp", "rock", "+1", "life"]),
    ("Phyrexian Atlas", 3, "spell", 0, 0, ["ramp", "rock", "+1", "anycolor"]),
    ("The Eternity Elevator", 5, "spell", 0, 0, ["ramp", "rock", "+3"]),
    ("Burnished Hart", 3, "creature", 0, 0, ["ramp", "hart"]),
    ("PuPu UFO", 2, "creature", 0, 0, ["ramp", "pupu"]),
    ("Three Tree Mascot", 2, "creature", 0, 0, ["ramp", "rock", "+1", "anycolor"]),
    ("Myr Convert", 2, "creature", 0, 0, ["ramp", "rock", "+1", "anycolor"]),
    ("Koth, Fire of Resistance", 4, "spell", 0, 2, ["ramp", "koth"]),
    ("The Fire Crystal", 4, "spell", 0, 2, ["redcost", "firecrystal"]),
    ("Skirk Prospector", 1, "creature", 0, 1, ["skirk", "buy"]),
    # --- Draw (16) ---
    ("Skullclamp", 1, "spell", 0, 0, ["clamp"]),
    
    
    ("Grab the Prize", 2, "spell", 0, 1, ["draw2", "is"]),
    
    ("Lunar Insight", 3, "spell", 2, 0, ["draw", "lunar", "is"]),
    ("Marina Vendrell's Grimoire", 6, "spell", 1, 0, ["draw5", "grimoire"]),
    ("Travel the Overworld", 7, "spell", 2, 0, ["draw4", "travel", "towns", "is"]),
    ("Vivisurgeon's Insight", 5, "spell", 2, 0, ["draw3", "is"]),
    ("Unfathomable Truths", 5, "spell", 1, 0, ["draw3", "body", "is"]),
    ("Focus the Mind", 5, "spell", 1, 0, ["draw3", "focus", "is"]),
    ("Cerebral Download", 5, "spell", 1, 0, ["draw3", "is"]),
    ("Glimmerburst", 4, "spell", 1, 0, ["draw2", "body", "is"]),
    
    ("Windfall", 3, "spell", 1, 0, ["windfall", "is", "buy"]),
    ("Echo of Eons", 6, "spell", 2, 0, ["echo", "is", "buy"]),
    # --- Interaction (10) ---
    ("Cryptic Command", 4, "spell", 3, 0, ["counter", "draw1", "is"]),
    ("An Offer You Can't Refuse", 1, "spell", 1, 0, ["counter", "is"]),
    
    
    
    
    
    
    
    
    # --- Engines / creatures (17) ---
    ("Tellah, Great Sage", 5, "creature", 1, 1, ["tellah"]),
    ("Goblin Rabblemaster", 3, "creature", 0, 2, ["rabble"]),
    
    
    
    ("Thryx, the Sudden Storm", 5, "creature", 2, 0, ["thryx"]),
    ("Trinket Mage", 3, "creature", 2, 0, ["trinket"]),
    
    ("Urabrask's Forge", 3, "spell", 0, 2, ["forge"]),
    ("Krenko, Mob Boss", 4, "creature", 0, 2, ["krenko", "buy"]),
    ("Veyran, Voice of Duality", 3, "creature", 1, 1, ["veyran", "buy"]),
    ("Goblin Electromancer", 2, "creature", 1, 1, ["electromancer", "buy"]),
    ("Storm-Kiln Artist", 4, "creature", 0, 3, ["stormkiln", "buy"]),
    ("Saheeli, the Gifted", 4, "spell", 1, 1, ["saheeli", "buy"]),
    ("Shark Typhoon", 6, "spell", 1, 0, ["shark", "buy"]),
    ("Metallurgic Summonings", 5, "spell", 2, 0, ["metallurgic", "buy"]),
    ("Strionic Resonator", 2, "spell", 0, 0, ["strionic", "buy"]),
    # --- Big payoffs (10) ---
    
    
    ("Breaching Dragonstorm", 5, "spell", 0, 4, ["big", "breach"]),
    
    ("Purphoros's Intervention", 1, "spell", 0, 1, ["big", "purphoros", "xspell", "is"]),
    ("Mizzix's Mastery", 4, "spell", 0, 1, ["big", "mizzix", "is", "buy"]),
    ("Brass's Bounty", 7, "spell", 0, 4, ["big", "bounty", "buy"]),
    ("Mana Geyser", 5, "spell", 0, 2, ["big", "geyser", "is", "buy"]),
    ("Brightstone Ritual", 1, "spell", 0, 1, ["big", "brightstone", "is", "buy"]),
    ("Song of Totentanz", 1, "spell", 0, 1, ["big", "song", "xspell", "is", "buy"]),
    # --- Rooms (5) ---
    ("Smoky Lounge // Misty Salon", 3, "spell", 0, 2, ["room", "smoky"]),
    ("Meat Locker // Drowned Diner", 3, "spell", 2, 0, ["room", "meat"]),
    ("Ticket Booth // Tunnel of Hate", 3, "spell", 0, 2, ["room", "ticket"]),
    
    ("Central Elevator // Promising Stairs", 4, "spell", 2, 0, ["room", "elevator"]),
    # --- Misc (6) ---
    
    ("Krenko's Command", 2, "spell", 0, 1, ["body2", "is", "buy"]),
    ("Dragon Fodder", 2, "spell", 0, 1, ["body2", "is", "buy"]),
    
    
    ("Lightning Greaves", 2, "spell", 0, 0, ["greaves", "buy"]),
    # --- v3 upgrades ---
    ("Frantic Search", 3, "spell", 2, 0, ["frantic", "is", "buy"]),
    ("Hordeling Outburst", 3, "spell", 0, 2, ["body3", "goblin", "is", "buy"]),
    ("Empty the Warrens", 4, "spell", 0, 2, ["warrens", "goblin", "is", "buy"]),
    ("Past in Flames", 3, "spell", 0, 2, ["past", "is", "buy"]),
    ("Battle Hymn", 2, "spell", 0, 1, ["hymn", "is", "buy"]),
    ("Seething Song", 3, "spell", 0, 2, ["seething", "is", "buy"]),
    ("Mogg War Marshal", 2, "creature", 0, 1, ["body2", "goblin", "buy"]),
    ("Siege-Gang Commander", 5, "creature", 0, 3, ["body3", "goblin", "buy"]),
    ("Goblin Warchief", 3, "creature", 0, 2, ["warchief", "goblin", "buy"]),
    ("Mana Echoes", 3, "spell", 0, 0, ["echoes", "buy"]),
    ("Jeska's Will", 3, "spell", 0, 2, ["jeskas", "is", "buy"]),
    # --- v7 convoke package ---
    ("Transcendent Message", 4, "spell", 4, 0, ["xspell", "convoke", "message", "is", "buy"]),
    ("Meeting of Minds", 4, "spell", 1, 0, ["convoke", "draw2", "is", "buy"]),
    ("Stoke the Flames", 4, "spell", 0, 2, ["convoke", "removal", "is", "buy"]),
    ("Complete the Circuit", 6, "spell", 1, 0, ["convoke", "big", "circuit", "is", "buy"]),
    ("Unexpected Assistance", 5, "spell", 2, 0, ["convoke", "draw3", "is", "buy"]),
    ("Will-Forged Golem", 6, "creature", 0, 0, ["convoke", "body", "buy"]),
    ("Artistic Refusal", 6, "spell", 2, 0, ["convoke", "counter", "draw2", "is", "buy"]),
    ("Shatter the Source", 6, "spell", 0, 1, ["convoke", "removal", "is", "buy"]),
    ("Temporal Cleansing", 4, "spell", 1, 0, ["convoke", "removal", "is", "buy"]),
]
