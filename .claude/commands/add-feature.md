# /add-feature

Add a new game mechanic, system, or in-game command to Takomud.

## What to do

The user wants to add a feature. Before implementing, clarify:

1. **What it does** — player-facing behavior in plain language
2. **Scope** — is this a new command? A new typeclass attribute? A new script? A new system (combat, crafting, etc.)?
3. **Who can use it** — all players, or staff only (Builder/Admin lock)?

## Implementation guide

### New in-game command
- Add to `commands/horror.py` (horror/atmosphere commands) or create a new file `commands/<feature>.py`
- Inherit from `evennia.commands.command.Command`
- Register in `commands/default_cmdsets.py` → `CharacterCmdSet.at_cmdset_creation()`
- Follow the existing pattern in `commands/horror.py`

### New typeclass attribute
- Add to `typeclasses/characters.py` → `at_object_creation()` for character stats
- Add to `typeclasses/rooms.py` → `at_object_creation()` for room properties
- Add to `typeclasses/objects.py` for item properties

### New timed script
- Add to `typeclasses/scripts.py`
- Inherit from `DefaultScript`
- Implement `at_script_creation()` (set interval, persistent) and `at_repeat()`

### New world content (NPC, object prototype)
- Add prototype dict to `world/prototypes.py`
- Spawn via `world/batch_build.py` or in-game `spawn` command

## After implementing

Run the server reload to pick up code changes:
```bash
.venv/bin/evennia reload
```

Or restart if making settings changes:
```bash
.venv/bin/evennia restart
```

## Horror design principle

Every mechanic should have a cost or risk. Exploration degrades sanity. Light sources are finite. Safety is temporary. The game should never feel *comfortable*.
