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


class RespawnScript(DefaultScript):
    """Global script managing mob respawn queue."""

    def at_script_creation(self):
        self.key = "respawn_manager"
        self.desc = "Manages mob respawn timers."
        self.interval = 30
        self.persistent = True
        self.start_delay = True
        self.db.queue = []

    def enqueue(self, mob):
        import time
        if not mob.location:
            return
        entry = {
            "respawn_at": time.time() + (mob.db.respawn_delay or 300),
            "room_dbref": mob.location.dbref,
            "mob_data": {
                "key":          mob.key,
                "desc":         mob.db.desc or "",
                "hp":           mob.db.hp_max or mob.db.hp or 30,
                "attack_bonus": mob.db.attack_bonus or 3,
                "defense":      mob.db.defense or 8,
                "damage_dice":  mob.db.damage_dice or "1d6",
                "xp_reward":    mob.db.xp_reward or 25,
                "gold_drop":    mob.db.gold_drop or 0,
                "faction":      mob.db.faction or "neutral",
                "aggro":        mob.db.aggro if mob.db.aggro is not None else True,
                "wanders":      mob.db.wanders or False,
                "loot_table":   list(mob.db.loot_table or []),
                "respawn_delay":mob.db.respawn_delay or 300,
                "status_effect":mob.db.status_effect,
                "is_boss":      bool(mob.db.is_boss),
            },
        }
        queue = list(self.db.queue or [])
        queue.append(entry)
        self.db.queue = queue

    def at_repeat(self):
        import time
        import evennia
        now = time.time()
        queue = list(self.db.queue or [])
        remaining = []
        for entry in queue:
            if now >= entry["respawn_at"]:
                self._spawn(entry)
            else:
                remaining.append(entry)
        self.db.queue = remaining

    def _spawn(self, entry):
        import evennia
        from typeclasses.npcs import Mob, Boss
        from typeclasses.scripts import WanderScript
        results = evennia.search_object(entry["room_dbref"], use_dbref=True)
        if not results:
            return
        room = results[0]
        d = entry["mob_data"]
        cls = Boss if d.get("is_boss") else Mob
        mob = evennia.create_object(cls, key=d["key"], location=room)
        mob.db.desc = d["desc"]
        mob.db.hp = d["hp"]
        mob.db.hp_max = d["hp"]
        mob.db.attack_bonus = d["attack_bonus"]
        mob.db.defense = d["defense"]
        mob.db.damage_dice = d["damage_dice"]
        mob.db.xp_reward = d["xp_reward"]
        mob.db.gold_drop = d["gold_drop"]
        mob.db.faction = d["faction"]
        mob.db.aggro = d["aggro"]
        mob.db.wanders = d["wanders"]
        mob.db.loot_table = d["loot_table"]
        mob.db.respawn_delay = d["respawn_delay"]
        mob.db.status_effect = d["status_effect"]
        if d["wanders"]:
            mob.scripts.add(WanderScript)
        room.msg_contents(f"|x{mob.key} emerges from the dark.|n")


class WanderScript(DefaultScript):
    """Attached to a Mob. Moves it through a random exit periodically."""

    def at_script_creation(self):
        self.key = "wander_script"
        self.desc = "Mob wandering."
        self.interval = 90
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        mob = self.obj
        if not mob or mob.db.combat_target or not mob.location:
            return
        exits = mob.location.exits
        if not exits:
            return
        exit_obj = random.choice(exits)
        mob.move_to(exit_obj.destination, quiet=True)


class StatusEffectScript(DefaultScript):
    """Attached to a Character. Ticks down bleed/poison/stun each interval."""

    def at_script_creation(self):
        self.key = "status_effects"
        self.desc = "Processes active status effects."
        self.interval = 3
        self.persistent = False
        self.start_delay = True

    def at_repeat(self):
        char = self.obj
        if not char:
            self.stop()
            return
        effects = dict(char.db.status_effects or {})
        if not effects:
            self.stop()
            return
        to_remove = []
        for name, data in effects.items():
            if name == "bleed":
                dmg = data.get("dmg", 3)
                char.msg(f"|rYou bleed for {dmg} damage.|n")
                char.adjust_hp(-dmg)
            elif name == "poison":
                dmg = data.get("dmg", 2)
                san = data.get("san", 1)
                char.msg(f"|gPoison: -{dmg} HP, -{san} Sanity.|n")
                char.adjust_hp(-dmg)
                char.adjust_sanity(-san)
            elif name == "stun":
                char.msg("|yYou are stunned and cannot act.|n")
            data["ticks"] -= 1
            if data["ticks"] <= 0:
                to_remove.append(name)
                char.msg(f"|y{name.title()} has worn off.|n")
        for name in to_remove:
            del effects[name]
        char.db.status_effects = effects
        if not effects:
            self.stop()


class HazardScript(DefaultScript):
    """
    Attached to a Room. Each tick deals damage/sanity/fear loss to all
    characters present. Configure via room.db.hazard_* attributes.
    """

    def at_script_creation(self):
        self.key = "hazard_script"
        self.desc = "Environmental hazard."
        self.interval = 15
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        room = self.obj
        if not room:
            self.stop()
            return
        from evennia.utils import utils as ev_utils
        hp_dmg = room.db.hazard_hp or 0
        san_dmg = room.db.hazard_sanity or 0
        fear_dmg = room.db.hazard_fear or 0
        msg = room.db.hazard_message or "|rThe environment tears at you.|n"
        for obj in list(room.contents):
            if ev_utils.inherits_from(obj, "typeclasses.characters.Character"):
                obj.msg(msg)
                if hp_dmg:
                    obj.adjust_hp(-hp_dmg)
                if san_dmg:
                    obj.adjust_sanity(-san_dmg)
                if fear_dmg:
                    obj.adjust_fear(fear_dmg)


class MerchantRestockScript(DefaultScript):
    """
    Attached to an NPC merchant. Restores shop_stock quantities each interval.
    shop_stock: {prototype_key: current_qty}  (-1 = unlimited)
    restock_list: [{prototype_key, qty, max_qty}]
    """

    def at_script_creation(self):
        self.key = "merchant_restock"
        self.desc = "Restocks merchant inventory."
        self.interval = 3600   # 1 hour default
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        merchant = self.obj
        if not merchant:
            self.stop()
            return
        restock = merchant.db.restock_list or []
        stock = dict(merchant.db.shop_stock or {})
        restocked = 0
        for entry in restock:
            key = entry.get("prototype_key")
            max_qty = entry.get("max_qty", 5)
            current = stock.get(key, 0)
            if current < max_qty:
                stock[key] = max_qty
                restocked += 1
        merchant.db.shop_stock = stock
        if restocked:
            merchant.location and merchant.location.msg_contents(
                f"|x{merchant.key} restocks their wares.|n"
            )


class SurgeScript(DefaultScript):
    """Survivor class Surge ability. +5 attack bonus for 30 seconds."""

    def at_script_creation(self):
        self.key = "surge_script"
        self.desc = "Survivor surge."
        self.interval = 30
        self.persistent = False
        self.start_delay = True   # fire AFTER 30s, not immediately
        self.repeats = 1          # fire once to remove the buff

    def at_repeat(self):
        char = self.obj
        if not char:
            self.stop()
            return
        char.db.attack_bonus = max(1, (char.db.attack_bonus or 1) - 5)
        char.msg("|yThe surge fades. Your focus returns to its usual edge.|n")
        self.stop()


class HunterTrapScript(DefaultScript):
    """
    Attached to a Room after a Hunter sets a trap.
    The next mob entering the room is stunned and takes damage.
    """

    def at_script_creation(self):
        self.key = "hunter_trap"
        self.desc = "Hunter's trap."
        self.interval = 300   # auto-disarm after 5 minutes
        self.persistent = False
        self.start_delay = True
        self.repeats = 1

    def at_repeat(self):
        room = self.obj
        if room:
            room.msg_contents("|xThe trap rusts and falls apart.|n")
        self.stop()


class RestScript(DefaultScript):
    """
    Attached to a Character while resting.
    Recovers HP and Sanity each tick. Cancelled if combat_target is set.
    """

    def at_script_creation(self):
        self.key = "rest_script"
        self.desc = "Resting recovery."
        self.interval = 10
        self.persistent = False
        self.start_delay = True
        self.db.ticks = 0

    def at_repeat(self):
        char = self.obj
        if not char:
            self.stop()
            return
        if char.db.combat_target:
            char.msg("|rYou are jolted out of your rest.|n")
            self.stop()
            return
        hp_max = char.db.hp_max or 100
        san_max = char.db.sanity_max or 100
        hp = char.db.hp or 0
        san = char.db.sanity or 100

        hp_gain = min(5, hp_max - hp)
        san_gain = min(3, san_max - san)

        if hp_gain > 0:
            char.adjust_hp(hp_gain)
        if san_gain > 0:
            char.adjust_sanity(san_gain)

        self.db.ticks = (self.db.ticks or 0) + 1
        if hp_gain == 0 and san_gain == 0:
            char.msg("|xYou are fully recovered. You stand.|n")
            self.stop()
            return
        if self.db.ticks % 3 == 0:
            char.msg(f"|xYou rest. (+{hp_gain} HP, +{san_gain} Sanity)|n")


class RandomEncounterScript(DefaultScript):
    """
    Attached to a Room. On each tick, chance to spawn a transient mob from
    the room's encounter_table. Mob deletes itself when it leaves the room
    or is killed. Does not respawn.
    """

    def at_script_creation(self):
        self.key = "random_encounter"
        self.desc = "Random encounter spawner."
        self.interval = 120
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        room = self.obj
        if not room:
            self.stop()
            return
        table = room.db.encounter_table or []
        if not table:
            return

        from evennia.utils import utils as ev_utils
        has_players = any(
            ev_utils.inherits_from(obj, "typeclasses.characters.Character")
            for obj in room.contents
        )
        if not has_players:
            return

        chance = room.db.encounter_chance or 0.3
        if random.random() > chance:
            return

        entry = random.choice(table)
        prototype_key = entry.get("prototype_key")
        mob_key = entry.get("key", "Lurking Shape")

        mob = None
        if prototype_key:
            try:
                from evennia.prototypes import spawner
                objs = spawner.spawn(prototype_key)
                if objs:
                    mob = objs[0]
                    mob.location = room
            except Exception:
                pass

        if not mob:
            from typeclasses.npcs import Mob
            import evennia
            mob = evennia.create_object(Mob, key=mob_key, location=room)
            mob.db.hp = entry.get("hp", 20)
            mob.db.hp_max = mob.db.hp
            mob.db.attack_bonus = entry.get("attack_bonus", 2)
            mob.db.defense = entry.get("defense", 8)
            mob.db.damage_dice = entry.get("damage_dice", "1d4")
            mob.db.xp_reward = entry.get("xp_reward", 15)
            mob.db.aggro = True
            mob.db.respawn_delay = 0  # transient — no respawn

        room.msg_contents(f"|xSomething emerges from the shadows. {mob.key}.|n")


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
