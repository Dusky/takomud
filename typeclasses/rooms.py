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
        self.db.recommended_level = 1

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

    def at_object_receive(self, obj, source_location, move_type="move", **kwargs):
        """Warn characters entering rooms above their recommended level."""
        super().at_object_receive(obj, source_location, move_type=move_type, **kwargs)
        rec = self.db.recommended_level or 1
        if rec <= 1:
            return
        if not utils.inherits_from(obj, "typeclasses.characters.Character"):
            return
        char_level = obj.db.level or 1
        if char_level < rec:
            obj.msg(
                f"|rWarning: this area is recommended for level {rec}+. "
                f"You are level {char_level}. Proceed with caution.|n"
            )

    def emit_atmosphere(self):
        """Send a random atmosphere string to all occupants."""
        msgs = self.db.atmosphere
        if not msgs:
            return
        msg = random.choice(msgs)
        for char in self.contents:
            if utils.inherits_from(char, "typeclasses.characters.Character"):
                char.msg(f"|x{msg}|n")
