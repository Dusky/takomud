"""
Characters for Takomud.

Core stats:
  hp / hp_max       — physical survival
  sanity / san_max  — mental stability; 0 = psychotic break
  fear              — 0–100 tension meter; mechanical effects at 40 and 75
  xp / level        — experience and progression
  gold              — currency
  attack_bonus      — flat combat modifier
  defense           — difficulty to hit (d20 roll must meet or beat this)
  reputation        — per-faction standing, -100 to +100

Character classes (set at creation via char_class):
  survivor  — Grit: survive one killing blow per hour at 1 HP
  scholar   — Veil-sight: lore/reading costs no sanity
  cultist   — Commune: Hollow mobs do not aggro you
  hunter    — Track: sense hostile mobs in adjacent rooms
  vagrant   — Wanderer: +2 XP per new room discovered
"""

import time
from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent

XP_TABLE = [100, 250, 500, 900, 1400, 2000, 3000, 4500, 6500, 9000]


class Character(ObjectParent, DefaultCharacter):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.hp = 100
        self.db.hp_max = 100
        self.db.sanity = 100
        self.db.sanity_max = 100
        self.db.fear = 0
        self.db.xp = 0
        self.db.level = 1
        self.db.xp_to_next = XP_TABLE[0]
        self.db.gold = 0
        self.db.attack_bonus = 1
        self.db.defense = 10
        self.db.char_class = None
        self.db.equipped = {}
        self.db.quests = {}
        self.db.discovered_rooms = []
        self.db.combat_target = None
        self.db.grit_last_used = 0
        self.db.reputation = {
            "remnants": 0, "hollow": 0, "scholars": 0,
            "wardens": 0, "unspoken": 0,
        }
        from typeclasses.scripts import FuelDrainScript
        self.scripts.add(FuelDrainScript)

    # ------------------------------------------------------------------
    # Class application
    # ------------------------------------------------------------------

    def apply_class(self, class_key):
        from world.world_bible import CHARACTER_CLASSES
        cls = CHARACTER_CLASSES.get(class_key)
        if not cls:
            return False
        self.db.char_class = class_key
        self.db.hp_max = 100 + cls["hp_bonus"]
        self.db.hp = self.db.hp_max
        self.db.sanity_max = 100 + cls["sanity_bonus"]
        self.db.sanity = self.db.sanity_max
        self.db.fear = cls["fear_start"]
        self.db.attack_bonus = cls["attack_bonus"]
        self.db.defense = cls["defense"]
        return True

    # ------------------------------------------------------------------
    # HP
    # ------------------------------------------------------------------

    def adjust_hp(self, amount):
        current = self.db.hp or 0
        new_hp = max(0, min(self.db.hp_max or 100, current + amount))

        # Grit: Survivor survives one killing blow per hour
        if new_hp == 0 and amount < 0 and self.db.char_class == "survivor":
            last = self.db.grit_last_used or 0
            if time.time() - last >= 3600:
                self.db.grit_last_used = time.time()
                self.db.hp = 1
                self.msg("|YGrit. You're still here — barely.|n")
                return

        self.db.hp = new_hp
        if self.db.hp == 0:
            self.at_death()

    # ------------------------------------------------------------------
    # Sanity
    # ------------------------------------------------------------------

    def adjust_sanity(self, amount):
        old = self.db.sanity or 100
        self.db.sanity = max(0, min(self.db.sanity_max or 100, old + amount))
        new = self.db.sanity

        if amount < 0:
            if new <= 25 and old > 25:
                self._start_sanity_effects()
            elif new <= 50 and old > 50:
                self.msg("|xSomething at the edge of your vision moves when you look away.|n")

        if new == 0:
            self.at_sanity_break()

    def _start_sanity_effects(self):
        from typeclasses.scripts import SanityHallucinationScript
        if not self.scripts.get("sanity_hallucination"):
            self.scripts.add(SanityHallucinationScript)
        self.msg("|mYour thoughts are no longer entirely your own.|n")

    def at_sanity_break(self):
        self.msg(
            "|mThe last thread snaps. Reality folds inward. "
            "You are not there to witness it — and then, horribly, you are again.|n"
        )
        self.db.sanity = 10
        self.adjust_fear(30)
        # Stop hallucination script if running — reset state
        for s in self.scripts.all():
            if s.key == "sanity_hallucination":
                s.stop()

    # ------------------------------------------------------------------
    # Fear
    # ------------------------------------------------------------------

    def adjust_fear(self, amount):
        old = self.db.fear or 0
        self.db.fear = max(0, min(100, old + amount))
        new = self.db.fear

        if amount > 0:
            if new >= 75 and old < 75:
                self.msg("|rPanic takes hold. Your hands will not stop shaking.|n")
            elif new >= 40 and old < 40:
                self.msg("|yDread settles in your chest. Everything feels dangerous.|n")

        if new >= 100:
            self._fear_panic()

    def _fear_panic(self):
        import random
        self.db.fear = 80
        self.db.combat_target = None
        exits = self.location.exits if self.location else []
        if exits and random.random() < 0.6:
            exit_obj = random.choice(exits)
            self.msg("|rPanic overwhelms you. You run.|n")
            self.move_to(exit_obj.destination, quiet=False)
        else:
            self.msg("|rYou are frozen. Your body refuses to obey.|n")

    # ------------------------------------------------------------------
    # XP and leveling
    # ------------------------------------------------------------------

    def adjust_xp(self, amount):
        self.db.xp = (self.db.xp or 0) + amount
        while self.db.xp >= (self.db.xp_to_next or XP_TABLE[0]):
            self._level_up()

    def _level_up(self):
        level = (self.db.level or 1) + 1
        self.db.level = level
        self.db.xp_to_next = XP_TABLE[min(level - 1, len(XP_TABLE) - 1)]
        self.db.hp_max = (self.db.hp_max or 100) + 10
        self.db.hp = self.db.hp_max
        self.db.sanity_max = (self.db.sanity_max or 100) + 5
        self.db.sanity = min(self.db.sanity or 100, self.db.sanity_max)
        self.db.attack_bonus = (self.db.attack_bonus or 1) + 1
        self.msg(
            f"\n|Y=== LEVEL {level} ===|n\n"
            f"|g+10 HP max  +5 Sanity max  +1 Attack bonus|n\n"
        )

    # ------------------------------------------------------------------
    # Gold
    # ------------------------------------------------------------------

    def gain_gold(self, amount):
        self.db.gold = (self.db.gold or 0) + amount
        if amount > 0:
            self.msg(f"|y+{amount} gold|n")

    def spend_gold(self, amount):
        current = self.db.gold or 0
        if current < amount:
            self.msg(f"|rNot enough gold. You have {current}, need {amount}.|n")
            return False
        self.db.gold = current - amount
        return True

    # ------------------------------------------------------------------
    # Reputation
    # ------------------------------------------------------------------

    def adjust_reputation(self, faction, amount):
        rep = dict(self.db.reputation or {})
        old = rep.get(faction, 0)
        rep[faction] = max(-100, min(100, old + amount))
        self.db.reputation = rep
        if amount > 0:
            self.msg(f"|g+{amount} reputation with {faction.title()}|n")
        elif amount < 0:
            self.msg(f"|r{amount} reputation with {faction.title()}|n")

    # ------------------------------------------------------------------
    # Defense
    # ------------------------------------------------------------------

    def effective_defense(self):
        base = self.db.defense or 10
        bonus = 0
        for slot, dbref in (self.db.equipped or {}).items():
            if dbref:
                from evennia import search_object
                results = search_object(dbref, use_dbref=True)
                if results:
                    bonus += results[0].db.defense_bonus or 0
        return base + bonus

    # ------------------------------------------------------------------
    # Death
    # ------------------------------------------------------------------

    def at_death(self):
        self.msg("|rYour vision goes dark. The cold takes you.\n"
                 "You will wake — changed — at the beginning.|n")
        self.db.combat_target = None
        for s in self.scripts.all():
            if s.key == "player_combat":
                s.stop()
        from evennia.utils import search
        from django.conf import settings
        start = None
        if hasattr(settings, "START_LOCATION"):
            results = search.search_object(settings.START_LOCATION, use_dbref=True)
            start = results[0] if results else None
        if start:
            self.location = start
        self.db.hp = max(1, (self.db.hp_max or 100) // 2)
        self.db.sanity = max(1, (self.db.sanity or 100) - 10)
        self.adjust_fear(20)

    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------

    def at_post_move(self, source_location, **kwargs):
        room = self.location
        if room and room.dbref not in (self.db.discovered_rooms or []):
            discovered = self.db.discovered_rooms or []
            discovered.append(room.dbref)
            self.db.discovered_rooms = discovered
            if self.db.char_class == "vagrant":
                self.adjust_xp(2)
            from world.quest_system import check_objective
            check_objective(self, "visit", room.key)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def at_post_login(self, account=None, session=None, **kwargs):
        super().at_post_login(account=account, session=session, **kwargs)
        if not self.db.char_class:
            self._prompt_class_selection()

    def _prompt_class_selection(self):
        from world.world_bible import CHARACTER_CLASSES
        lines = [
            "",
            "|wYou are no one yet. Choose what you are — you cannot change it later.|n",
            "",
        ]
        for key, cls in CHARACTER_CLASSES.items():
            lines.append(f"  |w{key:<10}|n {cls['desc']}")
            lines.append(f"             |xSpecial: {cls['special']}|n")
            lines.append("")
        lines.append("|yType |wclass <name>|y to begin.|n")
        self.msg("\n".join(lines))

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def get_display_name(self, looker, **kwargs):
        name = super().get_display_name(looker, **kwargs)
        fear = self.db.fear or 0
        if fear >= 75:
            name = f"|r{name}|n"
        elif fear >= 40:
            name = f"|y{name}|n"
        return name
