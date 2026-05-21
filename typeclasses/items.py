"""
Item typeclass for Takomud.

Item types:
  weapon      — has damage_dice, attack_bonus
  armor       — has defense_bonus, slot
  consumable  — single-use; triggers at_use()
  quest       — cannot be dropped; plot-critical
  light       — has fuel, is_light_source flag
  misc        — flavor/tradeable, no mechanical effect
"""

from evennia.objects.objects import DefaultObject
from .objects import ObjectParent


EQUIPMENT_SLOTS = ("head", "chest", "hands", "legs", "feet",
                   "main_hand", "off_hand", "neck")


class Item(ObjectParent, DefaultObject):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.item_type = "misc"      # weapon / armor / consumable / quest / light / misc
        self.db.slot = None             # equipment slot (armor/weapon only)
        self.db.damage_dice = "1d4"     # weapon
        self.db.attack_bonus = 0        # weapon
        self.db.defense_bonus = 0       # armor
        self.db.effect = {}             # consumable: {"hp": 20, "sanity": 10, "fear": -20}
        self.db.fuel = None             # light: int ticks remaining, None = infinite
        self.db.lit = False             # light source state
        self.db.is_light_source = False
        self.db.droppable = True
        self.db.value = 0               # currency value (for shops)
        self.db.weight = 1

    def at_get(self, getter, **kwargs):
        if self.db.item_type == "quest":
            getter.msg(f"|yYou take {self.key}. Something about it feels important.|n")

    def at_drop(self, dropper, **kwargs):
        if not self.db.droppable:
            dropper.msg(f"|rYou cannot bring yourself to discard {self.key}.|n")
            return False

    def at_use(self, user):
        """Called when a consumable is used."""
        effect = self.db.effect or {}
        msgs = []
        if "hp" in effect:
            user.adjust_hp(effect["hp"])
            sign = "+" if effect["hp"] >= 0 else ""
            msgs.append(f"{sign}{effect['hp']} HP")
        if "sanity" in effect:
            user.adjust_sanity(effect["sanity"])
            sign = "+" if effect["sanity"] >= 0 else ""
            msgs.append(f"{sign}{effect['sanity']} Sanity")
        if "fear" in effect:
            user.adjust_fear(effect["fear"])
            sign = "+" if effect["fear"] >= 0 else ""
            msgs.append(f"{sign}{effect['fear']} Fear")
        if msgs:
            user.msg(f"|g{self.key}: {', '.join(msgs)}|n")
        else:
            user.msg(f"You use {self.key}. Nothing obvious happens.")
        self.delete()

    def toggle_light(self, handler):
        """Toggle a light source on/off."""
        if not self.db.is_light_source:
            handler.msg(f"{self.key} is not a light source.")
            return
        if self.db.fuel is not None and self.db.fuel <= 0:
            handler.msg(f"{self.key} has no fuel remaining.")
            return
        self.db.lit = not self.db.lit
        state = "flickers to life" if self.db.lit else "goes dark"
        handler.msg(f"|y{self.key} {state}.|n")

    def get_display_name(self, looker, **kwargs):
        name = self.key
        t = self.db.item_type
        if t == "weapon":
            name = f"|w{name}|n"
        elif t == "armor":
            name = f"|C{name}|n"
        elif t == "consumable":
            name = f"|g{name}|n"
        elif t == "quest":
            name = f"|y{name}|n"
        elif t == "light":
            name = f"|Y{name}|n" if self.db.lit else f"|x{name}|n"
        return name
