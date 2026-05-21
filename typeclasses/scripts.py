"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

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
        # Populated after creation:
        # self.db.message       — string sent to players in target rooms
        # self.db.room_dbrefs   — list of dbref strings
        # self.db.sanity_cost   — int, sanity drained each fire
        # self.db.fear_cost     — int, fear added each fire

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
