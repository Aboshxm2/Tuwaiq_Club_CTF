# 18 — Deleted but Not Forgotten

| Category          | Points | Difficulty |
|-------------------|--------|------------|
| Forensics (Git)   | 250    | Medium     |

## Description

A developer at Oasis Travel accidentally committed the **payment gateway API key** to the company's Git repository. He noticed a day later, removed it, and pushed a fix:

> *"Don't worry, the key isn't in the code anymore. I checked."*

The repository was later leaked online. Is the key really gone?

## Files

- [`files/oasis-portal.tar.gz`](files/oasis-portal.tar.gz) — a copy of the repository, including its `.git` folder

```bash
tar -xzf oasis-portal.tar.gz
cd oasis-portal
```

## Hints

<details>
<summary>Hint 1 (free)</summary>

Git keeps **every version of every file** that was ever committed. Deleting a line in a new commit doesn't remove it from older ones.

```bash
git log --oneline
```
</details>

<details>
<summary>Hint 2 (-50 points)</summary>

Show the full changes (the "patch") of every commit:

```bash
git log -p
```

Or view one file at a specific commit: `git show <commit>:config.py`
</details>

## Flag Format

`TAIBAH{...}`

## Discussion (after the CTF)

Once a secret has been pushed, what must you do? (Hint: **rotate the key**. Rewriting history with tools like `git filter-repo` is not enough, because copies may already exist.) Tools like `gitleaks` and `trufflehog` scan repositories for exactly this.
