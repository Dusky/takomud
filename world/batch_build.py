"""
Takomud starting world builder.

Run from in-game as superuser:
  @batchcode world.batch_build

Or from the shell (after the server is running):
  .venv/bin/evennia shell
  >>> from world.batch_build import build_world; build_world()
"""

import evennia


def build_world():
    from typeclasses.rooms import Room
    from typeclasses.scripts import AtmosphereScript

    def make_room(key, desc, lore="", atmosphere=None, dark=False):
        existing = evennia.search_object(key, typeclass=Room)
        if existing:
            room = existing[0]
        else:
            room = evennia.create_object(Room, key=key)
        room.db.desc = desc
        room.db.lore = lore
        room.db.dark = dark
        room.db.atmosphere = atmosphere or []
        if atmosphere and not room.scripts.get("atmosphere_script"):
            room.scripts.add(AtmosphereScript)
        return room

    def link(src, dst, exit_key, back_key, exit_desc="", back_desc=""):
        from typeclasses.exits import Exit
        if not src.exits or not any(e.key == exit_key for e in src.exits):
            evennia.create_object(Exit, key=exit_key, location=src, destination=dst,
                                  aliases=[exit_key[0]])
        if not dst.exits or not any(e.key == back_key for e in dst.exits):
            evennia.create_object(Exit, key=back_key, location=dst, destination=src,
                                  aliases=[back_key[0]])

    # ----------------------------------------------------------------
    # Rooms
    # ----------------------------------------------------------------

    liminal = make_room(
        key="The Liminal Gate",
        desc=(
            "You stand on a threshold that should not exist. The stone "
            "beneath your feet is warm — not from sun, but from something "
            "that breathes below. Mist clings to your ankles. Behind you "
            "is where you came from. Ahead is Takomud."
        ),
        lore=(
            "The Gate was not built. It grew — accretion of despair layered "
            "over centuries until the boundary between places thinned enough "
            "to walk through. Those who built the first roads here did not "
            "survive to name it."
        ),
        atmosphere=[
            "The mist shifts. Something behind it blinks.",
            "A low vibration rises through the stone into your bones.",
            "You hear your own name, whispered in a voice that is not yours.",
            "The air tastes of iron and old rain.",
        ],
    )

    vestibule = make_room(
        key="Vestibule of Ash",
        desc=(
            "Walls of blackened stone rise on either side, streaked with "
            "the grey residue of something that burned long ago. Sconces "
            "hold no flame — only calcified wax, centuries cold. The floor "
            "is thick with fine grey dust that holds no footprints but your own."
        ),
        lore=(
            "A settlement once crowded this hall with warmth and argument. "
            "Its name was burned out of every record. What the fire was, "
            "and whose hand lit it, no surviving text will say."
        ),
        atmosphere=[
            "Ash drifts down from nowhere above you.",
            "The dust on the floor shifts, though there is no wind.",
            "You catch the ghost of woodsmoke — ancient, cold.",
            "One of the sconces creaks on its bracket.",
        ],
    )

    corridor = make_room(
        key="The Long Corridor",
        desc=(
            "The passage stretches further than the light should permit. "
            "Doors line both sides, all sealed, all unmarked. The wood is "
            "swollen and dark, as though the walls wept into them for years. "
            "At the far end, something that might be a window admits no light."
        ),
        lore=(
            "Each door was sealed from the inside. Investigators who "
            "catalogued this corridor in an earlier age noted that the seals "
            "were made in haste — the locks turned, in some cases, with "
            "broken fingers still wrapped around them."
        ),
        atmosphere=[
            "One of the sealed doors trembles in its frame.",
            "You hear slow breathing on the other side of a door — then nothing.",
            "The passage seems longer than it did a moment ago.",
            "Scratching. Brief. Definitive. Then silence.",
        ],
        dark=True,
    )

    # ----------------------------------------------------------------
    # Exits
    # ----------------------------------------------------------------
    link(liminal, vestibule, "north", "south")
    link(vestibule, corridor, "north", "south")

    # ----------------------------------------------------------------
    # Set the default start room
    # ----------------------------------------------------------------
    from django.conf import settings
    settings.START_LOCATION = f"#{liminal.id}"

    print(f"World built. Start room: #{liminal.id} ({liminal.key})")
    print(f"  #{vestibule.id} — {vestibule.key}")
    print(f"  #{corridor.id} — {corridor.key}")
    return liminal
