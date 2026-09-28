from CTFd.models import Teams
from CTFd.utils import get_config
from CTFd.utils.user import get_current_user


def instance_owner_id(user=None):
    """User id that owns the running instance.

    In teams mode the whole team shares the captain's container and flag.
    """
    user = user or get_current_user()
    if user is None:
        return None
    if get_config("user_mode") == "teams":
        if not user.team_id:
            return None
        team = Teams.query.filter_by(id=user.team_id).first()
        if team is not None and team.captain_id:
            return team.captain_id
    return user.id
