# /mud-status

Check the current state of the Takomud server, world, and all active systems.

## What to do

Run the checks below and summarize: server state, world content counts, active scripts, any errors.

```bash
# Server status
.venv/bin/evennia status

# Recent errors
grep -E "ERROR|WARNING|CRITICAL" server/logs/server.log 2>/dev/null | tail -20 || echo "No log yet"

# World state from generator
python -c "
import json, os
path = 'world/world_state.json'
if not os.path.exists(path):
    print('No world_state.json — generator has not run yet.')
else:
    s = json.load(open(path))
    print(f'Areas generated : {s[\"generation_count\"]}')
    print(f'Rooms           : {len(s[\"all_rooms\"])}')
    print(f'NPCs + Mobs     : {len(s[\"all_npcs\"])}')
    print(f'Items           : {len(s[\"all_items\"])}')
    print(f'Quests          : {len(s[\"all_quests\"])}')
    print(f'Prototypes      : {len(s[\"all_prototypes\"])}')
    print(f'Main questline  : {s.get(\"main_questline_created\", False)}')
    print()
    print('Region queue:', s.get('region_queue', []))
    print()
    for a in s['areas']:
        print(f'  {a[\"name\"]} ({len(a[\"rooms\"])} rooms) — {a[\"theme\"]}')
"

# DB object counts (server must be running)
.venv/bin/evennia shell -c "
import evennia
from typeclasses.rooms import Room
from typeclasses.characters import Character
from typeclasses.npcs import NPC, Mob, Boss
from typeclasses.items import Item

rooms  = evennia.search_object('', typeclass=Room)
chars  = evennia.search_object('', typeclass=Character)
mobs   = evennia.search_object('', typeclass=Mob)
bosses = evennia.search_object('', typeclass=Boss)
items  = evennia.search_object('', typeclass=Item)
print(f'Rooms={len(rooms)} Players={len(chars)} Mobs={len(mobs)} Bosses={len(bosses)} Items={len(items)}')
print(f'Dark rooms: {len([r for r in rooms if r.db.dark])}')
print(f'Hazard rooms: {len([r for r in rooms if r.db.hazard_hp or r.db.hazard_sanity])}')
print(f'Cleared boss rooms: {len([r for r in rooms if r.db.cleared])}')
scripts = evennia.search_script('')
print()
for s in scripts:
    print(f'  [{s.key}] interval={s.interval}s')
" 2>/dev/null || echo "(Server not running — skipping DB counts)"
```

## Report format

- **Server**: running / stopped
- **World**: N areas, N rooms, N mobs, N quests, region queue remaining
- **Systems**: which global scripts are running (RespawnScript is critical)
- **Errors**: any ERROR/WARNING from the log
- **Gaps**: missing starting zone, missing main questline, RespawnScript not running
