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
