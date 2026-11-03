#!/usr/bin/env python3
"""Stage the curated pack without starting a round or deleting legacy data.

Default: print the plan, no writes. Apply only after a backup, image builds and
CTFd deployment, with global Pause CTF enabled. Existing started pack rounds,
pack solves or generated instances make staging refuse to alter the pack.
"""
import argparse
import importlib
import io
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/opt/CTFd")


def stage(round_name, osint_phone, apply=False):
    from CTFd.models import Challenges, ChallengeFiles, Flags, Hints, Solves, Tags, db
    from CTFd.utils import get_config
    from CTFd.utils.uploads import upload_file
    from CTFd.cache import clear_challenges
    from werkzeug.datastructures import FileStorage

    plugin = "CTFd.plugins.ctfd-rounds"
    catalog = importlib.import_module(plugin + ".curated_catalog")
    files = importlib.import_module(plugin + ".curated_files")
    models = importlib.import_module(plugin + ".models")
    docker = importlib.import_module("CTFd.plugins.ctfd-whale.models").DynamicDockerChallenge
    tag_value = "curated-pack-v1"
    items = catalog.CHALLENGES
    rnd = models.Rounds.query.filter_by(name=round_name).first()
    if rnd and rnd.state != "pending":
        raise RuntimeError("The pack round has started; staging is not allowed.")
    by_key = {}
    for item in items:
        tagged = Tags.query.filter_by(value=tag_value + ":" + item["key"]).first()
        existing = Challenges.query.get(tagged.challenge_id) if tagged else None
        if not existing:
            existing = Challenges.query.filter_by(name=item["name"]).first()
            # The OSINT draft may already have been staged through the admin UI.
            if existing and not (item["kind"] == "shared" and existing.state == "hidden"
                                 and existing.category == "OSINT" and "shared-handout" in existing.description):
                raise RuntimeError("Unmanaged challenge name conflict: " + item["name"])
        if existing:
            if Solves.query.filter_by(challenge_id=existing.id).first() or models.PersonalFlags.query.filter_by(challenge_id=existing.id).first():
                raise RuntimeError("Pack challenge already has participant activity: " + item["name"])
            expected = "dynamic_docker" if item["kind"] == "web" else "standard"
            if existing.type != expected:
                raise RuntimeError("Challenge type conflict: " + item["name"])
        by_key[item["key"]] = existing
        print(("UPDATE " if existing else "CREATE ") + item["name"] + " [hidden]")
    if not apply:
        print("Dry run only. No changes were written.")
        return
    if not get_config("paused"):
        raise RuntimeError("Enable Pause CTF before staging the pack.")
    if not re.fullmatch(r"[1-9][0-9]{6,14}", osint_phone or ""):
        raise RuntimeError("Set CURATED_OSINT_PHONE to the verified international digits, without + or a domestic leading zero.")

    for index, item in enumerate(items, start=1):
        challenge = by_key[item["key"]]
        if not challenge:
            cls = docker if item["kind"] == "web" else Challenges
            challenge = cls(name=item["name"], value=item["points"], category=item["category"],
                            type="dynamic_docker" if item["kind"] == "web" else "standard", state="hidden")
            db.session.add(challenge)
            db.session.flush()
        challenge.name = item["name"]
        challenge.description = item["description"]
        challenge.category = item["category"]
        challenge.value = item["points"]
        challenge.position = 100 + index
        challenge.state = "hidden"
        if item["kind"] == "web":
            challenge.initial = challenge.minimum = item["points"]
            challenge.decay = 0
            challenge.dynamic_score = 0
            challenge.docker_image = "taibah-ctf/curated-" + item["mode"] + ":v1"
            challenge.redirect_type = "http"
            challenge.redirect_port = 8080
            challenge.memory_limit = "128m"
            challenge.cpu_limit = 0.5
        else:
            challenge.function = "static"
        if item["kind"] == "file":
            meta = models.ChallengeMeta.query.filter_by(challenge_id=challenge.id).first()
            if not meta:
                db.session.add(models.ChallengeMeta(challenge_id=challenge.id, slug=item["slug"]))
            elif meta.slug != item["slug"]:
                raise RuntimeError("Generator mapping conflict")
        if not Tags.query.filter_by(challenge_id=challenge.id, value=tag_value + ":" + item["key"]).first():
            db.session.add(Tags(challenge_id=challenge.id, value=tag_value + ":" + item["key"]))
        for tag in (item["difficulty"], "Batch " + str(item["batch"]) if item["batch"] else "Reserve"):
            if not Tags.query.filter_by(challenge_id=challenge.id, value=tag).first():
                db.session.add(Tags(challenge_id=challenge.id, value=tag))
        for index_hint, content in enumerate(item["hints"], start=1):
            title = "Hint " + str(index_hint)
            hint = Hints.query.filter_by(challenge_id=challenge.id, title=title).first()
            if not hint:
                db.session.add(Hints(challenge_id=challenge.id, title=title, content=content, cost=0))
            else:
                hint.content = content
        by_key[item["key"]] = challenge
    if not rnd:
        rnd = models.Rounds(name=round_name, duration=180 * 60, position=100, state="pending")
        db.session.add(rnd)
    db.session.flush()
    # Only the initial batch is assigned. Later batches are added cumulatively
    # through Rounds admin, using the saved release plan. No existing links move.
    for item in items:
        if item["batch"] != 1:
            continue
        challenge = by_key[item["key"]]
        linked = models.RoundChallenges.query.filter_by(challenge_id=challenge.id).first()
        if linked and linked.round_id != rnd.id:
            raise RuntimeError("A pack challenge is already assigned to another round")
        if not linked:
            db.session.add(models.RoundChallenges(round_id=rnd.id, challenge_id=challenge.id))
    shared = by_key["O1"]
    answer = "TAIBAH{" + osint_phone + "}"
    old_flags = Flags.query.filter_by(challenge_id=shared.id).all()
    if old_flags and any(row.content != answer for row in old_flags):
        raise RuntimeError("Existing OSINT flag differs from verified number")
    if not old_flags:
        db.session.add(Flags(challenge_id=shared.id, type="static", content=answer, data=""))
    db.session.commit()

    # CTFd's upload utility commits its own database row and supports both disk
    # and S3 providers. A failed upload leaves the pack hidden and can be retried.
    if not ChallengeFiles.query.filter_by(challenge_id=shared.id).first():
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            files.osint_handout(folder)
            content = (folder / "found-note.png").read_bytes()
            upload_file(file=FileStorage(stream=io.BytesIO(content), filename="found-note.png"), type="challenge", challenge_id=shared.id)
    clear_challenges()
    print("Pack staged. The round is pending. Pause CTF and scoreboard settings were not changed; the event was not started.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--round", default="Students - Wednesday")
    args = parser.parse_args()
    from CTFd import create_app
    app = create_app()
    with app.app_context():
        stage(args.round, os.environ.get("CURATED_OSINT_PHONE", ""), apply=args.apply)


if __name__ == "__main__":
    main()
