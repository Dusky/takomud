# Takomud — Agent Reference

Takomud is a horror MUD built on [Evennia](https://www.evennia.com/) (Python/Django). The world
is autonomously generated via the Anthropic API. All game content flows through a two-stage
AI review pipeline (quality → consistency) before touching the database.

---

## Evennia reference — read this before touching any typeclass or command

Evennia is the framework everything inherits from. When implementing or debugging anything,
consult these docs first — do not guess at hook names or method signatures.

| Topic | URL |
|-------|-----|
| **General overview** | https://www.evennia.com/docs/latest/index.html |
| **Typeclasses** (Objects, Characters, Rooms, Exits) | https://www.evennia.com/docs/latest/Typeclasses.html |
| **Commands** (syntax, switches, locks, help) | https://www.evennia.com/docs/latest/Commands.html |
| **Command sets** (registration, priority, merging) | https://www.evennia.com/docs/latest/Command-Sets.html |
| **Scripts** (at_script_creation, at_repeat, persistent) | https://www.evennia.com/docs/latest/Scripts.html |
| **Objects** (DefaultObject hooks, at_get, at_drop, at_move) | https://www.evennia.com/docs/latest/Objects.html |
| **Rooms** (DefaultRoom, return_appearance, at_object_receive) | https://www.evennia.com/docs/latest/Rooms.html |
| **Characters** (DefaultCharacter, at_post_login, at_post_move) | https://www.evennia.com/docs/latest/Characters.html |
| **Exits** (DefaultExit, at_traverse, locks) | https://www.evennia.com/docs/latest/Exits.html |
| **DB attributes** (`obj.db.foo`, `obj.ndb.foo`, `AttributeProperty`) | https://www.evennia.com/docs/latest/Attributes.html |
| **Searching** (`evennia.search_object`, `search_script`, `use_dbref`) | https://www.evennia.com/docs/latest/Searching.html |
| **Prototypes** (save_prototype, spawner.spawn) | https://www.evennia.com/docs/latest/Prototypes.html |
| **Locks** (lock strings, access checks, perm()) | https://www.evennia.com/docs/latest/Locks.html |
| **Messaging** (`obj.msg()`, `room.msg_contents()`, exclude=[]) | https://www.evennia.com/docs/latest/Messaging.html |
| **Sessions** (SESSION_HANDLER, get_puppet) | https://www.evennia.com/docs/latest/Sessions.html |
| **Help system** (FILE_HELP_ENTRY_MODULES, HELP_ENTRY_DICTS) | https://www.evennia.com/docs/latest/Help-System.html |
| **Spawner / batch creation** | https://www.evennia.com/docs/latest/Spawner-and-Prototypes.html |
| **Unit testing** | https://www.evennia.com/docs/latest/Unit-Testing.html |

### Critical patterns agents commonly get wrong

**DB attributes** — always use `obj.db.attr`, never `obj.attr` for persistent data.
`obj.ndb.attr` is non-persistent (lost on reload). Do not access Django model fields directly.

**Hook names** — these are the ones we use; all are defined by Evennia:
```
at_object_creation()       # called once when object first created
at_post_login()            # called after account logs in to puppet
at_post_move(source)       # called on character after successful move
at_object_receive(obj, src)# called on container/room when obj arrives
at_traverse(traveller, dest)# called on exit; return False to block
at_get(getter)             # called on item when picked up
at_drop(dropper)           # called on item when dropped
at_repeat()                # called on script each interval
at_script_creation()       # called once when script is created
```

**Searching** — use `evennia.search_object(key, typeclass=MyClass)` or
`evennia.search_object(dbref, use_dbref=True)`. Returns a list, not a single object.
Always check `if results:` before indexing.

**Creating objects** — `evennia.create_object(TypeClass, key="Name", location=room)`.
Never instantiate typeclasses directly with `MyClass()`.

**Creating scripts** — `obj.scripts.add(MyScript)` for object-attached scripts.
`evennia.create_script(MyScript)` for global scripts (no obj).

**Messages** — `obj.msg("text")` sends to that object's session.
`room.msg_contents("text", exclude=[char])` sends to everyone in room except char.
Evennia color codes: `|r` red, `|g` green, `|y` yellow, `|w` white, `|x` dark, `|n` reset,
`|m` magenta, `|c` cyan, `|Y` bright yellow, `|R` bright red.

**Command func()** — `self.caller` is the character. `self.args` is the raw argument string
(already stripped). `self.switches` is a list of `/switch` flags. `self.lhs` / `self.rhs`
split on `=`. Use `self.caller.search(name)` to find objects visible to the caller.

**Locks** — `locks = "cmd:perm(Admin)"` restricts to Admin+.
`"cmd:perm(Builder)"` for Builder+. `"cmd:all()"` for everyone (default).
Check in code: `obj.access(caller, "lock_type")`.

**Typeclass inheritance** — always call `super().at_object_creation()` first.
`utils.inherits_from(obj, "typeclasses.npcs.Mob")` for isinstance-style checks across
the typeclass system (use the string path, not the class itself, for safety).

---

## Quick orientation

```
takomud/
├── typeclasses/        Core game objects (characters, rooms, items, npcs, scripts, exits)
├── commands/           In-game commands grouped by domain
├── world/              Generator, quest system, lore registry, world bible
├── server/conf/        Evennia configuration (settings, at_initial_setup, mssp)
└── .claude/commands/   Agent skills (slash commands)
```

Start the server: `.venv/bin/evennia start`
Reload after code changes: `.venv/bin/evennia reload`
Run shell: `.venv/bin/evennia shell`
Run generator: `python world/generator.py --cycles 1`

---

## Typeclass map

### `typeclasses/characters.py` — `Character`

Player characters. Key attributes (all set in `at_object_creation`):

| Attribute | Default | Purpose |
|-----------|---------|---------|
| `hp` / `hp_max` | 100 | Physical health |
| `sanity` / `sanity_max` | 100 | Mental stability |
| `fear` | 0 | 0–100 tension meter |
| `xp` / `level` / `xp_to_next` | 0/1/100 | Progression |
| `gold` | 0 | Currency |
| `attack_bonus` | 1 | Flat combat modifier |
| `defense` | 10 | d20 roll must meet or beat this |
| `char_class` | None | survivor/scholar/cultist/hunter/vagrant |
| `equipped` | {} | slot → dbref |
| `status_effects` | {} | `{"bleed": {"dmg": 4, "ticks": 4}, ...}` |
| `reputation` | {} | faction → -100..+100 |
| `discovered_rooms` | [] | list of dbrefs (for Vagrant Blink) |
| `combat_target` | None | dbref of current enemy |

Key methods: `adjust_hp`, `adjust_sanity`, `adjust_fear`, `adjust_xp`, `gain_gold`,
`spend_gold`, `adjust_reputation`, `apply_status_effect`, `at_death`, `apply_class`.

**Sanity thresholds:** ≤50 → edge-of-vision message; ≤25 → hallucinations start
(`SanityHallucinationScript`); 0 → psychotic break (reset to 10, +30 fear).

**Fear thresholds:** ≥40 → -2 attack; ≥75 → -4 attack, 20% freeze chance; 100 → panic
(flee through random exit or freeze, reset to 80).

**Death:** drops half gold in room as a coin pile, warps to `START_LOCATION`, HP→50%,
Sanity-10, Fear+20.

**Classes (set via `apply_class(key)`):**
| Class | Passive special |
|-------|----------------|
| survivor | Grit: survive one killing blow/hour at 1 HP |
| scholar | Veil-sight: lore/read commands cost no Sanity |
| cultist | Commune: Hollow mobs don't aggro on sight |
| hunter | Track: sense hostile mobs in adjacent rooms |
| vagrant | Wanderer: +2 XP per new room discovered |

**Active abilities** (all via `ability` command):
- survivor → Surge (-20 HP, +5 attack 30s via SurgeScript)
- scholar → Analyze (reveal target stats)
- cultist → Commune (extract lore from Hollow mob, clear aggro)
- hunter → Trap (HunterTrapScript on room; next mob stunned)
- vagrant → Blink (teleport to discovered room, -20 Sanity)

---

### `typeclasses/rooms.py` — `Room`

| Attribute | Purpose |
|-----------|---------|
| `dark` | True = absolute darkness without a lit light source |
| `atmosphere` | List of strings; fired randomly by AtmosphereScript |
| `lore` | Hidden text revealed via `lore` command (Scholar sees for free) |
| `recommended_level` | Warning shown to under-leveled characters on entry |
| `encounter_table` | List of mob templates for RandomEncounterScript |
| `encounter_chance` | Float 0–1; chance per tick to spawn (default 0.3) |
| `cleared` / `cleared_boss` | Set True when a Boss dies here; shown in header |
| `hazard_hp/sanity/fear` | Damage/tick from HazardScript |
| `hazard_message` | Text shown each hazard tick |

Dark rooms: characters without a lit light source see only darkness and cannot see exits.
Recommended level: shown in room header as `[Recommended: Level N+]` (red if under-leveled).

---

### `typeclasses/items.py` — `Item`, `Container`, `LoreDocument`

**Item** attributes: `item_type` (weapon/armor/consumable/quest/light/misc), `slot`,
`damage_dice`, `attack_bonus`, `defense_bonus`, `effect` (dict: hp/sanity/fear),
`is_light_source`, `fuel`, `lit`, `droppable`, `value`, `weight`.

`at_get`: auto-converts gold coin piles to gold attribute; triggers collect quest objectives.
`at_use`: applies consumable effects then deletes item.
`toggle_light`: flips lit state; FuelDrainScript handles fuel depletion (1/min).

**Container** adds: `is_container`, `is_open`, `locked`, `lock_key`, `capacity`.
Open/close/lock/unlock via commands. Items stored as Evennia object contents.

**LoreDocument** adds: `readable`, `doc_text`, `doc_title`, `sanity_cost`.
`at_read()` shows text and deducts sanity (free for Scholars).

---

### `typeclasses/npcs.py` — `NPC`, `Mob`, `Boss`

**NPC**: `faction`, `dialogue` (dict: greeting + topics dict), `quest_keys` (list),
`shop` (list of prototype_keys), `shop_stock` (dict: proto_key → qty, -1=unlimited),
`restock_list`, `min_reputation` (int or None — gates dialogue by faction rep).

`at_talked_to(speaker, topic)`: checks `min_reputation` first; returns dialogue string.

**Mob** adds: `aggro`, `damage_dice`, `xp_reward`, `gold_drop`, `respawn_delay`,
`wanders`, `status_effect` (bleed/poison/stun, 35% chance on hit).

`execute_attack(target)`: rolls d20+attack vs defense; applies status effect.
`at_death(killer)`: grants XP/gold/faction rep to killer; queues respawn via RespawnScript.
`_start_combat(target)`: skips aggro if target is Cultist and mob faction is "hollow".

**Boss** adds: `phases` list, `phase_triggered` list.
`at_death`: broadcasts global kill message to all connected players, sets room.cleared.
`_check_phases`: triggers phase escalation on HP thresholds.

---

### `typeclasses/exits.py` — `Exit`

Extends DefaultExit with: `locked`, `key_item` (item name required), `lock_desc`.
`at_traverse`: blocks when locked. `get_display_name`: appends `[locked]` tag.

---

### `typeclasses/scripts.py` — all scripts

| Script | Attached to | Purpose |
|--------|------------|---------|
| `AtmosphereScript` | Room | Fires random atmosphere string every 90s |
| `WorldEventScript` | Global | Sends message+sanity/fear cost to set of rooms |
| `FuelDrainScript` | Character | Drains 1 fuel/min from lit light sources |
| `SanityHallucinationScript` | Character | Fires hallucination at sanity ≤25; stops if sanity recovers |
| `PlayerCombatScript` | Character | Auto-attacks combat_target every 4s |
| `RespawnScript` | Global | 30s tick; maintains mob respawn queue |
| `WanderScript` | Mob | Moves mob through random exit every 90s if not in combat |
| `StatusEffectScript` | Character | Ticks bleed/poison/stun every 3s |
| `RestScript` | Character | +5 HP / +3 Sanity every 10s; cancelled by combat |
| `RandomEncounterScript` | Room | 120s tick; spawns mob from encounter_table at encounter_chance |
| `HazardScript` | Room | 15s tick; deals hazard_hp/sanity/fear damage to all characters |
| `MerchantRestockScript` | NPC | Hourly; refills shop_stock quantities from restock_list |
| `SurgeScript` | Character | Survivor Surge: removes +5 attack after 30s |
| `HunterTrapScript` | Room | Traps next mob entry (stunned + 5-15 dmg); auto-disarms 5min |
| `CombatScript` (npcs.py) | Mob | Mob auto-attacks combat_target every 3s |

---

## Command map

| File | Commands | Who |
|------|----------|-----|
| `commands/horror.py` | stat, score, lore, read, charclass, track, ability, map, shout, who, unlock, lock, atmosphere, setlore, setdark, sethazard, setencounter | all / Builder |
| `commands/combat.py` | attack, stop, flee, consider | all |
| `commands/inventory.py` | inventory, equip, unequip, use, drop, give, rest, inspect, open, close, put, take | all |
| `commands/quest.py` | quest, talk, abandon | all |
| `commands/economy.py` | browse, buy, sell | all |
| `commands/admin.py` | generate, genstart, genquest, genregion, where | Admin |

All commands are registered in `commands/default_cmdsets.py`.

---

## World generation system

`world/generator.py` is the autonomous content engine.

**Entry points:**
- `generate(cycles=N)` — main loop; picks next region, calls Claude, applies to DB
- `generate_starting_zone()` — generates The Threshold (called at first boot)
- `generate_main_questline()` — generates overarching meta-narrative
- `generate_faction_questline(faction)` — generates faction-specific questline (with review pass)
- `generate_region(name, areas=4, delay=10, with_questline=True)` — generates N coordinated areas
  locked to one region, then auto-generates a faction questline with herald in the first room

**Review pipeline (every generated area):**
1. Claude generates raw area data (`_call_claude`)
2. Quality review (`_review_area(stage="quality")`) — fixes thin descriptions, string objectives, bad factions
3. Consistency review (`_review_area(stage="consistency")`) — validates exits, faction placement, horror tone
4. `_apply_area()` writes to database

**`_apply_area()` steps:**
1. Register item prototypes (Evennia prototype system)
2. Create rooms (with atmosphere, lore, recommended_level)
3. Create exits (with auto-reverse)
4. Place items in rooms
5. Create NPCs (with dialogue, shop, quest_keys)
6. Create mobs (with gold_drop, wanders→WanderScript, status_effect, respawn_delay)
7. Register quests (via quest_registry)
8. Create lore documents
9. Create boss encounters
10. Create world events (WorldEventScript)

**World state** persisted to `world/world_state.json`:
```json
{
  "areas": [...],
  "all_rooms": {"room key": "#dbref"},
  "all_npcs": {"npc key": "#dbref"},
  "all_items": {"item key": "#dbref"},
  "all_quests": ["quest_key"],
  "all_prototypes": ["PROTO_KEY"],
  "generation_count": N,
  "region_queue": ["The Sunken City", ...]
}
```

---

## Quest system

`world/quest_system.py` — core quest logic.
`world/quest_registry.py` — in-memory registry of all quest data.

**Quest data structure:**
```python
{
  "key": "my_quest",
  "title": "...",
  "desc": "...",
  "giver_npc_key": "The Archivist",
  "stages": [
    {
      "text": "Stage description shown to player",
      "objective": {
        "type": "kill",      # kill / collect / visit / talk / deliver
        "target": "hollow wretch",
        "count": 3,
        "current": 0,
      }
    }
  ],
  "reward": {
    "xp": 100,
    "gold": 50,
    "items": ["PROTOTYPE_KEY"],
    "reputation": {"remnants": 10, "hollow": -5}
  }
}
```

**Trigger points:**
- `check_objective(char, "kill", mob.key)` — called in `_execute_player_attack` on mob death
- `check_objective(char, "visit", room.key)` — called in `Character.at_post_move`
- `check_objective(char, "deliver", "item:npc")` — called in `CmdGive`
- `check_collect_trigger(char, item.key)` — called in `Item.at_get`
- Talk objectives: `CmdTalk` calls `check_objective(char, "talk", npc.key)`

---

## World bible

`world/world_bible.py` defines:
- `REGIONS` — list of region dicts with name, theme, horror_type
- `FACTIONS` — dict of faction keys with descriptions
- `CHARACTER_CLASSES` — dict of class dicts (name, desc, special, hp_bonus, etc.)
- `HORROR_STYLES` — keys: psychological/eldritch/folk/gothic/cosmic/body
- `GENERATION_PROMPT_SYSTEM` — system prompt used for all Claude generation calls
- `LORE_CODEX` — dict of topic → lore text (used by `lore` command)
- `XP_TABLE` — level thresholds

---

## Adding things

### New command
1. Add class to the appropriate `commands/*.py` file (inherit `BaseCommand`)
2. Add `self.add(CmdFoo())` in `commands/default_cmdsets.py`
3. Add help entry to `world/help_entries.py`

### New script
1. Add class to `typeclasses/scripts.py` (inherit `DefaultScript`)
2. Set `key`, `interval`, `persistent` in `at_script_creation`
3. Implement `at_repeat`

### New typeclass attribute
1. Add to `at_object_creation` in the relevant typeclass
2. Document in this file

### New room (manual)
1. Add to `world/batch_build.py` following existing patterns
2. Run `evennia shell -c "from world.batch_build import build_world; build_world()"`

### New quest (manual)
1. Call `quest_registry.register(quest_data)` from a script or shell
2. Set `npc.db.quest_keys = ["quest_key"]` on the giver NPC

### New generated area
- In-game: `generate` (Admin command) or `generate 5` for 5 areas
- CLI: `python world/generator.py --cycles 1`

### New faction questline
- In-game: `genquest <faction>` (Admin command)
- Code: `from world.generator import generate_faction_questline; generate_faction_questline("remnants")`

### New full region (areas + questline + populated rooms)
- In-game: `genregion <name> [areas]` (Admin command, default 4 areas)
- Code: `from world.generator import generate_region; generate_region("The Ashfields", areas=6)`

---

## Design principles

Every mechanic must have a **cost or a risk**:
- Exploration degrades sanity
- Light is finite
- Resting can be interrupted
- Death has gold and sanity penalties
- Class abilities cost HP, sanity, or fear

**Do not add "comfortable" features.** No passive regeneration without rest. No safe zones
(except The Threshold, which is merely less dangerous). No guaranteed rewards.

Horror tone per style:
- Psychological: implication, wrongness, uncertainty
- Eldritch: scale, indifference, the unknowable
- Folk: old rules, bargains, things that used to be respected
- Gothic: decay, memory, the weight of the past
- Cosmic: insignificance, the void, things that predate understanding
- Body: unreliable self, transformation, violation of physical norms

---

## Key file list (quick reference)

```
typeclasses/characters.py   — Character stats, HP/san/fear/XP/gold/class systems
typeclasses/rooms.py        — Room, darkness, atmosphere, level gating, hazards
typeclasses/items.py        — Item, Container, LoreDocument
typeclasses/npcs.py         — NPC (dialogue/shop/rep gate), Mob (combat/loot), Boss (phases/broadcast)
typeclasses/scripts.py      — All timed scripts
typeclasses/exits.py        — Exit with lock/key support
commands/horror.py          — Most player commands + all builder commands
commands/combat.py          — attack, stop, flee, consider
commands/inventory.py       — inv, equip, use, drop, give, rest, inspect, containers
commands/quest.py           — quest, talk, abandon
commands/economy.py         — browse, buy, sell (with finite stock)
commands/admin.py           — generate, genstart, genquest, genregion, where
commands/default_cmdsets.py — Command registration
world/generator.py          — Autonomous world generator (Claude API)
world/quest_system.py       — Quest objective checking and completion
world/quest_registry.py     — In-memory+disk quest data store (persists to quest_data.json)
world/world_bible.py        — Lore, factions, classes, generation prompts
world/help_entries.py       — In-game help text for all custom systems
server/conf/at_initial_setup.py     — First-boot: generate starting zone, start RespawnScript
server/conf/at_server_startstop.py  — at_server_start: reload quests, ensure RespawnScript running
server/conf/mssp.py         — MUD listing metadata
world/world_state.json      — Generator state (do not edit manually)
```
