# Production deployment

This guide puts the platform on real servers for the event: CTFd with rounds, and a live container per team for the deployable challenges (01 Inspect the Oasis, 20 Token of Trust).

[README.md](README.md) covers running CTFd on a laptop. Use this guide for anything players will connect to.

---

## How it fits together

```
                       players
                          │ 80 / 443
              ┌───────────▼───────────── CTFd server (swarm manager) ──────────────┐
              │  Caddy ── ctf.example.edu ──────────▶ CTFd ──▶ Redis               │
              │    │                                   │ docker.sock (whale)       │
              │    └── *.chal.example.edu ─▶ frps      │ frp admin API             │
              │                               ▲        ▼                           │
              │                               └──── frpc                           │
              └──────────────────────────────────────┬─────────────────────────────┘
                                                     │ "challenges" overlay network
              ┌──────────────────────────────────────▼──── challenge server ───────┐
              │   team A container    team B container    team C container  ...     │
              └─────────────────────────────────────────────────────────────────────┘
```

When a team presses **Launch an instance**:

1. whale (a CTFd plugin) creates a swarm service from the challenge image and puts the team's flag in `FLAG`. The swarm starts it on a node labelled `name=linux-1`.
2. whale rewrites frpc's config with one route per running instance: `<uuid>.chal.example.edu` → that container.
3. The player opens `http://<uuid>.chal.example.edu/`. Caddy passes it to frps, frps to frpc, and frpc to the container over the overlay network.

The challenge server needs no public ports. All player traffic enters through Caddy on the CTFd server.

The added pieces live in [`docker-compose.production.yml`](docker-compose.production.yml), [`conf/`](conf) and [`.env.example`](.env.example).

---

## 1. Pick a layout

| Layout | When |
|--------|------|
| **Two servers:** a CTFd server (swarm manager) and a challenge server (swarm worker) | Recommended. Team containers never run next to CTFd. |
| **One server:** everything on one machine | Fine for a small event, or if you only have one machine. Skip the worker steps below. |

Sizing: each team has at most one instance running at a time, even in the two rounds that hold two deployable challenges (whale replaces a team's container when they launch another). The images cap at 64–128 MB and 0.5 CPU each. These are ceilings, not reservations; idle, they use much less. Plan the challenge server for **teams × 128 MB** plus about 1 GB for the OS. With 60 teams, that is about 8.5 GB. A server with 2–4 vCPUs is enough. The CTFd server is fine with 2 vCPUs and 4 GB.

Both servers: Ubuntu 22.04 or 24.04 (any Linux with Docker works), and **Docker Engine 25 or newer** with the Compose plugin **2.24 or newer**. Install Docker with:

```bash
curl -fsSL https://get.docker.com | sh
docker version && docker compose version
```

Clone this repository on the CTFd server and on every challenge server.

---

## 2. DNS

You need two records, and **both point at the CTFd server**. frps runs there, not on the challenge server.

| Record | Type | Value |
|--------|------|-------|
| `ctf.example.edu` | A | CTFd server's public IP |
| `*.chal.example.edu` | A | CTFd server's public IP (wildcard) |

- `chal.example.edu` becomes `CHALLENGE_DOMAIN` in `.env`. Each instance gets one subdomain under it.
- **HSTS:** whale always links instances over plain `http://`. If the parent domain sends `Strict-Transport-Security` with `includeSubDomains` (many university domains do), browsers will force the challenge links to https and they will fail. Test with `curl -sI https://example.edu | grep -i strict`. If `includeSubDomains` is there, use a domain that isn't covered for `CHALLENGE_DOMAIN`.
- **No domain?** Use [sslip.io](https://sslip.io), which resolves any name containing an IP to that IP. With server IP `203.0.113.10`, use `CTF_SITE=http://ctf.203.0.113.10.sslip.io` and `CHALLENGE_DOMAIN=chal.203.0.113.10.sslip.io`. It needs no setup, but players' DNS must reach the internet. Some campus resolvers refuse to return private IPs (`10.x`, `192.168.x`), so test from a player's network first.

---

## 3. Firewall

| Port | On | Open to | Why |
|------|----|---------|-----|
| 80/tcp, 443/tcp | CTFd server | players | Caddy: the site and every team instance |
| 10000–10099/tcp | CTFd server | players | `direct` (raw TCP) challenges. Used by challenge 25 (Floodgate Override); whale hands each instance a port in this range. |
| 2377/tcp | CTFd server | challenge server only | swarm management |
| 7946/tcp+udp | both | the other server only | swarm node gossip |
| 4789/udp | both | the other server only | overlay network traffic (VXLAN) |
| 22/tcp | both | organizers | SSH |

Never open 2377, 7946 or 4789 to the internet. Overlay traffic is not encrypted. That is fine when the two servers share a private network (the same LAN or VPC). If traffic between them crosses the internet, put them on a VPN such as WireGuard and use the VPN addresses for the swarm.

> `ufw` does not filter ports that Docker publishes for containers. The only published ports are Caddy's 80/443 and frps's 10000–10099, both intentional. Nothing else in the stack is published. CTFd's port 8000 is closed in production.

---

## 4. Create the swarm

On the **CTFd server**:

```bash
docker swarm init --advertise-addr <CTFd server private IP>
```

It prints a `docker swarm join --token ...` command.

**Two servers:** run that join command on the challenge server. Then, back on the CTFd server, label the challenge server so whale starts team containers there and only there:

```bash
docker node ls                                   # find the challenge server's hostname
docker node update --label-add name=linux-1 <challenge-server-hostname>
```

**One server:** label the CTFd server itself:

```bash
docker node update --label-add name=linux-1 $(docker node ls -q)
```

More challenge servers? Join each one and label them `linux-2`, `linux-3`, and so on. whale picks one at random for each launch.

---

## 5. Use local images only on challenge servers

By default, a swarm node tries to **pull the image from Docker Hub on every launch**, even when the image exists locally. It falls back to the local copy only if the pull fails. Nobody owns the `taibah-ctf` name on Docker Hub. If someone registers it and pushes an image with the same name, the swarm would run their image for every team. Every launch also wastes time on the failed pull.

Turn the pull off on **every labelled node** (the challenge server, or the single server). This restarts Docker, so do it before starting the platform:

```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/offline-images.conf >/dev/null <<'EOF'
[Service]
Environment=DOCKER_SERVICE_PREFER_OFFLINE_IMAGE=1
EOF
sudo systemctl daemon-reload && sudo systemctl restart docker
```

After this, a node only runs images it already has, so step 6 must be done on each of them.

---

## 6. Build the challenge images on every challenge server

On each labelled node:

```bash
./ctfd-platform/deploy/build.sh
docker image ls 'taibah-ctf/*'      # expect 01-inspect-the-oasis and 20-token-of-trust
```

After you change anything in `deploy/<slug>/`, run `build.sh` again on every labelled node. New launches use the new image. Running instances keep the old one until the team relaunches.

---

## 7. Configure and start the platform

On the **CTFd server**:

```bash
cd ctfd-platform
cp .env.example .env
nano .env        # set CTF_SITE and CHALLENGE_DOMAIN
```

`.env` also sets `COMPOSE_FILE`, so every plain `docker compose` command in this folder loads both `docker-compose.yml` and `docker-compose.production.yml`. Run all commands from `ctfd-platform/`.

```bash
docker compose up -d --build
docker compose ps                                   # caddy, ctfd, cache, frps, frpc: all running
docker compose logs frpc | grep 'login to server success'
```

Import the challenges. This also creates the admin account the first time:

```bash
export CTFD_ADMIN_PASSWORD='choose-a-long-password'
docker compose exec -e CTFD_ADMIN_PASSWORD="$CTFD_ADMIN_PASSWORD" ctfd \
  python /ctf/ctfd-platform/scripts/import_ctf.py
```

Open `https://ctf.example.edu` and log in as `admin@taibah.local` with that password. When `CTF_SITE` is a bare hostname, Caddy gets the HTTPS certificate on its own. That requires ports 80 and 443 to be reachable from the internet. If the server is only reachable inside the campus network, set `CTF_SITE=http://ctf.example.edu` and use plain http.

The CTFd container holds the Docker socket of the swarm manager, so the admin account can effectively control the servers. Use a long password and don't share the admin login.

---

## 8. Whale settings

Open `https://ctf.example.edu/plugins/ctfd-whale/admin/settings` and set:

| Tab | Setting | Value |
|-----|---------|-------|
| Docker | API URL | `unix:///var/run/docker.sock` (default; keep) |
| Docker | Swarm Nodes | `linux-1`, or every label, comma-separated: `linux-1,linux-2` |
| Docker | Auto Connect Network | `taibah-ctf_challenges` |
| Router | Router type | `frp` |
| Router | API URL | `http://frpc:7400` (default; keep) |
| Router | Http Domain Suffix | your `CHALLENGE_DOMAIN`, e.g. `chal.example.edu` |
| Router | External Http Port | `80` |
| Router | Direct IP Address | the CTFd server's public IP or hostname. **Required for challenge 25** (Floodgate Override, `direct`/TCP): whale prints it to players as `nc <this> <port>`, so set it to the address players can reach, not an internal IP. |
| Router | Direct Minimum / Maximum Port | `10000` / `10099` (must match the published range and `allow_ports`; challenge 25 uses it) |
| Router | Frpc config template | leave empty. whale fills it from frpc on the first launch. |
| Limits | Max Container Count | at least the number of teams, plus a few for testing |
| Limits | Docker Container Timeout | `3600` (seconds; longer than any round) |
| Limits | Max Renewal Times | `5` (default) |
| Challenges | Flag Template | leave it. The importer sets it to `TAIBAH{...}`. |

Press **Submit** on each tab. The page lists configuration errors at the top: it checks the Docker API, that the swarm is up, and that frpc answers. It should list none.

---

## 9. Test before the event

**Automated end-to-end test.** For every deployable challenge, this launches an instance for a hidden throwaway team and opens it through Caddy the way a browser would. It then solves the challenge, checks that the flag it gets is the one whale will accept, stops the instance and deletes the team. It doesn't touch rounds, so it is safe to run at any time:

```bash
docker compose exec ctfd python /ctf/ctfd-platform/scripts/whale_selftest.py
```

Expected output:

```
PASS 01-inspect-the-oasis: solved via http://<uuid>.chal.example.edu/ after 7.1s
PASS 20-token-of-trust: solved via http://<uuid>.chal.example.edu/ after 6.7s
PASS 21-caravan-ledger: solved via http://<uuid>.chal.example.edu/ after 6.9s
PASS 22-sealed-scroll: solved via http://<uuid>.chal.example.edu/ after 6.8s
PASS 23-desert-diagnostics: solved via http://<uuid>.chal.example.edu/ after 7.0s
PASS 24-mirage-preview: solved via http://<uuid>.chal.example.edu/ after 6.9s
PASS 25-floodgate-override: solved via frps:10000 after 6.5s
PASS all deployable challenges launch, route, solve, and stop
```

**From a player's network.** The test above runs inside the server, so it doesn't check DNS or the firewall. From a laptop on the network players will use (campus Wi-Fi, not the server room):

```bash
curl -sI https://ctf.example.edu | head -1               # HTTP/2 200 (or HTTP/1.1 200 over http)
curl -s  http://anything.chal.example.edu/ -o /dev/null -w '%{http_code}\n'   # 404 from frps = routing works
```

`404` is the right answer for a made-up subdomain. It means DNS, the firewall, Caddy and frps all work. A timeout or `Could not resolve host` means DNS or the firewall is wrong.

**Rehearsal.** Also run the checklist in [`organizer/RUN_OF_SHOW.md`](../organizer/RUN_OF_SHOW.md) with a test team in a browser: launch 01, open the link, submit the flag.

---

## During the event

- **Running instances:** `docker service ls` shows one service per running instance. The admin page `/plugins/ctfd-whale/admin/containers` lists them by team, with buttons to renew or destroy.
- **One instance per team.** Launching a challenge replaces that team's previous instance. Rounds 1 and 4 each have **two** deployable challenges, so a team there can only run one at a time; relaunching the other is instant and gives a fresh flag. Brief players to finish and submit one live challenge before launching the next in the same round. Rounds 2, 3 and 5 have one deployable each.
- **Lifetime:** an instance stops after *Docker Container Timeout*. Teams can press *Renew* up to *Max Renewal Times*. After it stops, the team launches again and gets a **new** flag, and the old one no longer scores.
- **A link that 404s for the first few seconds is normal.** The container is still starting (about 4–7 seconds in testing).
- **Logs:** `docker compose logs -f ctfd frpc`.

---

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `docker compose up` fails with `network taibah-ctf_challenges not found`, or `This node is not a swarm manager` | The swarm isn't initialized on this server. Do step 4, then run `docker compose up -d` again. |
| `Pool overlaps with other one on this address space` | Another network on the server already uses `172.30.254.0/28`. Pick a free /28 and change it in three places: `docker-compose.production.yml` (the subnet and frpc's `ipv4_address`) and `conf/frp/frpc.ini` (`admin_addr`). Then follow *Changing the frp config* below. |
| Whale settings: `Docker swarm not available` | Same as the first row. |
| Whale settings: `Unable to access frpc admin api` | frpc isn't running. Check `docker compose ps` and `docker compose logs frpc`. |
| Player sees "Container creation failed" | Look for the traceback in `docker compose logs ctfd`. Usually *Auto Connect Network* is not `taibah-ctf_challenges`, or *Swarm Nodes* names a label that no node has (`docker node inspect <node> --format '{{.Spec.Labels}}'`). |
| Link stays 404 or 502 | `docker service ps <service> --no-trunc`. The service name is in `docker service ls`. `No such image` means the image isn't built on that node: run step 6 there. |
| Link doesn't resolve | Wildcard DNS for `*.CHALLENGE_DOMAIN` is missing (step 2). |
| Challenge links are forced to https and fail | HSTS on the parent domain (step 2). |

### Changing the frp config

whale reads `conf/frp/frpc.ini` once and saves it as *Frpc config template*. From then on, whale writes frpc's live config itself, and that config is kept in the `frpc-data` volume. So editing `frpc.ini` alone changes nothing. To apply a change:

```bash
docker compose rm -sf frpc
docker volume rm taibah-ctf_frpc-data
docker compose up -d
```

Then clear *Frpc config template* on the whale settings page and press Submit. Running instances lose their routes. Destroy them from the admin containers page and let teams relaunch. Do this before the event.

---

## Security notes

- Team containers sit on an internal network. They have no internet and can't reach CTFd, Redis, frps, or frpc's admin API. This was tested from inside a running instance.
- Team containers **can** reach each other on that network. That's harmless for 01 and 20, which give no code execution. If you add a challenge that gives players a shell, use whale's grouped containers, which give each instance its own network. See [the whale docs](plugins/ctfd-whale/docs/install.md#grouped-containers).
- Only admins should reach the whale settings page. Upstream notes a template-injection risk there.
- Back up the CTFd database before the event and after it: *Admin Panel → Config → Backup*.
