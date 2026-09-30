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

This is the laptop setup: rounds and the file challenges work, but the deployable challenges (01, 20, 21, 22, 23, 24, 25) cannot be launched without a swarm and frp. **For the event, deploy on servers with [PRODUCTION.md](PRODUCTION.md).** It adds HTTPS, per-team challenge containers, and an end-to-end check.

The admin navbar has a **Rounds** page:

| Button | What it does |
|--------|----------------|
| Start | Opens that round and hides every challenge that is not in it. The clock starts. |
| Freeze | Pauses the clock and rejects new submissions. Use this for prayer. |
| Resume | Continues the same round. Frozen time is not counted. |
| End | Hides the round's challenges. Scores stay. |

Only one round can be running or frozen at a time. The round ends by itself when the clock hits zero. Change the early-solve percent on the same page. The five rounds and their times come from `organizer/RUN_OF_SHOW.md`.

The same page has a **Hide scoreboard** / **Show scoreboard** button. Hiding sets CTFd's score visibility to *hidden*: players see "Scores are currently hidden" on the scoreboard, and every team's score, place and solve counts disappear from the site and the API. Solves still count and rounds keep running. Admins still see the full scoreboard, so a projector logged in as admin keeps showing live scores. Showing it again brings back the visibility it had before, public unless you changed it under Admin → Config → Visibility.

## What players do

1. Register.
2. Create a team, or join one with an invite. Maximum 5 members.
3. When a round is open, open a challenge and press **Launch instance**.
4. Most challenges: download the zip and solve it. Submit the flag from those files.
   Live challenges (01, 20–24): the button starts a live site for the team instead. Open its link and solve it there. Challenge 25 starts a raw TCP service you reach with `nc`.

A banner on the site shows the round name and the time left.

## Theme

The site uses the Tuwaiq Club theme in [`themes/tuwaiq/`](themes/tuwaiq/). The importer selects it (`ctf_theme = tuwaiq`) and writes the home page, which uses the theme's `tw-*` classes.

The theme is a skin over CTFd's core theme. It overrides only `base.html` and `components/navbar.html`, and adds `static/css/tuwaiq.css`. Every other template, and the compiled JS and CSS, come from core through `THEME_FALLBACK`, which is on by default. Do not turn it off.

Players can switch between light and dark with the navbar toggle. Uploading a logo under Admin → Config → Theme replaces the Tuwaiq Club logo in the navbar.

## Registration fields

The importer adds two required fields to the registration form:

- **University Major**: free text.
- **Level**: a dropdown with Beginner, Intermediate and Advanced. The `ctfd-registration` plugin draws the dropdown and rejects any other value.

Players cannot change these after registering. Admins see and edit them on each user's page (Admin → Users). Rename or delete them under Admin → Config → Custom Fields, but keep the name `Level` or the dropdown and the level leaderboards stop working.

## Level leaderboards

The scoreboard has a tab per level: All, Beginner, Intermediate and Advanced. The table and the graph both follow the selected tab. They are CTFd team brackets, which the importer creates.

A team is on the leaderboard of its most experienced member. One Advanced member makes the whole team Advanced. A team whose members have no level counts as Beginner. Players do not choose a bracket: the plugin hides CTFd's bracket picker on the new-team form and sets the bracket itself.

The bracket is recalculated after every change that can affect it: creating or joining a team, an admin removing a member, and an admin editing someone's Level. Players cannot leave a team by themselves in CTFd 3.8, so moving someone means an admin removes them under Admin → Teams. An admin's manual bracket choice on a team is overwritten at the next recalculation. Keep the bracket names `Beginner`, `Intermediate` and `Advanced`.

## Hints

The importer does not create hints and does not read the `## Hints` sections in the challenge READMEs. Those sections are organizer reference only.

CTFd's normal hint feature is on. A hint you add in the admin challenge editor is shown to players, and re-running the importer leaves it in place.

## Whale

[ctfd-whale](https://github.com/frankli0324/ctfd-whale) is installed and patched for this event:

- It runs on CTFd 3.8 (newer Docker and scheduler libraries).
- In teams mode the whole team shares the captain's container and the same dynamic flag.
- The launch cooldown is configurable (`whale:frequency_limit`, set to 5 seconds by the importer).

Most challenges are files, so their instance button builds a per-team zip inside CTFd, with no container. Seven challenges (01, 20, 21, 22, 23, 24 and 25) are live services: whale starts a container per team and routes it through frp — an HTTP link for all but 25, which is a raw TCP (`direct`) service. Those images are in [`deploy/`](deploy/README.md). Running them needs Docker Swarm, frp and wildcard DNS; [PRODUCTION.md](PRODUCTION.md) sets all of that up. The CTFd container has the Docker socket mounted, and it runs as root for that reason. Do not expose the admin account.

On the Whale settings page, a missing swarm or frp shows as a configuration error. The rounds and the file instances still work.

## Check it

After import, with round 1 still unstarted:

```bash
docker compose exec ctfd python /ctf/ctfd-platform/scripts/selftest.py
```

That starts round 1, solves one challenge as two different teams, checks the early-solve bonus, rejects a copied flag, freezes, and ends the round. Do not run it once the real event has started.
