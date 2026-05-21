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
        # Gold piles: auto-convert to gold attribute
        if self.db.item_type == "misc" and self.db.value and not self.db.droppable is False:
            if "coin" in self.key.lower() or "gold" in self.key.lower():
                amount = self.db.value
                if amount and hasattr(getter, "gain_gold"):
                    getter.gain_gold(amount)
                    self.delete()
                    return
        if self.db.item_type == "quest":
            getter.msg(f"|yYou take {self.key}. Something about it feels important.|n")
        try:
            from world.quest_system import check_collect_trigger
            check_collect_trigger(getter, self.key)
        except Exception:
            pass

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


class Container(Item):
    """
    A container item: chest, bag, box. Can hold other items.
    Supports open/close state and optional locking.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.item_type = "misc"
        self.db.is_container = True
        self.db.is_open = False
        self.db.locked = False
        self.db.lock_key = None    # key item name required to unlock
        self.db.capacity = 10      # max items

    def get_display_name(self, looker, **kwargs):
        state = "|yopen|n" if self.db.is_open else "|xclosed|n"
        return f"|C{self.key}|n [{state}]"

    def open_container(self, opener):
        if self.db.locked:
            opener.msg(f"|r{self.key} is locked.|n")
            return
        if self.db.is_open:
            opener.msg(f"{self.key} is already open.")
            return
        self.db.is_open = True
        opener.msg(f"|yYou open {self.key}.|n")
        contents = [obj for obj in self.contents]
        if contents:
            names = ", ".join(obj.get_display_name(opener) for obj in contents)
            opener.msg(f" Inside: {names}")
        else:
            opener.msg(f" |xIt is empty.|n")

    def close_container(self, closer):
        if not self.db.is_open:
            closer.msg(f"{self.key} is already closed.")
            return
        self.db.is_open = False
        closer.msg(f"You close {self.key}.")

    def return_appearance(self, looker, **kwargs):
        if not self.db.is_open:
            return f"{self.key} — closed."
        contents = [obj for obj in self.contents]
        if not contents:
            return f"{self.key} — open, empty."
        names = "\n  ".join(obj.get_display_name(looker) for obj in contents)
        return f"{self.key} — open:\n  {names}"


class LoreDocument(Item):
    """A readable document: book, journal, inscription, note, letter."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.item_type = "misc"
        self.db.readable = True
        self.db.doc_text = ""
        self.db.doc_title = self.key
        self.db.sanity_cost = 2

    def get_display_name(self, looker, **kwargs):
        return f"|m{self.key}|n"

    def at_read(self, reader):
        if not self.db.doc_text:
            reader.msg("|xThe pages are blank — or perhaps you simply cannot read them.|n")
            return
        reader.msg(
            f"\n|w=== {self.db.doc_title} ===|n\n\n"
            f"{self.db.doc_text}\n\n"
            f"|x(You set it down. The words do not leave you.)|n"
        )
        cost = self.db.sanity_cost or 0
        if cost and hasattr(reader, "adjust_sanity"):
            reader.adjust_sanity(-cost)
