"""
Takomud World Bible — constants used by the generator and the game.

This module is the single source of truth for world lore, factions,
regions, and horror tone. Import from here; do not scatter magic strings.
"""

WORLD_NAME = "Takomud"

WORLD_PREMISE = """
Something broke the world — not explosively, but quietly, like a tooth
going soft. The event has no agreed-upon name. Those who were present
disagree on what they witnessed. The boundary between the living and the
absent has thinned. People change. Places remember things they shouldn't.
The sky at night is not the sky that was there before.
"""

FACTIONS = {
    "remnants": {
        "name": "The Remnants",
        "desc": (
            "Survivors trying to hold normal life together. Pragmatic, "
            "suspicious of outsiders, quietly terrified. They trade in "
            "useful things: food, warmth, information."
        ),
        "attitude": "cautious_neutral",
        "enemies": ["hollow", "unspoken"],
    },
    "hollow": {
        "name": "The Hollow",
        "desc": (
            "Those who lost their sanity and now serve something else. "
            "They do not appear broken — they appear calm. Too calm. "
            "They speak in borrowed phrases and remember things that "
            "haven't happened yet."
        ),
        "attitude": "hostile",
        "enemies": ["remnants", "wardens"],
    },
    "scholars": {
        "name": "Scholars of the Veil",
        "desc": (
            "Academics and investigators cataloguing the anomaly. "
            "Brilliant, obsessive, increasingly unreliable. Their notes "
            "are meticulous but their conclusions contradict each other. "
            "They will trade knowledge for knowledge."
        ),
        "attitude": "neutral",
        "enemies": [],
    },
    "wardens": {
        "name": "The Wardens",
        "desc": (
            "Former soldiers and guards enforcing order through fear. "
            "They have rules. The rules change. Breaking one is fatal. "
            "They are the only group with organized weapons."
        ),
        "attitude": "lawful_hostile",
        "enemies": ["hollow", "unspoken"],
    },
    "unspoken": {
        "name": "The Unspoken",
        "desc": (
            "Not human. May once have been. They have no agenda legible "
            "to human minds. They appear where they should not, do things "
            "that make no sense, and leave behind an altered silence."
        ),
        "attitude": "unknowable",
        "enemies": ["wardens"],
    },
}

REGIONS = [
    {
        "name": "The Threshold",
        "theme": "liminal horror — the edge of the known world",
        "horror_type": "psychological",
        "existing": True,
        "connects_to": ["The Sunken City", "The Pale Forest"],
    },
    {
        "name": "The Sunken City",
        "theme": "drowned ruins, rising water, things from below",
        "horror_type": "eldritch",
        "existing": False,
        "connects_to": ["The Threshold", "The Ossuarium"],
    },
    {
        "name": "The Pale Forest",
        "theme": "corrupted woodland, folk horror, wrong seasons",
        "horror_type": "folk",
        "existing": False,
        "connects_to": ["The Threshold", "The Ossuarium"],
    },
    {
        "name": "The Ossuarium",
        "theme": "ancient catacombs, ancestor worship gone wrong",
        "horror_type": "gothic",
        "existing": False,
        "connects_to": ["The Sunken City", "The Pale Forest", "The Observatory"],
    },
    {
        "name": "The Observatory",
        "theme": "scholars and wrong stars, cosmic dread",
        "horror_type": "cosmic",
        "existing": False,
        "connects_to": ["The Ossuarium"],
    },
]

HORROR_STYLES = {
    "psychological": "Dread comes from implication. The horror is in what the mind fills in. Never show the monster directly.",
    "eldritch": "The horror is alien and incomprehensible. Scale is wrong. Logic breaks near it.",
    "folk": "The horror is old, rooted, tied to place and season. It follows rules — terrible ones.",
    "gothic": "Decay, inheritance, trapped cycles. The past refuses to die.",
    "cosmic": "The horror is indifferent and vast. Knowing the truth is the worst outcome.",
    "body": "The self is no longer trustworthy. Flesh changes. Identity dissolves.",
}

CHARACTER_CLASSES = {
    "survivor": {
        "name": "Survivor",
        "desc": "You endure. You do not ask why.",
        "hp_bonus": 20,
        "sanity_bonus": -20,
        "fear_start": 0,
        "attack_bonus": 2,
        "defense": 10,
        "special": "Grit — once per hour, survive a killing blow at 1 HP",
    },
    "scholar": {
        "name": "Scholar",
        "desc": "You name things. Names are not always safe.",
        "hp_bonus": -20,
        "sanity_bonus": 20,
        "fear_start": 0,
        "attack_bonus": 0,
        "defense": 8,
        "special": "Veil-sight — lore command costs no sanity; reveals extra details",
    },
    "cultist": {
        "name": "Cultist",
        "desc": "You made an arrangement. You have not yet paid all of it.",
        "hp_bonus": -10,
        "sanity_bonus": -10,
        "fear_start": 30,
        "attack_bonus": 3,
        "defense": 9,
        "special": "Commune — can speak to Hollow NPCs without triggering hostility",
    },
    "hunter": {
        "name": "Hunter",
        "desc": "You track. You kill. The things you hunt have started tracking back.",
        "hp_bonus": 0,
        "sanity_bonus": -10,
        "fear_start": 0,
        "attack_bonus": 5,
        "defense": 12,
        "special": "Track — can sense nearby hostile mobs through walls",
    },
    "vagrant": {
        "name": "Vagrant",
        "desc": "You have nothing. That means you have nothing to lose.",
        "hp_bonus": 0,
        "sanity_bonus": 0,
        "fear_start": 0,
        "attack_bonus": 1,
        "defense": 10,
        "special": "Wanderer — gain +2 XP for each new room discovered",
    },
}

GENERATION_PROMPT_SYSTEM = f"""You are the content generator for {WORLD_NAME}, a dark horror MUD.

WORLD PREMISE:
{WORLD_PREMISE}

FACTIONS:
{chr(10).join(f'- {v["name"]}: {v["desc"]}' for v in FACTIONS.values())}

HORROR GUIDELINES:
- Second person, present tense ("You stand...", "The air smells of...")
- Sensory detail: sound, smell, texture, temperature — not just visual
- Imply rather than state. Suggest rather than confirm.
- Every mechanic should have a cost or a risk.
- Leave gaps. Contradiction is intentional.
- Avoid clichés: no dripping blood, no cobwebs, no generic skeletons.
- Names should feel like they belong: old, worn, meaningful.

PROSE REGISTERS: psychological dread | eldritch incomprehension | folk horror | gothic decay | cosmic indifference
"""
