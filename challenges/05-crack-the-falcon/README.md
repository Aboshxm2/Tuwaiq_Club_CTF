# 05 — Crack the Falcon

| Category          | Points | Difficulty |
|-------------------|--------|------------|
| Password Cracking | 100    | Easy       |

## Description

We found a leaked database from a falconry club's website. The admin's password wasn't stored in plain text — it was stored as a hash:

```
fa0d1a60ef6616bb28038515c8ea4cb2
```

The admin was lazy and used a **single, common, lowercase English word** as his password.

Find the password. The flag is the password wrapped in the flag format.

**Example:** if the password is `camel`, the flag is `TAIBAH{camel}`.

## Hints

<details>
<summary>Hint 1 (free)</summary>

Count the characters in the hash. A hash with **32 hex characters** is very likely **MD5**.
</details>

<details>
<summary>Hint 2 (-20 points)</summary>

Hashes can't be "decrypted", but common passwords can be looked up in huge precomputed tables. Try [CrackStation](https://crackstation.net/), or crack it yourself:

```bash
echo "fa0d1a60ef6616bb28038515c8ea4cb2" > hash.txt
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```
</details>

## Discussion (after the CTF)

Why is MD5 a bad choice for storing passwords? What should websites use instead? (Think: **bcrypt**, **Argon2**, and **salting**.)

## Flag Format

`TAIBAH{...}`
