# 23 — Desert Diagnostics

| Category | Points | Difficulty  |
|----------|--------|-------------|
| Web      | 300    | Medium-Hard |

## Description

The **Oasis Network Diagnostics** page lets relay operators ping a host to check
that it is reachable. The check runs on the server.

Launch your instance and get it to run a little more than a ping. The flag is in
a file on the server.

Your instance and its flag are unique to your team.

## Access

This challenge runs as a **live website**. Open the challenge on the platform,
click **Launch an instance**, and open the link it gives you.

## Hints

<details>
<summary>Hint 1 (free)</summary>

The host you type is placed straight onto a shell command line. If you can add a
second command, its output comes back with the ping results.
</details>

<details>
<summary>Hint 2</summary>

Spaces, `;` and `&` are rejected, but a shell has other ways to make a space
(`${IFS}`) and to chain a command (a pipe `|`, or a `<` redirect). The flag lives
at `/flag.txt`.
</details>

## Flag Format

`TAIBAH{...}`
