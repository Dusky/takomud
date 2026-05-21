"""
Takomud help entries — in-world flavored documentation for all custom systems.
"""

HELP_ENTRY_DICTS = [
    {
        "key": "stat",
        "aliases": ["stats"],
        "category": "Character",
        "text": """
|wstat|n — Display your vital statistics.

Shows your current HP, Sanity, Fear, and other quick stats.
For a full character sheet including level, gold, and reputation, use |wscore|n.

Usage: stat
        """,
    },
    {
        "key": "score",
        "aliases": ["sc"],
        "category": "Character",
        "text": """
|wscore|n — Full character sheet.

Displays everything about your character:
  |wLevel / XP|n       — Your current level and experience progress
  |wClass|n            — Your chosen character class and its special ability
  |wHP|n               — Physical health (0 = death)
  |wSanity|n           — Mental stability (0 = psychotic break, then reset to 10)
  |wFear|n             — Tension meter (40+ = attack penalty; 75+ = panic risk)
  |wAttack / Defense|n — Combat modifiers
  |wGold|n             — Currency
  |wReputation|n       — Standing with each faction (-100 to +100)
  |wActive Quests|n    — Current quest objectives

Usage: score
        """,
    },
    {
        "key": "class",
        "aliases": ["charclass"],
        "category": "Character",
        "text": """
|wclass <name>|n — Choose your character class (one-time, permanent).

Available classes:
  |wsurvivor|n  — |xGrit:|n Survive one killing blow per hour at 1 HP instead of dying.
  |wscholar|n   — |xVeil-sight:|n Reading lore and using the 'lore' command costs no Sanity.
  |wcultist|n   — |xCommune:|n Hollow-faction mobs do not aggro you on sight.
  |whunter|n    — |xTrack:|n Sense hostile mobs in adjacent rooms (costs 5 Fear).
  |wvagrant|n   — |xWanderer:|n Gain +2 XP each time you discover a new room.

You cannot change your class after selecting one.

Usage: class survivor
        """,
    },
    {
        "key": "track",
        "category": "Character",
        "text": """
|wtrack|n — Hunter class ability: sense hostile mobs in adjacent rooms.

Lists mobs in rooms directly connected to your current location.
Costs 5 Fear each use. Only available to the Hunter class.

Usage: track
        """,
    },
    {
        "key": "attack",
        "aliases": ["kill", "fight"],
        "category": "Combat",
        "text": """
|wattack <target>|n — Begin combat with a target.

Initiates auto-attack. You will strike your target every 4 seconds automatically.
Your first strike fires immediately.

Fear affects combat:
  |yFear 40-74|n — |x-2 attack penalty|n
  |rFear 75+|n   — |x-4 attack penalty; 20% chance to freeze instead of striking|n

Use |wstop|n to disengage. Use |wflee|n to attempt escape.

Usage: attack hollow wretch
        """,
    },
    {
        "key": "stop",
        "category": "Combat",
        "text": """
|wstop|n — Disengage from combat without fleeing.

Clears your combat target and halts auto-attack. The mob may still be hostile.
If the mob has its own combat script running, it will continue attacking you
until you leave the room.

Usage: stop
        """,
    },
    {
        "key": "flee",
        "category": "Combat",
        "text": """
|wflee|n — Attempt to escape combat by running through a random exit.

Drops combat and moves you to an adjacent room. Not guaranteed to succeed
if there are no exits. Raises Fear slightly.

Usage: flee
        """,
    },
    {
        "key": "consider",
        "aliases": ["con"],
        "category": "Combat",
        "text": """
|wconsider <target>|n — Gauge how dangerous a target is relative to you.

Compares the target's HP, attack, and defense against your own stats
and gives a rough threat assessment.

Usage: consider hollow wretch
        """,
    },
    {
        "key": "inventory",
        "aliases": ["inv", "i"],
        "category": "Inventory",
        "text": """
|winventory|n — List everything you are carrying.

Shows all items in your possession, grouped by type, with equipment slots noted.

Usage: inventory
        """,
    },
    {
        "key": "equip",
        "aliases": ["wear", "wield"],
        "category": "Inventory",
        "text": """
|wequip <item>|n — Equip a weapon or piece of armor.

Slots: head, chest, hands, legs, feet, main_hand, off_hand, neck.
Weapons go to main_hand. Equipped armor adds defense_bonus to your effective defense.
Equipped weapons use their damage_dice and attack_bonus in combat.

Usage: equip rusted blade
        """,
    },
    {
        "key": "unequip",
        "aliases": ["remove", "unwield"],
        "category": "Inventory",
        "text": """
|wunequip <slot>|n — Remove equipped item from a slot.

Usage: unequip main_hand
        """,
    },
    {
        "key": "use",
        "category": "Inventory",
        "text": """
|wuse <item>|n — Use a consumable item.

Consumables are destroyed on use and apply their effects immediately:
HP restoration, Sanity restoration, Fear reduction, and combinations thereof.

Usage: use herbal tincture
        """,
    },
    {
        "key": "drop",
        "category": "Inventory",
        "text": """
|wdrop <item>|n — Drop an item in your current room.

Quest items cannot be dropped. Some cursed items resist being discarded.

Usage: drop iron key
        """,
    },
    {
        "key": "give",
        "category": "Inventory",
        "text": """
|wgive <item> to <target>|n — Give an item to an NPC.

Used to complete delivery quest objectives. The NPC must be in the same room.

Usage: give sealed letter to the archivist
        """,
    },
    {
        "key": "read",
        "category": "Exploration",
        "text": """
|wread <document>|n — Read a lore document, book, journal, or inscription.

Most documents cost 1-5 Sanity to read. The Scholar class (Veil-sight) reads
lore without Sanity cost.

The things written here are true. That is what makes them dangerous.

Usage: read the warden's journal
        """,
    },
    {
        "key": "lore",
        "category": "Exploration",
        "text": """
|wlore <topic>|n — Recall lore about a subject from memory.

Costs 3 Sanity (free for Scholars). Returns world lore if a matching
entry exists in the codex.

Usage: lore hollow
Usage: lore unspoken
        """,
    },
    {
        "key": "map",
        "aliases": ["m"],
        "category": "Exploration",
        "text": """
|wmap|n — Display a text map of your current location and nearby rooms.

Shows your current room at center with adjacent rooms visible to two hops.
Dark rooms (requiring a light source) show as unknown until lit.

Usage: map
        """,
    },
    {
        "key": "quest",
        "aliases": ["quests", "q"],
        "category": "Quests",
        "text": """
|wquest|n — View your active quests and current objectives.

Shows all quests in your log, the current stage text, and progress
toward the active objective (e.g. 2/3 hollow slain).

Usage: quest
        """,
    },
    {
        "key": "talk",
        "category": "Quests",
        "text": """
|wtalk <npc>|n                — Greet an NPC.
|wtalk <npc> about <topic>|n  — Ask about a specific topic.

NPCs may offer quests when talked to. Quest givers are listed with |yavailable quest|n.
Topics vary by NPC; try talking about factions, places, or events you have encountered.

Usage: talk the Warden Scout
Usage: talk the Warden Scout about hollow
        """,
    },
    {
        "key": "abandon",
        "category": "Quests",
        "text": """
|wabandon <quest key>|n — Remove a quest from your log.

Progress is lost and cannot be recovered. The quest giver can re-assign it.

Usage: abandon find_the_key
        """,
    },
    {
        "key": "browse",
        "aliases": ["shop"],
        "category": "Economy",
        "text": """
|wbrowse|n — View an NPC merchant's wares.

Must be in the same room as a merchant NPC who has a shop.
Displays item names and prices in gold.

Usage: browse
        """,
    },
    {
        "key": "buy",
        "category": "Economy",
        "text": """
|wbuy <item name>|n — Purchase an item from a nearby merchant.

Deducts the item's listed price from your gold. The item is added to your inventory.

Usage: buy tallow candle
        """,
    },
    {
        "key": "sell",
        "category": "Economy",
        "text": """
|wsell <item>|n — Sell an item to a nearby merchant.

You receive half the item's listed value in gold. Quest items cannot be sold.

Usage: sell rusted knife
        """,
    },
    {
        "key": "light",
        "aliases": ["torch", "lantern"],
        "category": "Exploration",
        "text": """
Light sources must be toggled on with |wuse <item>|n or equipped.
Lit sources drain fuel over time (1 unit per minute via FuelDrainScript).

At 3 fuel remaining: |y"It won't last much longer."|n
At 0 fuel: the light extinguishes automatically.

Dark rooms (|xdark: true|n) are dangerous without a light source.
        """,
    },
    {
        "key": "sanity",
        "aliases": ["san"],
        "category": "Mechanics",
        "text": """
|wSanity|n — Mental stability. Starts at 100 (modified by class). Max 100 + level bonuses.

Sanity costs:
  Reading lore documents   — 1-5 per document (free for Scholars)
  Using the 'lore' command — 3 (free for Scholars)
  World events             — variable per event
  Being poisoned           — 1/tick

Sanity thresholds:
  |xBelow 50|n  — "Something moves at the edge of your vision."
  |mBelow 25|n  — Hallucinations begin (random flavor messages every 2 minutes)
  |r0|n         — Psychotic break: Sanity resets to 10, Fear +30

Sanity regenerates only through consumables and quest rewards.
        """,
    },
    {
        "key": "fear",
        "category": "Mechanics",
        "text": """
|wFear|n — Tension meter. 0-100. Never goes above 100.

Fear accumulates from:
  Being struck in combat     — +5 per hit
  World events               — variable
  Dying and respawning       — +20
  Psychotic break            — +30

Fear thresholds:
  |y40+|n  — Attack penalty -2. "Dread settles in your chest."
  |r75+|n  — Attack penalty -4. 20% chance to freeze instead of attacking.
  |r100|n  — Panic: Fear drops to 80, you flee through a random exit (60% chance)
             or freeze in place (40% chance). Combat target cleared.

Fear decreases slowly through consumables and some quest rewards.
        """,
    },
    {
        "key": "factions",
        "aliases": ["faction", "reputation"],
        "category": "World",
        "text": """
|wFactions|n — The five powers of Takomud.

  |wRemnants|n   — Survivors of the breaking. Cautious, practical, mistrustful.
  |wHollow|n     — The changed ones. Once human. Their motives are unclear.
  |wScholars|n   — Archivists of the old world. Knowledge is their currency.
  |wWardens|n    — Former enforcers. Maintain order through controlled violence.
  |wUnspoken|n   — Something else. They should not exist. Their agenda is unknown.

Reputation runs from -100 (hostile) to +100 (allied). Killing faction members
lowers rep with that faction and raises rep with their enemies.

Faction effects:
  Cultists are not attacked by Hollow mobs (Commune ability).
  Faction rep affects dialogue options and some quest availability (future).
        """,
    },
    {
        "key": "status effects",
        "aliases": ["bleed", "poison", "stun", "status"],
        "category": "Combat",
        "text": """
|wStatus Effects|n — Applied by certain mobs on hit (35% chance).

  |rBleed|n   — 4 damage per tick for 4 ticks (3-second intervals). |r"You are bleeding."|n
  |gPoison|n  — 2 damage + 1 Sanity per tick for 6 ticks. |g"Poison courses through you."|n
  |yStun|n    — Cannot act for 2 ticks. |y"You are stunned."|n

Effects stack: a new application of the same effect resets its duration.
Effects wear off automatically. |y"[Effect] has worn off."|n
        """,
    },
    {
        "key": "leveling",
        "aliases": ["level", "xp", "experience"],
        "category": "Character",
        "text": """
|wLeveling|n — Killing mobs and completing quests grants XP.

Each level up:
  |g+10 HP max|n
  |g+5 Sanity max|n
  |g+1 Attack bonus|n

Level thresholds: 100 / 250 / 500 / 900 / 1400 / 2000 / 3000 / 4500 / 6500 / 9000 XP

Vagrants gain +2 XP per new room discovered.
        """,
    },
]
