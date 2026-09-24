# 03 — Julius in the Desert

| Category     | Points | Difficulty |
|--------------|--------|------------|
| Cryptography | 100    | Easy       |

## Description

A Roman general once protected his military messages by **shifting** every letter of the alphabet by a fixed number. Over 2000 years later, someone used the same trick to hide our flag:

```
WDLEDK{mx11xv_z0xog_e3_su0xg}
```

Numbers and symbols were not changed — only letters.

## Hints

<details>
<summary>Hint 1 (free)</summary>

You already know that every flag starts with `TAIBAH`. Compare `T` with `W`. How many letters apart are they?
</details>

<details>
<summary>Hint 2 (-20 points)</summary>

This is the **Caesar cipher**. Use the **ROT13** operation in [CyberChef](https://gchq.github.io/CyberChef/) and change the amount, or use the Caesar tool on [dCode.fr](https://www.dcode.fr/caesar-cipher).
</details>

## Flag Format

`TAIBAH{...}`
