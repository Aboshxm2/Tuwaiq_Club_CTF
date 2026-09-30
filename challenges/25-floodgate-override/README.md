# 25 — Floodgate Override

| Category | Points | Difficulty |
|----------|--------|------------|
| Pwn      | 400    | Hard       |

## Description

The **Oasis Dam floodgate terminal** demands a 32-character override code before
it opens the gates. We recovered the control program; it hands you a copy when
you connect.

This is a **raw TCP** service. Analyse the program, then send input that makes it
open the floodgates instead of denying you.

Your instance and its flag are unique to your team.

## Access

This challenge runs as a **live TCP service**. Open the challenge on the
platform, click **Launch an instance**, and connect with `nc`:

```bash
nc <host> <port>
```

When you connect, the program prints itself as **base64**. Decode it to a file
and analyse it:

```bash
# paste the base64 between the BEGIN/END markers into floodgate.b64
base64 -d floodgate.b64 > floodgate && chmod +x floodgate && file floodgate
```

## Hints

<details>
<summary>Hint 1 (free)</summary>

The program is a Linux x86-64 executable, built **without a stack canary and
without PIE**. Decompile it (Ghidra, Binary Ninja, Dogbolt) and look at the two
functions besides `main`.
</details>

<details>
<summary>Hint 2</summary>

`vuln()` reads far more bytes than its buffer holds, so you can overwrite the
saved return address. `win()` prints the flag but is never called. Overflow the
64-byte buffer (plus the 8-byte saved base pointer) and overwrite the return
address with the address of `win`. Because the binary is not PIE, that address
is fixed.
</details>

## Flag Format

`TAIBAH{...}`
