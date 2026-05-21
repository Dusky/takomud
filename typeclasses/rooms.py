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
        self.db.encounter_table = []     # [{key, hp, attack_bonus, defense, damage_dice, xp_reward}]
        self.db.encounter_chance = 0.3   # probability per script tick
        self.db.cleared = False          # set True when a boss dies here
        self.db.cleared_boss = None
        self.db.hazard_hp = 0            # HP damage per hazard tick
        self.db.hazard_sanity = 0        # Sanity damage per hazard tick
        self.db.hazard_fear = 0          # Fear added per hazard tick
        self.db.hazard_message = ""      # Message shown to characters

    def return_appearance(self, looker, **kwargs):
        if self.db.dark and not self._has_light(looker):
            return (
                "|[000|wDarkness.|n\n"
                "The black is absolute. You can feel something in it.\n"
                "|x(You cannot see the exits.)|n"
            )
        text = super().return_appearance(looker, **kwargs)
        rec = self.db.recommended_level or 1
        if rec > 1:
            char_level = getattr(looker.db, "level", 1) or 1
            level_color = "|r" if char_level < rec else "|x"
            text = f"{level_color}[Recommended: Level {rec}+]|n\n" + text
        if self.db.cleared:
            boss = self.db.cleared_boss or "the boss"
            text = f"|x[{boss} has been defeated here]|n\n" + text
        return text

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
