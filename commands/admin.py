"""
Admin commands for Takomud.
"""

import os
import threading
from evennia.commands.command import Command as BaseCommand


class CmdGenerate(BaseCommand):
    """
    Autonomously generate world content via the Claude API.

    Usage:
      generate [<cycles>]

    Generates <cycles> new areas (default 1). Runs in a background thread
    so the game stays responsive. Requires ANTHROPIC_API_KEY in the environment.

      generate        — generate 1 area
      generate 5      — generate 5 areas back-to-back
      generate 0      — generate indefinitely until server stops

    Watch the server log (logs/server.log) for per-area progress.
    """

    key = "generate"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.caller.msg(
                "|rANTHROPIC_API_KEY is not set in the environment.|n\n"
                "Export it before starting Evennia:\n"
                "  export ANTHROPIC_API_KEY=sk-ant-..."
            )
            return

        args = self.args.strip()
        try:
            cycles = int(args) if args else 1
        except ValueError:
            self.caller.msg("Usage: generate [<number>]")
            return

        caller = self.caller
        label = "∞" if cycles == 0 else str(cycles)
        noun = "area" if cycles == 1 else "areas"

        def _run():
            try:
                from world.generator import generate
                generate(cycles=cycles, delay=5)
                if cycles != 0:
                    caller.msg(f"|g[Generator] Done — {cycles} {noun} added to the world.|n")
            except Exception as exc:
                caller.msg(f"|r[Generator] Failed: {exc}|n")

        thread = threading.Thread(target=_run, daemon=True, name="takomud-generator")
        thread.start()
        caller.msg(
            f"|y[Generator] Running: {label} {noun} generating in background.|n"
            f"|xCheck server logs for room-by-room progress.|n"
        )


class CmdGenerateStart(BaseCommand):
    """
    Regenerate the starting zone via the Claude API.

    Usage:
      genstart

    Calls generate_starting_zone() and writes the resulting spawn room
    to server/conf/secret_settings.py. Takes effect on the next server
    restart. Only needed if the starting zone was never created or was deleted.
    """

    key = "genstart"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.caller.msg("|rANTHROPIC_API_KEY is not set.|n")
            return

        caller = self.caller

        def _run():
            try:
                from world.generator import generate_starting_zone, _apply_area, _load_state, _save_state
                caller.msg("|y[GenStart] Generating starting zone...|n")
                zone_data = generate_starting_zone()
                if not zone_data:
                    caller.msg("|r[GenStart] No data returned.|n")
                    return
                state = _load_state()
                area_data = {
                    "area_name": "The Threshold",
                    "theme": "starting zone",
                    "rooms": zone_data.get("rooms", []),
                    "npcs": zone_data.get("npcs", []),
                    "mobs": [],
                    "items": zone_data.get("items", []),
                    "quests": [],
                    "lore_documents": zone_data.get("lore_documents", []),
                    "boss_encounters": [],
                    "world_events": [],
                }
                _apply_area(area_data, state)
                _save_state(state)

                start_data = next(
                    (r for r in zone_data.get("rooms", []) if r.get("is_start")),
                    (zone_data.get("rooms") or [{}])[0],
                )
                start_key = start_data.get("key", "")
                if start_key:
                    import evennia
                    from typeclasses.rooms import Room
                    results = evennia.search_object(start_key, typeclass=Room)
                    if results:
                        _write_start_location(results[0].dbref)
                        caller.msg(
                            f"|g[GenStart] Done. Start room: {start_key} ({results[0].dbref})\n"
                            f"Restart the server for START_LOCATION to take effect.|n"
                        )
                    else:
                        caller.msg(f"|r[GenStart] Could not find room '{start_key}' after creation.|n")
            except Exception as exc:
                caller.msg(f"|r[GenStart] Error: {exc}|n")

        threading.Thread(target=_run, daemon=True, name="takomud-genstart").start()


class CmdGenerateQuest(BaseCommand):
    """
    Generate a faction-specific questline via the Claude API.

    Usage:
      genquest <faction>

    Faction must be one of: remnants, hollow, scholars, wardens, unspoken

    Places a herald NPC in The Threshold and registers the questline.
    Runs in a background thread. ANTHROPIC_API_KEY must be set.
    """

    key = "genquest"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    FACTIONS = ("remnants", "hollow", "scholars", "wardens", "unspoken")

    def func(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.caller.msg("|rANTHROPIC_API_KEY is not set.|n")
            return

        faction = self.args.strip().lower()
        if faction not in self.FACTIONS:
            self.caller.msg(
                f"|rUnknown faction.|n Valid: {', '.join(self.FACTIONS)}"
            )
            return

        caller = self.caller

        def _run():
            try:
                from world.generator import generate_faction_questline
                caller.msg(f"|y[GenQuest] Generating {faction} questline...|n")
                data = generate_faction_questline(faction)
                if data:
                    caller.msg(
                        f"|g[GenQuest] Done — '{data.get('title')}' questline "
                        f"for {faction} created.|n"
                    )
                else:
                    caller.msg("|r[GenQuest] Generator returned no data.|n")
            except Exception as exc:
                caller.msg(f"|r[GenQuest] Error: {exc}|n")

        threading.Thread(target=_run, daemon=True, name="takomud-genquest").start()


class CmdGenerateRegion(BaseCommand):
    """
    Generate an entire populated region via the Claude API.

    Usage:
      genregion <region name> [areas]

    Generates <areas> coordinated areas (default 4) all set within the named
    region, then creates a full faction questline with a herald NPC placed in
    the first generated room. Everything runs in a background thread.

    Example:
      genregion The Ashfields
      genregion The Sunken Library 6

    Requires ANTHROPIC_API_KEY in the environment. Watch server logs for progress.
    """

    key = "genregion"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.caller.msg("|rANTHROPIC_API_KEY is not set.|n")
            return

        args = self.args.strip().split()
        if not args:
            self.caller.msg("Usage: genregion <region name> [areas]")
            return

        # Last token is areas count if numeric
        if len(args) > 1 and args[-1].isdigit():
            areas = int(args[-1])
            region_name = " ".join(args[:-1])
        else:
            areas = 4
            region_name = " ".join(args)

        if areas < 1 or areas > 20:
            self.caller.msg("|rAreas must be between 1 and 20.|n")
            return

        caller = self.caller

        def _run():
            try:
                from world.generator import generate_region
                caller.msg(
                    f"|y[GenRegion] Generating {areas} areas in '{region_name}' "
                    f"+ faction questline. This may take a few minutes...|n"
                    f"|xWatch server logs for per-area progress.|n"
                )
                generate_region(region_name, areas=areas, delay=8)
                caller.msg(
                    f"|g[GenRegion] Done — '{region_name}' is live "
                    f"({areas} areas, quests, populated rooms).|n"
                )
            except Exception as exc:
                caller.msg(f"|r[GenRegion] Error: {exc}|n")

        threading.Thread(target=_run, daemon=True, name="takomud-genregion").start()


def _write_start_location(dbref):
    """Persist START_LOCATION and DEFAULT_HOME to secret_settings.py."""
    import os
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "server", "conf", "secret_settings.py",
    )
    lines = []
    if os.path.exists(path):
        with open(path) as f:
            lines = [
                l for l in f.readlines()
                if not l.startswith("START_LOCATION") and not l.startswith("DEFAULT_HOME")
            ]
    lines += [
        f'START_LOCATION = "{dbref}"\n',
        f'DEFAULT_HOME = "{dbref}"\n',
    ]
    with open(path, "w") as f:
        f.writelines(lines)
