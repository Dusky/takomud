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


class CmdRest(BaseCommand):
    """
    Sit and rest to recover HP and Sanity over time.

    Usage:
      rest

    Recovery: +5 HP and +3 Sanity every 10 seconds.
    Interrupted instantly if you enter combat.
    Type any movement command or 'stop' to stand up early.
    """

    key = "rest"
    aliases = ["sit", "sleep"]
    help_category = "General"

    def func(self):
        char = self.caller
        if char.db.combat_target:
            char.msg("|rYou cannot rest while in combat.|n")
            return
        if char.scripts.get("rest_script"):
            char.msg("|xYou are already resting.|n")
            return
        hp = char.db.hp or 0
        hp_max = char.db.hp_max or 100
        san = char.db.sanity or 100
        san_max = char.db.sanity_max or 100
        if hp >= hp_max and san >= san_max:
            char.msg("|xYou are already at full health and clarity.|n")
            return
        from typeclasses.scripts import RestScript
        char.scripts.add(RestScript)
        char.msg("|xYou settle down to rest. Recovery begins.|n")
        char.location.msg_contents(
            f"{char.name} sits down to rest.", exclude=[char]
        )


class CmdInspect(BaseCommand):
    """
    Examine an item for detailed information.

    Usage:
      inspect <item>

    Shows all mechanical properties of the item.
    """

    key = "inspect"
    aliases = ["examine", "ex"]
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Inspect what?")
            return

        obj = self.caller.search(self.args.strip())
        if not obj:
            return

        if not utils.inherits_from(obj, "typeclasses.items.Item"):
            # Fall through to default look
            self.caller.msg(obj.db.desc or "You see nothing special.")
            return

        lines = [
            f"\n|w=== {obj.get_display_name(self.caller)} ===|n",
            f" {obj.db.desc or ''}",
            f"",
            f" Type:    {obj.db.item_type or 'misc'}",
        ]

        if obj.db.item_type == "weapon":
            lines.append(f" Damage:  {obj.db.damage_dice or '1d4'}")
            lines.append(f" Attack:  +{obj.db.attack_bonus or 0}")
            if obj.db.slot:
                lines.append(f" Slot:    {obj.db.slot}")

        elif obj.db.item_type == "armor":
            lines.append(f" Defense: +{obj.db.defense_bonus or 0}")
            if obj.db.slot:
                lines.append(f" Slot:    {obj.db.slot}")

        elif obj.db.item_type == "consumable":
            effect = obj.db.effect or {}
            parts = []
            if "hp" in effect:
                parts.append(f"HP {effect['hp']:+d}")
            if "sanity" in effect:
                parts.append(f"Sanity {effect['sanity']:+d}")
            if "fear" in effect:
                parts.append(f"Fear {effect['fear']:+d}")
            lines.append(f" Effect:  {', '.join(parts) or 'unknown'}")

        elif obj.db.item_type == "light":
            fuel = obj.db.fuel
            fuel_str = str(fuel) if fuel is not None else "infinite"
            lit_str = "|ylit|n" if obj.db.lit else "|xunlit|n"
            lines.append(f" Fuel:    {fuel_str}")
            lines.append(f" State:   {lit_str}")

        value = obj.db.value or 0
        lines.append(f" Value:   {value} gold")
        weight = obj.db.weight or 1
        lines.append(f" Weight:  {weight}")

        self.caller.msg("\n".join(lines))


class CmdOpenContainer(BaseCommand):
    """
    Open a container (chest, bag, box).

    Usage:
      open <container>
    """

    key = "open"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Open what?")
            return
        obj = self.caller.search(self.args.strip())
        if not obj:
            return
        if not utils.inherits_from(obj, "typeclasses.items.Container"):
            self.caller.msg(f"You can't open {obj.key}.")
            return
        obj.open_container(self.caller)


class CmdCloseContainer(BaseCommand):
    """
    Close an open container.

    Usage:
      close <container>
    """

    key = "close"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Close what?")
            return
        obj = self.caller.search(self.args.strip())
        if not obj:
            return
        if not utils.inherits_from(obj, "typeclasses.items.Container"):
            self.caller.msg(f"You can't close {obj.key}.")
            return
        obj.close_container(self.caller)


class CmdPutIn(BaseCommand):
    """
    Put an item into a container.

    Usage:
      put <item> in <container>
    """

    key = "put"
    help_category = "General"

    def func(self):
        if not self.args or " in " not in self.args:
            self.caller.msg("Usage: put <item> in <container>")
            return
        item_name, cont_name = self.args.split(" in ", 1)
        item = self.caller.search(item_name.strip(), location=self.caller)
        if not item:
            return
        cont = self.caller.search(cont_name.strip())
        if not cont:
            return
        if not utils.inherits_from(cont, "typeclasses.items.Container"):
            self.caller.msg(f"{cont.key} is not a container.")
            return
        if not cont.db.is_open:
            self.caller.msg(f"{cont.key} is closed.")
            return
        if not item.db.droppable:
            self.caller.msg(f"You can't put {item.key} in there.")
            return
        item.location = cont
        self.caller.msg(f"You put {item.key} into {cont.key}.")


class CmdTakeFrom(BaseCommand):
    """
    Take an item from a container.

    Usage:
      take <item> from <container>
    """

    key = "take"
    aliases = ["get"]
    help_category = "General"

    def func(self):
        if not self.args or " from " not in self.args:
            # Fall back to normal get if no "from"
            self.caller.msg("Usage: take <item> from <container>")
            return
        item_name, cont_name = self.args.split(" from ", 1)
        cont = self.caller.search(cont_name.strip())
        if not cont:
            return
        if not utils.inherits_from(cont, "typeclasses.items.Container"):
            self.caller.msg(f"{cont.key} is not a container.")
            return
        if not cont.db.is_open:
            self.caller.msg(f"{cont.key} is closed.")
            return
        item = cont.search(item_name.strip(), location=cont)
        if not item:
            return
        item.location = self.caller
        self.caller.msg(f"You take {item.key} from {cont.key}.")
