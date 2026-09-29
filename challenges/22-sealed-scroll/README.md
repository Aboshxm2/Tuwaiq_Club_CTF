# 22 — Sealed Scroll

| Category     | Points | Difficulty |
|--------------|--------|------------|
| Cryptography | 400    | Hard       |

## Description

The archive hands every visitor an encrypted **session scroll** (`AES-CBC`). The
vault opens only for an *administrator* scroll, and yours says *guest*.

The scroll carries no signature. Launch your instance, look at how the scroll
decodes, and change your role **without** the key.

Your instance and its flag are unique to your team.

## Access

This challenge runs as a **live website**. Open the challenge on the platform,
click **Launch an instance**, and open the link it gives you.

## Hints

<details>
<summary>Hint 1 (free)</summary>

The scroll is `base64url(IV || ciphertext)`. In CBC mode the first plaintext
block is `P0 = decrypt(C0) XOR IV`. The page shows you exactly what your first
block says.
</details>

<details>
<summary>Hint 2</summary>

Flipping one byte of the IV flips the same byte of the first plaintext block, and
nothing else. Turn `guest` into `admin` (both five letters) by XOR-ing the IV at
those five offsets. The rest of the scroll is untouched, so it stays valid.
</details>

## Flag Format

`TAIBAH{...}`
