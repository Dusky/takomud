"""

MSSP (Mud Server Status Protocol) meta information

Modify this file to specify what MUD listing sites will report about your game.
All fields are static. The number of currently active players and your game's
current uptime will be added automatically by Evennia.

You don't have to fill in everything (and most fields are not shown/used by all
crawlers anyway); leave the default if so needed. You need to reload the server
before the updated information is made available to crawlers (reloading does
not affect uptime).

After changing the values in this file, you must register your game with the
MUD website list you want to track you. The listing crawler will then regularly
connect to your server to get the latest info. No further configuration is
needed on the Evennia side.

"""

MSSPTable = {
    # Required fields
    "NAME": "Takomud",
    # Generic
    "CRAWL DELAY": "-1",
    "HOSTNAME": "",
    "PORT": ["4000"],
    "CODEBASE": "Evennia",
    "CONTACT": "",
    "CREATED": "2024",
    "ICON": "",
    "IP": "",
    "LANGUAGE": "English",
    "LOCATION": "",
    "MINIMUM AGE": "18",
    "WEBSITE": "",
    # Categorisation
    "FAMILY": "Evennia",
    "GENRE": "Horror",
    "GAMEPLAY": "Roleplaying",
    "STATUS": "Alpha",
    "GAMESYSTEM": "Custom",
    "SUBGENRE": "Cosmic Horror",
    # World
    "AREAS": "0",
    "HELPFILES": "0",
    "MOBILES": "0",
    "OBJECTS": "0",
    "ROOMS": "0",
    "CLASSES": "5",
    "LEVELS": "10",
    "RACES": "0",
    "SKILLS": "0",
    # Protocols
    "ANSI": "1",
    "GMCP": "1",
    "MSDP": "1",
    "MXP": "1",
    "SSL": "1",
    "UTF-8": "1",
    "MCCP": "1",
    "XTERM 256 COLORS": "1",
    "XTERM TRUE COLORS": "0",
    "ATCP": "0",
    "MCP": "0",
    "MSP": "0",
    "VT100": "0",
    "PUEBLO": "0",
    "ZMP": "0",
    # Commercial
    "PAY TO PLAY": "0",
    "PAY FOR PERKS": "0",
    # Hiring
    "HIRING BUILDERS": "0",
    "HIRING CODERS": "0",
    # Extended
    "DBSIZE": "0",
    "EXITS": "0",
    "EXTRA DESCRIPTIONS": "0",
    "MUDPROGS": "0",
    "MUDTRIGS": "0",
    "RESETS": "0",
    # Game
    "ADULT MATERIAL": "0",
    "MULTICLASSING": "0",
    "NEWBIE FRIENDLY": "0",
    "PLAYER CITIES": "0",
    "PLAYER CLANS": "0",
    "PLAYER CRAFTING": "0",
    "PLAYER GUILDS": "0",
    "EQUIPMENT SYSTEM": "Level",
    "MULTIPLAYING": "Restricted",
    "PLAYERKILLING": "None",
    "QUEST SYSTEM": "Integrated",
    "ROLEPLAYING": "Encouraged",
    "TRAINING SYSTEM": "Level",
    "WORLD ORIGINALITY": "All Original",
}
