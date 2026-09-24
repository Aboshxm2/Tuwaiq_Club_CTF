# 08 — Camel Caravan

| Category | Points | Difficulty |
|----------|--------|------------|
| Linux    | 150    | Easy       |

## Description

A camel caravan travelled across the desert for 4 days and kept a log of everything in these folders.

The caravan leader says the flag is in there somewhere, but warns: *"Not everything in the desert is visible to the naked eye."*

## Files

- [`files/caravan.tar.gz`](files/caravan.tar.gz)

Extract it with:

```bash
tar -xzf caravan.tar.gz
cd caravan
```

## Hints

<details>
<summary>Hint 1 (free)</summary>

On Linux, files and folders whose names start with a **dot** (`.`) are **hidden**. A normal `ls` won't show them.
</details>

<details>
<summary>Hint 2 (-30 points)</summary>

Try:

```bash
ls -la
```

in each folder, or search everything at once:

```bash
find . -name "*flag*"
```
</details>

## Flag Format

`TAIBAH{...}`
