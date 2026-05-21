# /write-lore

Write or revise lore text for a Takomud room, NPC, item, or area.

## What to do

The user wants lore written for a piece of the world. Ask for (or infer from context):

1. **Subject** — which room, NPC, object, or area needs lore
2. **What is known** — any facts the user has already decided (events, factions, names)
3. **Tone** — eldritch cosmic horror / gothic decay / psychological dread / folk horror / body horror (pick one unless told otherwise)
4. **Length** — short (2–3 sentences), medium (a paragraph), or long (multiple paragraphs for a codex entry)

## Output rules

- Write lore as if it comes from an unreliable in-world source: a fragmented journal, a scholar's footnote, a survivor's account, an inscription.
- Never confirm facts outright — use hedged language: "it is said", "records suggest", "those who returned claimed".
- Leave at least one deliberate gap or contradiction in every piece of lore.
- Avoid named deities or monsters unless the user provides them. Reference "the presence", "the event", "what came after".
- End on an implication, not a conclusion.

After writing, ask the user if they want the lore applied to the codebase (setlore on a room) or saved to a world notes file at `world/lore_notes.md`.

## If applying to a room

Find the room's `make_room(...)` call in `world/batch_build.py` and update its `lore=` argument, then re-run the build script:

```bash
.venv/bin/evennia shell -c "from world.batch_build import build_world; build_world()"
```
