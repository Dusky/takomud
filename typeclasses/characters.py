"""
Characters for Takomud.

Core horror stats:
  hp       — hit points (physical survival)
  hp_max
  sanity   — mental stability; 0 = psychotic break
  sanity_max
  fear     — 0–100 tension meter; high fear amplifies horror events
"""

from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.hp = 100
        self.db.hp_max = 100
        self.db.sanity = 100
        self.db.sanity_max = 100
        self.db.fear = 0

    # ------------------------------------------------------------------
    # Stat helpers
    # ------------------------------------------------------------------

    def adjust_hp(self, amount):
        self.db.hp = max(0, min(self.db.hp_max, self.db.hp + amount))
        if self.db.hp == 0:
            self.at_death()

    def adjust_sanity(self, amount):
        self.db.sanity = max(0, min(self.db.sanity_max, self.db.sanity + amount))
        if self.db.sanity == 0:
            self.at_sanity_break()

    def adjust_fear(self, amount):
        self.db.fear = max(0, min(100, self.db.fear + amount))

    def at_death(self):
        self.msg("|rYour vision goes dark. The cold takes you.|n")

    def at_sanity_break(self):
        self.msg(
            "|mThe last thread snaps. Reality folds inward "
            "and you are not there to witness it.|n"
        )

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def get_display_name(self, looker, **kwargs):
        name = super().get_display_name(looker, **kwargs)
        if self.db.fear >= 75:
            name = f"|r{name}|n"
        elif self.db.fear >= 40:
            name = f"|y{name}|n"
        return name
