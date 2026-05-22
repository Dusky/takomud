# /worldgen

Run one autonomous world generation cycle for Takomud, producing one complete area with
rooms, NPCs, mobs, items, quests, lore, and optional boss — reviewed by two AI passes
before being written to the database.

## Prerequisites

```bash
export ANTHROPIC_API_KEY=sk-ant-...
.venv/bin/evennia migrate   # if not done
```

## Run one cycle

```bash
.venv/bin/python world/generator.py --cycles 1
```

Or from the evennia shell:
```bash
.venv/bin/evennia shell -c "from world.generator import generate; generate(cycles=1)"
```

## Review pipeline

Every area passes through:
1. **Raw generation** — Claude writes rooms, NPCs, mobs, items, quests
2. **Quality review** — second Claude call fixes: thin descriptions, clichés, vague objectives, missing prices, bad faction names
3. **Consistency review** — third Claude call validates: exit targets exist, faction enemies not sharing rooms, horror tone matches declared style

Only the final reviewed data is written to the database.

## What gets created in the database

**Rooms**: description, lore, atmosphere list, dark flag, recommended_level, encounter_table set.
If atmosphere messages present → AtmosphereScript attached.

**NPCs**: faction, dialogue (greeting + topics), quest_keys, shop (prototype keys), shop_stock.
min_reputation can be set manually after generation.

**Mobs**: full combat stats + gold_drop, wanders, status_effect, respawn_delay.
If wanders=True → WanderScript attached at creation.

**Items**: registered as Evennia prototypes (so mob loot tables work), then spawned into rooms.

**Quests**: registered in quest_registry with structured objective dicts (type/target/count).

**Lore documents**: LoreDocument objects with sanity_cost.

**Bosses**: Boss typeclass with phases list; aggro=True; respawn_delay applies.

**World events**: WorldEventScript instances targeting specific room dbrefs.

## State file

`world/world_state.json` tracks everything generated. If you delete a room from the DB,
also remove it from `all_rooms` in the state file or the next consistency review will try
to connect exits to it.

## Common errors

**"No tool_use block in Claude response"** — Claude occasionally returns text instead of a
tool call. The generator logs this and skips the cycle; re-run to try again.

**"Could not save prototype"** — prototype_key collision. Usually harmless; the existing
prototype is used.

**"Mob room not found"** — the generator referenced a room key that doesn't exist. The
consistency review should catch this; if it still happens, check that the area's room keys
are all unique and all exit targets exist.
