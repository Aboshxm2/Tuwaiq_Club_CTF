# 19 — Onion Layers

| Category | Points | Difficulty |
|----------|--------|------------|
| Encoding | 250    | Medium     |

## Description

A suspect hid the flag under **five layers** of encoding and compression, one wrapped around the other like an onion. Each layer has a fingerprint that tells you what it is.

Peel them one at a time.

## Files

- [`files/layers.txt`](files/layers.txt)

## Hints

<details>
<summary>Hint 1 (free)</summary>

Learn to recognize the fingerprints:

| Looks like | Probably |
|------------|----------|
| `A-Z a-z 0-9 + /`, ends with `=` | Base64 |
| Only `0-9 a-f`, even length | Hex |
| Only `A-Z 2-7`, ends with `=` | Base32 |
| Binary bytes starting with `78 DA` or `78 9C` | zlib-compressed data |
| Readable shape but wrong letters | ROT13 / Caesar |
</details>

<details>
<summary>Hint 2 (-50 points)</summary>

[CyberChef](https://gchq.github.io/CyberChef/)'s **Magic** operation can detect some layers automatically. For the compressed layer, use **Zlib Inflate**.
</details>

<details>
<summary>Hint 3 (-50 points)</summary>

The order is: Base64 → Hex → Base32 → Zlib → ROT13.
</details>

## Flag Format

`TAIBAH{...}`
