# Taibah University Cybersecurity Workshop — Final Day CTF

Welcome to the final-day **Capture The Flag (CTF)** competition of the 5-day Cybersecurity Workshop!

This is a **Jeopardy-style** CTF. Each challenge hides a secret string called a **flag**. Find it, submit it, and earn points.

---

## Flag Format

Every flag looks like this:

```
TAIBAH{s0m3_t3xt_h3r3}
```

Flags are **case-sensitive**. Submit the whole thing, including `TAIBAH{` and `}`.

---

## Challenges

| #  | Challenge                                                        | Category             | Points |
|----|------------------------------------------------------------------|----------------------|--------|
| 01 | [Inspect the Oasis](challenges/01-inspect-the-oasis/README.md)   | Web                  | 50     |
| 02 | [Strange Letters](challenges/02-strange-letters/README.md)       | Encoding             | 50     |
| 03 | [Julius in the Desert](challenges/03-julius-in-the-desert/README.md) | Cryptography     | 100    |
| 04 | [Ones and Zeros](challenges/04-ones-and-zeros/README.md)         | Encoding             | 100    |
| 05 | [Crack the Falcon](challenges/05-crack-the-falcon/README.md)     | Password Cracking    | 100    |
| 06 | [Desert Picture](challenges/06-desert-picture/README.md)         | Forensics            | 100    |
| 07 | [Not a PDF](challenges/07-not-a-pdf/README.md)                   | Forensics            | 150    |
| 08 | [Camel Caravan](challenges/08-camel-caravan/README.md)           | Linux                | 150    |
| 09 | [Password Checker](challenges/09-password-checker/README.md)     | Reverse Engineering  | 150    |
| 10 | [Who Broke In?](challenges/10-who-broke-in/README.md)            | Log Analysis (Blue Team) | 200 |
| 11 | [Sandstorm XOR](challenges/11-sandstorm-xor/README.md)           | Cryptography         | 200    |
| 12 | [Close Primes](challenges/12-close-primes/README.md)             | Cryptography         | 350    |
| 13 | [The Merchant's Letter](challenges/13-the-merchants-letter/README.md) | Cryptography    | 200    |
| 14 | [Locked Vault](challenges/14-locked-vault/README.md)             | Password Cracking    | 200    |
| 15 | [Wiretap](challenges/15-wiretap/README.md)                       | Network Forensics    | 200    |
| 16 | [Pixel Secrets](challenges/16-pixel-secrets/README.md)           | Steganography        | 300    |
| 17 | [Floodgate](challenges/17-floodgate/README.md)                   | Reverse Engineering  | 400    |
| 18 | [Deleted but Not Forgotten](challenges/18-deleted-not-forgotten/README.md) | Forensics (Git) | 250 |
| 19 | [Onion Layers](challenges/19-onion-layers/README.md)             | Encoding             | 250    |
| 20 | [Token of Trust](challenges/20-token-of-trust/README.md)         | Web / Cryptography   | 350    |
|    | **Total**                                                        |                      | **3850** |

Challenges 01–10 are **Easy**. Challenges 11–20 are **Medium** and **Hard**, so try them once you're comfortable with the basics. Start at the top if you're new!

---

## Rules

1. Work **individually** or in **teams of up to 3** (as announced by the organizers).
2. **Do not attack** the scoreboard, the competition infrastructure, or other teams.
3. **Do not share flags** or solutions with other teams during the competition.
4. Brute-forcing the flag submission form is **not allowed**.
5. Everything you need is inside the challenge files — no real systems need to be hacked.
6. Hints are available for each challenge. Using a hint may cost points (see each challenge).
7. In case of a tie, the team that reached the score **first** wins.
8. The organizers' decisions are final.

---

## Recommended Tools

You can solve every challenge with free tools. A Linux machine (Kali, Ubuntu, or WSL on Windows) is recommended.

| Tool | Used For |
|------|----------|
| Web browser (Chrome / Firefox) + DevTools (`F12`) | Web challenges |
| [CyberChef](https://gchq.github.io/CyberChef/) | Encoding / decoding / ciphers |
| [dCode.fr](https://www.dcode.fr/) | Classic ciphers |
| [CrackStation](https://crackstation.net/) / `john` / `hashcat` | Password hashes |
| `file`, `strings`, `exiftool`, `unzip` | Forensics |
| `ls -la`, `find`, `cat`, `tar` | Linux basics |
| `grep`, `sort`, `uniq`, `wc` | Log analysis |
| Python 3 | Scripting and reverse engineering |
| [Wireshark](https://www.wireshark.org/) | Network captures (`.pcap`) |
| [Ghidra](https://ghidra-sre.org/) / [Dogbolt](https://dogbolt.org/) | Decompiling binaries |
| `zsteg`, [Aperi'Solve](https://www.aperisolve.com/) | Image steganography |
| `git` | Repository forensics |
| [jwt.io](https://jwt.io/), `hashcat`, `john` | JWTs and password cracking |

---

## Getting Help

Raise your hand or talk to any organizer if something seems broken. Organizers won't solve challenges for you, but they will confirm whether a file or service is working.

**Good luck, and have fun!**
