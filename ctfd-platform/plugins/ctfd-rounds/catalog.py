"""Challenge and round definitions shared by the importer and the running plugin."""

CHALLENGES = [
    {"slug": "01-inspect-the-oasis", "name": "Inspect the Oasis", "category": "Web", "points": 50},
    {"slug": "02-strange-letters", "name": "Strange Letters", "category": "Encoding", "points": 50},
    {"slug": "03-julius-in-the-desert", "name": "Julius in the Desert", "category": "Cryptography", "points": 100},
    {"slug": "04-ones-and-zeros", "name": "Ones and Zeros", "category": "Encoding", "points": 100},
    {"slug": "05-crack-the-falcon", "name": "Crack the Falcon", "category": "Password Cracking", "points": 100},
    {"slug": "06-desert-picture", "name": "Desert Picture", "category": "Forensics", "points": 100},
    {"slug": "07-not-a-pdf", "name": "Not a PDF", "category": "Forensics", "points": 150},
    {"slug": "08-camel-caravan", "name": "Camel Caravan", "category": "Linux", "points": 150},
    {"slug": "09-password-checker", "name": "Password Checker", "category": "Reverse Engineering", "points": 150},
    {"slug": "10-who-broke-in", "name": "Who Broke In?", "category": "Log Analysis", "points": 200},
    {"slug": "11-sandstorm-xor", "name": "Sandstorm XOR", "category": "Cryptography", "points": 200},
    {"slug": "12-close-primes", "name": "Close Primes", "category": "Cryptography", "points": 350},
    {"slug": "13-the-merchants-letter", "name": "The Merchant's Letter", "category": "Cryptography", "points": 200},
    {"slug": "14-locked-vault", "name": "Locked Vault", "category": "Password Cracking", "points": 200},
    {"slug": "15-wiretap", "name": "Wiretap", "category": "Network Forensics", "points": 200},
    {"slug": "16-pixel-secrets", "name": "Pixel Secrets", "category": "Steganography", "points": 300},
    {"slug": "17-floodgate", "name": "Floodgate", "category": "Reverse Engineering", "points": 400},
    {"slug": "18-deleted-not-forgotten", "name": "Deleted but Not Forgotten", "category": "Forensics", "points": 250},
    {"slug": "19-onion-layers", "name": "Onion Layers", "category": "Encoding", "points": 250},
    {"slug": "20-token-of-trust", "name": "Token of Trust", "category": "Web", "points": 350},
]

# Minutes match organizer/RUN_OF_SHOW.md.
ROUNDS = [
    {
        "name": "Round 1 — Warm-up",
        "minutes": 25,
        "position": 1,
        "slugs": [
            "01-inspect-the-oasis",
            "02-strange-letters",
            "04-ones-and-zeros",
            "19-onion-layers",
        ],
    },
    {
        "name": "Round 2 — Ciphers",
        "minutes": 25,
        "position": 2,
        "slugs": [
            "03-julius-in-the-desert",
            "13-the-merchants-letter",
            "11-sandstorm-xor",
            "12-close-primes",
        ],
    },
    {
        "name": "Round 3 — Hidden in Files",
        "minutes": 30,
        "position": 3,
        "slugs": [
            "06-desert-picture",
            "07-not-a-pdf",
            "18-deleted-not-forgotten",
            "16-pixel-secrets",
        ],
    },
    {
        "name": "Round 4 — Breaking Locks",
        "minutes": 30,
        "position": 4,
        "slugs": [
            "05-crack-the-falcon",
            "09-password-checker",
            "14-locked-vault",
            "20-token-of-trust",
        ],
    },
    {
        "name": "Round 5 — The Investigation",
        "minutes": 35,
        "position": 5,
        "slugs": [
            "08-camel-caravan",
            "10-who-broke-in",
            "15-wiretap",
            "17-floodgate",
        ],
    },
]

NOTES = {
    "05-crack-the-falcon": (
        "The flag format is `TAIBAH{<password>_<case-id>}`. "
        "The case-id is in `CASE.txt` inside your instance."
    ),
    "10-who-broke-in": (
        "The flag format is `TAIBAH{<attacker_ip>_<username>_<case-id>}`. "
        "The case-id is on the first line of your `auth.log`."
    ),
    "17-floodgate": "Your instance includes a Linux x86-64 binary named `floodgate`. Run `chmod +x floodgate` before you start it.",
}

INSTANCE_NOTE = (
    "Launch an instance to download files made only for your team. "
    "The flag inside them scores for your team and for nobody else."
)
