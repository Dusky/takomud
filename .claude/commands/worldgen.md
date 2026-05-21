# /worldgen

Run one autonomous world generation cycle for Takomud.

Each cycle generates one complete area: rooms, NPCs, mobs, items, and quests — all written
by Claude (claude-sonnet-4-6) using the Takomud world bible for thematic consistency.

## Prerequisites

1. The Evennia database must be initialized:
   ```bash
   .venv/bin/evennia migrate
   ```
2. `ANTHROPIC_API_KEY` must be set:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

## Run one cycle

```bash
.venv/bin/python world/generator.py --cycles 1
```

Or from within the evennia shell (if server is running):
```bash
.venv/bin/evennia shell -c "from world.generator import generate; generate(cycles=1)"
```

## Run N cycles

```bash
.venv/bin/python world/generator.py --cycles 5 --delay 15
```

## What gets generated per cycle

- **1 area** (group of 4–6 thematically linked rooms)
- **Rooms** with 100+ word atmospheric descriptions, lore, and optional darkness
- **NPCs** (non-hostile, faction-aligned, with dialogue trees and quest-giving ability)
- **Mobs** (hostile creatures with combat stats, loot tables, and XP rewards)
- **Items** (weapons, armor, consumables, light sources — placed in rooms and on mob loot)
- **Quests** (multi-stage, given by NPCs, with XP and item rewards)

## After generation

Reload the server to pick up any code changes (the generator only modifies the DB, so reload is
usually not needed — but run it if you've edited typeclasses):

```bash
.venv/bin/evennia reload
```

Check what was created:
```bash
.venv/bin/evennia shell -c "
import json
with open('world/world_state.json') as f:
    s = json.load(f)
print(f\"Areas: {len(s['areas'])}\")
print(f\"Rooms: {len(s['all_rooms'])}\")
print(f\"NPCs:  {len(s['all_npcs'])}\")
print(f\"Items: {len(s['all_items'])}\")
print(f\"Quests: {len(s['all_quests'])}\")
"
```

## State file

Generation history is tracked in `world/world_state.json`. Do not edit it manually unless
you are removing content — the generator reads it to maintain world consistency.
