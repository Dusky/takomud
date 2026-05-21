"""
Characters for Takomud.

Core stats:
  hp / hp_max       — physical survival
  sanity / san_max  — mental stability; 0 = psychotic break
  fear              — 0–100 tension meter
  xp                — experience points
  attack_bonus      — flat combat modifier
  defense           — difficulty to hit (d20 roll must meet or beat this)

Character classes (set at creation via char_class):
  survivor, scholar, cultist, hunter, vagrant
"""

from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):

    def at_object_creation(self):
        super().at_object_creation()
        self.db.hp = 100
        self.db.hp_max = 100
        self.db.sanity = 100
        self.db.sanity_max = 100
        self.db.fear = 0
        self.db.xp = 0
        self.db.attack_bonus = 1
        self.db.defense = 10
        self.db.char_class = None       # set during character creation
        self.db.equipped = {}           # slot -> dbref string
        self.db.quests = {}             # quest_key -> quest dict
        self.db.discovered_rooms = []   # list of room dbrefs seen

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
    # Stat helpers
    # ------------------------------------------------------------------

    def adjust_hp(self, amount):
        self.db.hp = max(0, min(self.db.hp_max, (self.db.hp or 0) + amount))
        if self.db.hp == 0:
            self.at_death()

    def adjust_sanity(self, amount):
        # Scholar pays no sanity for lore (handled at command level)
        self.db.sanity = max(0, min(self.db.sanity_max, (self.db.sanity or 0) + amount))
        if self.db.sanity == 0:
            self.at_sanity_break()

    def adjust_fear(self, amount):
        self.db.fear = max(0, min(100, (self.db.fear or 0) + amount))

    def effective_defense(self):
        base = self.db.defense or 10
        equipped = self.db.equipped or {}
        bonus = 0
        for slot, dbref in equipped.items():
            if dbref:
                from evennia import search_object
                results = search_object(dbref, use_dbref=True)
                if results and hasattr(results[0].db, "defense_bonus"):
                    bonus += results[0].db.defense_bonus or 0
        return base + bonus

    def at_death(self):
        self.msg("|rYour vision goes dark. The cold takes you.\n"
                 "You will wake — changed — at the beginning.|n")
        # Respawn at start location with penalty
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

    def at_sanity_break(self):
        self.msg(
            "|mThe last thread snaps. Reality folds inward. "
            "You are not there to witness it — and then, horribly, you are again.|n"
        )
        self.db.sanity = 10
        self.adjust_fear(30)

    # ------------------------------------------------------------------
    # Exploration tracking
    # ------------------------------------------------------------------

    def at_post_move(self, source_location, **kwargs):
        room = self.location
        if room and room.dbref not in (self.db.discovered_rooms or []):
            discovered = self.db.discovered_rooms or []
            discovered.append(room.dbref)
            self.db.discovered_rooms = discovered
            # Vagrant bonus
            if self.db.char_class == "vagrant":
                self.db.xp = (self.db.xp or 0) + 2
            from world.quest_system import check_objective
            check_objective(self, "visit", room.key)

    # ------------------------------------------------------------------
    # Display
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

    def get_display_name(self, looker, **kwargs):
        name = super().get_display_name(looker, **kwargs)
        fear = self.db.fear or 0
        if fear >= 75:
            name = f"|r{name}|n"
        elif fear >= 40:
            name = f"|y{name}|n"
        return name
