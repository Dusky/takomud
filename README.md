# Takomud

A horror MUD built on [Evennia](https://www.evennia.com/) (Python 3 / Django). The world
is generated autonomously by the Anthropic API — rooms, NPCs, mobs, quests, lore, and bosses
are written by Claude and reviewed by a two-stage AI pipeline before being committed to the
database. No room is authored by hand after the starting zone.

**Genre:** Cosmic / psychological horror  
**Tech:** Evennia 4.x, Python 3.11+, Anthropic claude-sonnet-4-6  
**Protocol:** Telnet (port 4000) + web client (port 4001)

---

## Setup

```bash
# 1. Clone and create virtualenv
git clone <repo-url> takomud
cd takomud
python3 -m venv .venv
source .venv/bin/activate
pip install evennia anthropic

# 2. Initialize the database
.venv/bin/evennia migrate

# 3. Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Start
.venv/bin/evennia start
# Creates a superuser on first run — follow the prompt.
```

Connect via any MUD client at `localhost:4000`, or open `http://localhost:4001` in a browser.

---

## Developer workflow

```bash
# After code changes (no restart needed for most changes)
.venv/bin/evennia reload

# Full restart (clears non-persistent scripts)
.venv/bin/evennia restart

# Django shell (server can be running or stopped)
.venv/bin/evennia shell

# Run generator standalone (server can be running or stopped)
python world/generator.py --cycles 1

# Syntax check all game files
python -m py_compile typeclasses/characters.py typeclasses/rooms.py \
  typeclasses/items.py typeclasses/npcs.py typeclasses/scripts.py typeclasses/exits.py \
  commands/horror.py commands/combat.py commands/inventory.py \
  commands/quest.py commands/economy.py commands/admin.py \
  commands/default_cmdsets.py world/generator.py world/quest_system.py
```

---

## Project layout

```
takomud/
├── typeclasses/         Core game objects
│   ├── characters.py    Player character (HP, sanity, fear, XP, classes)
│   ├── rooms.py         Room (darkness, atmosphere, hazards, level gating)
│   ├── items.py         Item, Container, LoreDocument
│   ├── npcs.py          NPC (dialogue/shop), Mob (combat/loot), Boss (phases)
│   ├── scripts.py       All timed scripts (14 total)
│   └── exits.py         Exit with lock/key support
├── commands/
│   ├── horror.py        Most player commands + all builder commands
│   ├── combat.py        attack, stop, flee, consider
│   ├── inventory.py     inv, equip, use, drop, give, rest, inspect, containers
│   ├── quest.py         quest, talk, abandon
│   ├── economy.py       browse, buy, sell
│   ├── admin.py         generate, genstart, genquest, genregion, where
│   └── default_cmdsets.py  Command registration
├── world/
│   ├── generator.py     Autonomous world generator (Claude API)
│   ├── quest_system.py  Quest objective checking and completion
│   ├── quest_registry.py In-memory+disk quest store
│   ├── world_bible.py   Regions, factions, classes, generation prompts
│   ├── batch_build.py   Manual room builder (for The Threshold)
│   ├── help_entries.py  In-game help text for all custom systems
│   └── world_state.json Generator state (do not edit manually)
├── server/conf/
│   ├── settings.py      Evennia configuration
│   ├── at_server_startstop.py  Boot hooks (quest reload, RespawnScript)
│   └── at_initial_setup.py     First-boot: generate starting zone
├── CLAUDE.md            Full agent reference — read this before editing code
└── .claude/commands/    Slash commands for Claude Code sessions
```

---

## World generation

The generator (`world/generator.py`) calls Claude to produce full areas, then runs them
through two review passes before writing to the database. It can run while the server
is up — all database writes are thread-safe through Evennia's ORM.

### Quick generate

```bash
# CLI (server can be running or stopped)
python world/generator.py --cycles 1
python world/generator.py --cycles 0   # infinite

# In-game (Admin account)
generate 5          # 5 areas in background thread
genregion The Ashfields 6   # full region: 6 coordinated areas + faction questline
genquest hollow     # one faction questline only
genstart            # regenerate The Threshold starting zone
```

### Pipeline

```
Claude (raw area) → quality review → consistency review → write to DB
```

Every area includes: 4–6 rooms, 1–3 NPCs, 2–4 mobs, 0–1 boss, 4–8 items,
1–2 lore documents, 1–2 quests, 0–2 world events.

### State file

`world/world_state.json` tracks everything generated. Back it up before clearing the DB.

---

## Character classes

| Class | Passive | Active (ability command) |
|-------|---------|--------------------------|
| survivor | Survive one killing blow/hour at 1 HP | Surge: -20 HP for +5 attack 30s |
| scholar | Lore/read costs no sanity | Analyze: reveal target stats |
| cultist | Hollow mobs don't aggro | Commune: extract lore, clear aggro |
| hunter | Sense mobs in adjacent rooms | Trap: stun next mob entering room |
| vagrant | +2 XP per new room discovered | Blink: teleport to any visited room |

---

## Stats and systems

| Stat | Range | Effect |
|------|-------|--------|
| HP | 0–max | 0 = death |
| Sanity | 0–max | ≤50 hallucination warnings, ≤25 effects start, 0 = psychotic break |
| Fear | 0–100 | ≥40 -2 attack, ≥75 -4 attack + freeze chance, 100 = panic flee |
| Gold | 0+ | Currency; half dropped on death |
| XP/Level | 10 levels | Level-up: +10 HP max, +5 San max, +1 attack bonus |

**Death:** drops half gold in room, warps to start, HP→50%, Sanity-10, Fear+20.

**Status effects:** bleed (HP drain), poison (HP+San drain), stun (skip attacks) — applied by mob attacks at 35% chance.

---

## Factions

| Key | Description |
|-----|-------------|
| remnants | Survivors of the old world, wary and pragmatic |
| hollow | Transformed cultists, inhuman but structured |
| scholars | Seekers of forbidden knowledge |
| wardens | Authoritarian order keepers |
| unspoken | Those who made bargains with the dark |

Reputation range: -100 to +100 per faction. NPCs can gate dialogue behind minimum rep.
Killing a faction member: -5 rep with that faction, +2 with their enemies.

---

## Slash commands (Claude Code)

When working in this repo with Claude Code, these `/commands` are available:

| Command | What it does |
|---------|--------------|
| `/mud-status` | Check server state, world counts, active scripts, recent errors |
| `/worldgen` | Generate one area via the CLI |
| `/autogen` | Run continuous generation with options |
| `/genregion` | *(see genregion help)* |
| `/add-feature` | Add a new command, script, or system |
| `/remove-feature` | Safely remove a command, script, or attribute |
| `/create-room` | Scaffold a hand-authored room |
| `/write-lore` | Write or revise lore text |
| `/verify-mechanic` | Trace a mechanic's code path and find gaps |
| `/debug` | Diagnose a broken mechanic from an error or symptom |
| `/run` | Start the server and connect |

Full agent reference: see `CLAUDE.md`.

---

## Design principles

Every mechanic has a **cost or a risk**. Nothing is free.

- Exploration degrades sanity
- Light is finite (fuel burns every minute)
- Resting can be interrupted by combat
- Death has gold and sanity penalties
- Class abilities cost HP, sanity, or fear
- No passive regeneration without resting
- No safe zones (The Threshold is merely less dangerous)

Horror tone: implication over statement, cost over reward, atmosphere over exposition.
