"""
Registry of all quests. Populated by the generator at runtime.
Import QUESTS from here to look up quest data by key.
"""

QUESTS = {}


def register(quest_data):
    QUESTS[quest_data["key"]] = quest_data
