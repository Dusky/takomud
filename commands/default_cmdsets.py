"""
Command sets for Takomud.
"""

from evennia import default_cmds

from commands.horror import CmdStat, CmdLore, CmdAtmosphere, CmdSetLore, CmdSetDark
from commands.combat import CmdAttack, CmdFlee, CmdConsider
from commands.inventory import CmdInventory, CmdEquip, CmdUnequip, CmdUse, CmdDrop
from commands.quest import CmdQuest, CmdTalk


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        # Horror / atmosphere
        self.add(CmdStat())
        self.add(CmdLore())
        self.add(CmdAtmosphere())
        self.add(CmdSetLore())
        self.add(CmdSetDark())
        # Combat
        self.add(CmdAttack())
        self.add(CmdFlee())
        self.add(CmdConsider())
        # Inventory / equipment
        self.add(CmdInventory())
        self.add(CmdEquip())
        self.add(CmdUnequip())
        self.add(CmdUse())
        self.add(CmdDrop())
        # Quests / dialogue
        self.add(CmdQuest())
        self.add(CmdTalk())


class AccountCmdSet(default_cmds.AccountCmdSet):
    key = "DefaultAccount"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class SessionCmdSet(default_cmds.SessionCmdSet):
    key = "DefaultSession"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
