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
    {
        "key": "rest",
        "aliases": ["sit", "sleep"],
        "category": "Survival",
        "text": """
|wrest|n — Sit and recover HP and Sanity over time.

Recovery rate: +5 HP and +3 Sanity every 10 seconds.
Interrupted instantly if you enter combat.
Stops automatically when fully recovered.

You cannot rest in combat. Use |wstop|n first to disengage.

Usage: rest
        """,
    },
    {
        "key": "inspect",
        "aliases": ["examine", "ex"],
        "category": "General",
        "text": """
|winspect <item>|n — Examine an item for full mechanical details.

Shows item type, damage/defense values, effects, fuel level, and gold value.
More informative than the standard look command.

Usage: inspect rusted blade
Usage: inspect tallow candle
        """,
    },
    {
        "key": "containers",
        "aliases": ["container", "chest", "bag"],
        "category": "General",
        "text": """
|wContainers|n — Chests, bags, and boxes that hold other items.

Commands:
  |wopen <container>|n           — Open a container to see its contents
  |wclose <container>|n          — Close an open container
  |wput <item> in <container>|n  — Place an item inside a container
  |wtake <item> from <container>|n — Retrieve an item from a container

Locked containers require a specific key item to open.
Quest items cannot be placed in containers.
        """,
    },
    {
        "key": "random encounters",
        "aliases": ["encounter", "encounters"],
        "category": "World",
        "text": """
|wRandom Encounters|n — Certain rooms spawn transient creatures.

Some rooms have an encounter_table — a list of possible creatures that
can materialize while players are present. These creatures do not respawn
and vanish after being killed or moving away.

The chance of an encounter per tick is set per room (default 30%).
Intervals are at minimum 2 minutes between potential spawns.
        """,
    },
    {
        "key": "death",
        "category": "Mechanics",
        "text": """
|wDeath|n — What happens when your HP reaches 0.

On death:
  |r- Half your current gold drops in the room where you died.|n
  |r- Sanity -10|n
  |r- Fear +20|n
  |r- HP restored to 50% of maximum|n
  You are transported back to The Threshold (starting zone).

The dropped gold can be picked up by anyone — including other players.

Survivor class: once per hour, a killing blow leaves you at 1 HP instead.
        """,
    },
    {
        "key": "who",
        "category": "General",
        "text": """
|wwho|n — List all currently connected players.

Shows each player's name, level, class, and current location.

Usage: who
        """,
    },
    {
        "key": "shout",
        "aliases": ["yell"],
        "category": "General",
        "text": """
|wshout <message>|n — Shout so nearby rooms can hear you.

Your message is heard in your current room and all adjacent rooms.
Costs 5 Fear — screaming in the dark is not without consequence.

Usage: shout Is anyone out there?
        """,
    },
    {
        "key": "unlock",
        "category": "General",
        "text": """
|wunlock <direction>|n            — Unlock a locked exit (if no key required)
|wunlock <direction> with <item>|n — Unlock using a specific key item

Some exits require a specific item (a key, a sigil, a severed hand).
You must be carrying the required item. Unlocking does not consume the key.

Usage: unlock north
Usage: unlock east with iron key
        """,
    },
    {
        "key": "lock",
        "category": "General",
        "text": """
|wlock <direction>|n — Lock an unlocked exit.

Requires the same key item used to unlock it, if one was required.
Other players can still unlock it if they have the key.

Usage: lock north
        """,
    },
    {
        "key": "ability",
        "aliases": ["ab", "special"],
        "category": "Character",
        "text": """
|wability|n or |wability <target>|n — Use your class active ability.

  |wSurvivor — Surge|n
    Spend 20 HP. Gain +5 attack bonus for 30 seconds.
    Cannot be used if HP ≤ 20.

  |wScholar — Analyze|n
    Reveal a target's current HP, defense, attack, and status effect.
    Usage: ability <target>

  |wCultist — Commune|n
    Speak with a Hollow mob in the room. They may share hidden lore.
    Also clears their combat target (they stop attacking you).

  |wHunter — Trap|n
    Set a hidden snare in the current room. The next mob to enter
    takes 5-15 damage and is stunned. Auto-disarms after 5 minutes.

  |wVagrant — Blink|n
    Teleport to any previously discovered room. Costs 20 Sanity.
    Usage: ability <room name or partial name>
        """,
    },
    {
        "key": "hazards",
        "aliases": ["hazard", "environmental"],
        "category": "World",
        "text": """
|wEnvironmental Hazards|n — Rooms that damage everyone present.

Some rooms are inherently hostile: acid fog, cursed ground, psychic static.
Every 15 seconds (configurable), all characters in the room take:
  - HP damage (if hazard_hp > 0)
  - Sanity damage (if hazard_sanity > 0)
  - Fear increase (if hazard_fear > 0)

The hazard message is shown each tick. The only protection is to leave.
        """,
    },
    {
        "key": "genregion",
        "aliases": ["generate region", "region generation"],
        "category": "Admin",
        "text": """
|wgenregion|n — Generate an entire populated region (Admin only).

Usage:
  genregion <region name>
  genregion <region name> <areas>

Generates N coordinated areas (default 4, max 20) all set within the named
region, then creates a faction questline with a herald NPC placed in the
first room that was generated. The entire process runs in a background thread.

Examples:
  genregion The Ashfields
  genregion The Sunken Library 6

Requires ANTHROPIC_API_KEY to be set in the server environment.
Watch the server log for per-area progress messages.

See also: |wgenerate|n, |wgenquest|n, |wgenstart|n
        """,
    },
    {
        "key": "reputation gates",
        "aliases": ["rep gate", "reputation requirement"],
        "category": "World",
        "text": """
|wReputation Gates|n — Some NPCs require minimum faction standing.

Certain NPCs will not speak with characters who have negative standing
with their faction. They turn away with cold contempt instead of engaging.

Build reputation by:
  - Completing faction quests (+rep with faction)
  - Killing enemy faction mobs (+2 rep with their rivals)

Lose reputation by:
  - Killing faction members (-5 rep with their faction)

See |whelp factions|n for faction relationships.
        """,
    },
]
