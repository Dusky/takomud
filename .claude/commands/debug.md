# /debug

Diagnose a broken or misbehaving mechanic in Takomud. Start from a symptom or error
and trace back to the root cause.

## What to do

Ask the user (or infer from context) one of:
- **Symptom** — "players can't use the ability command", "mobs aren't respawning", "quest never completes"
- **Error** — paste a Python traceback or server log error
- **Expected vs actual** — "attack should deal damage but nothing happens"

Then follow this diagnosis flow:

---

## Step 1 — Check the server log

```bash
# Last 50 lines of errors/warnings
grep -E "ERROR|WARNING|Traceback|Exception" server/logs/server.log | tail -50

# Full last 100 lines
tail -100 server/logs/server.log
```

Look for: tracebacks, import errors, missing attribute errors (`AttributeError: db`), name errors.

---

## Step 2 — Syntax check everything

```bash
python -c "
import ast, sys
files = [
    'typeclasses/characters.py', 'typeclasses/rooms.py', 'typeclasses/items.py',
    'typeclasses/npcs.py', 'typeclasses/scripts.py', 'typeclasses/exits.py',
    'commands/horror.py', 'commands/combat.py', 'commands/inventory.py',
    'commands/quest.py', 'commands/economy.py', 'commands/admin.py',
    'commands/default_cmdsets.py',
    'world/generator.py', 'world/quest_system.py', 'world/quest_registry.py',
    'world/help_entries.py', 'world/world_bible.py',
]
ok = True
for f in files:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'SYNTAX ERR {f}:{e.lineno}: {e.msg}')
        ok = False
if ok:
    print('All files OK')
"
```

---

## Step 3 — Trace the mechanic's code path

For each broken feature, here is the canonical code path:

### Combat
```
CmdAttack.func()                           commands/combat.py
  → char.db.combat_target = mob
  → char.scripts.add(PlayerCombatScript)   typeclasses/scripts.py
     PlayerCombatScript.at_repeat()
       → _execute_player_attack(char, mob) commands/combat.py
          → rolls d20 + attack_bonus vs mob.db.defense
          → mob.take_damage(dmg, attacker=char)
             → mob.db.hp -= dmg
             → mob.at_death(killer=char) if hp <= 0
                → killer.adjust_xp(xp)
                → killer.gain_gold(gold)
                → killer.adjust_reputation(faction, -5)
                → _queue_respawn(self) → RespawnScript.enqueue()
                → check_objective(char, "kill", mob.key)
```

### Quest completion
```
check_objective(char, type, target)        world/quest_system.py
  → iterates char.db.quests
  → finds matching stage objective
  → increments current count
  → if count >= target count → advance_quest_stage()
     → if final stage → complete_quest_reward()
        → adjust_xp / gain_gold / adjust_reputation / spawn items

Trigger points:
  "kill"    → _execute_player_attack (combat.py) after take_damage
  "collect" → Item.at_get → check_collect_trigger (items.py)
  "visit"   → Character.at_post_move (characters.py)
  "deliver" → CmdGive after moving item to NPC location (inventory.py)
  "talk"    → CmdTalk after at_talked_to (quest.py)
```

### Sanity
```
adjust_sanity(amount)                      typeclasses/characters.py
  → clamps to [0, sanity_max]
  → ≤50 threshold → prints edge-of-vision message
  → ≤25 threshold → _start_sanity_effects() → starts SanityHallucinationScript
  → ==0 → at_sanity_break() → resets to 10, +30 fear, stops hallucination script
```

### Fear
```
adjust_fear(amount)                        typeclasses/characters.py
  → clamps to [0, 100]
  → ≥40 threshold → dread message
  → ≥75 threshold → panic message
  → ==100 → _fear_panic() → random flee or freeze, reset to 80
```

### Light / dark rooms
```
Room.return_appearance(looker)             typeclasses/rooms.py
  → calls _has_light(looker)
     → checks looker.contents for item where db.is_light_source and db.lit
  → if room.db.dark and no light → returns darkness-only string
  → else → normal appearance including exits

FuelDrainScript.at_repeat()               typeclasses/scripts.py
  → attached to Character at creation
  → every 60s: for each lit light source in char.contents, db.fuel -= 1
  → fuel ≤ 0 → item.db.lit = False, item.db.is_light_source = False
```

### Respawn
```
Mob.at_death(killer)                       typeclasses/npcs.py
  → _queue_respawn(self) → finds global "respawn_manager" script
     → RespawnScript.enqueue(mob)          typeclasses/scripts.py
        → serializes mob.typeclass_path, stats, location, loot_table etc.
        → calculates respawn_at = now + respawn_delay

RespawnScript.at_repeat()  (30s tick)
  → for each entry where now >= respawn_at:
     → _spawn(entry) → evennia.create_object(typeclass, location=room, ...)
```

### Class abilities
```
CmdAbility.func()                          commands/horror.py
  → reads char.db.char_class
  → dispatches to _do_survivor / _do_scholar / _do_cultist / _do_hunter / _do_vagrant

survivor → SurgeScript: +5 attack for 30s (start_delay=True so doesn't fire immediately)
scholar  → prints mob stats if combat_target present
cultist  → Commune: extract lore from Hollow mob, clear its aggro
hunter   → HunterTrapScript on room: stuns next mob that enters
vagrant  → Blink: move to random room in discovered_rooms, -20 sanity
```

### Merchant / shop
```
CmdBrowse.func()                           commands/economy.py
  → finds NPC with db.shop list in room
  → for each proto_key in shop: check shop_stock[proto_key] (qty or -1=unlimited)
  → shows items with qty > 0 or unlimited

CmdBuy.func()
  → calls spawner.spawn(proto_key) to create item
  → moves item to buyer
  → decrements shop_stock if qty != -1

MerchantRestockScript.at_repeat() (hourly) typeclasses/scripts.py
  → for each key in npc.db.restock_list: shop_stock[key] = original qty
```

---

## Step 4 — Check registration

For broken commands:
```bash
grep -n "CmdFoo\|add(Cmd" commands/default_cmdsets.py
```

For broken scripts — check whether they were started:
```bash
# In-game (Admin): @scripts to list all running scripts
# Or in shell:
.venv/bin/evennia shell -c "
import evennia
for s in evennia.search_script(''):
    print(s.key, '— interval:', s.interval, '— persistent:', s.persistent)
"
```

For broken quest:
```bash
python -c "
from world import quest_registry
quest_registry.load_all()
import json
print(json.dumps(list(quest_registry.QUESTS.keys()), indent=2))
"
```

---

## Step 5 — Check attribute initialization

If you see `AttributeError: 'NoneType' has no attribute ...` on a db attribute:
- The attribute wasn't initialized in `at_object_creation`
- Or the object predates the attribute being added

Fix: add a `or default` guard in code: `self.db.foo or 0`. Then update `at_object_creation`
so future objects have the attribute from creation.

---

## Step 6 — Test in the shell

```bash
.venv/bin/evennia shell -c "
import evennia
from typeclasses.characters import Character
chars = evennia.search_object('', typeclass=Character)
if chars:
    c = chars[0]
    print('HP:', c.db.hp, '/', c.db.hp_max)
    print('Sanity:', c.db.sanity)
    print('Class:', c.db.char_class)
    print('Scripts:', [s.key for s in c.scripts.all()])
"
```

---

## Common root causes

| Symptom | Likely cause |
|---------|-------------|
| Command does nothing | Not registered in `default_cmdsets.py` |
| Script fires immediately | `start_delay = False` (should be `True` for delayed effects) |
| Quest never progresses | `check_objective` not called from the right trigger point |
| DB attribute None | Not set in `at_object_creation`; add `or default` guard |
| Mobs don't respawn | `RespawnScript` not running — check `at_server_start()` |
| Quests lost on restart | `quest_registry.load_all()` not called in `at_server_start()` |
| NPC won't speak | `min_reputation` check failing; check faction and rep value |
| Light not draining | `FuelDrainScript` not attached to character at creation |
| Combat never ends | `combat_target` not cleared in `at_death` or `CmdStop` |
