# 12 — Close Primes

| Category     | Points | Difficulty |
|--------------|--------|------------|
| Cryptography | 350    | Hard       |

## Description

The Oasis Bank rolled its own RSA key generator to save time. The developer explains:

> *"I pick a random 512-bit prime `p`, then I just search upward from `p` for the next prime `q`. Both are 512 bits, so the key is 1024 bits. Totally secure!"*

We captured a message encrypted with the bank's public key. Recover it.

## Files

- [`files/public.txt`](files/public.txt) — the modulus `n`, the public exponent `e`, and the ciphertext `c`

## Hints

<details>
<summary>Hint 1 (free)</summary>

RSA is only secure if `n = p * q` cannot be factored. The developer's method makes `p` and `q` **very close to each other**, and so both are very close to `√n`.
</details>

<details>
<summary>Hint 2 (-70 points)</summary>

Look up **Fermat's factorization method**. Start from `a = ceil(√n)` and increase `a` until `a² - n` is a perfect square `b²`. Then `p = a - b` and `q = a + b`.

In Python, use `math.isqrt()` for exact integer square roots. Floats are not precise enough for numbers this large.
</details>

<details>
<summary>Hint 3 (-70 points)</summary>

Once you have `p` and `q`:

```python
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)
m = pow(c, d, n)
print(m.to_bytes((m.bit_length() + 7) // 8, "big"))
```
</details>

## Flag Format

`TAIBAH{...}`
