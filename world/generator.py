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
                        "recommended_level": {"type": "integer", "minimum": 1, "description": "Suggested minimum player level for this area"},
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
                        "quest_keys": {"type": "array", "items": {"type": "string"}},
                        "shop_items": {
                            "type": "array",
                            "description": "prototype_keys of items this NPC sells (merchant NPCs only)",
                            "items": {"type": "string"}
                        }
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
                        "gold_drop":    {"type": "integer", "minimum": 0, "description": "Gold coins dropped on death"},
                        "wanders":      {"type": "boolean", "description": "Does this mob wander randomly?"},
                        "status_effect": {
                            "type": "string",
                            "enum": ["bleed", "poison", "stun"],
                            "description": "Optional status effect inflicted on hit (35% chance)"
                        },
                        "respawn_delay": {"type": "integer", "minimum": 0, "description": "Seconds before respawn (0 = no respawn)"},
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
                                "required": ["text", "objective"],
                                "properties": {
                                    "text": {"type": "string"},
                                    "objective": {
                                        "description": "Structured objective dict.",
                                        "type": "object",
                                        "required": ["type"],
                                        "properties": {
                                            "type":    {"type": "string", "enum": ["kill","collect","visit","talk","deliver"]},
                                            "target":  {"type": "string", "description": "mob name/key (kill)"},
                                            "count":   {"type": "integer", "minimum": 1, "description": "required kills"},
                                            "current": {"type": "integer", "default": 0},
                                            "item":    {"type": "string", "description": "item name (collect/deliver)"},
                                            "room":    {"type": "string", "description": "room name/key (visit)"},
                                            "npc":     {"type": "string", "description": "npc name/key (talk/deliver)"}
                                        }
                                    }
                                }
                            }
                        },
                        "reward": {
                            "type": "object",
                            "properties": {
                                "xp":    {"type": "integer"},
                                "gold":  {"type": "integer"},
                                "items": {"type": "array", "items": {"type": "string"}},
                                "reputation": {
                                    "type": "object",
                                    "description": "faction -> reputation change",
                                    "additionalProperties": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            },
            "lore_documents": {
                "type": "array",
                "description": "Readable books, journals, notes, inscriptions placed in rooms.",
                "items": {
                    "type": "object",
                    "required": ["key", "title", "text", "room_key"],
                    "properties": {
                        "key":         {"type": "string"},
                        "title":       {"type": "string"},
                        "text":        {"type": "string", "minLength": 80},
                        "room_key":    {"type": "string"},
                        "sanity_cost": {"type": "integer", "minimum": 0, "maximum": 15}
                    }
                }
            },
            "boss_encounters": {
                "type": "array",
                "maxItems": 1,
                "description": "One optional named boss for this area.",
                "items": {
                    "type": "object",
                    "required": ["key", "room_key", "desc", "hp", "damage_dice", "xp_reward", "phases"],
                    "properties": {
                        "key":          {"type": "string"},
                        "room_key":     {"type": "string"},
                        "desc":         {"type": "string"},
                        "hp":           {"type": "integer", "minimum": 80},
                        "attack_bonus": {"type": "integer"},
                        "defense":      {"type": "integer"},
                        "damage_dice":  {"type": "string"},
                        "xp_reward":    {"type": "integer"},
                        "phases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "hp_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                                    "message":      {"type": "string"},
                                    "damage_bonus": {"type": "integer"}
                                }
                            }
                        },
                        "loot_table": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "prototype_key": {"type": "string"},
                                    "chance":        {"type": "number", "minimum": 0, "maximum": 1}
                                }
                            }
                        }
                    }
                }
            },
            "world_events": {
                "type": "array",
                "description": "Recurring timed events fired into specific rooms.",
                "items": {
                    "type": "object",
                    "required": ["key", "message", "interval_seconds", "room_keys"],
                    "properties": {
                        "key":              {"type": "string"},
                        "message":          {"type": "string"},
                        "interval_seconds": {"type": "integer", "minimum": 120},
                        "room_keys":        {"type": "array", "items": {"type": "string"}},
                        "sanity_cost":      {"type": "integer", "minimum": 0, "maximum": 10},
                        "fear_cost":        {"type": "integer", "minimum": 0, "maximum": 20}
                    }
                }
            }
        }
    }
}


STARTING_ZONE_TOOL = {
    "name": "create_starting_zone",
    "description": "Create the Threshold — the liminal starting zone where all players begin.",
    "input_schema": {
        "type": "object",
        "required": ["rooms", "npcs", "items", "lore_documents"],
        "properties": {
            "rooms": {
                "type": "array",
                "minItems": 3,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "required": ["key", "desc", "exits", "is_start"],
                    "properties": {
                        "key":        {"type": "string"},
                        "desc":       {"type": "string", "minLength": 100},
                        "is_start":   {"type": "boolean", "description": "Exactly one room must be true — the spawn point"},
                        "atmosphere": {"type": "array", "items": {"type": "string"}},
                        "lore":       {"type": "string"},
                        "exits":      {"type": "object", "additionalProperties": {"type": "string"}}
                    }
                }
            },
            "npcs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["key", "room_key", "desc", "dialogue"],
                    "properties": {
                        "key":      {"type": "string"},
                        "room_key": {"type": "string"},
                        "desc":     {"type": "string"},
                        "faction":  {"type": "string"},
                        "dialogue": {
                            "type": "object",
                            "properties": {
                                "greeting": {"type": "string"},
                                "topics":   {"type": "object", "additionalProperties": {"type": "string"}}
                            }
                        }
                    }
                }
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["key", "desc", "item_type", "room_key"],
                    "properties": {
                        "key":             {"type": "string"},
                        "prototype_key":   {"type": "string"},
                        "desc":            {"type": "string"},
                        "item_type":       {"type": "string", "enum": ["weapon","armor","consumable","light","misc"]},
                        "room_key":        {"type": "string"},
                        "damage_dice":     {"type": "string"},
                        "attack_bonus":    {"type": "integer"},
                        "defense_bonus":   {"type": "integer"},
                        "effect":          {"type": "object"},
                        "is_light_source": {"type": "boolean"},
                        "fuel":            {"type": ["integer","null"]},
                        "value":           {"type": "integer"}
                    }
                }
            },
            "lore_documents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["key", "title", "text", "room_key"],
                    "properties": {
                        "key":         {"type": "string"},
                        "title":       {"type": "string"},
                        "text":        {"type": "string", "minLength": 80},
                        "room_key":    {"type": "string"},
                        "sanity_cost": {"type": "integer", "minimum": 0, "maximum": 5}
                    }
                }
            }
        }
    }
}


def generate_starting_zone(api_key=None):
    """
    Generate The Threshold starting zone via the Claude API.
    Returns raw zone_data dict, or None if no API key is available.
    """
    import anthropic
    from world.world_bible import GENERATION_PROMPT_SYSTEM

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.warning("ANTHROPIC_API_KEY not set — skipping starting zone generation.")
        return None

    user_prompt = """Generate the starting zone for Takomud: "The Threshold".

This is where all players spawn. It is a liminal border — not quite the real world, not yet the deep horror.

Requirements:
- 3-5 rooms. Exactly one must have is_start: true. Name that room "The Threshold".
- The spawn room is an ambiguous, quiet border-place. Dread is present but subdued.
- 1-2 NPCs who can orient new arrivals (never cheerful; horror tone always; faction: remnants or scholars).
- 4-6 starter items: a light source, a simple weapon, at least one consumable.
- 2-3 lore documents hinting at the world's history (sanity_cost 0-2).
- Exits from edge rooms can reference stub names like "The Sunken City Gate" or "The Pale Forest Edge"
  (these rooms don't exist yet and won't be created — they are future connection points).
- Atmosphere: psychological dread, liminal unease, something has already gone wrong here.
"""

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=GENERATION_PROMPT_SYSTEM,
        tools=[STARTING_ZONE_TOOL],
        tool_choice={"type": "tool", "name": "create_starting_zone"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_starting_zone":
            return block.input

    raise ValueError("No tool_use block in Claude response for starting zone")


MAIN_QUESTLINE_TOOL = {
    "name": "create_main_questline",
    "description": "Create the overarching meta-narrative questline that connects all world regions.",
    "input_schema": {
        "type": "object",
        "required": ["title", "premise", "herald_npc", "stages"],
        "properties": {
            "title": {"type": "string"},
            "premise": {"type": "string", "description": "2-3 sentences: what happened, what the player must do"},
            "herald_npc": {
                "type": "object",
                "description": "NPC placed in The Threshold who gives the main quest.",
                "required": ["key", "desc", "dialogue"],
                "properties": {
                    "key":      {"type": "string"},
                    "faction":  {"type": "string"},
                    "desc":     {"type": "string"},
                    "dialogue": {
                        "type": "object",
                        "properties": {
                            "greeting": {"type": "string"},
                            "topics":   {"type": "object", "additionalProperties": {"type": "string"}}
                        }
                    }
                }
            },
            "stages": {
                "type": "array",
                "minItems": 4,
                "maxItems": 7,
                "items": {
                    "type": "object",
                    "required": ["title", "text", "region", "objective"],
                    "properties": {
                        "title":   {"type": "string"},
                        "text":    {"type": "string"},
                        "region":  {"type": "string", "description": "Which region this stage sends the player to"},
                        "objective": {
                            "type": "object",
                            "required": ["type"],
                            "properties": {
                                "type":    {"type": "string", "enum": ["kill","collect","visit","talk","deliver"]},
                                "target":  {"type": "string"},
                                "count":   {"type": "integer", "minimum": 1},
                                "current": {"type": "integer", "default": 0},
                                "item":    {"type": "string"},
                                "room":    {"type": "string"},
                                "npc":     {"type": "string"}
                            }
                        },
                        "reward": {
                            "type": "object",
                            "properties": {
                                "xp":   {"type": "integer"},
                                "gold": {"type": "integer"},
                                "reputation": {"type": "object", "additionalProperties": {"type": "integer"}}
                            }
                        }
                    }
                }
            },
            "conclusion": {"type": "string", "description": "What completing the questline reveals or resolves"}
        }
    }
}


def generate_main_questline(api_key=None, existing_areas=None):
    """
    Generate the overarching meta-narrative questline via Claude.
    Returns questline data dict, or None on failure.
    """
    import anthropic
    from world.world_bible import GENERATION_PROMPT_SYSTEM, REGIONS

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None

    area_summary = ""
    if existing_areas:
        area_summary = "Existing areas: " + ", ".join(
            f"{a['name']} ({a['theme']})" for a in existing_areas[:6]
        )

    region_names = ", ".join(r["name"] for r in REGIONS)

    user_prompt = f"""Create the main questline for Takomud — the overarching meta-narrative that ties the world together.

World regions: {region_names}
{area_summary}

Requirements:
- 4-7 stages, one per major region, sending the player progressively deeper into the horror
- A herald NPC in The Threshold who gives the quest and frames the mystery
- Each stage uses a structured objective (kill a named boss, visit a specific room, talk to a key NPC, deliver an artifact)
- Reward each stage with XP, gold, and faction reputation (faction should match the stage's region theme)
- The conclusion should reveal something about the world-breaking event — not resolve it, but reframe it
- Tone: psychological horror, slowly escalating dread, revelation is worse than ignorance
- The questline must feel like it was authored, not generated — give it a through-line
"""

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=GENERATION_PROMPT_SYSTEM,
        tools=[MAIN_QUESTLINE_TOOL],
        tool_choice={"type": "tool", "name": "create_main_questline"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_main_questline":
            return block.input

    log.error("No tool_use block in Claude response for main questline")
    return None


def _apply_main_questline(questline_data, state):
    """Place the herald NPC in The Threshold and register the main questline."""
    import evennia
    from typeclasses.npcs import NPC
    from typeclasses.rooms import Room
    from world import quest_registry

    herald = questline_data.get("herald_npc", {})
    if not herald:
        return

    # Find The Threshold spawn room
    threshold_key = "The Threshold"
    results = evennia.search_object(threshold_key, typeclass=Room)
    if not results:
        log.warning("Cannot place herald: The Threshold room not found.")
        return

    room = results[0]
    npc = evennia.create_object(NPC, key=herald["key"], location=room)
    npc.db.desc = herald.get("desc", "")
    npc.db.faction = herald.get("faction", "remnants")
    npc.db.dialogue = herald.get("dialogue", {})

    # Build quest data from the questline
    quest_data = {
        "key": "main_questline",
        "title": questline_data.get("title", "The Weight of What Remains"),
        "desc": questline_data.get("premise", ""),
        "giver_npc_key": herald["key"],
        "stages": [
            {"text": s["text"], "objective": s["objective"]}
            for s in questline_data.get("stages", [])
        ],
        "reward": {"xp": 500, "gold": 100},
    }
    quest_registry.register(quest_data)
    npc.db.quest_keys = ["main_questline"]
    state["all_npcs"][herald["key"]] = npc.dbref
    log.info(f"  + Main questline herald: {herald['key']} in The Threshold")


# ---------------------------------------------------------------------------
# Two-stage review pipeline
# ---------------------------------------------------------------------------

_QUALITY_SYSTEM = """You are a quality editor for Takomud, a dark horror MUD.

Review the generated area data and return a corrected version via the same create_area tool.
Fix:
- Descriptions shorter than 80 words (expand them with sensory detail)
- Generic or clichéd horror tropes (replace: no dripping blood, no cobwebs, no skeletons)
- NPCs with fewer than 3 dialogue topics (add more)
- Items with value=0 that should have prices (estimate based on item type and power)
- Any faction name not in: remnants, hollow, scholars, wardens, unspoken, neutral
- Quest objectives that are vague strings (convert to structured dict format)
- Missing prototype_key on items (generate a snake_case key from the item name)
Return the corrected data using the create_area tool."""

_CONSISTENCY_SYSTEM = """You are a world consistency editor for Takomud, a dark horror MUD.

You receive area data and context about the existing world. Return corrected data via create_area.
Check:
- Exit connections: if an exit target is not in the new area's rooms, is it in existing_rooms?
  If not, remove or replace it with a room that does exist.
- Faction logic: Hollow and Wardens are enemies. Scholars are neutral. Unspoken are unknowable.
  NPCs of enemy factions should not be in the same room unless there's clear tension.
- Horror tone consistency: prose must match the area's declared horror_style.
  Psychological = implication. Eldritch = wrongness of scale. Folk = old rules.
  Gothic = decay. Cosmic = indifference. Body = unreliable self.
- Lore consistency: generated lore should not contradict established world facts.
Return the corrected data using the create_area tool."""


def _review_area(area_data, api_key, existing_room_keys, stage="quality"):
    """Run one review pass over area_data. Returns (possibly corrected) area_data."""
    import anthropic
    system = _QUALITY_SYSTEM if stage == "quality" else _CONSISTENCY_SYSTEM

    context = ""
    if stage == "consistency" and existing_room_keys:
        context = f"\nExisting world rooms (valid exit targets): {', '.join(existing_room_keys[-20:])}"

    user_msg = (
        f"Review and correct this generated area data.{context}\n\n"
        f"Area data:\n{json.dumps(area_data, indent=2)}"
    )

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=system,
            tools=[AREA_TOOL],
            tool_choice={"type": "tool", "name": "create_area"},
            messages=[{"role": "user", "content": user_msg}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "create_area":
                log.info(f"  [{stage} review] Applied corrections.")
                return block.input
    except Exception as e:
        log.warning(f"  [{stage} review] Failed, using original: {e}")

    return area_data


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
- 1-3 NPCs (non-hostile, faction-aligned; include dialogue with at least 3 topics; merchant NPCs may have shop_items)
- 2-4 mobs (hostile creatures appropriate to the theme)
- 0-1 boss encounter (a named, dangerous creature with 2-3 combat phases; optional but strongly encouraged)
- 4-8 items (mix of weapons, armor, consumables, light sources; place in rooms or on mob/boss loot tables)
- 1-2 lore_documents (readable books, journals, or inscriptions; 80+ words of in-world prose each)
- 1-2 quests given by NPCs (multi-stage, thematically integrated; use structured objective dicts)
- 0-2 world_events (recurring timed messages sent to players in rooms; 120+ second intervals)
- Every mob loot_table entry must reference a prototype_key from the items list
- Quest reward should include gold (10-100) and reputation changes for relevant factions
- Rooms must interconnect to form a navigable layout — every room reachable from another

All prose must match the horror style: {horror_style}
All factions must be from: {', '.join(FACTIONS.keys())}
Use the create_area tool to return results.
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
            raw = block.input
            log.info("  [generation] Raw area received. Running quality review...")
            reviewed = _review_area(raw, api_key, existing_room_keys, stage="quality")
            log.info("  [quality] Done. Running consistency review...")
            final = _review_area(reviewed, api_key, existing_room_keys, stage="consistency")
            log.info("  [consistency] Done.")
            return final

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
        room.db.recommended_level = room_data.get("recommended_level", 1)

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
        npc.db.shop = npc_data.get("shop_items", [])
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
        mob.db.gold_drop = mob_data.get("gold_drop", 0)
        mob.db.faction = mob_data.get("faction", "unspoken")
        mob.db.aggro = mob_data.get("aggro", True)
        mob.db.wanders = mob_data.get("wanders", False)
        mob.db.status_effect = mob_data.get("status_effect", None)
        mob.db.respawn_delay = mob_data.get("respawn_delay", 300)
        mob.db.loot_table = mob_data.get("loot_table", [])
        if mob.db.wanders:
            from typeclasses.scripts import WanderScript
            mob.scripts.add(WanderScript)
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
    # 8. Create lore documents
    # ----------------------------------------------------------------
    from typeclasses.items import LoreDocument

    for doc_data in area_data.get("lore_documents", []):
        room = _get_room(doc_data.get("room_key", ""))
        if not room:
            log.warning(f"  Lore doc room not found: {doc_data.get('room_key')}")
            continue
        doc = evennia.create_object(LoreDocument, key=doc_data["key"], location=room)
        doc.db.doc_title = doc_data.get("title", doc_data["key"])
        doc.db.doc_text = doc_data.get("text", "")
        doc.db.sanity_cost = doc_data.get("sanity_cost", 2)
        log.info(f"  + LoreDoc: {doc_data['key']} in {doc_data.get('room_key')}")

    # ----------------------------------------------------------------
    # 9. Create boss encounters
    # ----------------------------------------------------------------
    from typeclasses.npcs import Boss

    for boss_data in area_data.get("boss_encounters", []):
        key = boss_data["key"]
        room = _get_room(boss_data.get("room_key", ""))
        if not room:
            log.warning(f"  Boss room not found: {boss_data.get('room_key')}")
            continue
        boss = evennia.create_object(Boss, key=key, location=room)
        boss.db.desc = boss_data.get("desc", "")
        boss.db.hp = boss_data.get("hp", 100)
        boss.db.hp_max = boss.db.hp
        boss.db.attack_bonus = boss_data.get("attack_bonus", 5)
        boss.db.defense = boss_data.get("defense", 12)
        boss.db.damage_dice = boss_data.get("damage_dice", "2d8")
        boss.db.xp_reward = boss_data.get("xp_reward", 200)
        boss.db.aggro = True
        boss.db.phases = boss_data.get("phases", [])
        boss.db.phase_triggered = []
        boss.db.loot_table = boss_data.get("loot_table", [])
        state["all_npcs"][key] = boss.dbref
        log.info(f"  + Boss: {key} in {boss_data.get('room_key')} (#{boss.id})")

    # ----------------------------------------------------------------
    # 10. Create world events
    # ----------------------------------------------------------------
    from typeclasses.scripts import WorldEventScript

    for event_data in area_data.get("world_events", []):
        room_dbrefs = []
        for rk in event_data.get("room_keys", []):
            r = _get_room(rk)
            if r:
                room_dbrefs.append(r.dbref)
        if not room_dbrefs:
            log.warning(f"  World event '{event_data['key']}' has no valid rooms; skipping.")
            continue
        script = evennia.create_script(WorldEventScript, key=event_data["key"])
        script.db.message = event_data.get("message", "")
        script.db.room_dbrefs = room_dbrefs
        script.db.sanity_cost = event_data.get("sanity_cost", 0)
        script.db.fear_cost = event_data.get("fear_cost", 0)
        script.interval = event_data.get("interval_seconds", 300)
        script.start()
        log.info(f"  + WorldEvent: {event_data['key']} ({script.interval}s)")

    # ----------------------------------------------------------------
    # 11. Record area
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

    # Generate main questline on the first run if not already created
    if not state.get("main_questline_created"):
        log.info("=== Generating main questline ===")
        try:
            ql_data = generate_main_questline(api_key=key, existing_areas=state.get("areas", []))
            if ql_data:
                _apply_main_questline(ql_data, state)
                state["main_questline_created"] = True
                _save_state(state)
                log.info(f"=== Main questline created: {ql_data.get('title')} ===")
        except Exception as e:
            log.error(f"Main questline generation failed: {e}", exc_info=True)

    i = 0
    while cycles == 0 or i < cycles:
        region = _pick_next_region(state)
        log.info(f"=== Generating area {i+1}: {region['name']} (+ quality & consistency review) ===")

        try:
            area_data = _call_claude(
                prompt=None,
                api_key=key,
                existing_room_keys=existing_rooms[-15:],
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
# Faction questline generator
# ---------------------------------------------------------------------------

FACTION_QUESTLINE_TOOL = {
    "name": "create_faction_questline",
    "description": "Create a multi-stage questline for a specific faction in Takomud.",
    "input_schema": {
        "type": "object",
        "required": ["faction", "title", "premise", "herald_npc", "stages"],
        "properties": {
            "faction": {
                "type": "string",
                "enum": ["remnants", "hollow", "scholars", "wardens", "unspoken"],
            },
            "title":   {"type": "string"},
            "premise": {"type": "string"},
            "herald_npc": {
                "type": "object",
                "required": ["key", "desc", "dialogue"],
                "properties": {
                    "key":      {"type": "string"},
                    "desc":     {"type": "string"},
                    "dialogue": {
                        "type": "object",
                        "properties": {
                            "greeting": {"type": "string"},
                            "topics":   {"type": "object", "additionalProperties": {"type": "string"}},
                        },
                    },
                },
            },
            "stages": {
                "type": "array",
                "minItems": 3,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "required": ["title", "text", "objective"],
                    "properties": {
                        "title": {"type": "string"},
                        "text":  {"type": "string"},
                        "objective": {
                            "type": "object",
                            "required": ["type"],
                            "properties": {
                                "type":    {"type": "string", "enum": ["kill", "collect", "visit", "talk", "deliver"]},
                                "target":  {"type": "string"},
                                "count":   {"type": "integer", "minimum": 1},
                                "current": {"type": "integer", "default": 0},
                                "item":    {"type": "string"},
                                "room":    {"type": "string"},
                                "npc":     {"type": "string"},
                            },
                        },
                        "reward": {
                            "type": "object",
                            "properties": {
                                "xp":         {"type": "integer"},
                                "gold":        {"type": "integer"},
                                "reputation":  {"type": "object", "additionalProperties": {"type": "integer"}},
                            },
                        },
                    },
                },
            },
            "conclusion": {"type": "string"},
        },
    },
}

_FACTION_WORLD_CONTEXT = {
    "remnants": "Survivors of the breaking — cautious, practical, mistrustful of outsiders. They hoard information and resources. Their questline should explore what they lost and what they protect.",
    "hollow":   "The changed ones — once human, now something adjacent. They are not monsters, but they are not people anymore. Their questline should blur the line between predator and victim.",
    "scholars": "Archivists of the old world — knowledge is their religion and their poison. They record horrors without intervening. Their questline should force a choice between knowledge and action.",
    "wardens":  "Former enforcers maintaining order through controlled violence. They know the rules are broken but enforce them anyway. Their questline should expose their complicity.",
    "unspoken": "Something else entirely. They should not exist. Their questline is about the player approaching something they cannot understand — and what understanding costs.",
}


def generate_faction_questline(faction, api_key=None, herald_room_key=None):
    """
    Generate a faction-specific questline via Claude.
    Returns questline data dict or None.
    faction: one of remnants/hollow/scholars/wardens/unspoken
    herald_room_key: where to place the herald NPC (defaults to The Threshold).
    """
    import anthropic
    from world.world_bible import GENERATION_PROMPT_SYSTEM

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.warning("ANTHROPIC_API_KEY not set — skipping faction questline generation.")
        return None

    faction_context = _FACTION_WORLD_CONTEXT.get(faction, "")
    user_prompt = f"""Create a faction questline for the {faction.upper()} faction in Takomud.

Faction context: {faction_context}

Requirements:
- 3-5 stages, escalating in stakes
- A herald NPC who is a member of this faction and gives the quest
- Each stage uses structured objective dicts
- Rewards include XP, gold, and reputation changes (positive for faction, negative for enemies)
- The conclusion must change something — an NPC's fate, a room's meaning, or the player's understanding
- Match the faction's ideology in all dialogue and quest text
- Tone: horror throughout, but each faction has its own flavor

Use the create_faction_questline tool.
"""

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        system=GENERATION_PROMPT_SYSTEM,
        tools=[FACTION_QUESTLINE_TOOL],
        tool_choice={"type": "tool", "name": "create_faction_questline"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_faction_questline":
            data = block.input
            _apply_faction_questline(data, herald_room_key=herald_room_key)
            return data

    log.error(f"No tool_use block in Claude response for {faction} questline")
    return None


def _apply_faction_questline(data, herald_room_key=None):
    """Place herald NPC and register faction questline."""
    import evennia
    from typeclasses.npcs import NPC
    from typeclasses.rooms import Room
    from world import quest_registry

    herald = data.get("herald_npc", {})
    if not herald:
        return

    room_key = herald_room_key or "The Threshold"
    results = evennia.search_object(room_key, typeclass=Room)
    if not results:
        log.warning(f"Cannot place faction herald: room '{room_key}' not found.")
        return

    room = results[0]
    npc = evennia.create_object(NPC, key=herald["key"], location=room)
    npc.db.desc = herald.get("desc", "")
    npc.db.faction = data.get("faction", "neutral")
    npc.db.dialogue = herald.get("dialogue", {})

    faction = data.get("faction", "unknown")
    quest_key = f"faction_{faction}"
    quest_data = {
        "key": quest_key,
        "title": data.get("title", f"{faction.title()} Questline"),
        "desc": data.get("premise", ""),
        "giver_npc_key": herald["key"],
        "stages": [
            {"text": s["text"], "objective": s["objective"]}
            for s in data.get("stages", [])
        ],
        "reward": {"xp": 300, "gold": 50, "reputation": {faction: 20}},
    }
    quest_registry.register(quest_data)
    npc.db.quest_keys = [quest_key]

    state = _load_state()
    state["all_npcs"][herald["key"]] = npc.dbref
    _save_state(state)
    log.info(f"  + Faction questline herald: {herald['key']} ({faction}) in {room_key}")


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
