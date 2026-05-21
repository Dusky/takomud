"""
Combat commands for Takomud.
"""

import random
from evennia.commands.command import Command as BaseCommand
from evennia.utils import utils


class CmdAttack(BaseCommand):
    """
    Attack a target in the room.

    Usage:
      attack <target>
      kill <target>

    Starts continuous combat — you auto-attack every 4 seconds.
    Use |wstop|n or |wflee|n to disengage.
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

        if self.caller.db.combat_target == target:
            self.caller.msg(f"You are already fighting {target.key}.")
            return

        self.caller.db.combat_target = target
        self.caller.msg(f"|rYou engage {target.key}.|n")
        self.caller.location.msg_contents(
            f"|r{self.caller.name} attacks {target.key}!|n",
            exclude=[self.caller],
        )

        # Start auto-attack loop
        from typeclasses.scripts import PlayerCombatScript, _execute_player_attack
        if not self.caller.scripts.get("player_combat"):
            self.caller.scripts.add(PlayerCombatScript)

        # Immediate first strike
        _execute_player_attack(self.caller, target)

        # Wake mob's retaliation
        if utils.inherits_from(target, "typeclasses.npcs.Mob") and not target.db.combat_target:
            target.db.combat_target = self.caller
            from typeclasses.npcs import CombatScript
            if not target.scripts.get("combat_script"):
                target.scripts.add(CombatScript)


class CmdStop(BaseCommand):
    """
    Stop fighting and disengage from combat.

    Usage:
      stop

    Clears your combat target. The enemy may still be hostile.
    """

    key = "stop"
    aliases = ["disengage", "stand"]
    help_category = "Combat"

    def func(self):
        if not self.caller.db.combat_target:
            self.caller.msg("You are not in combat.")
            return
        self.caller.db.combat_target = None
        for s in self.caller.scripts.all():
            if s.key == "player_combat":
                s.stop()
        self.caller.msg("|yYou disengage.|n")


class CmdFlee(BaseCommand):
    """
    Flee combat through a random exit.

    Usage:
      flee

    Sanity cost: 5. Fails if cornered.
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

        self.caller.db.combat_target = None
        for s in self.caller.scripts.all():
            if s.key == "player_combat":
                s.stop()

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
        is_boss = bool(getattr(target.db, "is_boss", False))

        if is_boss:
            assessment = "|RThis is something you should not fight alone.|n"
        elif ratio < 0.5:
            assessment = "|gWell within your means. For now.|n"
        elif ratio < 1.0:
            assessment = "|yFormidable. Caution is warranted.|n"
        elif ratio < 2.0:
            assessment = "|rDangerous. You may not survive.|n"
        else:
            assessment = "|rDo not fight this. Do not.|n"

        self.caller.msg(f"You study {target.key}: {assessment}")
