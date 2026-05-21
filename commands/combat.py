"""
Combat commands for Takomud.
"""

import random
from evennia.commands.command import Command as BaseCommand
from evennia.utils import utils


def _roll_dice(dice_str):
    try:
        count, sides = dice_str.lower().split("d")
        return sum(random.randint(1, int(sides)) for _ in range(int(count)))
    except Exception:
        return 1


class CmdAttack(BaseCommand):
    """
    Attack a target in the room.

    Usage:
      attack <target>
      kill <target>

    Initiates combat. You and the target exchange blows each round.
    Use |wflee|n to attempt escape.
    """

    key = "attack"
    aliases = ["kill", "hit", "fight"]
    help_category = "Combat"

    def func(self):
        if not self.args:
            self.caller.msg("Attack what?")
            return

        target = self.caller.search(self.args.strip(), location=self.caller.location)
        if not target:
            return

        if target == self.caller:
            self.caller.msg("You contemplate it. Then think better of it.")
            return

        if not utils.inherits_from(target, "typeclasses.npcs.NPC"):
            self.caller.msg("You cannot attack that.")
            return

        # Resolve one player attack round
        caller = self.caller
        weapon = _get_equipped_weapon(caller)
        dice = weapon.db.damage_dice if weapon else "1d4"
        atk_bonus = (caller.db.attack_bonus or 0) + (weapon.db.attack_bonus if weapon else 0)
        defense = target.db.defense or 10

        roll = random.randint(1, 20) + atk_bonus
        if roll >= defense:
            dmg = _roll_dice(dice)
            caller.msg(f"|wYou strike {target.key} for {dmg} damage.|n")
            caller.location.msg_contents(
                f"|w{caller.name} strikes {target.key} for {dmg} damage.|n",
                exclude=[caller]
            )
            target.take_damage(dmg, attacker=caller)
            from world.quest_system import check_objective
            check_objective(caller, "kill", target.key)
        else:
            caller.msg(f"|yYou swing at {target.key} and miss.|n")
            caller.location.msg_contents(
                f"|y{caller.name} swings at {target.key} and misses.|n",
                exclude=[caller]
            )

        # Trigger mob retaliation if mob is still alive
        if target.pk and utils.inherits_from(target, "typeclasses.npcs.Mob"):
            if not target.db.combat_target:
                target.db.combat_target = caller
                from typeclasses.npcs import CombatScript
                if not target.scripts.get("combat_script"):
                    target.scripts.add(CombatScript)


class CmdFlee(BaseCommand):
    """
    Attempt to flee combat through a random exit.

    Usage:
      flee

    Sanity cost: 5. May fail if you are cornered.
    """

    key = "flee"
    aliases = ["run", "escape"]
    help_category = "Combat"

    def func(self):
        exits = self.caller.location.exits
        if not exits:
            self.caller.msg("|rThere is nowhere to run.|n")
            self.caller.adjust_sanity(-5)
            return

        exit_obj = random.choice(exits)
        self.caller.msg(f"|yYou flee through {exit_obj.key}!|n")
        self.caller.adjust_sanity(-5)
        self.caller.move_to(exit_obj.destination, quiet=False)


class CmdConsider(BaseCommand):
    """
    Assess how dangerous a target appears.

    Usage:
      consider <target>
      con <target>
    """

    key = "consider"
    aliases = ["con"]
    help_category = "Combat"

    def func(self):
        if not self.args:
            self.caller.msg("Consider what?")
            return

        target = self.caller.search(self.args.strip(), location=self.caller.location)
        if not target:
            return

        if not utils.inherits_from(target, "typeclasses.npcs.NPC"):
            self.caller.msg("That is not a creature you can assess.")
            return

        my_hp = self.caller.db.hp or 100
        their_hp = target.db.hp or 50
        ratio = their_hp / max(my_hp, 1)

        if ratio < 0.5:
            assessment = "|gWell within your means. For now.|n"
        elif ratio < 1.0:
            assessment = "|yFormidable. Caution is warranted.|n"
        elif ratio < 2.0:
            assessment = "|rDangerous. You may not survive.|n"
        else:
            assessment = "|rDo not fight this. Do not.|n"

        self.caller.msg(f"You study {target.key}: {assessment}")


def _get_equipped_weapon(char):
    equipped = char.db.equipped or {}
    dbref = equipped.get("main_hand")
    if dbref:
        from evennia import search_object
        results = search_object(dbref, use_dbref=True)
        if results:
            return results[0]
    return None
