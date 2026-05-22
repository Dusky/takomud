# /verify-mechanic

Verify that a specific game mechanic works correctly by reading the relevant code and tracing the full execution path.

## What to do

Ask the user which mechanic to verify (or infer from context). Then:

1. **Trace the code path** — read every file involved from trigger to resolution
2. **Check for gaps** — is anything called but not implemented? Any missing imports?
3. **Check registration** — is the command in `default_cmdsets.py`? Is the script started somewhere?
4. **Check data dependencies** — does the mechanic depend on DB attributes that are initialized in `at_object_creation`?
5. **Report clearly** — what works, what doesn't, what's missing

## Common things to verify

### Combat loop
- `CmdAttack` → sets `combat_target`, starts `PlayerCombatScript`, calls `_execute_player_attack`
- `PlayerCombatScript.at_repeat` → calls `_execute_player_attack` every 4s
- `_execute_player_attack` → rolls d20 + attack vs defense, calls `target.take_damage(dmg)`
- `Mob.take_damage` → calls `at_death(killer)` if HP ≤ 0
- `Mob.at_death` → grants XP via `adjust_xp`, gold via `gain_gold`, rep via `adjust_reputation`, queues respawn

### Quest completion
- `check_objective(char, type, target)` in `world/quest_system.py`
- For "kill": called from `_execute_player_attack` after `take_damage`
- For "collect": called from `Item.at_get` via `check_collect_trigger`
- For "visit": called from `Character.at_post_move`
- For "deliver": called from `CmdGive` after `obj.location = target`
- For "talk": called from `CmdTalk` after `at_talked_to`
- On completion: `complete_quest_reward` runs → `adjust_xp`, `gain_gold`, `adjust_reputation`

### Sanity system
- `adjust_sanity(amount)` in `characters.py`
- Thresholds: ≤50 → flavor msg; ≤25 → `_start_sanity_effects` (starts `SanityHallucinationScript`)
- 0 → `at_sanity_break` (reset to 10, +30 fear, stop hallucination script)

### Light / darkness
- `FuelDrainScript` attached to Character at creation; drains 1 fuel/min from `item.db.lit` items
- `Room.return_appearance` checks `_has_light(looker)` → if dark and no light, shows darkness only
- `Exit.at_traverse` → not blocked by darkness, but room appearance hides exits

### Respawn
- `Mob.at_death` → calls `_queue_respawn(self)` → finds global `respawn_manager` script
- `RespawnScript.enqueue(mob)` → serializes mob data, calculates `respawn_at`
- `RespawnScript.at_repeat` (30s) → checks queue, calls `_spawn(entry)` for ready entries
- `_spawn` → creates new Mob/Boss at original room, attaches WanderScript if needed

## Syntax check all files

```bash
python -c "
import ast, sys
files = [
    'typeclasses/characters.py', 'typeclasses/rooms.py', 'typeclasses/items.py',
    'typeclasses/npcs.py', 'typeclasses/scripts.py', 'typeclasses/exits.py',
    'commands/horror.py', 'commands/combat.py', 'commands/inventory.py',
    'commands/quest.py', 'commands/economy.py', 'commands/admin.py',
    'commands/default_cmdsets.py',
    'world/generator.py', 'world/quest_system.py', 'world/help_entries.py',
]
ok = True
for f in files:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'ERR {f}:{e.lineno}: {e.msg}')
        ok = False
if ok:
    print('All files OK')
"
```
