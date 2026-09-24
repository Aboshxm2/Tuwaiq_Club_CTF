# 04 — Ones and Zeros

| Category | Points | Difficulty |
|----------|--------|------------|
| Encoding | 100    | Easy       |

## Description

A robot left us a message. Computers only understand `0` and `1`... but people don't. Translate it back to human language.

```
01010100 01000001 01001001 01000010 01000001 01001000 01111011 01100010
00110001 01101110 00110100 01110010 01111001 01011111 00110001 01110011
01011111 01110100 01101000 00110011 01011111 01101100 00110100 01101110
01100111 01110101 00110100 01100111 00110011 01111101
```

## Hints

<details>
<summary>Hint 1 (free)</summary>

Each group of **8 bits** (one byte) represents **one character**. Look up an **ASCII table**.

For example: `01010100` = 84 in decimal = `T` in ASCII.
</details>

<details>
<summary>Hint 2 (-20 points)</summary>

Use the **"From Binary"** operation in [CyberChef](https://gchq.github.io/CyberChef/), or in Python:

```python
bits = "01010100 01000001 ..."
print("".join(chr(int(b, 2)) for b in bits.split()))
```
</details>

## Flag Format

`TAIBAH{...}`
