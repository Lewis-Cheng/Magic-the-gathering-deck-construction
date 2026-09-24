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
    
    
    
    ("Koth, Fire of Resistance", 4, "spell", 0, 2, ["ramp", "koth"]),
    ("The Fire Crystal", 4, "spell", 0, 2, ["redcost", "firecrystal"]),
    ("Skirk Prospector", 1, "creature", 0, 1, ["skirk", "buy"]),
    # --- Draw (16) ---
    ("Skullclamp", 1, "spell", 0, 0, ["clamp"]),
    ("Think Twice", 2, "spell", 1, 0, ["draw1", "is"]),
    ("Thrill of Possibility", 2, "spell", 0, 1, ["draw2", "is"]),
    ("Grab the Prize", 2, "spell", 0, 1, ["draw2", "is"]),
    ("Light Up the Stage", 3, "spell", 0, 2, ["draw2", "is"]),
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
    ("Shock Brigade", 2, "creature", 0, 1, ["mobilize"]),
    ("Chimney Rabble", 4, "creature", 0, 3, ["body2"]),
    ("Heroes of the Revel", 5, "creature", 0, 4, ["body2"]),
    ("Thryx, the Sudden Storm", 5, "creature", 2, 0, ["thryx"]),
    ("Trinket Mage", 3, "creature", 2, 0, ["trinket"]),
    ("Micromancer", 4, "creature", 2, 0, ["micromancer"]),
    
    ("Krenko, Mob Boss", 4, "creature", 0, 2, ["krenko", "buy"]),
    ("Veyran, Voice of Duality", 3, "creature", 1, 1, ["veyran", "buy"]),
    ("Goblin Electromancer", 2, "creature", 1, 1, ["electromancer", "buy"]),
    ("Storm-Kiln Artist", 4, "creature", 0, 3, ["stormkiln", "buy"]),
    ("Saheeli, the Gifted", 4, "spell", 1, 1, ["saheeli", "buy"]),
    ("Shark Typhoon", 6, "spell", 1, 0, ["shark", "buy"]),
    ("Metallurgic Summonings", 5, "spell", 2, 0, ["metallurgic", "buy"]),
    ("Strionic Resonator", 2, "spell", 0, 0, ["strionic", "buy"]),
    # --- Big payoffs (10) ---
    ("Sea God's Scorn", 6, "spell", 2, 0, ["big", "is"]),
    
    
    ("Triple Triad", 6, "spell", 0, 3, ["big", "triad"]),
    ("Purphoros's Intervention", 1, "spell", 0, 1, ["big", "purphoros", "xspell", "is"]),
    ("Mizzix's Mastery", 4, "spell", 0, 1, ["big", "mizzix", "is", "buy"]),
    ("Brass's Bounty", 7, "spell", 0, 4, ["big", "bounty", "buy"]),
    ("Mana Geyser", 5, "spell", 0, 2, ["big", "geyser", "is", "buy"]),
    ("Brightstone Ritual", 1, "spell", 0, 1, ["big", "brightstone", "is", "buy"]),
    ("Song of Totentanz", 1, "spell", 0, 1, ["big", "song", "xspell", "is", "buy"]),
    # --- Rooms (5) ---
    ("Smoky Lounge // Misty Salon", 3, "spell", 0, 2, ["room", "smoky"]),
    
    ("Ticket Booth // Tunnel of Hate", 3, "spell", 0, 2, ["room", "ticket"]),
    
    
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
    ("Island", 0, "land", 0, 0, ["basic", "u", "island", "buy"]),
    ("Island", 0, "land", 0, 0, ["basic", "u", "island", "buy"]),
    ("Mountain", 0, "land", 0, 0, ["basic", "r", "mountain", "buy"]),
    ("Swiftwater Cliffs", 0, "land", 0, 0, ["u", "r", "buy"]),
    ("Shivan Reef", 0, "land", 0, 0, ["u", "r", "buy"]),
    ("Mind Stone", 2, "spell", 0, 0, ["ramp", "rock", "+1", "buy"]),
    ("Izzet Signet", 2, "spell", 0, 0, ["ramp", "rock", "+1", "anycolor", "buy"]),
    ("Fellwar Stone", 2, "spell", 0, 0, ["ramp", "rock", "+1", "anycolor", "buy"]),
    ("Wayfarer's Bauble", 1, "spell", 0, 0, ["ramp", "bauble", "buy"]),
]
