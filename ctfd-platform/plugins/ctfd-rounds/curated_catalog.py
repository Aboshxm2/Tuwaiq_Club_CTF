"""English participant copy and release plan. No static answer keys."""

FILE_NOTE = "Launch your file instance and download the bundle generated for your team. Submit the complete `TAIBAH{...}` flag."
WEB_NOTE = "Launch your instance and open its link. Your instance and flag belong to your team. Starting another live challenge replaces your current live instance; these apps do not require saved progress."


def file(key, name, slug, category, points, difficulty, batch, text, hints):
    return dict(key=key, name=name, slug="curated-" + slug, kind="file", category=category,
                points=points, difficulty=difficulty, batch=batch, description=text + "\n\n" + FILE_NOTE, hints=hints)


def web(key, name, mode, points, difficulty, batch, text, hints):
    return dict(key=key, name=name, mode=mode, kind="web", category="Web", points=points,
                difficulty=difficulty, batch=batch, description=text + "\n\n" + WEB_NOTE, hints=hints)


CHALLENGES = [
    web("W1", "Last Edit", "last-edit", 100, "Easy", 1,
        "The showcase site went live a little early. Two developers left three build notes behind. Find the notes and put their contents together in order.",
        ["The browser receives more than it displays.", "Follow the page's HTML, stylesheet and script references."]),
    web("W2", "Forgotten Route", "forgotten-route", 150, "Easy", 2,
        "The archive moved to a new portal. The old exports are gone from the menu, but the migration team may have left a route behind. Recover the handover code.",
        ["What instructions does a site leave for crawlers?", "A retired export may contain more than its public summary."]),
    web("W3", "Frontend Pass", "frontend-pass", 125, "Easy", 2,
        "The designer disabled the staff preview button and called the job done. Review that assumption. The browser remembers your preview preferences.",
        ["A disabled control is a browser instruction, not a server permission.", "Inspect how your preview preference is stored. Encoding is not a signature."]),
    web("W4", "Trial Account", "trial-login", 150, "Easy", 0,
        "A legacy staff login protects a handover note. You have no valid account. Find out whether the login checks only what it was intended to check.",
        ["How might a legacy login build its database query?", "Think about quotes and boolean conditions, not password guessing."]),
    web("W5", "Not Your Request", "refund-desk", 250, "Medium", 3,
        "Your demonstration account has one refund request. A staff-only attachment belongs to someone else. Can you get the server to approve that request and return its audit code? All accounts and records are fictional.",
        ["Inspect the requests the interface makes.", "The interface may enforce ownership while the API forgets to."]),
    web("W6", "Caravan Ledger: Audit", "caravan-ledger", 300, "Medium", 3,
        "The public ledger lists caravans and their cargo. Private audit records live in the same database. Make the search tell you more than the public view was designed to show.",
        ["An unexpected quote may reveal the kind of query being built.", "First discover the database schema, then match the result's column count."]),
    web("W7", "Template Studio", "template-studio", 300, "Medium", 0,
        "The card editor supports automatic fields. The preview context seems to contain more than a visitor's name. Find the internal audit code without leaving the preview application.",
        ["Does the server interpret expressions in your card?", "The page lists the objects made available to templates. Inspect their values."]),
    file("E1", "Archive Telegram", "26-archive-telegram", "Encoding", 75, "Easy", 1,
         "An archive tool exported a transport-safe telegram as printed octets. Restore the message the sender originally wrote.",
         ["Pairs of characters can represent bytes.", "After the first conversion, identify the new format before continuing."]),
    file("E2", "Machine Language", "04-ones-and-zeros", "Encoding", 50, "Easy", 0,
         "A device saved a short message as groups of zeroes and ones. Recover its text.",
         ["Each group contains eight bits.", "Convert the bytes into characters."]),
    file("C1", "Guard's Message", "03-julius-in-the-desert", "Cryptography", 100, "Easy", 3,
         "The guard shifts every letter by the same amount before sending a message. Digits and punctuation keep their places. Recover the original text.",
         ["You know how a flag begins.", "A Roman general used this kind of cipher."]),
    file("C2", "Known Beginning", "11-sandstorm-xor", "Cryptography", 250, "Medium", 2,
         "A sender reused a short key across an entire XOR-encrypted message. The message begins with a flag. Recover the key and the message.",
         ["A known part of the plaintext can reveal part of the key.", "Test short repeating key lengths against the known beginning."]),
    file("C3", "Close Neighbours", "12-close-primes", "Cryptography", 300, "Medium", 0,
         "The vault developer selected two large primes very close to each other. The public values and an encrypted message are all you have.",
         ["When two factors are close, their product is near a square.", "Look into Fermat factorization and exact integer square roots."]),
    file("F1", "The Photo Remembers", "28-photo-remembers", "Forensics", 100, "Easy", 1,
         "Someone removed the caption from a field-survey post. The original image survived. Find what the pixels alone do not tell you.",
         ["An image can contain text fields as well as pixels.", "Inspect the original file's metadata or readable strings."]),
    file("F2", "Two-Faced Report", "27-two-faced-report", "Forensics", 150, "Easy", 2,
         "The annual report refuses to open in a PDF reader. Before declaring it corrupt, identify what was actually sent. The reviewer kept a private handover note with it.",
         ["Extensions are labels; signatures describe content.", "Check for hidden review material after opening the real container."]),
    file("F3", "Excess Baggage", "33-image-luggage", "Forensics", 150, "Easy", 0,
         "A perfectly ordinary postcard carries more luggage than it displays. Recover the attached handover note.",
         ["The image's end may not be the file's end.", "Look for a second file format inside the postcard."]),
    file("F4", "Editor's Note", "32-editors-note", "Forensics", 100, "Easy", 0,
         "The public handover document looks ready. The editor may have forgotten to remove a review note before sending it out.",
         ["Review comments are separate from the main document text.", "A DOCX file is a package of XML parts."]),
    file("F5", "Invisible Ink", "29-invisible-ink", "Steganography", 200, "Medium", 3,
         "The conservation team calls this scan empty. The colour channels disagree. Recover the text hidden by the way the image is displayed.",
         ["Transparency controls visibility, not necessarily stored colour.", "Inspect the RGB data separately from the alpha channel."]),
    file("N1", "The Final Parcel", "30-final-parcel", "Network Forensics", 250, "Medium", 2,
         "Several login attempts were captured at the archive. Follow the successful session, identify what it downloaded, and recover the handover code from that file.",
         ["An HTTP response can distinguish a failed login from a successful one.", "Use the session cookie to follow the client, then export the downloaded object."]),
    file("N2", "Who Asked?", "31-who-asked", "Network Forensics", 100, "Easy", 0,
         "A resolver captured requests from several devices. Find the source IPv4 address that requested the domain specified in CASE.txt. Use the case-id and answer format in that file.",
         ["Inspect DNS questions and the source address of the matching packet."]),
    file("B1", "Dawn Shift", "10-who-broke-in", "Log Analysis", 150, "Easy", 1,
         "During your SOC shift, an SSH server shows repeated authentication failures. Find the attacking IPv4 address and the account it successfully entered. Submit `TAIBAH{<attacker_ip>_<username>_<case-id>}`; the case-id is on the first line of auth.log.",
         ["Compare repeated failures with the accepted login that follows."]),
    dict(key="O1", name="Call Me If You Can", kind="shared", category="OSINT", points=150,
         difficulty="Easy", batch=1,
         description='<div class="shared-handout"><p>You found a note on the ground: "Call me if you can." The number looks wrong for a telephone. Work out where it leads, identify the pizza takeaway at that spot, and find the branch telephone number published on its official website.</p><p>Use the attached note. Submit <code>TAIBAH{international_number}</code>: country code followed by the number, digits only, removing the domestic leading zero.</p><p>Do not call or message the business; public sources are enough.</p></div>',
         hints=["Those numbers may identify a place rather than a telephone.", "Use the branch's own contact page, not the group's old footer number."]),
]

assert len(CHALLENGES) == 21
assert len({item["key"] for item in CHALLENGES}) == len(CHALLENGES)
