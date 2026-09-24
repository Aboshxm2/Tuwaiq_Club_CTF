# 11 — Sandstorm XOR

| Category     | Points | Difficulty |
|--------------|--------|------------|
| Cryptography | 200    | Medium     |

## Description

A smuggler known as **Sandstorm** encrypts his messages with XOR and a **short repeating key**. He believes nobody can read them without the key.

We intercepted one of his messages. Our analysts are sure it **starts with the flag**, because Sandstorm always signs his orders the same way.

## Files

- [`files/cipher.hex`](files/cipher.hex) — the ciphertext, hex-encoded

## Hints

<details>
<summary>Hint 1 (free)</summary>

XOR has a useful property:

```
plaintext ^ key        = ciphertext
ciphertext ^ plaintext = key
```

If you know part of the plaintext, you can recover part of the key.
</details>

<details>
<summary>Hint 2 (-40 points)</summary>

The message starts with `TAIBAH{`. XOR the first 7 ciphertext bytes with `TAIBAH{` and look for a pattern that repeats. The key is shorter than 7 bytes.

CyberChef: **From Hex**, then **XOR** (key type UTF8).
</details>

## Flag Format

`TAIBAH{...}`
