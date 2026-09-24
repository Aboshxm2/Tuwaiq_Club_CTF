# 07 — Not a PDF

| Category  | Points | Difficulty |
|-----------|--------|------------|
| Forensics | 150    | Easy       |

## Description

An employee emailed us his "quarterly report", but none of our PDF readers can open it. They all say the file is **damaged**.

Is it really broken? Or is it just *pretending* to be something it's not?

## Files

- [`files/report.pdf`](files/report.pdf)

## Hints

<details>
<summary>Hint 1 (free)</summary>

A file's extension (`.pdf`, `.jpg`, `.docx`) is just part of its name — anyone can change it. The **real** file type is decided by the first few bytes of the file, called **magic bytes** or the **file signature**.
</details>

<details>
<summary>Hint 2 (-30 points)</summary>

On Linux, run:

```bash
file report.pdf
```

Or look at the first bytes with `xxd report.pdf | head`. What does `PK` at the start of a file mean? Rename it and open it with the right program.
</details>

## Flag Format

`TAIBAH{...}`
