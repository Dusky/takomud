"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit

from .objects import ObjectParent


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms.

    Supports optional locking:
      db.locked   — bool; True blocks traverse
      db.key_item — str item name required to unlock (None = no key needed, just unlock cmd)
      db.lock_desc — flavor text shown when blocked (optional)
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.locked = False
        self.db.key_item = None      # item key name required to unlock
        self.db.lock_desc = ""       # shown when traverse is blocked

    def at_traverse(self, traversing_object, target_location, **kwargs):
        if self.db.locked:
            msg = self.db.lock_desc or f"|rThe way {self.key} is barred. You cannot pass.|n"
            traversing_object.msg(msg)
            return False
        return super().at_traverse(traversing_object, target_location, **kwargs)

    def get_display_name(self, looker, **kwargs):
        name = super().get_display_name(looker, **kwargs)
        if self.db.locked:
            name = f"{name} |x[locked]|n"
        return name
