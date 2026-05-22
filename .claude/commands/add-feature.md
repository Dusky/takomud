# /add-feature

Add a new game mechanic, system, or in-game command to Takomud.

## Evennia reference (read before touching any typeclass or command)

Full docs: https://www.evennia.com/docs/latest/index.html

Key pages:
- Commands: https://www.evennia.com/docs/latest/Commands.html
- Scripts: https://www.evennia.com/docs/latest/Scripts.html
- Objects/hooks: https://www.evennia.com/docs/latest/Objects.html
- DB attributes: https://www.evennia.com/docs/latest/Attributes.html
- Searching: https://www.evennia.com/docs/latest/Searching.html
- Prototypes/spawner: https://www.evennia.com/docs/latest/Prototypes.html
- Locks: https://www.evennia.com/docs/latest/Locks.html

**Patterns to get right:**
- `obj.db.attr` for persistent data; `obj.ndb.attr` for non-persistent
- `evennia.search_object(key_or_dbref)` returns a list — always check `if results:`
- `evennia.create_object(TypeClass, key="Name", location=room)` — never instantiate directly
- `obj.scripts.add(MyScript)` — attach script to object; `evennia.create_script(MyScript)` for global
- `self.caller.search(name)` in commands finds objects visible to the caller
- `room.msg_contents("text", exclude=[char])` sends to everyone in room except char
- Always call `super().at_object_creation()` first in typeclass overrides

---

## Before implementing, clarify

1. **What it does** — player-facing behavior in plain language
2. **Scope** — new command? new script? new typeclass attribute? new system?
3. **Who can use it** — all players, or staff only (`locks = "cmd:perm(Builder)"` / `Admin`)?
4. **Does it interact with existing systems?** — combat, quests, sanity, fear, economy?

## Implementation guide

### New in-game command

```python
# commands/horror.py (horror/exploration/utility) or commands/<domain>.py
from evennia.commands.command import Command as BaseCommand

class CmdFoo(BaseCommand):
    key = "foo"
    aliases = ["f"]
    help_category = "General"   # or "Combat", "Inventory", "Admin", etc.

    def func(self):
        # self.caller = the character
        # self.args = everything after the command name (stripped)
        # self.switches = list of /switch flags
        pass
```

Register in `commands/default_cmdsets.py`:
```python
from commands.horror import CmdFoo
# in CharacterCmdSet.at_cmdset_creation:
self.add(CmdFoo())
```

Add help entry to `world/help_entries.py` in `HELP_ENTRY_DICTS`.

### New timed script

```python
# typeclasses/scripts.py
from evennia.scripts.scripts import DefaultScript

class FooScript(DefaultScript):
    def at_script_creation(self):
        self.key = "foo_script"
        self.interval = 60        # seconds between at_repeat calls
        self.persistent = True    # survives server restart
        self.start_delay = True   # don't fire immediately

    def at_repeat(self):
        obj = self.obj  # attached object, or None if global
        if not obj:
            self.stop()
            return
        # do work
```

Attach: `obj.scripts.add(FooScript)` or `evennia.create_script(FooScript)` for global.

### New typeclass attribute

Add to `at_object_creation` of the relevant class:
```python
self.db.my_attr = default_value
```

Document in `CLAUDE.md` typeclass map.

### New room attribute + builder command

1. Add attribute in `Room.at_object_creation`
2. Add `CmdSetFoo` with `locks = "cmd:perm(Builder)"` in `commands/horror.py`
3. Register in cmdset

### New item type / container

Subclass `Item` in `typeclasses/items.py`, override `at_object_creation` and any hook methods.

### New quest objective type

Add handling to `check_objective()` in `world/quest_system.py` for the new `type` string.
Add trigger call in the appropriate command/hook.

## Syntax check after implementing

```bash
python -c "
import ast
for f in ['typeclasses/scripts.py','commands/horror.py','commands/default_cmdsets.py','world/help_entries.py']:
    try:
        ast.parse(open(f).read())
        print(f'OK  {f}')
    except SyntaxError as e:
        print(f'ERR {f}:{e.lineno}: {e.msg}')
"
```

## Reload

```bash
.venv/bin/evennia reload
```

## Horror design principle

Every mechanic must have a **cost or risk**. No free abilities. No safe states.
Exploration degrades sanity. Light is finite. Resting can be interrupted. Death costs gold.
