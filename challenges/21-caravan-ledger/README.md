# 21 — Caravan Ledger

| Category | Points | Difficulty |
|----------|--------|------------|
| Web      | 250    | Medium     |

## Description

The **Oasis Caravan Ledger** lets anyone search the public caravan manifest. The
same database also holds a private table the search page was never meant to
reach.

Launch your instance and make the search return more than the caravans it was
built to show.

Your instance and its flag are unique to your team.

## Access

This challenge runs as a **live website**. Open the challenge on the platform,
click **Launch an instance**, and open the link it gives you. A copied flag from
another team's instance will not score.

## Hints

<details>
<summary>Hint 1 (free)</summary>

Put a single quote `'` in the search box and read the error the page shows. What
does that tell you about how the search is built?
</details>

<details>
<summary>Hint 2</summary>

The results table has **two** columns. A `UNION SELECT` of two columns from
another table will be shown right next to the caravans. List the tables first
with `sqlite_master`.
</details>

## Flag Format

`TAIBAH{...}`
