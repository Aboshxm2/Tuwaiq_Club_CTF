# 21 — Caravan Ledger (deployable)

A SQL injection warm-up. Each team gets its own caravan-manifest search page.

- **Type:** `dynamic_docker` (ctfd-whale), HTTP redirect, port 80.
- **Flag:** injected by whale as the `FLAG` env var; stored in a `secrets` table
  that the manifest page never queries directly.
- **Vulnerability:** the search term is concatenated into
  `SELECT name, cargo FROM caravans WHERE name LIKE '%<input>%'`. SQL errors are
  shown on the page (error-based), and the query has two output columns.
- **Intended solve (organizer note):** enumerate with `sqlite_master`, then read
  the flag with a UNION:
  ```
  ' UNION SELECT label, secret FROM secrets --
  ```
  (URL: `/?q=' UNION SELECT label, secret FROM secrets --`). The flag appears in
  the `cargo` column.

The database is rebuilt in memory on every request, so nothing a team injects
persists or leaks another team's flag.

## Local test

```sh
docker build -t taibah-ctf/21-caravan-ledger:latest .
docker run --rm -p 8021:80 -e FLAG='TAIBAH{test}' taibah-ctf/21-caravan-ledger:latest
# then open http://localhost:8021/ and try the UNION above
```
