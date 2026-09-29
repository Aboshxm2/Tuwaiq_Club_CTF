# 01 — Inspect the Oasis (deployable)

Live version of the "view source" web warm-up. Each team gets its own site.

- **Type:** `dynamic_docker` (ctfd-whale), HTTP redirect, port 80.
- **Flag:** injected by whale as the `FLAG` env var. `entrypoint.sh` splits it
  into three parts and drops one part into a comment in `index.html`,
  `style.css`, and `script.js`.
- **Intended solve:** open the instance URL, then View Source / open the `.css`
  and `.js` files and read the three commented parts in order.

The flag is unique per team, so nothing here reveals another team's flag.
