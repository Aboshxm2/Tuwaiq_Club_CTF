from pathlib import Path

from flask import Blueprint, abort, redirect, render_template, request, send_file, send_from_directory, url_for
from flask_restx import Namespace, Resource
from sqlalchemy import event, text

from CTFd.api import CTFd_API_v1
from CTFd.models import Challenges, Solves, db
from CTFd.plugins import register_admin_plugin_menu_bar, register_plugin_script
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils.decorators import admins_only
from CTFd.utils.user import authed, get_current_user

from .logic import (
    active_round,
    award_for_solve,
    bundle_path,
    end_round,
    freeze_round,
    grade_personal,
    launch_instance,
    public_status,
    resume_round,
    scores_shown,
    set_scores_shown,
    set_speed_bonus_percent,
    speed_bonus_percent,
    start_round,
    submission_block_reason,
    tick,
)
from .models import ChallengeMeta, RoundChallenges, RoundFlagAlerts, Rounds

def load(app):
    app.db.create_all()

    plugin_root = "/plugins/ctfd-rounds"
    blueprint = Blueprint(
        "ctfd-rounds",
        __name__,
        template_folder="templates",
        url_prefix=plugin_root,
    )

    user_namespace = Namespace("ctfd-rounds", description="Round status and instances")

    @user_namespace.route("/status")
    class RoundStatus(Resource):
        @staticmethod
        def get():
            if not authed():
                return {"success": False, "message": "Login required."}, 403
            return public_status()

    @user_namespace.route("/instance")
    class RoundInstance(Resource):
        @staticmethod
        def post():
            if not authed():
                return {"success": False, "message": "Login required."}, 403
            challenge_id = request.args.get("challenge_id", type=int)
            challenge = Challenges.query.filter_by(id=challenge_id).first()
            if challenge is None:
                return {"success": False, "message": "No such challenge."}, 404
            try:
                ok, message, _row = launch_instance(challenge)
            except Exception as exc:
                db.session.rollback()
                return {"success": False, "message": f"Could not build the instance: {exc}"}, 500
            if not ok:
                return {"success": False, "message": message}, 403
            return {
                "success": True,
                "message": message,
                "download": f"{plugin_root}/download/{challenge.id}",
            }

    CTFd_API_v1.add_namespace(user_namespace, path="/plugins/ctfd-rounds")

    @blueprint.route("/download/<int:challenge_id>")
    def download(challenge_id):
        if not authed():
            abort(403)
        user = get_current_user()
        if user is None or user.account_id is None:
            abort(403)
        path = bundle_path(user.account_id, challenge_id)
        if not path.is_file():
            abort(404)
        meta = ChallengeMeta.query.filter_by(challenge_id=challenge_id).first()
        name = f"{meta.slug}.zip" if meta else "instance.zip"
        return send_file(path, as_attachment=True, download_name=name)

    @blueprint.route("/admin", methods=["GET"])
    @admins_only
    def admin_page():
        tick()
        challenges = Challenges.query.order_by(Challenges.position, Challenges.id).all()
        return render_template(
            "admin.html",
            rounds=Rounds.query.order_by(Rounds.position, Rounds.id).all(),
            challenges=challenges,
            assigned={row.challenge_id: row.round_id for row in RoundChallenges.query.all()},
            speed_bonus=speed_bonus_percent(),
            alerts=RoundFlagAlerts.query.order_by(RoundFlagAlerts.id.desc()).limit(30).all(),
            active=active_round(),
            scores_shown=scores_shown(),
        )

    @blueprint.route("/admin/bonus", methods=["POST"])
    @admins_only
    def admin_bonus():
        try:
            set_speed_bonus_percent(int(request.form.get("speed_bonus", 50)))
        except ValueError:
            pass
        return redirect(url_for("ctfd-rounds.admin_page"))

    @blueprint.route("/admin/scoreboard", methods=["POST"])
    @admins_only
    def admin_scoreboard():
        set_scores_shown(request.form.get("show") == "1")
        return redirect(url_for("ctfd-rounds.admin_page"))

    @blueprint.route("/admin/rounds", methods=["POST"])
    @admins_only
    def admin_create():
        name = (request.form.get("name") or "").strip()
        try:
            minutes = int(request.form.get("minutes", 0))
            position = int(request.form.get("position", 0))
        except ValueError:
            minutes, position = 0, 0
        if name and minutes > 0:
            db.session.add(
                Rounds(name=name, duration=minutes * 60, position=position, state="pending")
            )
            db.session.commit()
        return redirect(url_for("ctfd-rounds.admin_page"))

    @blueprint.route("/admin/rounds/<int:round_id>/update", methods=["POST"])
    @admins_only
    def admin_update(round_id):
        rnd = Rounds.query.get_or_404(round_id)
        name = (request.form.get("name") or rnd.name).strip()
        try:
            minutes = int(request.form.get("minutes", rnd.duration // 60))
            position = int(request.form.get("position", rnd.position))
        except ValueError:
            return redirect(url_for("ctfd-rounds.admin_page"))
        if name and minutes > 0:
            rnd.name = name
            rnd.duration = minutes * 60
            rnd.position = position
            db.session.commit()
        selected = {int(value) for value in request.form.getlist("challenges") if value.isdigit()}
        RoundChallenges.query.filter_by(round_id=rnd.id).delete(synchronize_session=False)
        if selected:
            RoundChallenges.query.filter(RoundChallenges.challenge_id.in_(selected)).delete(
                synchronize_session=False
            )
        db.session.flush()
        for challenge_id in selected:
            db.session.add(RoundChallenges(round_id=rnd.id, challenge_id=challenge_id))
        db.session.commit()
        tick()
        return redirect(url_for("ctfd-rounds.admin_page"))

    @blueprint.route("/admin/rounds/<int:round_id>/delete", methods=["POST"])
    @admins_only
    def admin_delete(round_id):
        rnd = Rounds.query.get_or_404(round_id)
        if rnd.state == "pending" or rnd.state == "ended":
            db.session.delete(rnd)
            db.session.commit()
            tick()
        return redirect(url_for("ctfd-rounds.admin_page"))

    @blueprint.route("/admin/rounds/<int:round_id>/<action>", methods=["POST"])
    @admins_only
    def admin_action(round_id, action):
        rnd = Rounds.query.get_or_404(round_id)
        actions = {
            "start": start_round,
            "freeze": freeze_round,
            "resume": resume_round,
            "end": end_round,
        }
        handler = actions.get(action)
        if handler:
            handler(rnd)
        return redirect(url_for("ctfd-rounds.admin_page"))

    assets_dir = Path(__file__).resolve().parent / "assets"

    @blueprint.route("/assets/<path:filename>")
    def assets(filename):
        return send_from_directory(assets_dir, filename)

    app.register_blueprint(blueprint)
    register_admin_plugin_menu_bar(title="Rounds", route=f"{plugin_root}/admin")
    register_plugin_script(f"{plugin_root}/assets/rounds.js")

    installed = {"done": False}

    @app.before_request
    def rounds_before_request():
        if not installed["done"]:
            _wrap_challenge_classes()
            installed["done"] = True
        path = request.path or ""
        if path.startswith(("/themes/", "/files/")) or path.endswith(
            (".js", ".css", ".png", ".svg", ".woff", ".woff2", ".map")
        ):
            return
        try:
            tick()
        except Exception:
            db.session.rollback()

    if not getattr(app, "_rounds_solve_hook", False):
        @event.listens_for(Solves, "after_delete")
        def _drop_speed_bonus(mapper, connection, target):
            rows = connection.execute(
                text("SELECT award_id FROM round_bonuses WHERE solve_id = :sid"),
                {"sid": target.id},
            ).fetchall()
            for (award_id,) in rows:
                connection.execute(text("DELETE FROM awards WHERE id = :id"), {"id": award_id})
            connection.execute(
                text("DELETE FROM round_bonuses WHERE solve_id = :sid"),
                {"sid": target.id},
            )

        app._rounds_solve_hook = True


def _wrap_challenge_classes():
    for cls in list(CHALLENGE_CLASSES.values()):
        if getattr(cls, "_rounds_wrapped", False):
            continue
        orig_attempt = cls.attempt.__func__
        orig_solve = cls.solve.__func__

        def attempt(cls, challenge, request, _orig=orig_attempt):
            reason = submission_block_reason(challenge)
            if reason:
                return False, reason
            if ChallengeMeta.query.filter_by(challenge_id=challenge.id).first() is None:
                return _orig(cls, challenge, request)
            return grade_personal(challenge, request)

        def solve(cls, user, team, challenge, request, _orig=orig_solve):
            _orig(cls, user, team, challenge, request)
            award_for_solve(user, team, challenge)

        cls.attempt = classmethod(attempt)
        cls.solve = classmethod(solve)
        cls._rounds_wrapped = True
