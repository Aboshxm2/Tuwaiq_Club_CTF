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

CTF_NAME = "Tuwaiq CTF"
THEME = "tuwaiq"

# The tw-* classes come from the Tuwaiq theme (themes/tuwaiq/static/css/tuwaiq.css).
HOME_HTML = """
<div class="tw-hero">
  <div class="tw-hero-logos">
    <img class="tw-hero-logo" src="/themes/tuwaiq/static/img/taibah-university.png" alt="Taibah University">
    <span class="tw-hero-divider" aria-hidden="true"></span>
    <img class="tw-hero-logo" src="/themes/tuwaiq/static/img/tuwaiq-club.png" alt="Tuwaiq Club">
  </div>
  <h1>Tuwaiq CTF</h1>
  <p class="lead">Final day of the cybersecurity workshop. Five rounds, one scoreboard.</p>
  <div class="tw-hero-actions">
    <a class="btn btn-light btn-lg" href="/challenges">Challenges</a>
    <a class="btn btn-outline-light btn-lg" href="/scoreboard">Scoreboard</a>
  </div>
</div>

<h2 class="tw-section-title">How to play</h2>
<ol class="tw-steps">
  <li><span class="tw-num">01</span>Register, then create a team. Play alone by being the only member, or invite up to 2 teammates (3 people total).</li>
  <li><span class="tw-num">02</span>Challenges open one round at a time. When a round ends, its challenges close. Points you already earned stay on the scoreboard.</li>
  <li><span class="tw-num">03</span>Open a challenge and click <strong>Launch instance</strong>. Download the files. They were generated for your team.</li>
  <li><span class="tw-num">04</span>Submit the flag you recover. A flag copied from another team will not score.</li>
  <li><span class="tw-num">05</span>Solving earlier in the round earns extra points. The bonus falls to zero as the clock runs out.</li>
</ol>

<div class="row g-4 mt-2 mb-4">
  <div class="col-lg-7">
    <div class="tw-panel">
      <h3>Rules</h3>
      <ul class="tw-list">
        <li>Do not attack the scoreboard, the platform, or other teams.</li>
        <li>Do not share flags. Sharing a flag does not give the other team points.</li>
        <li>Search engines and tools such as CyberChef, Wireshark, and Ghidra are allowed. Chatbots and AI assistants are not.</li>
      </ul>
    </div>
  </div>
  <div class="col-lg-5">
    <div class="tw-panel">
      <h3>Flag format</h3>
      <p><span class="tw-flag">TAIBAH{...}</span></p>
      <p class="mb-0">Flags are case-sensitive. Submit the whole thing, including <code>TAIBAH{</code> and <code>}</code>.</p>
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
        set_config("team_size", 3)
        set_config("ctf_name", CTF_NAME)
        return

    password = os.environ.get("CTFD_ADMIN_PASSWORD", "")
    if len(password) < 8:
        sys.exit("Set CTFD_ADMIN_PASSWORD to at least 8 characters, then run this script again.")
    name = os.environ.get("CTFD_ADMIN_NAME", "admin")
    email = os.environ.get("CTFD_ADMIN_EMAIL", "admin@taibah.local")

    set_config("ctf_name", CTF_NAME)
    set_config("ctf_description", "Final-day workshop CTF. Five timed rounds, one scoreboard.")
    set_config("user_mode", "teams")
    set_config("team_size", 3)
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
    page = Pages(title=CTF_NAME, route="index", content=HOME_HTML, draft=False)
    db.session.add(admin)
    db.session.add(page)
    db.session.commit()
    print(f"Created admin {name} ({email})")


def main():
    from CTFd import create_app
    from CTFd.cache import clear_challenges, clear_config, clear_standings
    from CTFd.models import Admins, Challenges, Pages, Users, db
    from CTFd.utils import get_config, set_config
    from CTFd.utils import config

    app = create_app()
    with app.app_context():
        import importlib

        catalog = importlib.import_module("CTFd.plugins.ctfd-rounds.catalog")
        models = importlib.import_module("CTFd.plugins.ctfd-rounds.models")
        whale_models = importlib.import_module("CTFd.plugins.ctfd-whale.models")
        DynamicDockerChallenge = whale_models.DynamicDockerChallenge
        registration = importlib.import_module("CTFd.plugins.ctfd-registration")

        ensure_setup(db, set_config, get_config, config, Users, Admins, Pages, None)
        page = Pages.query.filter_by(route="index").first()
        if page is not None:
            page.title = CTF_NAME
            page.content = HOME_HTML
        set_config("ctf_theme", THEME)
        set_config("user_mode", "teams")
        set_config("team_size", "3")
        set_config("rounds:speed_bonus", get_config("rounds:speed_bonus") or 50)
        set_config("whale:frequency_limit", 5)
        # Deployable challenges get a per-team flag from whale in the event format.
        set_config("whale:template_chall_flag", "TAIBAH{{ '{' }}{{ uuid.uuid4().hex }}{{ '}' }}")
        registration.ensure_fields()
        # One scoreboard bracket per level; teams are placed by their members.
        registration.ensure_brackets()
        registration.sync_team_brackets()

        def upsert_file_challenge(item, description):
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
            return challenge

        def upsert_deployable_challenge(item, deploy):
            # A challenge served as a live container (dynamic_docker) instead of a
            # downloadable bundle. No ChallengeMeta and no static Flags: whale
            # generates the per-team flag and checks it.
            challenge = Challenges.query.filter_by(name=item["name"]).first()
            if challenge is not None and challenge.type != "dynamic_docker":
                # This slug used to be a file challenge. Drop it and recreate it as
                # a container challenge. Do this before the event; it removes the
                # old challenge's solves.
                old_meta = models.ChallengeMeta.query.filter_by(slug=item["slug"]).first()
                if old_meta:
                    db.session.delete(old_meta)
                print(f"Converting {item['name']} from a file challenge to a container challenge.")
                db.session.delete(challenge)
                db.session.flush()
                challenge = None
            if challenge is None:
                challenge = DynamicDockerChallenge(
                    name=item["name"],
                    description=deploy["description"],
                    value=item["points"],
                    category=item["category"],
                    state="hidden",
                )
                challenge.position = int(item["slug"][:2])
                db.session.add(challenge)
                db.session.flush()
            else:
                challenge.description = deploy["description"]
                challenge.value = item["points"]
                challenge.category = item["category"]
            challenge.initial = item["points"]
            challenge.minimum = item["points"]
            challenge.decay = 0
            challenge.dynamic_score = 0
            challenge.docker_image = deploy["image"]
            challenge.redirect_type = deploy["redirect_type"]
            challenge.redirect_port = deploy["redirect_port"]
            challenge.memory_limit = deploy["memory_limit"]
            challenge.cpu_limit = deploy["cpu_limit"]
            return challenge

        by_slug = {}
        for item in catalog.CHALLENGES:
            deploy = catalog.DEPLOYABLE.get(item["slug"])
            if deploy:
                challenge = upsert_deployable_challenge(item, deploy)
            else:
                challenge = upsert_file_challenge(item, parse_readme(item["slug"], catalog.NOTES))
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
        clear_standings()
        print(f"Imported {len(by_slug)} challenges into {len(catalog.ROUNDS)} rounds.")
        print("All challenges are hidden until you press Start on the Rounds admin page.")


if __name__ == "__main__":
    main()
