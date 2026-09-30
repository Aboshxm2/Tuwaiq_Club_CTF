"""Round clock, visibility, per-team flags, and early-solve bonus."""

import datetime
import hmac
import secrets
import shutil
from pathlib import Path

from flask import current_app, request
from sqlalchemy.exc import IntegrityError

from CTFd.cache import clear_challenges, clear_standings
from CTFd.models import Awards, Challenges, Solves, db
from CTFd.utils import get_config, set_config
from CTFd.utils.user import get_current_user

from .models import (
    ACTIVE_STATES,
    ChallengeMeta,
    PersonalFlags,
    RoundBonuses,
    RoundChallenges,
    RoundFlagAlerts,
    Rounds,
)
from .personalize import generate

TOKEN_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


def speed_bonus_percent():
    try:
        return max(0, int(get_config("rounds:speed_bonus", 50)))
    except (TypeError, ValueError):
        return 50


def set_speed_bonus_percent(value):
    set_config("rounds:speed_bonus", int(value))


SHOWN_SCORE_VISIBILITIES = ("public", "private")


def scores_shown():
    return get_config("score_visibility") in SHOWN_SCORE_VISIBILITIES


def set_scores_shown(show):
    """Hide the scoreboard from players, or bring back the visibility it had before."""
    current = get_config("score_visibility")
    if show:
        if current not in SHOWN_SCORE_VISIBILITIES:
            previous = get_config("rounds:score_visibility_shown")
            if previous not in SHOWN_SCORE_VISIBILITIES:
                previous = "public"
            set_config("score_visibility", previous)
    else:
        if current in SHOWN_SCORE_VISIBILITIES:
            set_config("rounds:score_visibility_shown", current)
        set_config("score_visibility", "hidden")


def instance_root() -> Path:
    configured = current_app.config.get("ROUNDS_INSTANCE_DIR")
    if configured:
        root = Path(configured)
    else:
        root = Path(current_app.config.get("UPLOAD_FOLDER", "/var/uploads")).parent / "instances"
    root.mkdir(parents=True, exist_ok=True)
    return root


def account_of(user=None):
    user = user or get_current_user()
    if user is None:
        return None, None
    return user, user.account_id


def round_for_challenge(challenge_id):
    link = RoundChallenges.query.filter_by(challenge_id=challenge_id).first()
    return link.round if link else None


def active_round():
    return Rounds.query.filter(Rounds.state.in_(ACTIVE_STATES)).order_by(Rounds.position).first()


def apply_visibility():
    """Open only the active round. Every other challenge stays hidden."""
    current = active_round()
    open_ids = set(current.challenge_ids) if current else set()
    changed = False
    for challenge in Challenges.query.all():
        wanted = "visible" if challenge.id in open_ids else "hidden"
        if challenge.state != wanted:
            challenge.state = wanted
            changed = True
    if changed:
        db.session.commit()
        clear_challenges()
    return current


def tick():
    """End any running round whose clock has run out, then enforce visibility."""
    ended = False
    for rnd in Rounds.query.filter_by(state="running").all():
        if rnd.elapsed() >= rnd.duration:
            end_round(rnd)
            ended = True
    if not ended:
        apply_visibility()


def start_round(rnd: Rounds):
    other = (
        Rounds.query.filter(Rounds.id != rnd.id, Rounds.state.in_(ACTIVE_STATES)).first()
    )
    if other:
        return False, f"End {other.name} first. It is {other.state}."
    if not rnd.challenges:
        return False, "Add at least one challenge before starting this round."
    rnd.state = "running"
    rnd.started_at = datetime.datetime.utcnow()
    rnd.frozen_at = None
    rnd.ended_at = None
    rnd.paused_seconds = 0
    db.session.commit()
    apply_visibility()
    return True, f"{rnd.name} is open."


def freeze_round(rnd: Rounds):
    if rnd.state != "running":
        return False, "Only a running round can be frozen."
    rnd.state = "frozen"
    rnd.frozen_at = datetime.datetime.utcnow()
    db.session.commit()
    return True, f"{rnd.name} is frozen. The clock is paused and submissions are closed."


def resume_round(rnd: Rounds):
    if rnd.state != "frozen" or rnd.frozen_at is None:
        return False, "Only a frozen round can be resumed."
    paused = (datetime.datetime.utcnow() - rnd.frozen_at).total_seconds()
    rnd.paused_seconds += int(paused)
    rnd.frozen_at = None
    rnd.state = "running"
    db.session.commit()
    apply_visibility()
    return True, f"{rnd.name} is running again."


def end_round(rnd: Rounds):
    if rnd.state not in ACTIVE_STATES:
        return False, "This round is not running."
    if rnd.state == "frozen" and rnd.frozen_at is not None:
        rnd.paused_seconds += int((datetime.datetime.utcnow() - rnd.frozen_at).total_seconds())
        rnd.frozen_at = None
    rnd.state = "ended"
    rnd.ended_at = datetime.datetime.utcnow()
    db.session.commit()
    apply_visibility()
    clear_standings()
    return True, f"{rnd.name} has ended. Its points stay on the scoreboard."


def submission_block_reason(challenge):
    rnd = round_for_challenge(challenge.id)
    if rnd is None:
        return None
    if rnd.state == "running" and rnd.elapsed() >= rnd.duration:
        end_round(rnd)
        db.session.refresh(rnd)
    if rnd.state == "running":
        return None
    if rnd.state == "frozen":
        return "This round is frozen. Submissions are paused."
    if rnd.state == "ended":
        return "This round has ended."
    return "This round has not started."


def _new_token(challenge_id):
    for _ in range(20):
        token = "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(4))
        if not PersonalFlags.query.filter_by(challenge_id=challenge_id, token=token).first():
            return token
    raise RuntimeError("Could not allocate a unique instance token")


def launch_instance(challenge, user=None):
    user, account_id = account_of(user)
    if user is None:
        return False, "Log in first.", None
    if account_id is None:
        return False, "Create or join a team first. A team of one is allowed.", None
    meta = ChallengeMeta.query.filter_by(challenge_id=challenge.id).first()
    if meta is None:
        return False, "This challenge has no instance generator.", None
    reason = submission_block_reason(challenge)
    existing = PersonalFlags.query.filter_by(
        account_id=account_id, challenge_id=challenge.id
    ).first()
    folder = instance_root() / str(account_id) / str(challenge.id)
    bundle = folder / "bundle.zip"
    if existing:
        if not bundle.is_file():
            folder.mkdir(parents=True, exist_ok=True)
            flag = generate(meta.slug, existing.token, folder)
            if flag != existing.flag:
                raise RuntimeError("Regenerated flag does not match the stored flag")
        return True, "Your instance is ready.", existing
    if reason:
        if reason.startswith("This round is frozen"):
            return False, "This round is frozen. New instances are paused.", None
        return False, reason, None

    folder.mkdir(parents=True, exist_ok=True)
    token = _new_token(challenge.id)
    try:
        flag = generate(meta.slug, token, folder)
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    row = PersonalFlags(
        account_id=account_id,
        challenge_id=challenge.id,
        flag=flag,
        token=token,
    )
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        row = PersonalFlags.query.filter_by(
            account_id=account_id, challenge_id=challenge.id
        ).first()
        if row is None:
            raise
    return True, "Your instance is ready.", row


def bundle_path(account_id, challenge_id) -> Path:
    return instance_root() / str(account_id) / str(challenge_id) / "bundle.zip"


def grade_personal(challenge, source_request=None):
    source_request = source_request or request
    data = source_request.form or source_request.get_json(silent=True) or {}
    submission = str(data.get("submission", "")).strip()
    user, account_id = account_of()
    if user is None:
        return False, "Log in first."
    if account_id is None:
        return False, "Create or join a team first. A team of one is allowed."
    if len(submission) > 200:
        return False, "Incorrect"
    own = PersonalFlags.query.filter_by(
        account_id=account_id, challenge_id=challenge.id
    ).first()
    if own is None:
        return False, "Launch your instance first. Your flag is unique to your team."
    if hmac.compare_digest(own.flag, submission):
        return True, "Correct"
    stolen = PersonalFlags.query.filter_by(challenge_id=challenge.id, flag=submission).first()
    if stolen is not None and stolen.account_id != account_id:
        db.session.add(
            RoundFlagAlerts(
                challenge_id=challenge.id,
                user_id=user.id,
                account_id=account_id,
                owner_account_id=stolen.account_id,
                provided=submission,
            )
        )
        db.session.commit()
        return False, "That flag belongs to another team. It does not score."
    return False, "Incorrect"


def award_for_solve(user, team, challenge):
    """Add extra points that shrink to zero as the round clock runs out."""
    percent = speed_bonus_percent()
    if percent <= 0 or not challenge.value:
        return
    rnd = round_for_challenge(challenge.id)
    if rnd is None or rnd.started_at is None:
        return
    solve = (
        Solves.query.filter_by(user_id=user.id, challenge_id=challenge.id)
        .order_by(Solves.id.desc())
        .first()
    )
    if solve is None:
        return
    if RoundBonuses.query.filter_by(solve_id=solve.id, kind="speed").first():
        return
    ratio = max(0.0, 1.0 - (rnd.elapsed() / max(rnd.duration, 1)))
    bonus = int(round(challenge.value * (percent / 100.0) * ratio))
    if bonus <= 0:
        return
    award = Awards(
        user_id=user.id,
        team_id=team.id if team else None,
        name=f"Early solve: {challenge.name}"[:80],
        description=f"Solved early in {rnd.name}.",
        value=bonus,
        category="Speed bonus",
    )
    db.session.add(award)
    db.session.commit()
    db.session.add(RoundBonuses(solve_id=solve.id, award_id=award.id, kind="speed"))
    db.session.commit()
    clear_standings()


def public_status(user=None):
    tick()
    rnd = active_round()
    user = user if user is not None else get_current_user()
    payload = {
        "success": True,
        "speed_bonus_percent": speed_bonus_percent(),
        "user_mode": get_config("user_mode"),
        "team_size": int(get_config("team_size") or 0),
        "has_account": bool(user and user.account_id),
        "round": None,
    }
    if rnd is None:
        return payload
    payload["round"] = {
        "id": rnd.id,
        "name": rnd.name,
        "state": rnd.state,
        "position": rnd.position,
        "duration": rnd.duration,
        "remaining": int(rnd.remaining()),
        "elapsed": int(rnd.elapsed()),
    }
    return payload
