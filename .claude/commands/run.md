# /run

Start, stop, or restart the Takomud server and connect to verify things work.

## Check current state first

```bash
.venv/bin/evennia status
```

Look for: `Server running` / `Server stopped` / `Portal running`.

---

## Start the server

```bash
# Make sure the virtualenv is active and ANTHROPIC_API_KEY is set
export ANTHROPIC_API_KEY=sk-ant-...   # only needed if generating content

.venv/bin/evennia start
```

On first start, Evennia will prompt for a superuser username/password — enter them.
The server starts two processes: the Portal (handles connections) and the Server (game logic).

**Connect:**
- MUD client → `localhost:4000`  
- Browser → `http://localhost:4001` (web client)
- Login with the superuser account created on first start

---

## Reload after code changes

```bash
# Soft reload: reloads all Python code, keeps connections alive
.venv/bin/evennia reload
```

This covers most changes: new commands, new scripts, typeclass edits.
Does NOT reload: settings.py changes, new migrations, database schema changes.

For settings.py changes:
```bash
.venv/bin/evennia restart
```

---

## Stop

```bash
.venv/bin/evennia stop
```

---

## View logs

```bash
# Live server output
tail -f server/logs/server.log

# Errors only
grep -E "ERROR|WARNING|Traceback" server/logs/server.log | tail -30

# Portal log (connection issues)
tail -f server/logs/portal.log
```

---

## Verify a feature works in-game

After starting, log in as Admin and run the relevant command. Common test sequence:

```
# Check you can see the world
look

# Check stats
stat

# Test generation (requires ANTHROPIC_API_KEY)
generate 1

# Check scripts are running
@scripts

# Check world state
where
```

---

## Common startup issues

**"Address already in use"** — something else is on port 4000 or 4001.
```bash
lsof -i :4000
kill <PID>
```

**"No module named evennia"** — virtualenv not active.
```bash
source .venv/bin/activate
```

**"No such table: objects_objectdb"** — database not initialized.
```bash
.venv/bin/evennia migrate
```

**Server starts but no rooms** — first-boot generation may not have run.
```bash
# In-game as Admin:
genstart
```

**RespawnScript not running after restart** — `at_server_start()` handles this automatically.
Check `server/conf/at_server_startstop.py` if mobs aren't respawning after a restart.

---

## Running the generator standalone (server off or on)

```bash
# 1 area
python world/generator.py --cycles 1

# 5 areas, 10 second delay between
python world/generator.py --cycles 5 --delay 10

# Infinite, background
nohup python world/generator.py --cycles 0 --delay 20 > world/gen.log 2>&1 &
tail -f world/gen.log
```

The generator is thread-safe and can run while the server is up.
