# 09 — Password Checker

| Category            | Points | Difficulty |
|---------------------|--------|------------|
| Reverse Engineering | 150    | Easy       |

## Description

The **Oasis Vault** is protected by a Python password checker. The developer thought it was safe because the password isn't written directly in the code.

But if the program can check the password... the program must *know* the password. Can you figure it out?

## Files

- [`files/checker.py`](files/checker.py)

Run it with:

```bash
python3 checker.py
```

## Hints

<details>
<summary>Hint 1 (free)</summary>

Read the `check()` function carefully. For each character, the program does `ord(char) ^ KEY` and compares the result to a number in `SECRET`.

The `^` operator is **XOR**.
</details>

<details>
<summary>Hint 2 (-30 points)</summary>

XOR is its own inverse:

```
if   a ^ k = s
then s ^ k = a
```

So XOR each number in `SECRET` with `KEY`, then convert it to a character with `chr()`.
</details>

## Flag Format

`TAIBAH{...}`
