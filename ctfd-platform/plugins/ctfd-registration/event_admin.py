"""Administrator controls for independent workshop events and release batches."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from CTFd.models import Challenges, Users, db
from CTFd.plugins import register_admin_plugin_menu_bar
from CTFd.utils import set_config
from CTFd.utils.decorators import admins_only

from . import events
from .events_models import EventChallenges, EventUsers, WorkshopEvents


def static_scoring(challenge):
    if challenge.type == "dynamic_docker":
        return not challenge.dynamic_score
    return challenge.type == "standard" and getattr(challenge, "function", "static") == "static"


def register_admin(app):
    bp = Blueprint("workshop-admin", __name__, template_folder="templates",
                   url_prefix="/plugins/ctfd-registration/admin/events")

    @bp.route("", methods=["GET", "POST"])
    @admins_only
    def index():
        if request.method == "POST":
            if request.form.get("enable") == "1" and not events.enabled():
                if request.form.get("confirm") != "1":
                    abort(400)
                if app.config.get("APPLICATION_ROOT", "/") != "/":
                    abort(400, "Workshop events currently require deployment at the domain root.")
                events.ensure_default_events()
                set_config("workshop:events_enabled", True)
                set_config("user_mode", "teams")
                events.apply_visibility()
                flash("تم تفعيل الفعاليات. التحديات مغلقة حتى بدء فعالية ونشر دفعتها.", "info")
            return redirect(url_for("workshop-admin.index"))
        if events.enabled():
            events.expire_events()
        return render_template(
            "workshop/admin.html", enabled=events.enabled(),
            events=WorkshopEvents.query.order_by(WorkshopEvents.id).all(),
            challenges=Challenges.query.order_by(Challenges.category, Challenges.position, Challenges.id).all(),
            assignments={(x.event_id, x.challenge_id): x for x in EventChallenges.query.all()},
            unassigned=Users.query.filter(Users.type != "admin", ~Users.id.in_(
                db.session.query(EventUsers.user_id)
            )).order_by(Users.id).all(),
        )

    @bp.route("/<int:event_id>/<verb>", methods=["POST"])
    @admins_only
    def update(event_id, verb):
        if not events.enabled():
            abort(409)
        event = WorkshopEvents.query.get_or_404(event_id)
        events.expire_events()
        try:
            if verb == "save":
                name = request.form.get("name", "").strip()
                minutes = int(request.form.get("minutes", "180"))
                if not name or len(name) > 128 or not 1 <= minutes <= 1440:
                    raise ValueError("Use a name and a duration between 1 and 1440 minutes.")
                selected = {int(x) for x in request.form.getlist("challenges")}
                catalog = {c.id: c for c in Challenges.query.filter(Challenges.id.in_(selected))}
                if set(catalog) != selected:
                    raise ValueError("Unknown challenge.")
                if any(not static_scoring(c) for c in catalog.values()):
                    raise ValueError("Event challenges must use static scoring so one event cannot change another's points.")
                event.name = name
                # Changing score visibility must not round a clock previously
                # adjusted with "remaining minutes" down by up to 59 seconds.
                if minutes != event.duration // 60:
                    event.duration = minutes * 60
                event.registration_open = request.form.get("registration_open") == "1" and event.state == "pending"
                event.scores_visible = request.form.get("scores_visible") == "1"
                for row in EventChallenges.query.filter_by(event_id=event.id).all():
                    if row.challenge_id not in selected:
                        db.session.delete(row)
                for cid in selected:
                    row = EventChallenges.query.get((event.id, cid))
                    if row is None:
                        row = EventChallenges(event_id=event.id, challenge_id=cid, released=False)
                        db.session.add(row)
                    row.batch = (request.form.get(f"batch_{cid}", "").strip() or "الدفعة الأولى")[:80]
            elif verb == "remaining":
                minutes = int(request.form.get("remaining", "0"))
                if event.state not in ("running", "frozen") or not 1 <= minutes <= 1440:
                    raise ValueError("Set between 1 and 1440 remaining minutes on a running or paused event.")
                event.duration = event.elapsed() + minutes * 60
            elif verb in ("release", "hide"):
                rows = EventChallenges.query.filter_by(event_id=event.id)
                if request.form.get("category"):
                    ids = db.session.query(Challenges.id).filter_by(category=request.form["category"])
                    rows = rows.filter(EventChallenges.challenge_id.in_(ids))
                else:
                    rows = rows.filter_by(batch=request.form.get("batch", ""))
                for row in rows.all():
                    row.released = verb == "release"
            elif verb == "assign":
                user = Users.query.get_or_404(int(request.form.get("user_id", "0")))
                if user.type == "admin":
                    raise ValueError("Administrators do not need event membership.")
                events.assign_user(user, event)
            else:
                events.action(event, verb)
            db.session.commit()
            events.expire_events()
            events.apply_visibility()
            flash("تم حفظ إعدادات الفعالية.", "success")
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("workshop-admin.index"))

    app.register_blueprint(bp)
    register_admin_plugin_menu_bar(title="Events", route="/plugins/ctfd-registration/admin/events")
