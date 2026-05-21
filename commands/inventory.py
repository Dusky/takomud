"""
Inventory, equipment, and item-use commands for Takomud.
"""

from evennia.commands.command import Command as BaseCommand
from evennia.utils import utils
from typeclasses.items import EQUIPMENT_SLOTS


class CmdInventory(BaseCommand):
    """
    List what you are carrying and wearing.

    Usage:
      inventory
      i
    """

    key = "inventory"
    aliases = ["i", "inv"]
    help_category = "General"

    def func(self):
        char = self.caller
        carrying = [obj for obj in char.contents
                    if utils.inherits_from(obj, "typeclasses.items.Item")]
        equipped = char.db.equipped or {}

        lines = ["\n|w--- Inventory ---|n"]
        if not carrying:
            lines.append("  |xNothing. Your hands are empty.|n")
        else:
            for obj in carrying:
                slot_label = ""
                for slot, dbref in equipped.items():
                    if dbref == obj.dbref:
                        slot_label = f" |c[{slot}]|n"
                        break
                lines.append(f"  {obj.get_display_name(char)}{slot_label}")

        lines.append("\n|w--- Equipment ---|n")
        if not any(equipped.values()):
            lines.append("  |xNothing equipped.|n")
        else:
            for slot in EQUIPMENT_SLOTS:
                dbref = equipped.get(slot)
                if dbref:
                    from evennia import search_object
                    results = search_object(dbref, use_dbref=True)
                    name = results[0].get_display_name(char) if results else "|rMissing|n"
                    lines.append(f"  {slot:10s} {name}")

        self.caller.msg("\n".join(lines))


class CmdEquip(BaseCommand):
    """
    Equip an item from your inventory.

    Usage:
      equip <item>
      wear <item>
      wield <item>
    """

    key = "equip"
    aliases = ["wear", "wield"]
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Equip what?")
            return

        obj = self.caller.search(self.args.strip(), location=self.caller)
        if not obj:
            return

        if not utils.inherits_from(obj, "typeclasses.items.Item"):
            self.caller.msg("That is not an equippable item.")
            return

        slot = obj.db.slot
        if not slot:
            self.caller.msg(f"{obj.key} cannot be equipped.")
            return

        equipped = self.caller.db.equipped or {}

        # Unequip whatever is in that slot
        old_dbref = equipped.get(slot)
        if old_dbref and old_dbref != obj.dbref:
            self.caller.msg(f"You unequip whatever was in {slot}.")

        equipped[slot] = obj.dbref
        self.caller.db.equipped = equipped
        self.caller.msg(f"|gYou equip {obj.key} [{slot}].|n")


class CmdUnequip(BaseCommand):
    """
    Remove an equipped item.

    Usage:
      unequip <item>
      remove <item>
    """

    key = "unequip"
    aliases = ["remove"]
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Unequip what?")
            return

        obj = self.caller.search(self.args.strip(), location=self.caller)
        if not obj:
            return

        equipped = self.caller.db.equipped or {}
        for slot, dbref in list(equipped.items()):
            if dbref == obj.dbref:
                del equipped[slot]
                self.caller.db.equipped = equipped
                self.caller.msg(f"|yYou remove {obj.key}.|n")
                return

        self.caller.msg(f"{obj.key} is not equipped.")


class CmdUse(BaseCommand):
    """
    Use a consumable item from your inventory.

    Usage:
      use <item>
    """

    key = "use"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Use what?")
            return

        obj = self.caller.search(self.args.strip(), location=self.caller)
        if not obj:
            return

        if not utils.inherits_from(obj, "typeclasses.items.Item"):
            self.caller.msg("You cannot use that.")
            return

        itype = obj.db.item_type
        if itype == "consumable":
            obj.at_use(self.caller)
        elif itype == "light":
            obj.toggle_light(self.caller)
        else:
            self.caller.msg(f"You turn {obj.key} over in your hands. Nothing happens.")


class CmdDrop(BaseCommand):
    """
    Drop an item from your inventory.

    Usage:
      drop <item>
    """

    key = "drop"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Drop what?")
            return

        obj = self.caller.search(self.args.strip(), location=self.caller)
        if not obj:
            return

        if not utils.inherits_from(obj, "typeclasses.items.Item"):
            self.caller.msg("You can't drop that.")
            return

        if not obj.db.droppable:
            self.caller.msg(f"|rYou cannot discard {obj.key}.|n")
            return

        # Unequip if equipped
        equipped = self.caller.db.equipped or {}
        for slot, dbref in list(equipped.items()):
            if dbref == obj.dbref:
                del equipped[slot]
                self.caller.db.equipped = equipped
                break

        obj.location = self.caller.location
        self.caller.msg(f"You drop {obj.key}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} drops {obj.key}.", exclude=[self.caller]
        )


class CmdGive(BaseCommand):
    """
    Give an item from your inventory to another character or NPC in the room.

    Usage:
      give <item> to <target>
    """

    key = "give"
    help_category = "General"

    def func(self):
        if not self.args or " to " not in self.args:
            self.caller.msg("Usage: give <item> to <target>")
            return

        item_name, target_name = self.args.split(" to ", 1)
        item_name = item_name.strip()
        target_name = target_name.strip()

        obj = self.caller.search(item_name, location=self.caller)
        if not obj:
            return

        if not utils.inherits_from(obj, "typeclasses.items.Item"):
            self.caller.msg("You can't give that.")
            return

        if not obj.db.droppable:
            self.caller.msg(f"|rYou cannot give away {obj.key}.|n")
            return

        target = self.caller.search(target_name, location=self.caller.location)
        if not target:
            return

        obj.location = target

        self.caller.msg(f"You hand {obj.key} to {target.key}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} hands {obj.key} to {target.key}.",
            exclude=[self.caller]
        )

        if utils.inherits_from(target, "typeclasses.npcs.NPC"):
            from world.quest_system import check_objective
            check_objective(self.caller, "deliver", f"{obj.key}:{target.key}")
