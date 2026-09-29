from pathlib import Path

from flask import Blueprint, flash, request, send_from_directory

from CTFd.models import UserFields, db
from CTFd.plugins import register_plugin_script

MAJOR_FIELD = "University Major"
LEVEL_FIELD = "Level"
LEVELS = ("Beginner", "Intermediate", "Advanced")


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
