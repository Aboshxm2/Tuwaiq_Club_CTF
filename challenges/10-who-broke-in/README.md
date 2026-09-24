# 10 — Who Broke In?

| Category                 | Points | Difficulty |
|--------------------------|--------|------------|
| Log Analysis (Blue Team) | 200    | Easy       |

## Description

You are a **SOC analyst** on duty. This morning, the server `taibah-srv` started behaving strangely. Your manager believes someone broke in over **SSH** yesterday.

You've been handed the server's SSH authentication log. Find out:

1. The **IP address** of the attacker who ran a **brute-force attack**.
2. The **username** of the account the attacker **successfully logged into**.

## Files

- [`files/auth.log`](files/auth.log)

## Flag Format

```
TAIBAH{<attacker_ip>_<username>}
```

**Example:** `TAIBAH{1.2.3.4_ahmed}`

## Hints

<details>
<summary>Hint 1 (free)</summary>

A brute-force attack means **many failed login attempts** from the **same IP** in a short time. Look for lines containing `Failed password`.
</details>

<details>
<summary>Hint 2 (-40 points)</summary>

Count failed attempts per IP:

```bash
grep "Failed password" auth.log | grep -oE "from [0-9.]+" | sort | uniq -c | sort -rn
```

Then check whether that IP ever got an `Accepted password`:

```bash
grep "Accepted password" auth.log | grep "<IP>"
```
</details>

## Discussion (after the CTF)

How could this attack have been prevented? (Think: **strong passwords**, **SSH keys**, **fail2ban**, **disabling password login**, **MFA**.)
