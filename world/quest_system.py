"""
Quest system utilities for Takomud.

Quests are stored on the character as:
  character.db.quests = {
      "quest_key": {
          "title": str,
          "stage": int,          # current stage index (0-based)
          "stages": [            # ordered list of stages
              {"text": str, "objective": str, "completed": bool}
          ],
          "completed": bool,
          "reward_given": bool,
      }
  }
"""


def give_quest(character, quest_data):
    """
    Assign a quest to a character.

    quest_data = {
        "key": str,
        "title": str,
        "desc": str,
        "stages": [{"text": str, "objective": str}],
        "reward": {"items": [prototype_key], "xp": int},
    }
    """
    quests = character.db.quests or {}
    key = quest_data["key"]
    if key in quests:
        return False, "You are already on that quest."

    quests[key] = {
        "title": quest_data["title"],
        "desc": quest_data.get("desc", ""),
        "stage": 0,
        "stages": [
            {"text": s["text"], "objective": s["objective"], "completed": False}
            for s in quest_data.get("stages", [])
        ],
        "reward": quest_data.get("reward", {}),
        "completed": False,
        "reward_given": False,
    }
    character.db.quests = quests
    return True, quest_data["title"]


def advance_quest(character, quest_key):
    """Advance quest to next stage. Returns (advanced, message)."""
    quests = character.db.quests or {}
    if quest_key not in quests:
        return False, "Quest not found."

    q = quests[quest_key]
    if q["completed"]:
        return False, "Already completed."

    stage = q["stage"]
    if stage < len(q["stages"]):
        q["stages"][stage]["completed"] = True

    q["stage"] += 1
    if q["stage"] >= len(q["stages"]):
        q["completed"] = True
        character.db.quests = quests
        return True, f"|yQuest complete: {q['title']}|n"

    character.db.quests = quests
    next_stage = q["stages"][q["stage"]]
    return True, f"|cQuest updated — {q['title']}:|n {next_stage['text']}"


def complete_quest_reward(character, quest_key):
    """Grant rewards for a completed quest. Returns message."""
    from evennia.prototypes import spawner
    quests = character.db.quests or {}
    if quest_key not in quests:
        return "Quest not found."

    q = quests[quest_key]
    if not q["completed"] or q["reward_given"]:
        return None

    reward = q.get("reward", {})
    msgs = []

    xp = reward.get("xp", 0)
    if xp:
        character.db.xp = (character.db.xp or 0) + xp
        msgs.append(f"|y+{xp} XP|n")

    for proto_key in reward.get("items", []):
        try:
            objs = spawner.spawn(proto_key)
            for obj in objs:
                obj.location = character
            msgs.append(f"|gReceived: {objs[0].key}|n" if objs else "")
        except Exception:
            pass

    q["reward_given"] = True
    character.db.quests = quests

    return "\n".join(m for m in msgs if m) or "Reward given."


def check_objective(character, objective_type, target_key=None):
    """
    Signal that an objective may have been met.
    objective_type: "kill", "collect", "visit", "talk"
    target_key: the mob/item/room/npc key involved
    """
    quests = character.db.quests or {}
    for quest_key, q in quests.items():
        if q["completed"]:
            continue
        stage_idx = q["stage"]
        if stage_idx >= len(q["stages"]):
            continue
        stage = q["stages"][stage_idx]
        obj_str = stage.get("objective", "")
        if objective_type in obj_str and (not target_key or target_key in obj_str):
            advanced, msg = advance_quest(character, quest_key)
            if advanced and msg:
                character.msg(msg)
                if q.get("completed"):
                    reward_msg = complete_quest_reward(character, quest_key)
                    if reward_msg:
                        character.msg(reward_msg)
