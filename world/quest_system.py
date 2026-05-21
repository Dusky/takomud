"""
Quest system utilities for Takomud.

Quests are stored on the character as:
  character.db.quests = {
      "quest_key": {
          "title": str,
          "stage": int,          # current stage index (0-based)
          "stages": [            # ordered list of stages
              {
                  "text": str,
                  "objective": str | dict,  # legacy string OR structured dict
                  "completed": bool
              }
          ],
          "completed": bool,
          "reward_given": bool,
      }
  }

Structured objective dict forms:
  {"type": "kill",    "target": "mob name or key", "count": 1, "current": 0}
  {"type": "collect", "item":   "item name or key"}
  {"type": "visit",   "room":   "room name or key"}
  {"type": "talk",    "npc":    "npc name or key"}
  {"type": "deliver", "item":   "item name", "npc": "npc name"}
"""


def give_quest(character, quest_data):
    """
    Assign a quest to a character.

    quest_data = {
        "key": str,
        "title": str,
        "desc": str,
        "stages": [{"text": str, "objective": str | dict}],
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
        if hasattr(character, "adjust_xp"):
            character.adjust_xp(xp)
        else:
            character.db.xp = (character.db.xp or 0) + xp
        msgs.append(f"|y+{xp} XP|n")

    gold = reward.get("gold", 0)
    if gold and hasattr(character, "gain_gold"):
        character.gain_gold(gold)
        msgs.append(f"|y+{gold} gold|n")

    for faction, amount in (reward.get("reputation") or {}).items():
        if hasattr(character, "adjust_reputation"):
            character.adjust_reputation(faction, amount)

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


def _matches(value, pattern):
    """Case-insensitive substring match. Both coerced to str."""
    if value is None or pattern is None:
        return False
    return str(pattern).lower() in str(value).lower()


def check_objective(character, objective_type, target_key=None, *,
                    count=1, item_key=None, npc_key=None, room_key=None):
    """
    Signal that an objective-triggering action has occurred.

    objective_type : "kill" | "collect" | "visit" | "talk" | "deliver"
    target_key     : the mob/item/room/npc key involved (legacy & convenience)
    count          : number of kills in this call (default 1)
    item_key       : explicit item key for collect/deliver
    npc_key        : explicit npc key for talk/deliver
    room_key       : explicit room key for visit

    Existing callers (unchanged):
        check_objective(char, "kill",    target.key)
        check_objective(char, "visit",   room.key)
        check_objective(char, "talk",    target.key)
        check_objective(char, "deliver", f"{item.key}:{npc.key}")
        check_objective(char, "collect", item.key)
    """
    # Parse colon-encoded deliver string: "item_key:npc_key"
    if objective_type == "deliver" and target_key and ":" in target_key and not item_key and not npc_key:
        parts = target_key.split(":", 1)
        item_key = parts[0]
        npc_key = parts[1]

    quests = character.db.quests or {}
    for quest_key, q in quests.items():
        if q["completed"]:
            continue
        stage_idx = q["stage"]
        if stage_idx >= len(q["stages"]):
            continue
        stage = q["stages"][stage_idx]
        obj = stage.get("objective", "")

        # ------------------------------------------------------------------ #
        # Legacy string format                                                 #
        # ------------------------------------------------------------------ #
        if isinstance(obj, str):
            obj_str = obj
            if objective_type in obj_str and (not target_key or target_key in obj_str):
                advanced, msg = advance_quest(character, quest_key)
                if advanced and msg:
                    character.msg(msg)
                    if q.get("completed"):
                        reward_msg = complete_quest_reward(character, quest_key)
                        if reward_msg:
                            character.msg(reward_msg)
            continue

        # ------------------------------------------------------------------ #
        # Structured dict format                                               #
        # ------------------------------------------------------------------ #
        if not isinstance(obj, dict):
            continue

        obj_type = obj.get("type", "")
        if obj_type != objective_type:
            continue

        matched = False

        if objective_type == "kill":
            # target_key (or npc_key) must substring-match obj["target"]
            key_to_check = target_key or npc_key
            if _matches(key_to_check, obj.get("target")):
                required = obj.get("count", 1)
                obj["current"] = obj.get("current", 0) + count
                # Persist the incremented counter immediately
                character.db.quests = quests
                if obj["current"] >= required:
                    matched = True
                else:
                    # Partial progress message
                    character.msg(
                        f"|cQuest update: {q['title']} — "
                        f"{obj['current']}/{required} "
                        f"{obj.get('target', 'targets')} killed|n"
                    )

        elif objective_type == "collect":
            key_to_check = item_key or target_key
            if _matches(key_to_check, obj.get("item")):
                matched = True

        elif objective_type == "visit":
            key_to_check = room_key or target_key
            if _matches(key_to_check, obj.get("room")):
                matched = True

        elif objective_type == "talk":
            key_to_check = npc_key or target_key
            if _matches(key_to_check, obj.get("npc")):
                matched = True

        elif objective_type == "deliver":
            item_match = _matches(item_key or target_key, obj.get("item"))
            npc_match = _matches(npc_key, obj.get("npc"))
            if item_match and npc_match:
                matched = True

        if matched:
            advanced, msg = advance_quest(character, quest_key)
            if advanced and msg:
                character.msg(msg)
                if q.get("completed"):
                    reward_msg = complete_quest_reward(character, quest_key)
                    if reward_msg:
                        character.msg(reward_msg)


def check_collect_trigger(character, item_key):
    """Call this when a player picks up an item. Triggers collect objectives."""
    check_objective(character, "collect", item_key, item_key=item_key)
