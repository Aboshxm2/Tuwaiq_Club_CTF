# Deployable challenges

Most challenges in this event are **files**: the rounds plugin builds a per-team
zip and the player downloads it (see `ctfd-platform/plugins/ctfd-rounds`). A few
challenges are instead **live services**: each team clicks *Launch an instance*
and gets its own running container with a private URL. Those are the
"deployable" challenges, and they live here.

Deployable challenges use the [ctfd-whale](../plugins/ctfd-whale) plugin. Whale
starts one container per team, injects that team's unique flag, and routes a
link to it through frp.

Currently deployable (seven): **01 Inspect the Oasis**, **20 Token of Trust**,
**21 Caravan Ledger** (SQLi), **22 Sealed Scroll** (AES-CBC bit-flip),
**23 Desert Diagnostics** (command injection), **24 Mirage Preview** (SSRF), and
**25 Floodgate Override** (a `direct`/raw-TCP `pwn` challenge — the others are HTTP).

---

## How a deployable challenge works

1. The importer creates the challenge as type `dynamic_docker` (not a file
   challenge). It reads its settings from `catalog.DEPLOYABLE`.
2. When a team clicks *Launch an instance*, whale starts your image and passes
   the team's flag in the **`FLAG` environment variable**.
3. Your container must **bake that flag in at start-up** (into a page, a file, a
   response — wherever the challenge hides it) and listen on the port you
   declared.
4. Whale gives the team a link (an `http` subdomain, or a `host:port` for `tcp`).
5. The team solves it and submits the flag. Whale checks it against that team's
   container flag, so a flag copied from another team does not score.

Rounds still apply: a deployable challenge is hidden until its round opens,
submissions are blocked when the round is frozen or ended, and the early-solve
bonus is awarded on solve — the same as file challenges.

### The contract your image must follow

- Read the flag from `FLAG` at start-up. Don't hard-code a flag.
- Serve on one port, and declare it as `redirect_port`.
- Assume **one container per team across the whole event at a time**: whale
  replaces a team's container if they launch another challenge. A round may hold
  more than one deployable challenge (rounds 1 and 4 each have two), but a team
  can only run one at a time, so a player finishes and submits one live challenge
  before launching the next. That is fine for these challenges — the exploits
  re-run in seconds against the fresh instance — but design new ones the same way.
- Don't rely on writing to disk that must survive a restart. Renewal keeps the
  same container, but a fresh launch is a fresh container with a **new** flag.
- Keep the image small and give it a real memory/CPU ceiling (set in the catalog
  entry). Defaults here are 64–128 MB and 0.5 CPU.

---

## Add a new deployable challenge (checklist)

Say the new challenge slug is `21-sandy-shell`.

1. **Write the app.** Create `deploy/21-sandy-shell/` with a `Dockerfile` and
   your app. Read `FLAG` at start-up and embed it. Look at
   [`01-inspect-the-oasis`](01-inspect-the-oasis) (static site, flag baked by a
   shell entrypoint) and [`20-token-of-trust`](20-token-of-trust) (Flask app,
   flag returned by an endpoint) as templates.

2. **Register it** in `ctfd-platform/plugins/ctfd-rounds/catalog.py`:

   - Add a normal entry to `CHALLENGES` (name, category, points) if it isn't
     there already.
   - Add an entry to `DEPLOYABLE`:

     ```python
     "21-sandy-shell": {
         "image": "taibah-ctf/21-sandy-shell:latest",   # must match build.sh
         "redirect_type": "http",   # "http" for a web app, "direct" for raw TCP
         "redirect_port": 80,       # the port your app listens on in-container
         "memory_limit": "128m",
         "cpu_limit": 0.5,
         "description": "Markdown shown on the challenge page.",
     },
     ```

   - Add the slug to a round in `ROUNDS` (keep at most one deployable per round).

3. **Build the image** on the container host: `./deploy/build.sh`. It tags every
   folder as `taibah-ctf/<slug>:latest`.

4. **Re-run the importer:**

   ```sh
   docker compose exec -e CTFD_ADMIN_PASSWORD="$CTFD_ADMIN_PASSWORD" ctfd \
     python /ctf/ctfd-platform/scripts/import_ctf.py
   ```

That's it. No CTFd admin clicking, no per-challenge flag setup: the importer
creates the `dynamic_docker` challenge, and whale generates the per-team flag.

> If a slug that used to be a **file** challenge becomes deployable (as 01 and 20
> did), the importer removes the old file challenge and recreates it as a
> container challenge. Do that before the event; it drops that challenge's old
> solves.

### `http` vs `direct`

- `http` — a web challenge. Whale exposes it as `http://<id>.<suffix>/`. Use for
  anything a browser opens.
- `direct` — a raw TCP service (e.g. a `pwn` or netcat challenge). Whale exposes
  a `host:port`. Set `redirect_port` to the in-container port; whale picks the
  public port.

---

## Deploying the images on the swarm

Whale runs containers with **Docker Swarm** and routes them with **frp**. There
is no Kubernetes. Setting up the servers, swarm, frp, DNS, and the whale settings
is covered step by step in [**PRODUCTION.md**](../PRODUCTION.md).

What matters for the images:

- Run `build.sh` on **every node labelled for challenges** (the ones listed in
  whale's *Swarm Nodes* setting). The production setup makes those nodes use
  local images only, never Docker Hub, so an image that isn't built on a node
  can't start there.
- Rebuild on every such node after changing a challenge. New launches use the
  new image; running instances keep the old one.
- After adding a deployable challenge, run
  `docker compose exec ctfd python /ctf/ctfd-platform/scripts/whale_selftest.py`.
  It launches, opens, and stops an instance of every deployable challenge, and
  it fully solves all seven current ones (the HTTP challenges through Caddy, and
  the `direct` pwn challenge over a TCP socket to frps). For a new challenge it
  checks that the endpoint is reachable, unless you add a solver for it to that
  script (see `SOLVERS` there).

---

## Test one locally, without the platform

Challenge 01:

```sh
docker build -t taibah-ctf/01-inspect-the-oasis:latest deploy/01-inspect-the-oasis
docker run --rm -p 8080:80 -e FLAG='TAIBAH{demo_flag_01}' taibah-ctf/01-inspect-the-oasis:latest
# open http://localhost:8080/ and view source
```

Challenge 20:

```sh
docker build -t taibah-ctf/20-token-of-trust:latest deploy/20-token-of-trust
docker run --rm -p 8020:80 -e FLAG='TAIBAH{demo_flag_20}' taibah-ctf/20-token-of-trust:latest
# open http://localhost:8020/
```
