"""
NPC and Mob typeclasses for Takomud.

NPC  — non-hostile, dialogue-capable, may give quests, may sell/trade.
Mob  — inherits NPC; hostile, initiates combat, drops loot on death.
"""

import random
from evennia.objects.objects import DefaultCharacter
from evennia.scripts.scripts import DefaultScript
from evennia.utils import utils
from .objects import ObjectParent


# ---------------------------------------------------------------------------
# Combat script — drives mob retaliation each round
# ---------------------------------------------------------------------------

class CombatScript(DefaultScript):

    def at_script_creation(self):
        self.key = "combat_script"
        self.interval = 3
        self.persistent = False
        self.start_delay = True

    def at_repeat(self):
        mob = self.obj
        if not mob or not mob.db.combat_target:
            self.stop()
            return
        target = mob.db.combat_target
        if not target or target.location != mob.location:
            mob.db.combat_target = None
            mob.msg_contents(f"|x{mob.name} loses track of its quarry.|n")
            self.stop()
            return
        mob.execute_attack(target)


# ---------------------------------------------------------------------------
# NPC typeclass
# ---------------------------------------------------------------------------

class NPC(ObjectParent, DefaultCharacter):
    """Non-hostile NPC — talks, trades, gives quests."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_npc = True
        self.db.faction = "neutral"
        self.db.dialogue = {}          # {"greeting": "...", "topics": {"key": "response"}}
        self.db.quest_keys = []        # list of quest keys this NPC can give
        self.db.shop = []              # list of item prototype keys for sale
        self.db.hp = 50
        self.db.hp_max = 50
        self.db.attack_bonus = 0
        self.db.defense = 5
        self.db.xp_reward = 0
        self.db.loot_table = []        # list of {prototype_key, chance (0-1)}
        self.db.combat_target = None
        # Stop NPCs being puppeted
        self.locks.add("puppet:false()")

    def at_desc(self, looker=None, **kwargs):
        pass

    def get_display_name(self, looker, **kwargs):
        return f"|c{self.key}|n"

    def at_talked_to(self, speaker, topic=None):
        """Called by CmdTalk. Returns dialogue string."""
        dlg = self.db.dialogue or {}
        if topic:
            resp = dlg.get("topics", {}).get(topic.lower())
            if resp:
                return resp
            return dlg.get("unknown", "They regard you with distant eyes and say nothing.")
        return dlg.get("greeting", "They nod but do not speak.")

    def take_damage(self, amount, attacker=None):
        self.db.hp = max(0, self.db.hp - amount)
        if self.db.hp <= 0:
            self.at_death(attacker)
        return self.db.hp

    def at_death(self, killer=None):
        self.location.msg_contents(
            f"|r{self.key} collapses. The silence that follows is worse than the noise.|n",
            exclude=[self]
        )
        self._drop_loot()
        if killer:
            xp = self.db.xp_reward or 0
            if xp and hasattr(killer, "adjust_xp"):
                killer.adjust_xp(xp)
            elif xp:
                killer.db.xp = (killer.db.xp or 0) + xp
                killer.msg(f"|y+{xp} XP|n")
            # Gold drop
            gold = self.db.gold_drop or 0
            if gold and hasattr(killer, "gain_gold"):
                killer.gain_gold(gold)
            # Faction reputation consequence
            faction = self.db.faction or "neutral"
            if faction != "neutral" and hasattr(killer, "adjust_reputation"):
                killer.adjust_reputation(faction, -5)
                _FACTION_ENEMIES = {
                    "remnants": [], "hollow": ["remnants", "wardens"],
                    "scholars": [], "wardens": ["hollow", "unspoken"],
                    "unspoken": ["wardens"],
                }
                for ally in _FACTION_ENEMIES.get(faction, []):
                    killer.adjust_reputation(ally, 2)
        # Queue respawn
        if self.db.respawn_delay and self.location:
            _queue_respawn(self)
        self.delete()

    def _drop_loot(self):
        from evennia.prototypes import spawner
        for entry in (self.db.loot_table or []):
            key = entry.get("prototype_key")
            chance = entry.get("chance", 1.0)
            if key and random.random() <= chance:
                try:
                    objs = spawner.spawn(key)
                    for obj in objs:
                        obj.location = self.location
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Mob typeclass — hostile NPC
# ---------------------------------------------------------------------------

class Mob(NPC):
    """Hostile NPC. Attacks on sight if aggro=True."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_mob = True
        self.db.aggro = True
        self.db.attack_bonus = 5
        self.db.damage_dice = "1d6"
        self.db.defense = 8
        self.db.hp = 30
        self.db.hp_max = 30
        self.db.xp_reward = 25
        self.db.gold_drop = 0
        self.db.respawn_delay = 300     # seconds; 0 = no respawn
        self.db.wanders = False
        self.db.status_effect = None    # "bleed", "poison", "stun", or None

    def get_display_name(self, looker, **kwargs):
        return f"|r{self.key}|n"

    def at_object_receive(self, obj, source_location, **kwargs):
        pass

    def at_post_move(self, source_location, **kwargs):
        """Check for aggro targets when mob moves."""
        if self.db.aggro and not self.db.combat_target:
            self._check_aggro()

    def at_object_receive(self, obj, source_location, move_type="move", **kwargs):
        if (self.db.aggro and not self.db.combat_target
                and utils.inherits_from(obj, "typeclasses.characters.Character")):
            self._start_combat(obj)

    def _check_aggro(self):
        if not self.location:
            return
        for obj in self.location.contents:
            if utils.inherits_from(obj, "typeclasses.characters.Character"):
                self._start_combat(obj)
                break

    def _start_combat(self, target):
        if self.db.combat_target:
            return
        # Commune: Hollow mobs do not aggro Cultists
        if (self.db.faction == "hollow"
                and utils.inherits_from(target, "typeclasses.characters.Character")
                and (target.db.char_class or "") == "cultist"):
            return
        self.db.combat_target = target
        self.location.msg_contents(
            f"|r{self.key} turns on {target.name} with a terrible intent.|n"
        )
        if not self.scripts.get("combat_script"):
            self.scripts.add(CombatScript)

    def execute_attack(self, target):
        """Resolve one attack round against target."""
        import random as _r
        roll = _r.randint(1, 20) + (self.db.attack_bonus or 0)
        defense = target.db.defense if hasattr(target.db, "defense") else 10
        target_defense = defense or 10
        if roll >= target_defense:
            dmg = _roll_dice(self.db.damage_dice or "1d4")
            target.msg(f"|r{self.key} strikes you for {dmg} damage!|n")
            self.location.msg_contents(
                f"|r{self.key} strikes {target.name} for {dmg} damage!|n",
                exclude=[target]
            )
            if hasattr(target, "adjust_hp"):
                target.adjust_hp(-dmg)
            target.adjust_fear(5)
            # Apply status effect if mob has one
            effect = self.db.status_effect
            if effect and hasattr(target, "apply_status_effect") and _r.random() < 0.35:
                target.apply_status_effect(effect)
        else:
            target.msg(f"|y{self.key} swings at you and misses.|n")


class Boss(Mob):
    """Named boss mob with combat phases and unique display."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_boss = True
        self.db.phases = []          # [{hp_threshold (0-1), message, damage_bonus}]
        self.db.phase_triggered = [] # list of triggered phase indices

    def get_display_name(self, looker, **kwargs):
        return f"|R|u{self.key}|n"

    def take_damage(self, amount, attacker=None):
        hp = super().take_damage(amount, attacker)
        if hp > 0:
            self._check_phases(hp)
        return hp

    def _check_phases(self, current_hp):
        phases = self.db.phases or []
        hp_pct = current_hp / (self.db.hp_max or 1)
        triggered = list(self.db.phase_triggered or [])
        for i, phase in enumerate(phases):
            if i in triggered:
                continue
            if hp_pct <= phase.get("hp_threshold", 0):
                triggered.append(i)
                self.db.phase_triggered = triggered
                msg = phase.get("message", "")
                if msg and self.location:
                    self.location.msg_contents(f"|R{self.key}: {msg}|n")
                bonus = phase.get("damage_bonus", 0)
                if bonus:
                    try:
                        count, sides = (self.db.damage_dice or "1d6").lower().split("d")
                        self.db.damage_dice = f"{count}d{int(sides) + bonus}"
                    except Exception:
                        pass


def _roll_dice(dice_str):
    """Roll XdY and return total. Accepts '2d6', '1d4', etc."""
    import random as _r
    try:
        count, sides = dice_str.lower().split("d")
        return sum(_r.randint(1, int(sides)) for _ in range(int(count)))
    except Exception:
        return 1


def _queue_respawn(mob):
    """Add a dead mob to the global RespawnScript queue."""
    import evennia
    try:
        scripts = evennia.search_script("respawn_manager")
        if not scripts:
            return
        scripts[0].enqueue(mob)
    except Exception:
        pass
