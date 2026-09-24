# 14 — Locked Vault

| Category          | Points | Difficulty |
|-------------------|--------|------------|
| Password Cracking | 200    | Medium     |

## Description

The treasurer of the Oasis Trading Company keeps a backup of the vault inventory in a password-protected ZIP file. He's proud of his password policy:

> *"I use a **6-digit PIN**, just like my bank card. Nobody will ever guess it."*

Prove him wrong.

## Files

- [`files/vault.zip`](files/vault.zip)

## Hints

<details>
<summary>Hint 1 (free)</summary>

How many 6-digit PINs are there? A computer can try every one of them in seconds. This is called a **brute-force** attack.
</details>

<details>
<summary>Hint 2 (-40 points)</summary>

With John the Ripper:

```bash
zip2john vault.zip > vault.hash
john --mask='?d?d?d?d?d?d' vault.hash
john --show vault.hash
```

Or with `fcrackzip`:

```bash
fcrackzip -u -b -c 1 -l 6-6 vault.zip
```
</details>

<details>
<summary>Hint 3 (-40 points)</summary>

Or write your own cracker in Python. Loop over `000000` to `999999` and call `zipfile.ZipFile("vault.zip").read("flag.txt", pwd=pin.encode())`. A wrong PIN raises an exception, so wrap it in `try / except Exception`.
</details>

## Flag Format

`TAIBAH{...}`
