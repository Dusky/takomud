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
