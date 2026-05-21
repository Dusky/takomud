# /remove-feature

Safely remove a command, system, attribute, or room from Takomud.

## What to do

Ask the user what they want to remove and confirm before touching anything. Then:

### Remove a command
1. Delete or comment out the class in `commands/horror.py` or its file
2. Remove the `self.add(CmdFoo())` line from `commands/default_cmdsets.py`
3. Run `.venv/bin/evennia reload`

### Remove a typeclass attribute
1. Remove the `self.db.attr = ...` line from `at_object_creation()`
2. Optionally clean up existing objects in the shell:
   ```python
   for obj in evennia.search_object('', typeclass=TheClass):
       del obj.db.attr
   ```
3. Reload

### Remove a room
1. In `world/batch_build.py`, delete the `make_room(...)` call and any `link(...)` calls referencing it
2. Delete from the database via the shell:
   ```python
   import evennia
   room = evennia.search_object("Room Key", typeclass="typeclasses.rooms.Room")[0]
   room.delete()
   ```
3. **Check** that no exits or characters reference the deleted room before deleting.

### Remove a script
1. Stop and delete it in the shell:
   ```python
   obj.scripts.delete("script_key")
   ```
2. Remove the class from `typeclasses/scripts.py`

## Safety rules
- Never delete the `#1` Limbo room or the `#2` superuser character
- Always check that rooms are empty before deletion
- Confirm with the user before any destructive database operation
