#!/usr/bin/env python3
"""Create the admin account (once), the 20 challenges, and the five rounds.

Run inside the CTFd container after it is up:

    docker compose exec -e CTFD_ADMIN_PASSWORD=... ctfd python /ctf/ctfd-platform/scripts/import_ctf.py
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, "/opt/CTFd")

REPO = Path(os.environ.get("CTF_REPO", "/ctf"))
README_ROOT = REPO / "challenges"

HOME_HTML = """
<div class="container py-5">
  <div class="row">
    <div class="col-lg-8 offset-lg-2">
      <h1 class="text-center">Taibah University CTF</h1>
      <p class="lead text-center">Final day of the cybersecurity workshop. Five rounds, one scoreboard.</p>
      <h3>How to play</h3>
      <ol>
        <li>Register, then create a team. Play alone by being the only member, or invite up to 4 teammates (5 people total).</li>
        <li>Challenges open one round at a time. When a round ends, its challenges close. Points you already earned stay on the scoreboard.</li>
        <li>Open a challenge and click <strong>Launch instance</strong>. Download the files. They were generated for your team.</li>
        <li>Submit the flag you recover. A flag copied from another team will not score.</li>
        <li>Solving earlier in the round earns extra points. The bonus falls to zero as the clock runs out.</li>
      </ol>
      <h3>Rules</h3>
      <ul>
        <li>Do not attack the scoreboard, the platform, or other teams.</li>
        <li>Do not share flags. Sharing a flag does not give the other team points.</li>
        <li>Search engines and tools such as CyberChef, Wireshark, and Ghidra are allowed. Chatbots and AI assistants are not.</li>
      </ul>
      <p>Flag format: <code>TAIBAH{...}</code>. It is case-sensitive.</p>
    </div>
  </div>
</div>
"""


def section(text, heading):
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return match.group(1).strip() if match else ""


def strip_fences(text):
    return re.sub(r"```.*?```", "", text, flags=re.S).strip()


def strip_payload_lines(text):
    kept = []
    for line in text.splitlines():
        token = line.strip().strip("`")
        if re.fullmatch(r"[A-Za-z0-9+/=]{20,}", token):
            continue
        if re.fullmatch(r"[A-Fa-f0-9]{32}", token):
            continue
        if re.fullmatch(r"[01 ]{16,}", token):
            continue
        if token.startswith("WDLEDK{") or token.startswith("VEFJQk"):
            continue
        kept.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def parse_readme(slug, notes):
    folder = README_ROOT / slug / "README.md"
    text = folder.read_text()
    body = strip_payload_lines(strip_fences(section(text, "Description")))
    parts = [
        "Launch an instance to download files made only for your team. "
        "The flag inside them scores for your team and for nobody else.",
        body,
    ]
    if slug in notes:
        parts.append(notes[slug])
    description = "\n\n".join(part for part in parts if part)
    return description


def ensure_setup(db, set_config, get_config, config, Users, Admins, Pages, Teams):
    if config.is_setup():
        set_config("user_mode", "teams")
        set_config("team_size", 5)
        set_config("ctf_name", "Taibah University CTF")
        return

    password = os.environ.get("CTFD_ADMIN_PASSWORD", "")
    if len(password) < 8:
        sys.exit("Set CTFD_ADMIN_PASSWORD to at least 8 characters, then run this script again.")
    name = os.environ.get("CTFD_ADMIN_NAME", "admin")
    email = os.environ.get("CTFD_ADMIN_EMAIL", "admin@taibah.local")

    set_config("ctf_name", "Taibah University CTF")
    set_config("ctf_description", "Final-day workshop CTF. Five timed rounds, one scoreboard.")
    set_config("user_mode", "teams")
    set_config("team_size", 5)
    set_config("challenge_visibility", "private")
    set_config("account_visibility", "public")
    set_config("score_visibility", "public")
    set_config("registration_visibility", "public")
    set_config("verify_emails", None)
    set_config("start", None)
    set_config("end", None)
    set_config("freeze", None)
    set_config("setup", True)
    set_config("rounds:speed_bonus", 50)
    set_config("whale:frequency_limit", 5)

    admin = Admins(name=name, email=email, password=password, type="admin", hidden=True)
    page = Pages(title="Taibah University CTF", route="index", content=HOME_HTML, draft=False)
    db.session.add(admin)
    db.session.add(page)
    db.session.commit()
    print(f"Created admin {name} ({email})")


def main():
    from CTFd import create_app
    from CTFd.cache import clear_challenges, clear_config
    from CTFd.models import Admins, Challenges, Pages, Users, db
    from CTFd.utils import get_config, set_config
    from CTFd.utils import config

    app = create_app()
    with app.app_context():
        import importlib

        catalog = importlib.import_module("CTFd.plugins.ctfd-rounds.catalog")
        models = importlib.import_module("CTFd.plugins.ctfd-rounds.models")

        ensure_setup(db, set_config, get_config, config, Users, Admins, Pages, None)
        page = Pages.query.filter_by(route="index").first()
        if page is not None:
            page.content = HOME_HTML
        set_config("user_mode", "teams")
        set_config("team_size", "5")
        set_config("rounds:speed_bonus", get_config("rounds:speed_bonus") or 50)
        set_config("whale:frequency_limit", 5)

        by_slug = {}
        for item in catalog.CHALLENGES:
            description = parse_readme(item["slug"], catalog.NOTES)
            meta = models.ChallengeMeta.query.filter_by(slug=item["slug"]).first()
            if meta:
                challenge = Challenges.query.get(meta.challenge_id)
                challenge.name = item["name"]
                challenge.description = description
                challenge.value = item["points"]
                challenge.category = item["category"]
            else:
                challenge = Challenges(
                    name=item["name"],
                    description=description,
                    value=item["points"],
                    category=item["category"],
                    state="hidden",
                    type="standard",
                    position=int(item["slug"][:2]),
                )
                db.session.add(challenge)
                db.session.flush()
                db.session.add(models.ChallengeMeta(challenge_id=challenge.id, slug=item["slug"]))
            by_slug[item["slug"]] = challenge
        db.session.commit()

        for spec in catalog.ROUNDS:
            rnd = models.Rounds.query.filter_by(name=spec["name"]).first()
            if rnd is None:
                rnd = models.Rounds(
                    name=spec["name"],
                    duration=spec["minutes"] * 60,
                    position=spec["position"],
                    state="pending",
                )
                db.session.add(rnd)
                db.session.flush()
            elif rnd.state == "pending":
                rnd.duration = spec["minutes"] * 60
                rnd.position = spec["position"]
            if rnd.state == "pending":
                models.RoundChallenges.query.filter_by(round_id=rnd.id).delete(
                    synchronize_session=False
                )
                db.session.flush()
                for slug in spec["slugs"]:
                    challenge = by_slug[slug]
                    models.RoundChallenges.query.filter_by(challenge_id=challenge.id).delete(
                        synchronize_session=False
                    )
                    db.session.flush()
                    db.session.add(
                        models.RoundChallenges(round_id=rnd.id, challenge_id=challenge.id)
                    )
        db.session.commit()
        clear_challenges()
        clear_config()
        print(f"Imported {len(by_slug)} challenges into {len(catalog.ROUNDS)} rounds.")
        print("All challenges are hidden until you press Start on the Rounds admin page.")


if __name__ == "__main__":
    main()
