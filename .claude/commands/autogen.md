# /autogen

Autonomously generate the entire Takomud world — continuously, without user input.

The generator calls Claude claude-sonnet-4-6 once per area, producing rooms, NPCs, mobs, items, and quests
that are thematically consistent and directly applied to the database. It works through all
planned regions (Sunken City → Pale Forest → Ossuarium → Observatory) then invents new
sub-regions indefinitely.

## Before running

Set your API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Make sure the database is ready:
```bash
.venv/bin/evennia migrate
```

Optionally, start the MUD server first (generator works either way):
```bash
.venv/bin/evennia start
```

## Run autonomous generation

**Finite run (recommended first time — generates 10 areas):**
```bash
.venv/bin/python world/generator.py --cycles 10 --delay 15
```

**Infinite run (until you Ctrl+C):**
```bash
.venv/bin/python world/generator.py --cycles 0 --delay 20
```

**Background (detached, logs to file):**
```bash
nohup .venv/bin/python world/generator.py --cycles 0 --delay 20 > world/gen.log 2>&1 &
echo "Generator PID: $!"
```

To stop background generation:
```bash
kill $(cat world/gen.pid 2>/dev/null) 2>/dev/null || pkill -f "world/generator.py"
```

## Monitor progress

```bash
tail -f world/gen.log
```

Or check the state file:
```bash
.venv/bin/python -c "
import json
with open('world/world_state.json') as f:
    s = json.load(f)
print(f'Areas generated: {s[\"generation_count\"]}')
print(f'Rooms: {len(s[\"all_rooms\"])}')
print(f'NPCs+Mobs: {len(s[\"all_npcs\"])}')
print(f'Items: {len(s[\"all_items\"])}')
print(f'Quests: {len(s[\"all_quests\"])}')
print()
print('Areas:')
for a in s['areas']:
    print(f'  {a[\"name\"]} ({len(a[\"rooms\"])} rooms)')
"
```

## Design

- **Regions** are generated in order: Threshold → Sunken City → Pale Forest → Ossuarium → Observatory
- Each region has a distinct horror style (eldritch / folk / gothic / cosmic)
- After all planned regions are done, the generator invents new sub-regions
- Room connections are stitched to existing rooms so the world stays navigable
- Item prototypes are registered in Evennia's prototype system so mobs can drop them
- Quests are registered in `world/quest_registry.py` (in-memory) and on NPCs' `quest_keys` attribute

## What each cycle produces (typical)
| Content | Count |
|---------|-------|
| Rooms   | 4–6   |
| NPCs    | 1–3   |
| Mobs    | 2–4   |
| Items   | 4–8   |
| Quests  | 1–2   |

A complete world with all 5 planned regions = approximately 25–40 cycles (~150–240 rooms).
