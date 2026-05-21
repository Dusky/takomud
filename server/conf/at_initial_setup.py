"""
Takomud initial setup — runs once on the very first server start.

Generates the starting zone (The Threshold) via the Claude API if
ANTHROPIC_API_KEY is set, then writes the spawn room's dbref to
server/conf/secret_settings.py so START_LOCATION persists across restarts.
"""

import logging
import os

log = logging.getLogger("takomud.setup")


def at_initial_setup():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning(
            "ANTHROPIC_API_KEY not set — starting zone not generated. "
            "Set the key and run 'genstart' in-game as an Admin to generate it later."
        )
        return

    log.info("=== Takomud: generating starting zone (The Threshold) ===")
    try:
        from world.generator import (
            generate_starting_zone, _apply_area, _load_state, _save_state
        )

        zone_data = generate_starting_zone()
        if not zone_data:
            log.warning("Starting zone generator returned no data.")
            return

        state = _load_state()

        area_data = {
            "area_name": "The Threshold",
            "theme": "starting zone — liminal horror",
            "rooms":           zone_data.get("rooms", []),
            "npcs":            zone_data.get("npcs", []),
            "mobs":            [],
            "items":           zone_data.get("items", []),
            "quests":          [],
            "lore_documents":  zone_data.get("lore_documents", []),
            "boss_encounters": [],
            "world_events":    [],
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
                _persist_start_location(results[0].dbref)
                log.info(
                    f"=== Starting zone complete. "
                    f"Spawn: '{start_key}' ({results[0].dbref}) — "
                    f"restart server for START_LOCATION to take effect. ==="
                )
            else:
                log.error(f"Could not find room '{start_key}' after creation.")
        else:
            log.warning("No is_start room found in generated starting zone.")

    except Exception as exc:
        log.error(f"Starting zone generation failed: {exc}", exc_info=True)


def _persist_start_location(dbref):
    """Write START_LOCATION and DEFAULT_HOME to secret_settings.py."""
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "secret_settings.py",
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
