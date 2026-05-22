"""
Command sets for Takomud.
"""

from evennia import default_cmds

from commands.horror import (
    CmdStat, CmdLore, CmdAtmosphere, CmdSetLore, CmdSetDark,
    CmdRead, CmdCharClass, CmdScore, CmdTrack, CmdMap,
    CmdSetEncounter, CmdSetHazard,
    CmdWho, CmdWhere, CmdShout, CmdUnlock, CmdLock, CmdAbility,
)
from commands.combat import CmdAttack, CmdFlee, CmdConsider, CmdStop
from commands.inventory import (
    CmdInventory, CmdEquip, CmdUnequip, CmdUse, CmdDrop, CmdGive,
    CmdRest, CmdInspect, CmdOpenContainer, CmdCloseContainer, CmdPutIn, CmdTakeFrom,
)
from commands.quest import CmdQuest, CmdTalk, CmdAbandon
from commands.economy import CmdBrowse, CmdBuy, CmdSell
from commands.admin import CmdGenerate, CmdGenerateStart, CmdGenerateQuest, CmdGenerateRegion


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
        self.add(CmdSetEncounter())
        self.add(CmdSetHazard())
        # Social
        self.add(CmdWho())
        self.add(CmdShout())
        # Character / exploration
        self.add(CmdCharClass())
        self.add(CmdTrack())
        self.add(CmdMap())
        self.add(CmdAbility())
        # Navigation
        self.add(CmdUnlock())
        self.add(CmdLock())
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
        self.add(CmdInspect())
        self.add(CmdRest())
        self.add(CmdOpenContainer())
        self.add(CmdCloseContainer())
        self.add(CmdPutIn())
        self.add(CmdTakeFrom())
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
        self.add(CmdGenerateRegion())
        self.add(CmdWhere())


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class SessionCmdSet(default_cmds.SessionCmdSet):
    key = "DefaultSession"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
