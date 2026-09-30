# 24 — Mirage Preview

| Category | Points | Difficulty |
|----------|--------|------------|
| Web      | 350    | Hard       |

## Description

**Mirage Preview** fetches any link you paste and shows you what is there, so you
can preview a page before sharing it. It only allows *public* web addresses.

Launch your instance. There is an internal control panel the preview service can
reach but you cannot. Reach it anyway.

Your instance and its flag are unique to your team.

## Access

This challenge runs as a **live website**. Open the challenge on the platform,
click **Launch an instance**, and open the link it gives you.

## Hints

<details>
<summary>Hint 1 (free)</summary>

The server fetches the URL, not your browser. That means it can reach services
that only listen on the server itself (loopback). There is an admin panel on a
port other than 80.
</details>

<details>
<summary>Hint 2</summary>

The site refuses the words `localhost` and `127.0.0.1`, but loopback has other
spellings that mean the same address (for example `0.0.0.0` or the decimal form
`2130706433`). The admin panel serves the flag at `/flag`.
</details>

## Flag Format

`TAIBAH{...}`
