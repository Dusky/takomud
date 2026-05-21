"""
Command sets for Takomud.
"""

from evennia import default_cmds

from commands.horror import (
    CmdStat, CmdLore, CmdAtmosphere, CmdSetLore, CmdSetDark,
    CmdRead, CmdCharClass, CmdScore, CmdTrack, CmdMap,
)
from commands.combat import CmdAttack, CmdFlee, CmdConsider, CmdStop
from commands.inventory import CmdInventory, CmdEquip, CmdUnequip, CmdUse, CmdDrop, CmdGive
from commands.quest import CmdQuest, CmdTalk, CmdAbandon
from commands.economy import CmdBrowse, CmdBuy, CmdSell
from commands.admin import CmdGenerate, CmdGenerateStart, CmdGenerateQuest


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        # Horror / atmosphere / info
        self.add(CmdStat())
        self.add(CmdScore())
        self.add(CmdLore())
        self.add(CmdRead())
        self.add(CmdAtmosphere())
        self.add(CmdSetLore())
        self.add(CmdSetDark())
        # Character / exploration
        self.add(CmdCharClass())
        self.add(CmdTrack())
        self.add(CmdMap())
        # Combat
        self.add(CmdAttack())
        self.add(CmdStop())
        self.add(CmdFlee())
        self.add(CmdConsider())
        # Inventory / equipment
        self.add(CmdInventory())
        self.add(CmdEquip())
        self.add(CmdUnequip())
        self.add(CmdUse())
        self.add(CmdDrop())
        self.add(CmdGive())
        # Economy
        self.add(CmdBrowse())
        self.add(CmdBuy())
        self.add(CmdSell())
        # Quests / dialogue
        self.add(CmdQuest())
        self.add(CmdTalk())
        self.add(CmdAbandon())


class AccountCmdSet(default_cmds.AccountCmdSet):
    key = "DefaultAccount"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdGenerate())
        self.add(CmdGenerateStart())
        self.add(CmdGenerateQuest())


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class SessionCmdSet(default_cmds.SessionCmdSet):
    key = "DefaultSession"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
