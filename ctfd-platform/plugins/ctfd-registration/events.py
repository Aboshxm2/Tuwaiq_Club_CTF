"""Event membership and clocks. Disabled until an administrator enables it."""

import datetime

from flask import has_request_context

from CTFd.cache import clear_challenges, clear_standings, clear_team_session
from CTFd.models import Awards, Brackets, Challenges, Solves, Teams, Users, db
from CTFd.utils import get_config
from CTFd.utils.user import get_current_user

from .events_models import EventChallenges, EventTeams, EventUsers, WorkshopEvents


def enabled():
    return bool(get_config("workshop:events_enabled", False))


def user_event(user=None):
    user = user or (get_current_user() if has_request_context() else None)
    membership = EventUsers.query.filter_by(user_id=user.id).first() if user else None
    return WorkshopEvents.query.get(membership.event_id) if membership else None


def team_event(team_id):
    membership = EventTeams.query.filter_by(team_id=team_id).first()
    return WorkshopEvents.query.get(membership.event_id) if membership else None


def expire_events():
    changed = False
    for event in WorkshopEvents.query.filter_by(state="running").all():
        if event.remaining() == 0:
            event.state = "ended"
            event.ended_at = event.started_at + datetime.timedelta(
                seconds=event.duration + event.paused_seconds
            )
            changed = True
    if changed:
        db.session.commit()
        apply_visibility()


def apply_visibility():
    """CTFd visibility is the union; request guards enforce each event's subset."""
    open_ids = {
        row.challenge_id for row in EventChallenges.query.join(
            WorkshopEvents, EventChallenges.event_id == WorkshopEvents.id
        ).filter(
            WorkshopEvents.state.in_(("running", "frozen")),
            EventChallenges.released.is_(True),
        ).all()
    }
    for challenge in Challenges.query.all():
        challenge.state = "visible" if challenge.id in open_ids else "hidden"
    db.session.commit()
    clear_challenges()


def visible_challenge_ids(event):
    if event is None or event.state not in ("running", "frozen"):
        return set()
    if event.state == "running" and event.remaining() == 0:
        return set()
    return {row.challenge_id for row in EventChallenges.query.filter_by(
        event_id=event.id, released=True
    )}


def block_reason(challenge_id, user=None, writing=True):
    from CTFd.utils.dates import ctf_paused, ctftime

    if get_config("challenge_visibility") == "admins":
        return "Challenges are currently restricted to administrators."
    if writing and (ctf_paused() or not ctftime()):
        return "The competition is currently closed for submissions."
    event = user_event(user)
    if event is None:
        return "Choose your event before playing."
    if challenge_id not in visible_challenge_ids(event):
        return "This challenge is not open in your event."
    if writing and event.state != "running":
        return "This event is paused. Submissions and new instances are closed."
    if writing and not event.remaining():
        return "This event has ended."
    return None


def scores_shown(event):
    return bool(event and event.scores_visible and get_config("score_visibility") in ("public", "private"))


def event_team_ids(event):
    return {row.team_id for row in EventTeams.query.filter_by(event_id=event.id)}


def event_user_ids(event):
    return {row.user_id for row in EventUsers.query.filter_by(event_id=event.id)}


def standings(event):
    # Membership cannot change after a team has scores. CTFd's tie-breaking,
    # hint deductions, freeze time and awards therefore remain authoritative.
    from CTFd.utils.scores import get_standings

    teams = event_team_ids(event)
    return [row for row in get_standings(bracket_id=event.bracket_id) if row.account_id in teams]


def sync_teams():
    """Keep event brackets stable; never classify these teams by experience."""
    changed = False
    for membership in EventTeams.query.all():
        team = Teams.query.get(membership.team_id)
        event = WorkshopEvents.query.get(membership.event_id)
        if team and event and team.bracket_id != event.bracket_id:
            team.bracket_id = event.bracket_id
            clear_team_session(team_id=team.id)
            changed = True
    if changed:
        db.session.commit()
        clear_standings()


def assign_user(user, event):
    """Assign before play only. Assign a whole existing team as one unit."""
    users = Users.query.filter_by(team_id=user.team_id).all() if user.team_id else [user]
    ids = [member.id for member in users]
    team = Teams.query.get(user.team_id) if user.team_id else None
    old = team_event(team.id) if team else None
    if old and old.id != event.id:
        raise ValueError("A team already assigned to an event cannot be moved.")
    for member in users:
        current = user_event(member)
        if current and current.id != event.id:
            raise ValueError("A registered participant cannot switch events.")
    if Solves.query.filter(Solves.user_id.in_(ids)).first() or Awards.query.filter(
        Awards.user_id.in_(ids)
    ).first() or (team and Awards.query.filter_by(team_id=team.id).first()):
        raise ValueError("Accounts with existing scores cannot be reassigned. Use a new account for this event.")
    for member in users:
        if EventUsers.query.get(member.id) is None:
            db.session.add(EventUsers(user_id=member.id, event_id=event.id))
    if team:
        if EventTeams.query.get(team.id) is None:
            db.session.add(EventTeams(team_id=team.id, event_id=event.id))
        team.bracket_id = event.bracket_id
        clear_team_session(team_id=team.id)
    db.session.commit()
    clear_standings()


def ensure_default_events():
    for slug, name in (("boys", "الطلاب — الأربعاء"), ("girls", "الطالبات — الخميس")):
        if WorkshopEvents.query.filter_by(slug=slug).first():
            continue
        bracket = Brackets.query.filter_by(name=name, type="teams").first()
        if bracket is None:
            bracket = Brackets(name=name, description="تصنيف فرق الفعالية", type="teams")
            db.session.add(bracket)
            db.session.flush()
        db.session.add(WorkshopEvents(slug=slug, name=name, bracket_id=bracket.id))
    db.session.commit()


def action(event, verb):
    now = datetime.datetime.utcnow()
    if verb == "start":
        if event.state != "pending":
            raise ValueError("Only a pending event can start. Ended events cannot restart.")
        if not EventChallenges.query.filter_by(event_id=event.id).first():
            raise ValueError("Assign challenges before starting the event.")
        event.state, event.started_at = "running", now
        event.registration_open = False
    elif verb == "pause" and event.state == "running":
        event.state, event.frozen_at = "frozen", now
    elif verb == "resume" and event.state == "frozen":
        event.paused_seconds += int((now - event.frozen_at).total_seconds())
        event.state, event.frozen_at = "running", None
    elif verb == "end" and event.state in ("running", "frozen"):
        if event.frozen_at:
            event.paused_seconds += int((now - event.frozen_at).total_seconds())
        event.state, event.ended_at, event.frozen_at = "ended", now, None
        event.registration_open = False
    else:
        raise ValueError("This action is not available in the current event state.")
    db.session.commit()
    apply_visibility()


def status(user=None):
    expire_events()
    event = user_event(user)
    user = user or get_current_user()
    return {
        "success": True, "event_mode": True, "speed_bonus_percent": 0,
        "user_mode": get_config("user_mode"), "team_size": int(get_config("team_size") or 0),
        "has_account": bool(user and user.account_id),
        "round": None if event is None else {
            "id": event.id, "name": event.name, "state": event.state,
            "duration": event.duration, "remaining": event.remaining(), "elapsed": event.elapsed(),
        },
    }


def install(app):
    from .event_admin import register_admin
    from .event_views import register_views

    app.db.create_all()
    register_admin(app)
    register_views(app)
