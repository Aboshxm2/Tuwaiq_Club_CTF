from pathlib import Path

from flask import Blueprint, flash, request, send_from_directory
from werkzeug.datastructures import ImmutableMultiDict

from CTFd.cache import clear_standings
from CTFd.models import UserFields, db
from CTFd.plugins import register_plugin_script
from CTFd.utils.user import get_current_user

from .brackets import (
    LEVEL_FIELD,
    LEVELS,
    bracket_ids,
    ensure_brackets,
    sync_team_brackets,
    team_level,
    user_level,
)

MAJOR_FIELD = "University Major"

# Requests that can change who is on a team or what level a player has.
TEAM_CHANGE_PREFIXES = ("/team", "/api/v1/teams", "/api/v1/users", "/admin", "/register")

__all__ = ["ensure_fields", "ensure_brackets", "sync_team_brackets", "load"]


def ensure_fields():
    """Create the registration fields once. Safe to call repeatedly."""
    specs = [
        (MAJOR_FIELD, "For example: Computer Science, Information Systems."),
        (LEVEL_FIELD, "Your cybersecurity experience: " + ", ".join(LEVELS) + "."),
    ]
    for name, description in specs:
        if UserFields.query.filter_by(name=name).first() is None:
            db.session.add(
                UserFields(
                    name=name,
                    description=description,
                    field_type="text",
                    required=True,
                    public=False,
                    editable=False,
                )
            )
    db.session.commit()


def load(app):
    plugin_root = "/plugins/ctfd-registration"
    blueprint = Blueprint("ctfd-registration", __name__, url_prefix=plugin_root)
    assets_dir = Path(__file__).resolve().parent / "assets"

    @blueprint.route("/assets/<path:filename>")
    def assets(filename):
        return send_from_directory(assets_dir, filename)

    app.register_blueprint(blueprint)
    register_plugin_script(f"{plugin_root}/assets/registration.js")

    @app.before_request
    def registration_check_level():
        if request.method != "POST" or request.endpoint != "auth.register":
            return
        field = UserFields.query.filter_by(name=LEVEL_FIELD).first()
        if field is None:
            return
        value = request.form.get(f"fields[{field.id}]", "").strip()
        if value and value not in LEVELS:
            # CTFd's register view reads errors from this flash category and
            # re-renders the form instead of creating the account.
            flash("Choose a level: " + ", ".join(LEVELS) + ".", "auth.register.errors")

    @app.before_request
    def registration_team_bracket():
        # CTFd asks the creator to pick a team bracket. The bracket comes from
        # the creator's level instead, whatever the form sent.
        if request.method != "POST" or request.endpoint != "teams.new":
            return
        ids = bracket_ids()
        user = get_current_user()
        if len(ids) != len(LEVELS) or user is None:
            return
        form = request.form.to_dict(flat=False)
        form["bracket_id"] = [str(ids[team_level([user_level(user.id)])])]
        request.form = ImmutableMultiDict(form)

    @app.after_request
    def registration_sync_brackets(response):
        # Joining, leaving, kicking, and admin edits all go through these
        # paths. Re-check every team so its bracket follows its members.
        if request.method == "GET" or not request.path.startswith(TEAM_CHANGE_PREFIXES):
            return response
        try:
            if sync_team_brackets():
                clear_standings()
        except Exception:
            db.session.rollback()
        return response
