"""
Registry of all quests. Populated by the generator at runtime.
Quest data is persisted to world/quest_data.json and reloaded on server start.
"""

import os
import json

QUESTS = {}

_QUEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "quest_data.json")


def register(quest_data):
    QUESTS[quest_data["key"]] = quest_data
    _save()


def _save():
    try:
        with open(_QUEST_DATA_FILE, "w") as f:
            json.dump(QUESTS, f, indent=2)
    except Exception:
        pass


def load_all():
    """Re-populate QUESTS from disk. Call from at_server_start."""
    if not os.path.exists(_QUEST_DATA_FILE):
        return
    try:
        with open(_QUEST_DATA_FILE) as f:
            data = json.load(f)
        QUESTS.update(data)
    except Exception:
        pass
