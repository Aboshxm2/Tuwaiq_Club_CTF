# 20 — Token of Trust (deployable)

Live version of the JWT challenge. Each team gets its own portal.

- **Type:** `dynamic_docker` (ctfd-whale), HTTP redirect, port 80.
- **Flag:** injected by whale as the `FLAG` env var; returned by `/vault` to a
  valid administrator token.
- **Signing secret:** a random weak password chosen at start-up from
  `wordlist.txt`, which the portal itself leaks at `/backup/wordlist.txt`.
- **Intended solve (organizer note):** the portal issues a guest JWT signed with
  `HS256`. The secret is weak and present in the leaked wordlist, so it can be
  recovered offline (e.g. `hashcat -m 16500`, John, or a short script). With the
  secret, mint a token whose `role` is `admin` and send it to `/vault` (as
  `Authorization: Bearer <token>`, a `token` cookie, or `?token=`).

## Difference from the file-based challenge

The original (challenge 20 in `challenges/`) shipped `token.txt`, `wordlist.txt`,
`vault.enc`, and `vault_tool.py`, and the "vault" was an XOR-encrypted file. This
live version keeps the same core lesson (weak HS256 secret → forge an admin
token) but drops the XOR file step and serves the vault over HTTP instead. If you
run this version at the event, update `organizer/SOLUTIONS.md` accordingly.

## Local test

```sh
FLAG='TAIBAH{test}' PORT=8020 python3 app.py
# then open http://localhost:8020/
```
