# Taibah CTF platform

CTFd for the workshop, with five timed rounds on one scoreboard.

Players register and create a team of **1 to 5**. A person playing alone is a team of one. Each team launches an instance per challenge. The files, and the flag inside them, belong to that team. Submitting another team's flag does not score.

Solving earlier in the round earns extra points, up to 50% of the challenge value at the opening second and zero when the clock runs out. The listed challenge points never go down. Points from every round stay on the same scoreboard.

## Start it

From this directory:

```bash
export CTFD_ADMIN_PASSWORD='choose-a-long-password'
docker compose up -d --build
docker compose exec -e CTFD_ADMIN_PASSWORD="$CTFD_ADMIN_PASSWORD" ctfd \
  python /ctf/ctfd-platform/scripts/import_ctf.py
```

Open http://localhost:8000. Log in with `admin@taibah.local` / the password you set, unless you changed `CTFD_ADMIN_NAME` or `CTFD_ADMIN_EMAIL`.

Port 8000 is used because port 80 is often already taken. Put a reverse proxy in front of it if players should see a normal web address.

The admin navbar has a **Rounds** page:

| Button | What it does |
|--------|----------------|
| Start | Opens that round and hides every challenge that is not in it. The clock starts. |
| Freeze | Pauses the clock and rejects new submissions. Use this for prayer. |
| Resume | Continues the same round. Frozen time is not counted. |
| End | Hides the round's challenges. Scores stay. |

Only one round can be running or frozen at a time. The round ends by itself when the clock hits zero. Change the early-solve percent on the same page. The five rounds and their times come from `organizer/RUN_OF_SHOW.md`.

## What players do

1. Register.
2. Create a team, or join one with an invite. Maximum 5 members.
3. When a round is open, open a challenge and press **Launch instance**.
4. Download the zip and solve it. Submit the flag from those files.

A banner on the site shows the round name and the time left.

## Hints

The importer does not create hints and does not read the `## Hints` sections in the challenge READMEs. Those sections are organizer reference only.

CTFd's normal hint feature is on. A hint you add in the admin challenge editor is shown to players, and re-running the importer leaves it in place.

## Whale

[ctfd-whale](https://github.com/frankli0324/ctfd-whale) is installed and patched for this event:

- It runs on CTFd 3.8 (newer Docker and scheduler libraries).
- In teams mode the whole team shares the captain's container and the same dynamic flag.
- The launch cooldown is configurable (`whale:frequency_limit`, set to 5 seconds by the importer).

These 20 challenges are files, not network services, so launching a Docker container per team would not present them. The instance button builds the files inside CTFd instead: same idea (one private copy, one flag), without a container per team. Whale is there for a later challenge that really is a service. That path needs Docker Swarm and frp, which the upstream [install guide](https://github.com/frankli0324/ctfd-whale/blob/master/docs/install.md) describes. The CTFd container already has the Docker socket mounted, and it runs as root for that reason. Do not expose the admin account.

On the Whale settings page, a missing swarm or frp shows as a configuration error. The rounds and the file instances still work.

## Check it

After import, with round 1 still unstarted:

```bash
docker compose exec ctfd python /ctf/ctfd-platform/scripts/selftest.py
```

That starts round 1, solves one challenge as two different teams, checks the early-solve bonus, rejects a copied flag, freezes, and ends the round. Do not run it once the real event has started.
