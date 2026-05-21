"""
Quest and dialogue commands for Takomud.
"""

from evennia.commands.command import Command as BaseCommand
from evennia.utils import utils


class CmdQuest(BaseCommand):
    """
    View your quest log.

    Usage:
      quest            — list all active quests
      quest <name>     — show details for a specific quest
    """

    key = "quest"
    aliases = ["quests", "journal", "j"]
    help_category = "General"

    def func(self):
        quests = self.caller.db.quests or {}
        if not quests:
            self.caller.msg("|xYou carry no obligations. That may be about to change.|n")
            return

        if self.args:
            name = self.args.strip().lower()
            for key, q in quests.items():
                if name in key.lower() or name in q["title"].lower():
                    self._show_quest(key, q)
                    return
            self.caller.msg("No quest matches that name.")
            return

        lines = ["\n|w--- Quest Log ---|n"]
        for key, q in quests.items():
            status = "|g[DONE]|n" if q["completed"] else "|y[ACTIVE]|n"
            lines.append(f"  {status} {q['title']}")
            if not q["completed"] and q["stages"]:
                stage = q["stages"][q["stage"]] if q["stage"] < len(q["stages"]) else None
                if stage:
                    lines.append(f"         |x{stage['text']}|n")
        self.caller.msg("\n".join(lines))

    def _show_quest(self, key, q):
        lines = [f"\n|w{q['title']}|n", q.get("desc", "")]
        for i, stage in enumerate(q["stages"]):
            done = "|g[x]|n" if stage["completed"] else "|x[ ]|n"
            lines.append(f"  {done} {stage['text']}")
        self.caller.msg("\n".join(lines))


class CmdTalk(BaseCommand):
    """
    Speak to an NPC in the room.

    Usage:
      talk <npc>
      talk <npc> about <topic>

    Examples:
      talk merchant
      talk warden about the old gate
    """

    key = "talk"
    aliases = ["speak", "ask"]
    help_category = "General"

    def parse(self):
        raw = self.args.strip()
        if " about " in raw:
            parts = raw.split(" about ", 1)
            self.target_name = parts[0].strip()
            self.topic = parts[1].strip()
        else:
            self.target_name = raw
            self.topic = None

    def func(self):
        if not self.target_name:
            self.caller.msg("Talk to whom?")
            return

        target = self.caller.search(self.target_name, location=self.caller.location)
        if not target:
            return

        if not utils.inherits_from(target, "typeclasses.npcs.NPC"):
            self.caller.msg("You address them. They don't respond in any meaningful way.")
            return

        # Cultists can speak to Hollow without triggering hostility
        faction = target.db.faction or "neutral"
        char_class = self.caller.db.char_class or "survivor"
        if (faction == "hollow" and char_class != "cultist"
                and utils.inherits_from(target, "typeclasses.npcs.Mob")):
            self.caller.msg(f"|r{target.key} does not acknowledge your words. It acknowledges your presence.|n")
            return

        response = target.at_talked_to(self.caller, self.topic)
        self.caller.msg(f'\n|c{target.key} says:|n "{response}"')
        self.caller.location.msg_contents(
            f"{self.caller.name} speaks with {target.key}.",
            exclude=[self.caller]
        )

        # Quest trigger
        from world.quest_system import check_objective
        check_objective(self.caller, "talk", target.key)

        # Check if NPC offers a quest
        for quest_key in (target.db.quest_keys or []):
            quests = self.caller.db.quests or {}
            if quest_key not in quests:
                from world import quest_registry
                qdata = quest_registry.QUESTS.get(quest_key)
                if qdata:
                    from world.quest_system import give_quest
                    ok, title = give_quest(self.caller, qdata)
                    if ok:
                        self.caller.msg(f"\n|y{target.key} has given you a quest: {title}|n")


class CmdAbandon(BaseCommand):
    """
    Abandon an active quest.

    Usage:
      abandon <quest name>
    """

    key = "abandon"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Abandon which quest?")
            return

        name = self.args.strip().lower()
        quests = self.caller.db.quests or {}

        for quest_key, q in quests.items():
            if name in quest_key.lower() or name in q["title"].lower():
                if q.get("completed"):
                    self.caller.msg("You cannot abandon a completed quest.")
                    return
                title = q["title"]
                del quests[quest_key]
                self.caller.db.quests = quests
                self.caller.msg(
                    f"|rYou abandon {title}. Whatever you were meant to do is left undone.|n"
                )
                return

        self.caller.msg("You have no quest matching that name.")
