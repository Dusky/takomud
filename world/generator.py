"""
Takomud Autonomous World Generator

Uses the Anthropic API to generate rooms, NPCs, items, quests, and mobs,
then applies them directly to the Evennia database.

Usage (from shell):
    .venv/bin/python world/generator.py [--cycles N] [--delay S] [--api-key KEY]

    cycles: number of areas to generate (0 = infinite, default 1)
    delay:  seconds between cycles (default 10)

Usage (from evennia shell):
    from world.generator import generate
    generate(cycles=5)

Requires: ANTHROPIC_API_KEY environment variable (or pass api_key=).
"""

import os
import sys
import json
import time
import random
import argparse
import logging

log = logging.getLogger("takomud.generator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [GEN] %(message)s")

# ---------------------------------------------------------------------------
# Django/Evennia setup for standalone execution
# ---------------------------------------------------------------------------

def _setup_django():
    game_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if game_dir not in sys.path:
        sys.path.insert(0, game_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.conf.settings")
    import django
    django.setup()
    import evennia
    evennia._init()


# ---------------------------------------------------------------------------
# World state — persisted to world/world_state.json
# ---------------------------------------------------------------------------

STATE_FILE = os.path.join(os.path.dirname(__file__), "world_state.json")


def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "areas": [],
        "all_rooms": {},      # key -> dbref
        "all_npcs": {},       # key -> dbref
        "all_items": {},      # key -> dbref
        "all_quests": [],
        "all_prototypes": [], # prototype keys registered
        "generation_count": 0,
        "region_queue": [
            "The Sunken City",
            "The Pale Forest",
            "The Ossuarium",
            "The Observatory",
        ],
    }


def _save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Claude API call — returns structured area dict
# ---------------------------------------------------------------------------

AREA_TOOL = {
    "name": "create_area",
    "description": "Create a complete MUD area with rooms, NPCs, items, and quests.",
    "input_schema": {
        "type": "object",
        "required": ["area_name", "theme", "rooms", "npcs", "items", "quests", "mobs"],
        "properties": {
            "area_name": {"type": "string"},
            "theme": {"type": "string"},
            "horror_style": {
                "type": "string",
                "enum": ["psychological", "eldritch", "folk", "gothic", "cosmic", "body"]
            },
            "rooms": {
                "type": "array",
                "minItems": 3,
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "required": ["key", "desc", "exits"],
                    "properties": {
                        "key":         {"type": "string"},
                        "desc":        {"type": "string", "minLength": 100},
                        "lore":        {"type": "string"},
                        "atmosphere":  {"type": "array", "items": {"type": "string"}},
                        "dark":        {"type": "boolean"},
                        "exits": {
                            "type": "object",
                            "description": "direction -> room key (use existing room keys to connect to existing world)",
                            "additionalProperties": {"type": "string"}
                        }
                    }
                }
            },
            "npcs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["key", "room_key", "desc", "faction"],
                    "properties": {
                        "key":       {"type": "string"},
                        "room_key":  {"type": "string"},
                        "desc":      {"type": "string"},
                        "faction":   {"type": "string", "enum": ["remnants","hollow","scholars","wardens","unspoken","neutral"]},
                        "dialogue": {
                            "type": "object",
                            "properties": {
                                "greeting": {"type": "string"},
                                "topics":   {"type": "object", "additionalProperties": {"type": "string"}}
                            }
                        },
                        "quest_keys": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "mobs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["key", "room_key", "desc", "hp", "damage_dice", "xp_reward"],
                    "properties": {
                        "key":          {"type": "string"},
                        "room_key":     {"type": "string"},
                        "desc":         {"type": "string"},
                        "hp":           {"type": "integer", "minimum": 5},
                        "attack_bonus": {"type": "integer"},
                        "defense":      {"type": "integer"},
                        "damage_dice":  {"type": "string"},
                        "xp_reward":    {"type": "integer"},
                        "faction":      {"type": "string"},
                        "aggro":        {"type": "boolean"},
                        "loot_table": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "prototype_key": {"type": "string"},
                                    "chance": {"type": "number", "minimum": 0, "maximum": 1}
                                }
                            }
                        }
                    }
                }
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["key", "desc", "item_type"],
                    "properties": {
                        "key":           {"type": "string"},
                        "prototype_key": {"type": "string"},
                        "desc":          {"type": "string"},
                        "item_type":     {"type": "string", "enum": ["weapon","armor","consumable","quest","light","misc"]},
                        "slot":          {"type": "string"},
                        "damage_dice":   {"type": "string"},
                        "attack_bonus":  {"type": "integer"},
                        "defense_bonus": {"type": "integer"},
                        "effect":        {"type": "object"},
                        "is_light_source": {"type": "boolean"},
                        "fuel":          {"type": ["integer","null"]},
                        "value":         {"type": "integer"},
                        "room_key":      {"type": "string"},
                        "npc_key":       {"type": "string"},
                        "droppable":     {"type": "boolean"}
                    }
                }
            },
            "quests": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["key", "title", "giver_npc_key", "stages"],
                    "properties": {
                        "key":           {"type": "string"},
                        "title":         {"type": "string"},
                        "desc":          {"type": "string"},
                        "giver_npc_key": {"type": "string"},
                        "stages": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text":      {"type": "string"},
                                    "objective": {"type": "string"}
                                }
                            }
                        },
                        "reward": {
                            "type": "object",
                            "properties": {
                                "xp":    {"type": "integer"},
                                "items": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    }
                }
            }
        }
    }
}


def _call_claude(prompt, api_key, existing_room_keys, region_name, region_theme, horror_style):
    import anthropic
    from world.world_bible import GENERATION_PROMPT_SYSTEM, FACTIONS

    existing_summary = (
        f"Existing rooms you can connect to via exits: {', '.join(existing_room_keys)}\n"
        if existing_room_keys else "This is the first area beyond the starting zone.\n"
    )

    user_prompt = f"""Generate a new area for region: {region_name}
Theme: {region_theme}
Horror style: {horror_style}

{existing_summary}

Requirements:
- 4-6 rooms with rich, sensory descriptions (100+ words each)
- At least one room connected via exit to an existing room (if any exist)
- 1-3 NPCs (non-hostile, faction-aligned, with dialogue and at least 3 conversation topics)
- 2-4 mobs (hostile creatures appropriate to the theme)
- 4-8 items (mix of weapons, armor, consumables, light sources; place in rooms or on mob loot tables)
- 1-2 quests given by NPCs (multi-stage, thematically integrated)
- Every mob loot_table entry must reference a prototype_key from the items list
- Rooms must interconnect to form a navigable layout — every room reachable from another

All prose must match the horror style: {horror_style}
All factions must be from: {', '.join(FACTIONS.keys())}
Use the generate_content tool to return results.
"""

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=GENERATION_PROMPT_SYSTEM,
        tools=[AREA_TOOL],
        tool_choice={"type": "tool", "name": "create_area"},
        messages=[{"role": "user", "content": user_prompt}]
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_area":
            return block.input

    raise ValueError("No tool_use block in Claude response")


# ---------------------------------------------------------------------------
# Apply generated area to the database
# ---------------------------------------------------------------------------

def _apply_area(area_data, state):
    import evennia
    from typeclasses.rooms import Room
    from typeclasses.npcs import NPC, Mob
    from typeclasses.items import Item
    from typeclasses.scripts import AtmosphereScript
    from world import quest_registry
    from evennia.prototypes import prototypes as proto_handler

    created_rooms = {}   # key -> room object
    created_npcs = {}    # key -> npc object
    created_items = {}   # key -> item object (for in-world placement)
    item_prototypes = {} # prototype_key -> item_data (for loot tables)

    # ----------------------------------------------------------------
    # 1. Register item prototypes (needed before mobs reference them)
    # ----------------------------------------------------------------
    for item_data in area_data.get("items", []):
        proto_key = item_data.get("prototype_key") or item_data["key"].upper().replace(" ", "_")
        item_data["prototype_key"] = proto_key
        prototype = {
            "prototype_key": proto_key,
            "key": item_data["key"],
            "typeclass": "typeclasses.items.Item",
            "desc": item_data.get("desc", ""),
            "attrs": [
                ("item_type",    item_data.get("item_type", "misc")),
                ("slot",         item_data.get("slot")),
                ("damage_dice",  item_data.get("damage_dice", "1d4")),
                ("attack_bonus", item_data.get("attack_bonus", 0)),
                ("defense_bonus",item_data.get("defense_bonus", 0)),
                ("effect",       item_data.get("effect", {})),
                ("is_light_source", item_data.get("is_light_source", False)),
                ("fuel",         item_data.get("fuel")),
                ("lit",          False),
                ("value",        item_data.get("value", 0)),
                ("droppable",    item_data.get("droppable", True)),
            ]
        }
        try:
            proto_handler.save_prototype(prototype)
            item_prototypes[proto_key] = item_data
            if proto_key not in state["all_prototypes"]:
                state["all_prototypes"].append(proto_key)
        except Exception as e:
            log.warning(f"Could not save prototype {proto_key}: {e}")

    # ----------------------------------------------------------------
    # 2. Create rooms
    # ----------------------------------------------------------------
    for room_data in area_data.get("rooms", []):
        key = room_data["key"]
        if key in state["all_rooms"]:
            log.info(f"  Room already exists: {key}")
            results = evennia.search_object(key, typeclass=Room)
            created_rooms[key] = results[0] if results else None
            continue

        room = evennia.create_object(Room, key=key)
        room.db.desc = room_data.get("desc", "")
        room.db.lore = room_data.get("lore", "")
        room.db.dark = room_data.get("dark", False)
        room.db.atmosphere = room_data.get("atmosphere", [])

        if room.db.atmosphere:
            room.scripts.add(AtmosphereScript)

        state["all_rooms"][key] = room.dbref
        created_rooms[key] = room
        log.info(f"  + Room: {key} (#{room.id})")

    # ----------------------------------------------------------------
    # 3. Create exits between rooms
    # ----------------------------------------------------------------
    from typeclasses.exits import Exit

    OPPOSITES = {
        "north": "south", "south": "north",
        "east": "west",   "west": "east",
        "up": "down",     "down": "up",
        "in": "out",      "out": "in",
    }

    def _get_room(key):
        if key in created_rooms and created_rooms[key]:
            return created_rooms[key]
        if key in state["all_rooms"]:
            results = evennia.search_object(state["all_rooms"][key], use_dbref=True)
            return results[0] if results else None
        return None

    for room_data in area_data.get("rooms", []):
        src_room = _get_room(room_data["key"])
        if not src_room:
            continue
        for direction, dest_key in room_data.get("exits", {}).items():
            dst_room = _get_room(dest_key)
            if not dst_room:
                log.warning(f"  Exit target not found: {dest_key}")
                continue
            # Create exit if not already there
            existing = [e for e in src_room.exits if e.key == direction]
            if not existing:
                evennia.create_object(
                    Exit, key=direction, location=src_room, destination=dst_room,
                    aliases=[direction[0]] if len(direction) > 1 else []
                )
                log.info(f"  + Exit: {room_data['key']} --{direction}--> {dest_key}")
            # Create return exit
            back = OPPOSITES.get(direction)
            if back:
                existing_back = [e for e in dst_room.exits if e.key == back]
                if not existing_back:
                    evennia.create_object(
                        Exit, key=back, location=dst_room, destination=src_room,
                        aliases=[back[0]] if len(back) > 1 else []
                    )

    # ----------------------------------------------------------------
    # 4. Place items in rooms
    # ----------------------------------------------------------------
    for item_data in area_data.get("items", []):
        room_key = item_data.get("room_key")
        if not room_key:
            continue  # on a mob or nowhere
        room = _get_room(room_key)
        if not room:
            continue
        try:
            from evennia.prototypes import spawner
            objs = spawner.spawn(item_data["prototype_key"])
            for obj in objs:
                obj.location = room
                state["all_items"][item_data["key"]] = obj.dbref
                created_items[item_data["key"]] = obj
                log.info(f"  + Item: {item_data['key']} in {room_key}")
        except Exception as e:
            log.warning(f"  Could not place item {item_data['key']}: {e}")

    # ----------------------------------------------------------------
    # 5. Create NPCs
    # ----------------------------------------------------------------
    for npc_data in area_data.get("npcs", []):
        key = npc_data["key"]
        if key in state["all_npcs"]:
            continue
        room = _get_room(npc_data.get("room_key", ""))
        if not room:
            log.warning(f"  NPC room not found: {npc_data.get('room_key')}")
            continue

        npc = evennia.create_object(NPC, key=key, location=room)
        npc.db.desc = npc_data.get("desc", "")
        npc.db.faction = npc_data.get("faction", "neutral")
        npc.db.dialogue = npc_data.get("dialogue", {})
        npc.db.quest_keys = npc_data.get("quest_keys", [])
        state["all_npcs"][key] = npc.dbref
        created_npcs[key] = npc
        log.info(f"  + NPC: {key} in {npc_data.get('room_key')} (#{npc.id})")

    # ----------------------------------------------------------------
    # 6. Create mobs
    # ----------------------------------------------------------------
    for mob_data in area_data.get("mobs", []):
        key = mob_data["key"]
        room = _get_room(mob_data.get("room_key", ""))
        if not room:
            log.warning(f"  Mob room not found: {mob_data.get('room_key')}")
            continue

        mob = evennia.create_object(Mob, key=key, location=room)
        mob.db.desc = mob_data.get("desc", "")
        mob.db.hp = mob_data.get("hp", 30)
        mob.db.hp_max = mob.db.hp
        mob.db.attack_bonus = mob_data.get("attack_bonus", 3)
        mob.db.defense = mob_data.get("defense", 8)
        mob.db.damage_dice = mob_data.get("damage_dice", "1d6")
        mob.db.xp_reward = mob_data.get("xp_reward", 25)
        mob.db.faction = mob_data.get("faction", "unspoken")
        mob.db.aggro = mob_data.get("aggro", True)
        mob.db.loot_table = mob_data.get("loot_table", [])
        state["all_npcs"][key] = mob.dbref
        log.info(f"  + Mob: {key} in {mob_data.get('room_key')} (#{mob.id})")

    # ----------------------------------------------------------------
    # 7. Register quests
    # ----------------------------------------------------------------
    for quest_data in area_data.get("quests", []):
        key = quest_data["key"]
        if key in state["all_quests"]:
            continue
        quest_registry.register(quest_data)
        state["all_quests"].append(key)

        # Link quest key to giver NPC
        giver_key = quest_data.get("giver_npc_key")
        if giver_key in created_npcs:
            npc = created_npcs[giver_key]
            keys = npc.db.quest_keys or []
            if key not in keys:
                keys.append(key)
                npc.db.quest_keys = keys

        log.info(f"  + Quest: {quest_data['title']} (given by {giver_key})")

    # ----------------------------------------------------------------
    # 8. Record area
    # ----------------------------------------------------------------
    area_record = {
        "name": area_data.get("area_name", "Unknown"),
        "theme": area_data.get("theme", ""),
        "rooms": list(created_rooms.keys()),
    }
    state["areas"].append(area_record)
    state["generation_count"] += 1

    return area_record


# ---------------------------------------------------------------------------
# Main generation loop
# ---------------------------------------------------------------------------

def _pick_next_region(state):
    from world.world_bible import REGIONS, HORROR_STYLES
    queue = state.get("region_queue", [])
    if not queue:
        # Fallback: generate a random new sub-region
        horror_type = random.choice(list(HORROR_STYLES.keys()))
        return {
            "name": f"The Forgotten {random.choice(['Reach','Ward','Hollow','Breach','Crossing'])}",
            "theme": f"expansion area with {horror_type} horror",
            "horror_type": horror_type,
        }
    region_name = queue[0]
    for r in REGIONS:
        if r["name"] == region_name:
            return r
    return {"name": region_name, "theme": "unknown region", "horror_type": "psychological"}


def generate(cycles=1, delay=10, api_key=None):
    """
    Run the generator for `cycles` areas (0 = infinite).
    Call from evennia shell: from world.generator import generate; generate(cycles=5)
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("ERROR: ANTHROPIC_API_KEY not set. Export it or pass api_key=.")
        return

    state = _load_state()
    existing_rooms = list(state["all_rooms"].keys())

    i = 0
    while cycles == 0 or i < cycles:
        region = _pick_next_region(state)
        log.info(f"=== Generating area {i+1}: {region['name']} ===")

        try:
            area_data = _call_claude(
                prompt=None,
                api_key=key,
                existing_room_keys=existing_rooms[-10:],  # last 10 to avoid huge prompts
                region_name=region["name"],
                region_theme=region.get("theme", ""),
                horror_style=region.get("horror_type", "psychological"),
            )
            area_record = _apply_area(area_data, state)

            # Advance region queue
            if state.get("region_queue") and region["name"] == state["region_queue"][0]:
                state["region_queue"].pop(0)

            existing_rooms = list(state["all_rooms"].keys())
            _save_state(state)

            log.info(f"=== Done: {area_record['name']} | "
                     f"{len(area_record['rooms'])} rooms | "
                     f"total areas: {len(state['areas'])} ===")

        except Exception as e:
            log.error(f"Generation failed: {e}", exc_info=True)

        i += 1
        if cycles == 0 or i < cycles:
            log.info(f"Waiting {delay}s before next cycle...")
            time.sleep(delay)

    log.info("Generation complete.")


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _setup_django()

    parser = argparse.ArgumentParser(description="Takomud world generator")
    parser.add_argument("--cycles", type=int, default=1,
                        help="Areas to generate (0=infinite)")
    parser.add_argument("--delay",  type=int, default=10,
                        help="Seconds between cycles")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Anthropic API key (overrides env var)")
    args = parser.parse_args()

    generate(cycles=args.cycles, delay=args.delay, api_key=args.api_key)
