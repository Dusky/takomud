"""
Takomud horror-specific in-game commands.
"""

from evennia.commands.command import Command as BaseCommand


class CmdStat(BaseCommand):
    """
    Display your current vital statistics.

    Usage:
      stat

    Shows HP, Sanity, and Fear level with a simple visual bar.
    """

    key = "stat"
    aliases = ["stats", "status"]
    help_category = "General"

    def func(self):
        char = self.caller
        hp = char.db.hp or 0
        hp_max = char.db.hp_max or 100
        san = char.db.sanity or 0
        san_max = char.db.sanity_max or 100
        fear = char.db.fear or 0

        def bar(val, max_val, width=20):
            filled = int((val / max_val) * width) if max_val else 0
            empty = width - filled
            return f"|[022|w{'|' * filled}|n|[000|x{'.' * empty}|n"

        hp_color = "|r" if hp < hp_max * 0.25 else "|y" if hp < hp_max * 0.5 else "|g"
        san_color = "|r" if san < san_max * 0.25 else "|m" if san < san_max * 0.5 else "|c"
        fear_color = "|r" if fear >= 75 else "|y" if fear >= 40 else "|g"

        self.caller.msg(
            f"\n|w--- {char.name} ------|n\n"
            f" HP      {bar(hp, hp_max)} {hp_color}{hp}/{hp_max}|n\n"
            f" Sanity  {bar(san, san_max)} {san_color}{san}/{san_max}|n\n"
            f" Fear    {bar(fear, 100)} {fear_color}{fear}/100|n\n"
        )


class CmdLore(BaseCommand):
    """
    Read the hidden lore of your current location.

    Usage:
      lore

    Some places hold secrets not visible to ordinary senses. This command
    reveals them — if there is anything to reveal.
    """

    key = "lore"
    help_category = "General"

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("You are nowhere. That is concerning.")
            return
        text = room.db.lore
        if not text:
            self.caller.msg("|xSilence. Whatever history lived here has been consumed.|n")
            return
        self.caller.msg(f"|m--- Lore: {room.name} ---|n\n{text}")
        # Scholar Veil-sight: no sanity cost
        if (self.caller.db.char_class or "") != "scholar":
            self.caller.adjust_sanity(-3)


class CmdAtmosphere(BaseCommand):
    """
    Staff command: manage the atmosphere list of the current room.

    Usage:
      atmosphere              - list current atmosphere strings
      atmosphere/add <text>   - add an atmosphere message
      atmosphere/remove <#>   - remove by index (1-based)
      atmosphere/clear        - remove all atmosphere messages
      atmosphere/test         - emit one atmosphere message now
    """

    key = "atmosphere"
    aliases = ["atmo"]
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("No location.")
            return

        switch = self.switches[0] if self.switches else ""
        msgs = room.db.atmosphere or []

        if switch == "add":
            text = self.args.strip()
            if not text:
                self.caller.msg("Add what?")
                return
            msgs.append(text)
            room.db.atmosphere = msgs
            self.caller.msg(f"Added atmosphere message #{len(msgs)}.")

        elif switch == "remove":
            try:
                idx = int(self.args.strip()) - 1
                removed = msgs.pop(idx)
                room.db.atmosphere = msgs
                self.caller.msg(f"Removed: {removed}")
            except (ValueError, IndexError):
                self.caller.msg("Invalid index.")

        elif switch == "clear":
            room.db.atmosphere = []
            self.caller.msg("All atmosphere messages cleared.")

        elif switch == "test":
            room.emit_atmosphere()
            if not msgs:
                self.caller.msg("(room has no atmosphere messages)")

        else:
            if not msgs:
                self.caller.msg("This room has no atmosphere messages.")
                return
            lines = "\n".join(f" {i+1}. {m}" for i, m in enumerate(msgs))
            self.caller.msg(f"|mAtmosphere for {room.name}:|n\n{lines}")


class CmdSetLore(BaseCommand):
    """
    Staff command: set the lore text for the current room.

    Usage:
      setlore <text>    - set lore
      setlore/clear     - remove lore
    """

    key = "setlore"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("No location.")
            return

        if "clear" in self.switches:
            room.db.lore = ""
            self.caller.msg("Lore cleared.")
            return

        text = self.args.strip()
        if not text:
            self.caller.msg("Usage: setlore <text>")
            return
        room.db.lore = text
        self.caller.msg("Lore set.")


class CmdSetDark(BaseCommand):
    """
    Staff command: toggle darkness on the current room.

    Usage:
      setdark        - toggle dark on/off
      setdark on
      setdark off
    """

    key = "setdark"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("No location.")
            return

        arg = self.args.strip().lower()
        current = bool(room.db.dark)

        if arg == "on":
            room.db.dark = True
        elif arg == "off":
            room.db.dark = False
        else:
            room.db.dark = not current

        state = "dark" if room.db.dark else "lit"
        self.caller.msg(f"Room is now |w{state}|n.")


class CmdRead(BaseCommand):
    """
    Read a document, book, inscription, or letter.

    Usage:
      read <object>

    Some written things cost sanity to read.
    """

    key = "read"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Read what?")
            return
        obj = self.caller.search(self.args.strip())
        if not obj:
            return
        if not getattr(obj.db, "readable", False):
            self.caller.msg("You cannot read that.")
            return
        obj.at_read(self.caller)


class CmdCharClass(BaseCommand):
    """
    Choose your character class at the start of your descent.

    Usage:
      class              — show available classes
      class <name>       — select a class (one time only)

    Once chosen, your class cannot be changed.
    """

    key = "class"
    aliases = ["charclass"]
    help_category = "General"

    def func(self):
        from world.world_bible import CHARACTER_CLASSES
        if not self.args:
            self.caller._prompt_class_selection()
            return
        class_key = self.args.strip().lower()
        if self.caller.db.char_class:
            self.caller.msg(
                f"|yYou are already {self.caller.db.char_class}. "
                f"You cannot change what you already are.|n"
            )
            return
        if class_key not in CHARACTER_CLASSES:
            valid = ", ".join(CHARACTER_CLASSES.keys())
            self.caller.msg(f"|rUnknown class.|n Choose from: {valid}")
            return
        self.caller.apply_class(class_key)
        cls = CHARACTER_CLASSES[class_key]
        self.caller.msg(
            f"\n|wYou are {cls['name']}.|n\n"
            f"{cls['desc']}\n\n"
            f"|xSpecial: {cls['special']}|n\n"
        )


class CmdScore(BaseCommand):
    """
    Display your full character sheet.

    Usage:
      score
      sheet
    """

    key = "score"
    aliases = ["sheet", "sc"]
    help_category = "General"

    def func(self):
        char = self.caller
        from world.world_bible import CHARACTER_CLASSES

        hp = char.db.hp or 0
        hp_max = char.db.hp_max or 100
        san = char.db.sanity or 0
        san_max = char.db.sanity_max or 100
        fear = char.db.fear or 0
        xp = char.db.xp or 0
        xp_next = char.db.xp_to_next or 100
        level = char.db.level or 1
        gold = char.db.gold or 0
        cls_key = char.db.char_class or "none"
        atk = char.db.attack_bonus or 0
        defense = char.db.defense or 10

        cls_data = CHARACTER_CLASSES.get(cls_key, {})
        special = cls_data.get("special", "—")

        rep = char.db.reputation or {}
        rep_lines = "  ".join(
            f"{f.title()}: {v:+d}" for f, v in rep.items() if v != 0
        ) or "None"

        quests_active = sum(1 for q in (char.db.quests or {}).values() if not q.get("completed"))

        self.caller.msg(
            f"\n|w=== {char.name} — Level {level} {cls_key.title()} ===|n\n"
            f" HP      |g{hp}/{hp_max}|n\n"
            f" Sanity  |c{san}/{san_max}|n\n"
            f" Fear    |y{fear}/100|n\n"
            f" XP      {xp}/{xp_next}\n"
            f" Gold    |Y{gold}|n\n"
            f" Attack  +{atk}   Defense {defense}\n"
            f" Special |x{special}|n\n"
            f" Rep     {rep_lines}\n"
            f" Quests  {quests_active} active\n"
        )


class CmdTrack(BaseCommand):
    """
    Sense hostile creatures in adjacent rooms. Hunter special.

    Usage:
      track

    Requires the Hunter class. Costs 5 fear to use.
    """

    key = "track"
    help_category = "General"

    def func(self):
        if (self.caller.db.char_class or "") != "hunter":
            self.caller.msg("|xYou have no instinct for tracking.|n")
            return

        self.caller.adjust_fear(5)
        from evennia.utils import utils as ev_utils

        found = []
        for exit_obj in (self.caller.location.exits or []):
            dest = exit_obj.destination
            if not dest:
                continue
            for obj in dest.contents:
                if (ev_utils.inherits_from(obj, "typeclasses.npcs.Mob")
                        and obj.db.aggro):
                    found.append(f"  |r{obj.key}|n — to the {exit_obj.key}")

        if found:
            self.caller.msg("|xYou sense:|n\n" + "\n".join(found))
        else:
            self.caller.msg("|xYou sense nothing immediately hostile nearby.|n")


class CmdWho(BaseCommand):
    """
    List currently connected players.

    Usage:
      who
    """

    key = "who"
    help_category = "General"

    def func(self):
        import evennia
        from evennia.utils import utils as ev_utils
        lines = ["\n|w=== Who is Here ===|n"]
        count = 0
        for session in evennia.SESSION_HANDLER.values():
            puppet = session.get_puppet()
            if not puppet:
                continue
            if not ev_utils.inherits_from(puppet, "typeclasses.characters.Character"):
                continue
            level = puppet.db.level or 1
            cls = (puppet.db.char_class or "none").title()
            loc = puppet.location.key if puppet.location else "Unknown"
            lines.append(f"  |w{puppet.name:<20}|n Lv{level} {cls:<10} — {loc}")
            count += 1
        if count == 0:
            lines.append("  |xNo one but the darkness.|n")
        else:
            lines.append(f"\n|x{count} soul{'s' if count != 1 else ''} present.|n")
        self.caller.msg("\n".join(lines))


class CmdWhere(BaseCommand):
    """
    Admin: show location of all connected players.

    Usage:
      where
    """

    key = "where"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        import evennia
        from evennia.utils import utils as ev_utils
        lines = ["\n|w=== Player Locations ===|n"]
        for session in evennia.SESSION_HANDLER.values():
            puppet = session.get_puppet()
            if not puppet or not ev_utils.inherits_from(puppet, "typeclasses.characters.Character"):
                continue
            loc = puppet.location
            loc_str = f"{loc.key} ({loc.dbref})" if loc else "None"
            lines.append(f"  {puppet.name} — {loc_str}")
        self.caller.msg("\n".join(lines))


class CmdShout(BaseCommand):
    """
    Shout a message that echoes into adjacent rooms.

    Usage:
      shout <message>

    Costs 5 Fear. Everyone in your room and all adjacent rooms hears it.
    """

    key = "shout"
    aliases = ["yell"]
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Shout what?")
            return
        msg = self.args.strip()
        self.caller.adjust_fear(5)
        self.caller.location.msg_contents(
            f"|y{self.caller.name} shouts: \"{msg}\"|n"
        )
        for exit_obj in (self.caller.location.exits or []):
            dest = exit_obj.destination
            if dest:
                dest.msg_contents(
                    f"|xA voice from nearby shouts: \"{msg}\"|n"
                )


class CmdUnlock(BaseCommand):
    """
    Unlock a locked exit using a key item.

    Usage:
      unlock <direction>
      unlock <direction> with <item>

    If the exit requires a key item, you must be carrying it.
    Some exits can be unlocked without a key.
    """

    key = "unlock"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Unlock which exit?")
            return

        args = self.args.strip()
        key_name = None
        if " with " in args:
            dir_name, key_name = args.split(" with ", 1)
            dir_name = dir_name.strip()
            key_name = key_name.strip()
        else:
            dir_name = args

        exit_obj = None
        for ex in self.caller.location.exits:
            if ex.key.lower() == dir_name.lower() or dir_name.lower() in [a.lower() for a in ex.aliases.all()]:
                exit_obj = ex
                break

        if not exit_obj:
            self.caller.msg(f"No exit '{dir_name}' here.")
            return

        if not exit_obj.db.locked:
            self.caller.msg(f"The {exit_obj.key} exit is not locked.")
            return

        required_key = exit_obj.db.key_item
        if required_key:
            from evennia.utils import utils as ev_utils
            key_item = None
            for item in self.caller.contents:
                if item.key.lower() == required_key.lower():
                    key_item = item
                    break
            if not key_item:
                self.caller.msg(
                    f"|rYou need {required_key} to unlock this.|n"
                )
                return

        exit_obj.db.locked = False
        self.caller.msg(f"|gYou unlock the {exit_obj.key} exit.|n")
        self.caller.location.msg_contents(
            f"|x{self.caller.name} unlocks the {exit_obj.key} exit.|n",
            exclude=[self.caller],
        )


class CmdLock(BaseCommand):
    """
    Lock an unlocked exit (must have the required key item).

    Usage:
      lock <direction>
    """

    key = "lock"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Lock which exit?")
            return
        dir_name = self.args.strip()
        exit_obj = None
        for ex in self.caller.location.exits:
            if ex.key.lower() == dir_name.lower():
                exit_obj = ex
                break
        if not exit_obj:
            self.caller.msg(f"No exit '{dir_name}' here.")
            return
        if exit_obj.db.locked:
            self.caller.msg(f"The {exit_obj.key} exit is already locked.")
            return
        required_key = exit_obj.db.key_item
        if required_key:
            has_key = any(item.key.lower() == required_key.lower() for item in self.caller.contents)
            if not has_key:
                self.caller.msg(f"|rYou need {required_key} to lock this.|n")
                return
        exit_obj.db.locked = True
        self.caller.msg(f"|xYou lock the {exit_obj.key} exit.|n")
        self.caller.location.msg_contents(
            f"|x{self.caller.name} locks the {exit_obj.key} exit.|n",
            exclude=[self.caller],
        )


class CmdAbility(BaseCommand):
    """
    Use your character class's active ability.

    Usage:
      ability
      ability <target>     (for Analyze, Commune, Trap)

    Abilities:
      survivor  — Surge: spend 20 HP, gain +5 attack for 30 seconds
      scholar   — Analyze: reveal a target's HP, defense, and attack
      cultist   — Commune: ask a nearby Hollow mob for hidden lore
      hunter    — Trap: set a snare; next mob entering takes damage and is stunned
      vagrant   — Blink: teleport to any previously discovered room (costs 20 Sanity)
    """

    key = "ability"
    aliases = ["ab", "special"]
    help_category = "General"

    def func(self):
        cls = self.caller.db.char_class
        if not cls:
            self.caller.msg("|xYou have no class, and therefore no special ability.|n")
            return
        getattr(self, f"_do_{cls}", self._do_unknown)()

    def _do_survivor(self):
        char = self.caller
        hp = char.db.hp or 0
        if hp <= 20:
            char.msg("|rYou are too wounded to surge.|n")
            return
        if char.scripts.get("surge_script"):
            char.msg("|yYou are already surging.|n")
            return
        from typeclasses.scripts import SurgeScript
        char.adjust_hp(-20)
        char.db.attack_bonus = (char.db.attack_bonus or 1) + 5
        char.scripts.add(SurgeScript)
        char.msg("|YSurge. Pain sharpens into focus. +5 attack for 30 seconds.|n")
        char.location.msg_contents(
            f"|y{char.name} surges with desperate energy.|n", exclude=[char]
        )

    def _do_scholar(self):
        if not self.args:
            self.caller.msg("Analyze what? Usage: ability <target>")
            return
        target = self.caller.search(self.args.strip())
        if not target:
            return
        hp = target.db.hp or "?"
        hp_max = target.db.hp_max or "?"
        atk = target.db.attack_bonus or 0
        defense = target.db.defense or 10
        effect = target.db.status_effect or "none"
        self.caller.msg(
            f"\n|wAnalysis — {target.key}:|n\n"
            f"  HP      {hp}/{hp_max}\n"
            f"  Attack  +{atk}\n"
            f"  Defense {defense}\n"
            f"  Status  {effect}\n"
        )

    def _do_cultist(self):
        from evennia.utils import utils as ev_utils
        hollow_mobs = [
            obj for obj in self.caller.location.contents
            if ev_utils.inherits_from(obj, "typeclasses.npcs.Mob")
            and (obj.db.faction or "") == "hollow"
        ]
        if not hollow_mobs:
            self.caller.msg("|xThere are no Hollow here to commune with.|n")
            return
        mob = hollow_mobs[0]
        lore = mob.db.dialogue or {}
        response = (
            lore.get("commune")
            or lore.get("greeting")
            or "|xThe Hollow regards you. Something passes between you that has no words.|n"
        )
        self.caller.msg(f"|m{mob.key}: {response}|n")
        mob.db.combat_target = None
        for s in mob.scripts.all():
            if s.key == "combat_script":
                s.stop()

    def _do_hunter(self):
        room = self.caller.location
        if room.scripts.get("hunter_trap"):
            self.caller.msg("|xA trap is already set here.|n")
            return
        from typeclasses.scripts import HunterTrapScript
        room.scripts.add(HunterTrapScript)
        room.db._trap_setter = self.caller.dbref
        self.caller.msg("|xYou set a hidden snare. The next creature to enter will trigger it.|n")
        room.msg_contents(
            f"|x{self.caller.name} moves carefully near the floor.|n",
            exclude=[self.caller],
        )

    def _do_vagrant(self):
        if not self.args:
            discovered = self.caller.db.discovered_rooms or []
            count = len(discovered)
            self.caller.msg(
                f"|xYou have mapped {count} room{'s' if count != 1 else ''}.\n"
                f"Usage: ability <room name or partial name>|n"
            )
            return
        san = self.caller.db.sanity or 0
        if san < 20:
            self.caller.msg("|rYour mind is too fractured to find the path.|n")
            return
        target_name = self.args.strip().lower()
        import evennia
        from typeclasses.rooms import Room
        discovered = self.caller.db.discovered_rooms or []
        for dbref in discovered:
            results = evennia.search_object(dbref, use_dbref=True, typeclass=Room)
            if results and target_name in results[0].key.lower():
                dest = results[0]
                self.caller.adjust_sanity(-20)
                self.caller.msg(f"|mThe space between folds. You are elsewhere.|n")
                self.caller.move_to(dest, quiet=True)
                self.caller.msg(self.caller.location.return_appearance(self.caller))
                return
        self.caller.msg(f"|xYou haven't been anywhere matching '{self.args.strip()}'.|n")

    def _do_unknown(self):
        self.caller.msg("|xYour class has no registered active ability.|n")


class CmdSetHazard(BaseCommand):
    """
    Staff command: configure an environmental hazard for the current room.

    Usage:
      sethazard                    — show current hazard settings
      sethazard/hp <N>             — deal N HP damage per tick (default tick: 15s)
      sethazard/sanity <N>         — deal N Sanity damage per tick
      sethazard/fear <N>           — deal N Fear per tick
      sethazard/msg <text>         — set the message shown each tick
      sethazard/interval <seconds> — change tick interval
      sethazard/start              — attach HazardScript to this room
      sethazard/stop               — remove HazardScript from this room
      sethazard/clear              — zero all damage values and stop
    """

    key = "sethazard"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("No location.")
            return
        switch = self.switches[0] if self.switches else ""

        if switch == "hp":
            try:
                room.db.hazard_hp = int(self.args.strip())
                self.caller.msg(f"Hazard HP damage set to {room.db.hazard_hp} per tick.")
            except ValueError:
                self.caller.msg("Provide an integer.")
        elif switch == "sanity":
            try:
                room.db.hazard_sanity = int(self.args.strip())
                self.caller.msg(f"Hazard Sanity damage set to {room.db.hazard_sanity} per tick.")
            except ValueError:
                self.caller.msg("Provide an integer.")
        elif switch == "fear":
            try:
                room.db.hazard_fear = int(self.args.strip())
                self.caller.msg(f"Hazard Fear set to {room.db.hazard_fear} per tick.")
            except ValueError:
                self.caller.msg("Provide an integer.")
        elif switch == "msg":
            room.db.hazard_message = self.args.strip()
            self.caller.msg("Hazard message set.")
        elif switch == "interval":
            try:
                interval = max(5, int(self.args.strip()))
                for s in room.scripts.all():
                    if s.key == "hazard_script":
                        s.interval = interval
                self.caller.msg(f"Hazard interval set to {interval}s.")
            except ValueError:
                self.caller.msg("Provide an integer (seconds).")
        elif switch == "start":
            from typeclasses.scripts import HazardScript
            if room.scripts.get("hazard_script"):
                self.caller.msg("HazardScript already running.")
            else:
                room.scripts.add(HazardScript)
                self.caller.msg("HazardScript started.")
        elif switch == "stop":
            for s in room.scripts.all():
                if s.key == "hazard_script":
                    s.stop()
            self.caller.msg("HazardScript stopped.")
        elif switch == "clear":
            room.db.hazard_hp = 0
            room.db.hazard_sanity = 0
            room.db.hazard_fear = 0
            room.db.hazard_message = ""
            for s in room.scripts.all():
                if s.key == "hazard_script":
                    s.stop()
            self.caller.msg("Hazard cleared.")
        else:
            running = bool(room.scripts.get("hazard_script"))
            self.caller.msg(
                f"Hazard — HP:{room.db.hazard_hp or 0} "
                f"San:{room.db.hazard_sanity or 0} "
                f"Fear:{room.db.hazard_fear or 0} "
                f"Script:{'on' if running else 'off'}\n"
                f"Message: {room.db.hazard_message or '(none)'}"
            )


class CmdSetEncounter(BaseCommand):
    """
    Staff command: configure random encounters for the current room.

    Usage:
      setencounter                              — list current encounter table
      setencounter/add <key> <hp> <dice>        — add a mob template (e.g. add "Pale Shade" 20 1d4)
      setencounter/chance <0.0-1.0>             — set spawn probability per tick
      setencounter/clear                        — remove all encounter entries
      setencounter/start                        — attach RandomEncounterScript to this room
      setencounter/stop                         — remove RandomEncounterScript from this room
    """

    key = "setencounter"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("No location.")
            return

        switch = self.switches[0] if self.switches else ""

        if switch == "add":
            parts = self.args.strip().split(None, 2)
            if len(parts) < 3:
                self.caller.msg("Usage: setencounter/add <key> <hp> <damage_dice>")
                return
            mob_key, hp_str, dice = parts[0], parts[1], parts[2]
            try:
                hp = int(hp_str)
            except ValueError:
                self.caller.msg("HP must be an integer.")
                return
            table = list(room.db.encounter_table or [])
            table.append({"key": mob_key, "hp": hp, "damage_dice": dice, "xp_reward": hp})
            room.db.encounter_table = table
            self.caller.msg(f"Added: {mob_key} (HP {hp}, {dice}) to encounter table.")

        elif switch == "chance":
            try:
                val = float(self.args.strip())
                val = max(0.0, min(1.0, val))
            except ValueError:
                self.caller.msg("Provide a float between 0.0 and 1.0.")
                return
            room.db.encounter_chance = val
            self.caller.msg(f"Encounter chance set to {val:.0%}.")

        elif switch == "clear":
            room.db.encounter_table = []
            self.caller.msg("Encounter table cleared.")

        elif switch == "start":
            from typeclasses.scripts import RandomEncounterScript
            if room.scripts.get("random_encounter"):
                self.caller.msg("RandomEncounterScript already running.")
            else:
                room.scripts.add(RandomEncounterScript)
                self.caller.msg("RandomEncounterScript started.")

        elif switch == "stop":
            for s in room.scripts.all():
                if s.key == "random_encounter":
                    s.stop()
            self.caller.msg("RandomEncounterScript stopped.")

        else:
            table = room.db.encounter_table or []
            chance = room.db.encounter_chance or 0.3
            running = bool(room.scripts.get("random_encounter"))
            if not table:
                self.caller.msg(f"No encounter table set. Chance: {chance:.0%}. Script: {'running' if running else 'off'}.")
                return
            lines = [f"Encounter table ({chance:.0%} chance, script {'on' if running else 'off'}):"]
            for e in table:
                lines.append(f"  {e.get('key')} — HP {e.get('hp')} {e.get('damage_dice')}")
            self.caller.msg("\n".join(lines))


class CmdMap(BaseCommand):
    """
    Display a text map of your location and nearby rooms.

    Usage:
      map
    """

    key = "map"
    aliases = ["m"]
    help_category = "General"

    def func(self):
        from evennia.utils import utils as ev_utils
        char = self.caller
        origin = char.location
        if not origin:
            char.msg("You are nowhere.")
            return

        # Collect rooms up to 2 hops away with their direction paths
        visited = {}   # room -> (hop_distance, direction_label)
        queue = [(origin, 0, "")]
        seen = {origin.id}

        while queue:
            room, depth, label = queue.pop(0)
            visited[room] = (depth, label)
            if depth >= 2:
                continue
            for ex in room.exits:
                dest = ex.destination
                if dest and dest.id not in seen:
                    seen.add(dest.id)
                    child_label = ex.key if depth == 0 else f"{label}>{ex.key}"
                    queue.append((dest, depth + 1, child_label))

        lines = [f"\n|w[Map — {origin.name}]|n"]
        lines.append(f"  |w*|n |Y{origin.name}|n  ← you are here")

        for room, (depth, label) in sorted(visited.items(), key=lambda x: x[1][0]):
            if room is origin:
                continue
            rec_level = room.db.recommended_level or 1
            level_tag = f" |x(rec. lv{rec_level})|n" if rec_level > 1 else ""
            prefix = "  " * depth
            lines.append(f"{prefix}  [{label}] {room.name}{level_tag}")

        char.msg("\n".join(lines) + "\n")
