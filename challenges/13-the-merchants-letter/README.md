# 13 — The Merchant's Letter

| Category     | Points | Difficulty |
|--------------|--------|------------|
| Cryptography | 200    | Medium     |

## Description

A letter between two merchant brothers was found in an old caravan chest. It is written in their "family cipher". Their grandfather taught it to them, and it is much stronger than Caesar's.

The letters are scrambled, but the spaces, punctuation, and line breaks are untouched. Somewhere in the letter is the password to the family storehouse.

## Files

- [`files/letter.txt`](files/letter.txt)

## Hints

<details>
<summary>Hint 1 (free)</summary>

Julius Caesar used one shift for every letter. This cipher uses a **keyword**, where each letter of the keyword gives a different shift. It is named after a 16th-century French diplomat.
</details>

<details>
<summary>Hint 2 (-40 points)</summary>

This is the **Vigenère cipher**. With this much text, you don't need the key: automatic solvers like [dCode's Vigenère tool](https://www.dcode.fr/vigenere-cipher) can find the key length and key using frequency analysis.

Or use known plaintext: the password starts with `TAIBAH`.
</details>

<details>
<summary>Hint 3 (-60 points)</summary>

The key is 6 letters long and is something you might see in the desert that isn't really there.
</details>

## Flag Format

`TAIBAH{...}` (numbers and symbols are not encrypted)
