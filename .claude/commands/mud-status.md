# /mud-status

Check the current state of the Takomud server and project.

## What to do

Run the following checks and report results:

```bash
# Is the server running?
.venv/bin/evennia status

# Recent server log (last 30 lines)
tail -30 server/logs/server.log 2>/dev/null || echo "No log yet"

# List of rooms in the database
.venv/bin/evennia shell -c "
from typeclasses.rooms import Room
import evennia
rooms = evennia.search_object('', typeclass=Room)
for r in rooms:
    print(f'  #{r.id} {r.key} | dark={r.db.dark} | atmo={len(r.db.atmosphere or [])} msgs | lore={bool(r.db.lore)}')
"

# List of characters
.venv/bin/evennia shell -c "
from typeclasses.characters import Character
import evennia
chars = evennia.search_object('', typeclass=Character)
for c in chars:
    print(f'  #{c.id} {c.key} | hp={c.db.hp}/{c.db.hp_max} san={c.db.sanity}/{c.db.sanity_max} fear={c.db.fear}')
"
```

Summarize:
- Server up/down
- Number of rooms, which are dark, which have atmosphere scripts
- Number of player characters
- Any errors in the log
