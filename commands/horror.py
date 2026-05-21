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
