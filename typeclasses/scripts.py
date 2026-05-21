"""
Scripts for Takomud.
"""

import random
from evennia.scripts.scripts import DefaultScript


class Script(DefaultScript):
    pass


class AtmosphereScript(DefaultScript):
    """Attached to a Room; fires at_repeat to push flavor text to occupants."""

    def at_script_creation(self):
        self.key = "atmosphere_script"
        self.desc = "Emits atmospheric messages in a room."
        self.interval = 90
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        if self.obj:
            self.obj.emit_atmosphere()


class WorldEventScript(DefaultScript):
    """Global recurring event that fires messages into a set of rooms."""

    def at_script_creation(self):
        self.key = "world_event"
        self.desc = "Fires a world event into a set of rooms."
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        from evennia import search_object
        from evennia.utils import utils as ev_utils

        message = self.db.message or ""
        sanity_cost = self.db.sanity_cost or 0
        fear_cost = self.db.fear_cost or 0
        if not message:
            return

        for dbref in (self.db.room_dbrefs or []):
            results = search_object(dbref, use_dbref=True)
            if not results:
                continue
            room = results[0]
            for obj in room.contents:
                if ev_utils.inherits_from(obj, "typeclasses.characters.Character"):
                    obj.msg(f"|m{message}|n")
                    if sanity_cost and hasattr(obj, "adjust_sanity"):
                        obj.adjust_sanity(-sanity_cost)
                    if fear_cost and hasattr(obj, "adjust_fear"):
                        obj.adjust_fear(fear_cost)


class FuelDrainScript(DefaultScript):
    """Attached to a Character. Drains fuel from lit light sources every minute."""

    def at_script_creation(self):
        self.key = "fuel_drain"
        self.desc = "Drains lit light sources."
        self.interval = 60
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        char = self.obj
        if not char:
            return
        for item in char.contents:
            if not (item.db.is_light_source and item.db.lit):
                continue
            if item.db.fuel is None:
                continue
            item.db.fuel = max(0, item.db.fuel - 1)
            if item.db.fuel <= 3:
                char.msg(f"|y{item.key} flickers. It won't last much longer.|n")
            if item.db.fuel == 0:
                item.db.lit = False
                char.msg(f"|r{item.key} sputters and goes dark.|n")


_HALLUCINATIONS = [
    "Someone whispers your name. There is no one nearby.",
    "The walls breathe. When you look directly at them, they stop.",
    "You feel certain you have already done this — all of it — before.",
    "Something is behind you. You turn. Nothing is there yet.",
    "The exits look different than they did a moment ago.",
    "Your reflection in a puddle on the floor doesn't move when you do.",
    "You hear a door close. You have not heard a door open.",
    "The shadows contain the right number of people.",
    "The room is colder than it should be. Then it isn't.",
    "You blink. The room's layout has shifted — but only slightly. You are not sure.",
]


class SanityHallucinationScript(DefaultScript):
    """Fires hallucination messages at low sanity. Stops if sanity recovers above 25."""

    def at_script_creation(self):
        self.key = "sanity_hallucination"
        self.desc = "Low-sanity hallucinations."
        self.interval = 120
        self.persistent = False
        self.start_delay = True

    def at_repeat(self):
        char = self.obj
        if not char:
            self.stop()
            return
        san = char.db.sanity or 0
        if san > 25:
            self.stop()
            return
        char.msg(f"|m{random.choice(_HALLUCINATIONS)}|n")


class PlayerCombatScript(DefaultScript):
    """
    Attached to a Character when combat begins.
    Fires an attack against combat_target every 4 seconds.
    Stops when target is dead, leaves the room, or combat_target is cleared.
    """

    def at_script_creation(self):
        self.key = "player_combat"
        self.desc = "Drives player auto-attack."
        self.interval = 4
        self.persistent = False
        self.start_delay = True

    def at_repeat(self):
        char = self.obj
        if not char or not char.db.combat_target:
            self.stop()
            return
        target = char.db.combat_target
        if not target or not target.pk or target.location != char.location:
            char.db.combat_target = None
            char.msg("|xYou have lost your target.|n")
            self.stop()
            return
        _execute_player_attack(char, target)


def _execute_player_attack(char, target):
    """Resolve one player attack round. Called by PlayerCombatScript and CmdAttack."""
    from evennia import search_object
    from world.quest_system import check_objective

    fear = char.db.fear or 0
    fear_penalty = 0
    if fear >= 75:
        fear_penalty = -4
        if random.random() < 0.2:
            char.msg("|rFear seizes you. You cannot act.|n")
            return
    elif fear >= 40:
        fear_penalty = -2

    equipped = char.db.equipped or {}
    weapon = None
    dbref = equipped.get("main_hand")
    if dbref:
        results = search_object(dbref, use_dbref=True)
        if results:
            weapon = results[0]

    dice = (weapon.db.damage_dice if weapon else None) or "1d4"
    atk_bonus = (char.db.attack_bonus or 0) + (weapon.db.attack_bonus if weapon else 0) + fear_penalty
    defense = target.db.defense or 10

    roll = random.randint(1, 20) + atk_bonus
    if roll >= defense:
        try:
            count, sides = dice.lower().split("d")
            dmg = sum(random.randint(1, int(sides)) for _ in range(int(count)))
        except Exception:
            dmg = 1
        char.msg(f"|wYou strike {target.key} for {dmg} damage.|n")
        char.location.msg_contents(
            f"|w{char.name} strikes {target.key} for {dmg} damage.|n",
            exclude=[char],
        )
        target.take_damage(dmg, attacker=char)
        check_objective(char, "kill", target.key)
    else:
        char.msg(f"|yYou swing at {target.key} and miss.|n")
