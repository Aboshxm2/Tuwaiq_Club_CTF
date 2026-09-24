# 06 — Desert Picture

| Category  | Points | Difficulty |
|-----------|--------|------------|
| Forensics | 100    | Easy       |

## Description

A photographer shared this picture of the desert sand. It looks like a plain, boring image.

But pictures can carry more than just pixels. Look closer — not with your eyes, but with your tools.

## Files

- [`files/desert.png`](files/desert.png)

## Hints

<details>
<summary>Hint 1 (free)</summary>

Image files can contain hidden text such as **metadata** and comments. Try looking for readable text inside the file.
</details>

<details>
<summary>Hint 2 (-20 points)</summary>

On Linux, try:

```bash
strings desert.png
```

or

```bash
exiftool desert.png
```
</details>

## Flag Format

`TAIBAH{...}`
