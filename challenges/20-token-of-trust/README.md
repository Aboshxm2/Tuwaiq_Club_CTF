# 20 — Token of Trust

| Category           | Points | Difficulty |
|--------------------|--------|------------|
| Web / Cryptography | 350    | Hard       |

## Description

The Oasis Portal logs students in with a **JSON Web Token (JWT)**. You were given a guest token for your session.

The portal's developers were lazy. They used the same **signing secret** for the tokens and for encrypting the company vault. We also found their password list in a leaked backup, and it's very likely the secret is in it.

Recover the signing secret, then use it to decrypt the vault.

## Files

- [`files/token.txt`](files/token.txt) — your guest session token
- [`files/wordlist.txt`](files/wordlist.txt) — leaked list of passwords used by the developers
- [`files/vault.enc`](files/vault.enc) — the encrypted vault
- [`files/vault_tool.py`](files/vault_tool.py) — the tool that encrypted the vault (without the secret)

## Hints

<details>
<summary>Hint 1 (free)</summary>

A JWT has three Base64URL parts separated by dots: `header.payload.signature`. Paste your token into [jwt.io](https://jwt.io/) to read the header and payload.

The header says `HS256`, which means the signature is `HMAC-SHA256(secret, header + "." + payload)`.
</details>

<details>
<summary>Hint 2 (-70 points)</summary>

Crack the secret with a wordlist attack:

```bash
hashcat -m 16500 token.txt wordlist.txt
# or, with John the Ripper's jwt2john.py helper
python3 jwt2john.py "$(cat token.txt)" > token.john
john --wordlist=wordlist.txt token.john
```

Or in Python, try each word with `hmac.new(word.encode(), (header + "." + payload).encode(), hashlib.sha256)` and compare the result with the decoded signature.
</details>

<details>
<summary>Hint 3 (-70 points)</summary>

`vault_tool.py` uses XOR, and XOR is its own inverse. Run the same tool on the encrypted file to decrypt it:

```bash
JWT_SECRET='<secret>' python3 vault_tool.py vault.enc vault.txt
```
</details>

## Flag Format

`TAIBAH{...}`
