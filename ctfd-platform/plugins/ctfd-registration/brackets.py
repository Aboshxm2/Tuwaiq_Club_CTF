"""One scoreboard bracket per level.

Level is chosen per player at registration, but in teams mode CTFd brackets
belong to teams. A team is placed in the bracket of its most experienced
member: one Advanced member makes the whole team Advanced. A team whose
members have no level (older accounts, admins) counts as Beginner.
"""

from CTFd.models import Brackets, Teams, UserFieldEntries, UserFields, Users, db

LEVEL_FIELD = "Level"
LEVELS = ("Beginner", "Intermediate", "Advanced")
BRACKET_TYPE = "teams"
DESCRIPTIONS = {
    "Beginner": "Teams whose most experienced member is a Beginner.",
    "Intermediate": "Teams whose most experienced member is Intermediate.",
    "Advanced": "Teams with at least one Advanced member.",
}


def ensure_brackets():
    """Create the three team brackets once. Safe to call repeatedly."""
    existing = {b.name for b in Brackets.query.filter_by(type=BRACKET_TYPE).all()}
    for level in LEVELS:
        if level not in existing:
            db.session.add(
                Brackets(name=level, description=DESCRIPTIONS[level], type=BRACKET_TYPE)
            )
    db.session.commit()


def bracket_ids():
    """Map level name to bracket id. Empty if the brackets do not exist."""
    rows = Brackets.query.filter(
        Brackets.type == BRACKET_TYPE, Brackets.name.in_(LEVELS)
    ).all()
    return {row.name: row.id for row in rows}


def team_level(levels):
    """The highest known level in `levels`, or Beginner if none is known."""
    ranks = [LEVELS.index(level) for level in levels if level in LEVELS]
    return LEVELS[max(ranks)] if ranks else LEVELS[0]


def user_level(user_id):
    row = (
        db.session.query(UserFieldEntries.value)
        .join(UserFields, UserFieldEntries.field_id == UserFields.id)
        .filter(UserFields.name == LEVEL_FIELD, UserFieldEntries.user_id == user_id)
        .first()
    )
    return row.value.strip() if row and row.value else None


def sync_team_brackets():
    """Put every team in its level's bracket. Returns how many teams moved."""
    ids = bracket_ids()
    if len(ids) != len(LEVELS):
        return 0

    level_of_user = {
        user_id: (value or "").strip()
        for user_id, value in db.session.query(
            UserFieldEntries.user_id, UserFieldEntries.value
        )
        .join(UserFields, UserFieldEntries.field_id == UserFields.id)
        .filter(UserFields.name == LEVEL_FIELD)
        .all()
    }
    members = {}
    for user_id, team_id in db.session.query(Users.id, Users.team_id).filter(
        Users.team_id.isnot(None)
    ):
        members.setdefault(team_id, []).append(level_of_user.get(user_id))

    moved = 0
    for team in Teams.query.all():
        want = ids[team_level(members.get(team.id, []))]
        if team.bracket_id != want:
            team.bracket_id = want
            moved += 1
    if moved:
        db.session.commit()
    return moved
