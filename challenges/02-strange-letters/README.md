# 02 — Strange Letters

| Category | Points | Difficulty |
|----------|--------|------------|
| Encoding | 50     | Easy       |

## Description

Our team intercepted this message sent between two suspicious accounts. It looks like random letters, but the `=` at the end looks familiar...

```
VEFJQkFIe2I0czM2NF8xc19uMHRfM25jcnlwdDEwbn0=
```

Can you read the original message?

## Hints

<details>
<summary>Hint 1 (free)</summary>

This is a very common **encoding** (not encryption) used to send binary data as text. It often ends with `=` or `==`.
</details>

<details>
<summary>Hint 2 (-10 points)</summary>

Try the **"From Base64"** operation in [CyberChef](https://gchq.github.io/CyberChef/), or in Linux:

```bash
echo "..." | base64 -d
```
</details>

## Flag Format

`TAIBAH{...}`
