"""
Rooms for Takomud — dark/horror flavor.

Rooms support:
  - `dark` attribute: if True, characters without a light source see only the
    darkness description and cannot see other characters or exits.
  - `atmosphere` attribute: a list of strings randomly shown to occupants via
    AtmosphereScript.
  - `lore` attribute: hidden background text visible only to staff or via the
    `lore` command.
"""

import random
from evennia.objects.objects import DefaultRoom
from evennia.utils import utils
from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.dark = False
        self.db.atmosphere = []
        self.db.lore = ""

    def return_appearance(self, looker, **kwargs):
        if self.db.dark and not self._has_light(looker):
            return (
                "|[000|wDarkness.|n\n"
                "The black is absolute. You can feel something in it."
            )
        return super().return_appearance(looker, **kwargs)

    def _has_light(self, looker):
        if utils.inherits_from(looker, "typeclasses.characters.Character"):
            for obj in looker.contents:
                if obj.db.is_light_source and obj.db.lit:
                    return True
        return False

    def emit_atmosphere(self):
        """Send a random atmosphere string to all occupants."""
        msgs = self.db.atmosphere
        if not msgs:
            return
        msg = random.choice(msgs)
        for char in self.contents:
            if utils.inherits_from(char, "typeclasses.characters.Character"):
                char.msg(f"|x{msg}|n")
