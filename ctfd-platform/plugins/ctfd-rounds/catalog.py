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
    {"slug": "21-caravan-ledger", "name": "Caravan Ledger", "category": "Web", "points": 250},
    {"slug": "22-sealed-scroll", "name": "Sealed Scroll", "category": "Cryptography", "points": 400},
    {"slug": "23-desert-diagnostics", "name": "Desert Diagnostics", "category": "Web", "points": 300},
    {"slug": "24-mirage-preview", "name": "Mirage Preview", "category": "Web", "points": 350},
    {"slug": "25-floodgate-override", "name": "Floodgate Override", "category": "Pwn", "points": 400},
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
            "21-caravan-ledger",
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
            "22-sealed-scroll",
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
            "23-desert-diagnostics",
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
            "24-mirage-preview",
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
            "25-floodgate-override",
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

# Challenges served as a live container (ctfd-whale) instead of a downloadable
# bundle. The importer creates each of these as a `dynamic_docker` challenge; the
# per-team flag is generated by whale and injected as the container's FLAG env
# var. To add one, build an image (see ctfd-platform/deploy/README.md) and add an
# entry here, then assign the slug to a round in ROUNDS above.
#
#   image          the Docker image tag (matches ctfd-platform/deploy/build.sh)
#   redirect_type  "http" for a web app, "direct" for a raw TCP service
#   redirect_port  the port the app listens on inside the container
#   memory_limit   per-container memory ceiling (e.g. "128m")
#   cpu_limit      per-container CPU ceiling (cores, e.g. 0.5)
#   description    markdown shown on the challenge page
DEPLOYABLE = {
    "01-inspect-the-oasis": {
        "image": "taibah-ctf/01-inspect-the-oasis:latest",
        "redirect_type": "http",
        "redirect_port": 80,
        "memory_limit": "64m",
        "cpu_limit": 0.5,
        "description": (
            "The **Oasis Travel Agency** just launched their new website. Their "
            "junior developer was in a hurry and says he \"cleaned up everything\" "
            "before going live. We don't believe him.\n\n"
            "Launch your instance, open the site, and find what he left behind. "
            "The flag is split into **3 parts** across the page's files — put them "
            "together in order.\n\n"
            "Your instance and its flag are unique to your team."
        ),
    },
    "20-token-of-trust": {
        "image": "taibah-ctf/20-token-of-trust:latest",
        "redirect_type": "http",
        "redirect_port": 80,
        "memory_limit": "128m",
        "cpu_limit": 0.5,
        "description": (
            "The **Oasis Portal** logs staff in with a **JSON Web Token (JWT)**. "
            "Launch your instance to get your own copy of the portal and a guest "
            "session token.\n\n"
            "The developers were lazy: the token's signing secret is weak, and a "
            "backup of their password list leaked (the portal links to it). "
            "Recover the secret, forge an **administrator** token, and open the "
            "vault.\n\n"
            "Your instance and its flag are unique to your team."
        ),
    },
    "21-caravan-ledger": {
        "image": "taibah-ctf/21-caravan-ledger:latest",
        "redirect_type": "http",
        "redirect_port": 80,
        "memory_limit": "128m",
        "cpu_limit": 0.5,
        "description": (
            "The **Oasis Caravan Ledger** lets anyone search the public caravan "
            "manifest. The same database holds a private table the search page "
            "was never meant to reach.\n\n"
            "Launch your instance and make the search return more than the "
            "caravans it was built to show.\n\n"
            "Your instance and its flag are unique to your team."
        ),
    },
    "22-sealed-scroll": {
        "image": "taibah-ctf/22-sealed-scroll:latest",
        "redirect_type": "http",
        "redirect_port": 80,
        "memory_limit": "128m",
        "cpu_limit": 0.5,
        "description": (
            "The archive hands every visitor an encrypted **session scroll** "
            "(`AES-CBC`). The vault opens only for an *administrator* scroll, and "
            "yours says *guest*.\n\n"
            "The scroll carries no signature. Launch your instance, look at how "
            "the scroll decodes, and change your role **without** the key.\n\n"
            "Your instance and its flag are unique to your team."
        ),
    },
    "23-desert-diagnostics": {
        "image": "taibah-ctf/23-desert-diagnostics:latest",
        "redirect_type": "http",
        "redirect_port": 80,
        "memory_limit": "128m",
        "cpu_limit": 0.5,
        "description": (
            "The **Oasis Network Diagnostics** page lets relay operators ping a "
            "host to check that it is reachable. The check runs on the server.\n\n"
            "Launch your instance and get it to run a little more than a ping. "
            "The flag is in a file on the server.\n\n"
            "Your instance and its flag are unique to your team."
        ),
    },
    "24-mirage-preview": {
        "image": "taibah-ctf/24-mirage-preview:latest",
        "redirect_type": "http",
        "redirect_port": 80,
        "memory_limit": "128m",
        "cpu_limit": 0.5,
        "description": (
            "**Mirage Preview** fetches any link you paste and shows you what is "
            "there, so you can preview a page before sharing it. It only allows "
            "*public* web addresses.\n\n"
            "Launch your instance. There is an internal control panel the preview "
            "service can reach but you cannot. Reach it anyway.\n\n"
            "Your instance and its flag are unique to your team."
        ),
    },
    "25-floodgate-override": {
        "image": "taibah-ctf/25-floodgate-override:latest",
        "redirect_type": "direct",
        "redirect_port": 9999,
        "memory_limit": "64m",
        "cpu_limit": 0.5,
        "description": (
            "The **Oasis Dam floodgate terminal** demands a 32-character override "
            "code before it opens the gates. We recovered the control program; it "
            "hands you a copy when you connect.\n\n"
            "This is a **raw TCP** service — connect with `nc <host> <port>`. "
            "Analyse the program, then send input that makes it open the "
            "floodgates instead of denying you.\n\n"
            "The program is a Linux x86-64 executable. Decompile it (e.g. Ghidra), "
            "find the routine that prints the flag, and redirect execution to it.\n\n"
            "Your instance and its flag are unique to your team."
        ),
    },
}

