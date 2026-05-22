# /autogen

Continuously generate the Takomud world without user input. Each cycle produces one complete
area (rooms + NPCs + mobs + items + quests + lore docs + optional boss + world events), passed
through a two-stage AI review (quality → consistency) before being written to the database.

## Prerequisites

```bash
export ANTHROPIC_API_KEY=sk-ant-...
.venv/bin/evennia migrate   # if database not initialized
```

## Run

**Finite (generate 10 areas, wait 15s between each):**
```bash
.venv/bin/python world/generator.py --cycles 10 --delay 15
```

**Infinite (until Ctrl+C):**
```bash
.venv/bin/python world/generator.py --cycles 0 --delay 20
```

**Background:**
```bash
nohup .venv/bin/python world/generator.py --cycles 0 --delay 20 > world/gen.log 2>&1 &
echo "Generator PID: $!"
tail -f world/gen.log
```

**From evennia shell (server running):**
```python
from world.generator import generate
generate(cycles=5)
```

**In-game admin commands:**
- `generate 5` — 5 areas in background thread
- `generate 0` — infinite
- `genstart` — regenerate The Threshold starting zone
- `genquest <faction>` — generate faction questline (remnants/hollow/scholars/wardens/unspoken)

## Generation order

1. First run: generates **main questline** (herald NPC placed in The Threshold)
2. Cycles through **region queue** in order: Sunken City → Pale Forest → Ossuarium → Observatory
3. After all regions done: generates **sub-regions** with random horror styles
4. Each area goes through: raw generation → quality review → consistency review → apply to DB

## What each area contains (typical)

| Content | Count |
|---------|-------|
| Rooms | 4–6 |
| NPCs (non-hostile) | 1–3 |
| Mobs (hostile) | 2–4 |
| Boss encounters | 0–1 |
| Items | 4–8 |
| Lore documents | 1–2 |
| Quests | 1–2 |
| World events | 0–2 |

## What gets applied per mob

- HP, attack_bonus, defense, damage_dice, xp_reward, gold_drop
- faction, aggro, wanders (→ WanderScript attached), status_effect, respawn_delay
- loot_table (references item prototype_keys)

## Monitor progress

```bash
tail -f world/gen.log

# Or check state:
python -c "
import json
s = json.load(open('world/world_state.json'))
print(f'Areas: {s[\"generation_count\"]}  Rooms: {len(s[\"all_rooms\"])}  Mobs: {len(s[\"all_npcs\"])}')
for a in s['areas'][-5:]:
    print(f'  {a[\"name\"]} ({len(a[\"rooms\"])} rooms)')
"
```

## Faction questlines

Generate a questline for any of the 5 factions (3–5 stages, herald NPC placed in The Threshold):

```bash
# In-game
genquest remnants
genquest hollow
genquest scholars
genquest wardens
genquest unspoken

# From code
from world.generator import generate_faction_questline
generate_faction_questline("hollow")
```

## Notes

- World state persisted to `world/world_state.json` — do not edit manually
- Generator can run while server is running or offline
- Item prototypes are registered in Evennia's prototype system so mobs can drop them on death
- Dead mobs are queued in the global `RespawnScript` and respawn after `respawn_delay` seconds
