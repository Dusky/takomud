# /create-room

Scaffold a new Takomud room in `world/batch_build.py` or a dedicated area file.

## What to do

The user wants to add a new room to the MUD. Gather the following information if not already provided:

1. **Room key** (name) — the unique string identifier, e.g. `"The Weeping Chapel"`
2. **Description** — 3–6 sentences of immersive dark/horror prose shown when a player looks at the room. Make it sensory and atmospheric. Do NOT explain the lore here — just what the character perceives.
3. **Lore** (optional) — 2–4 sentences of hidden backstory revealed via the `lore` command. This is the "why" behind the room.
4. **Atmosphere messages** (optional) — 3–6 short strings (1–2 sentences each) that fire randomly to occupants. These should be unsettling, brief, and suggestive rather than explicit.
5. **Dark?** (bool) — true if the room is unlit by default and requires a light source.
6. **Connections** — what existing rooms this connects to and in which directions.

## Output

Write a `make_room(...)` call and the appropriate `link(...)` calls following the exact style used in `world/batch_build.py`. Place them in the correct section of the file.

Then run:
```bash
.venv/bin/evennia shell -c "from world.batch_build import build_world; build_world()"
```
to apply the changes to the running (or offline) database.

## Style guide for room prose

- Present tense, second person ("You stand...", "The walls press...")
- Sensory detail: sound, smell, texture, temperature — not just visual
- Imply rather than state the horror. "Something moved" beats "a monster is here."
- Avoid clichés: no dripping blood, no cobwebs, no skeletons (unless they serve a specific narrative purpose)
- Dark/horror tone: Gothic, psychological, eldritch — pick a register and stay in it
