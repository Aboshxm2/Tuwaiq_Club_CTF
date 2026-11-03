"""Scope the existing CTFd pages and API on the server, not just in the browser."""

from flask import (
    Blueprint, abort, g, json, jsonify, redirect,
    render_template, request, session, url_for,
)
from werkzeug.datastructures import ImmutableMultiDict

from CTFd.models import ChallengeFiles, Hints, Solves, Teams, Users, db
from CTFd.schemas.teams import TeamSchema
from CTFd.schemas.users import UserSchema
from CTFd.utils import get_config
from CTFd.utils.dates import isoformat
from CTFd.utils.user import get_current_user, is_admin

from . import events
from .events_models import EventTeams, EventUsers, WorkshopEvents


def deny(message="This resource is not available in your event.", code=403):
    if request.path.startswith("/api/"):
        return jsonify(success=False, message=message), code
    abort(code, description=message)


def public_accounts(event, model):
    ids = events.event_team_ids(event) if model is Teams else events.event_user_ids(event)
    return model.query.filter(model.id.in_(ids), model.hidden.is_(False), model.banned.is_(False))


def account_listing(event, model):
    query = public_accounts(event, model)
    field = request.args.get("field", "name")
    if field not in ("name", "affiliation", "website"):
        field = "name"
    q = request.args.get("q", "")
    if q:
        query = query.filter(getattr(model, field).contains(q))
    page = query.order_by(model.id).paginate(per_page=50, error_out=False)
    if request.path.startswith("/api/"):
        schema = TeamSchema if model is Teams else UserSchema
        data = schema(view="user", many=True, only=("id", "name", "website", "affiliation", "country")).dump(page.items)
        return jsonify(success=True, data=data.data, meta={"pagination": {
            "page": page.page, "next": page.next_num, "prev": page.prev_num,
            "pages": page.pages, "per_page": page.per_page, "total": page.total,
        }})
    args = request.args.to_dict()
    args.pop("page", None)
    kind = "teams" if model is Teams else "users"
    return render_template(
        f"{kind}/{kind}.html", **{kind: page}, q=q, field=field,
        prev_page=url_for(request.endpoint, page=page.prev_num, **args),
        next_page=url_for(request.endpoint, page=page.next_num, **args),
    )


def scoreboard_response(event):
    if not events.scores_shown(event):
        return deny("Scores are currently hidden.")
    rows = events.standings(event)
    if not request.path.startswith("/api/"):
        return render_template("scoreboard.html", standings=rows, infos=[event.name])
    if "/top/" in request.path:
        from CTFd.utils.scoreboard import get_scoreboard_detail

        count = max(1, min(int(request.view_args.get("count", 10)), 50))
        allowed = events.event_team_ids(event)
        data = get_scoreboard_detail(count=count, bracket_id=event.bracket_id)
        return jsonify(success=True, data={k: v for k, v in data.items() if v["id"] in allowed})
    data = []
    for pos, row in enumerate(rows, 1):
        members = public_accounts(event, Users).filter_by(team_id=row.account_id).all()
        data.append({
            "pos": pos, "account_id": row.account_id, "name": row.name,
            "account_type": "team", "account_url": f"/teams/{row.account_id}",
            "oauth_id": row.oauth_id, "score": int(row.score),
            "bracket_id": event.bracket_id, "bracket_name": event.name,
            "members": [{"id": u.id, "name": u.name, "score": u.get_score(),
                         "oauth_id": u.oauth_id, "bracket_id": None, "bracket_name": None} for u in members],
        })
    return jsonify(success=True, data=data)


class DisplayAccount:
    """Keep CTFd's profile editing UI while scoping display-only statistics."""

    def __init__(self, account, event):
        self._account, self._event = account, event

    def __getattr__(self, name):
        if name == "members":
            return [DisplayAccount(u, self._event) for u in self._account.members
                    if u.id in events.event_user_ids(self._event)]
        if name in ("account", "team"):
            value = getattr(self._account, name)
            return DisplayAccount(value, self._event) if value else None
        if name == "score":
            return self.get_score()
        if name == "place":
            return self.get_place()
        return getattr(self._account, name)

    def get_score(self, admin=False):
        return self._account.get_score() if events.scores_shown(self._event) else None

    def get_place(self, admin=False, numeric=False):
        if not events.scores_shown(self._event):
            return None
        if isinstance(self._account, Teams):
            ranking = [row.account_id for row in events.standings(self._event)]
        else:
            from CTFd.utils.scores import get_user_standings

            allowed = events.event_user_ids(self._event)
            ranking = [row.user_id for row in get_user_standings() if row.user_id in allowed]
        if self._account.id not in ranking:
            return None
        place = ranking.index(self._account.id) + 1
        if numeric:
            return place
        from CTFd.utils.humanize.numbers import ordinalize
        return ordinalize(place)


def register_views(app):
    bp = Blueprint("workshop", __name__, template_folder="templates")

    # /events is CTFd's notification stream. Keep workshop URLs separate.
    @bp.route("/workshops")
    @bp.route("/workshops/<slug>")
    def choose(slug=None):
        if not events.enabled():
            abort(404)
        event = WorkshopEvents.query.filter_by(slug=slug).first_or_404() if slug else None
        user = get_current_user()
        member_event = events.user_event(user) if user else None
        if member_event:
            if event and event.id != member_event.id:
                return deny("Your account belongs to another event.")
            return redirect(url_for("challenges.listing"))
        if event and event.registration_open:
            session["workshop_registration_event"] = event.id
            if user is None:
                return redirect(url_for("auth.register"))
        return render_template("workshop/choose.html", events=WorkshopEvents.query.filter_by(
            registration_open=True
        ).all(), selected=event, signed_in=bool(user))

    @bp.route("/workshops/select", methods=["POST"])
    def select():
        if not events.enabled() or get_current_user() is None:
            abort(403)
        event = WorkshopEvents.query.filter_by(id=request.form.get("event_id", type=int), registration_open=True).first_or_404()
        try:
            user = get_current_user()
            if user.team_id:
                raise ValueError("Ask an administrator to assign your existing team.")
            events.assign_user(user, event)
        except ValueError as exc:
            return deny(str(exc))
        return redirect(url_for("challenges.listing"))

    @app.context_processor
    def event_context():
        event = events.user_event() if events.enabled() else None
        registration = WorkshopEvents.query.get(session.get("workshop_registration_event")) if events.enabled() and session.get("workshop_registration_event") else None
        return {"workshop_event_mode": events.enabled(), "workshop_event": event,
                "workshop_registration": registration}

    @app.before_request
    def scope_event():
        if not events.enabled():
            return
        path = request.path.rstrip("/") or "/"
        # Do not bypass the guard by appending an asset extension to a private URL.
        if path.startswith(("/themes/", "/static/")) or request.endpoint in (
            "ctfd-registration.assets", "ctfd-rounds.assets", "plugins.ctfd-whale.assets"
        ):
            return
        events.expire_events()
        if is_admin():
            return
        user = get_current_user()
        if request.endpoint == "auth.register":
            event = WorkshopEvents.query.filter_by(id=session.get("workshop_registration_event"), registration_open=True).first()
            if event is None:
                if request.method == "GET":
                    return redirect(url_for("workshop.choose"))
                return deny("Choose an event whose registration is open.")
            g.workshop_registration_event = event.id
            return
        protected = path in ("/", "/user", "/team", "/challenges", "/scoreboard", "/users", "/teams") or path.startswith((
            "/api/v1/challenges", "/api/v1/scoreboard", "/api/v1/users", "/api/v1/teams",
            "/api/v1/hints", "/api/v1/solutions", "/api/v1/unlocks", "/api/v1/statistics",
            "/api/v1/plugins/ctfd-", "/users/", "/teams/", "/files/",
            "/plugins/ctfd-rounds/download/",
        ))
        if not protected:
            return
        event = events.user_event(user)
        if user is None or event is None:
            if path.startswith(("/api/", "/files/", "/plugins/")):
                return deny("Log in with an account assigned to an event.")
            return redirect(url_for("workshop.choose"))
        g.workshop_event = event
        account_path = path in ("/users", "/teams", "/scoreboard") or path.startswith((
            "/users/", "/teams/", "/api/v1/users", "/api/v1/teams", "/api/v1/scoreboard"
        ))
        if account_path and get_config("account_visibility") == "admins" and not path.startswith((
            "/teams/new", "/teams/join", "/teams/invite", "/api/v1/users/me", "/api/v1/teams/me"
        )):
            return deny(code=404)
        if path == "/":
            return render_template("workshop/home.html", event=event)

        # A team is permanently attached to its creator's event. Both password
        # joins and invite URLs are checked before CTFd can update membership.
        if path == "/teams/new" and request.method == "POST":
            form = request.form.to_dict(flat=False)
            form["bracket_id"] = [str(event.bracket_id)]
            request.form = ImmutableMultiDict(form)
        if (path == "/teams/join" and request.method == "POST") or path == "/teams/invite":
            if path == "/teams/join":
                team = Teams.query.filter_by(name=request.form.get("name")).first()
            else:
                try:
                    team = Teams.load_invite_code(request.args.get("code"))
                except Exception:
                    return deny("Invalid team invitation.")
            membership = events.team_event(team.id) if team else None
            if membership is None or membership.id != event.id:
                return deny("You can only join a team in your event.")

        if request.method == "GET":
            if path in ("/scoreboard", "/api/v1/scoreboard") or path.startswith("/api/v1/scoreboard/top/"):
                return scoreboard_response(event)
            if path in ("/users", "/teams", "/api/v1/users", "/api/v1/teams"):
                return account_listing(event, Teams if path.endswith("teams") else Users)

        view_args = request.view_args or {}
        for kind, key, ids in (
            ("users", "user_id", events.event_user_ids(event)),
            ("teams", "team_id", events.event_team_ids(event)),
        ):
            if path.startswith((f"/{kind}/", f"/api/v1/{kind}/")) and key in view_args:
                try:
                    target_id = int(view_args[key])
                except (TypeError, ValueError):
                    return deny(code=404)
                if target_id not in ids:
                    return deny(code=404)
        if path.startswith("/api/v1/statistics"):
            return deny()
        if not events.scores_shown(event) and path.endswith(("/solves", "/fails", "/awards", "/submissions")):
            return deny("Scores are currently hidden.")

        challenge_id = None
        if path.startswith("/api/v1/challenges/") and "challenge_id" in view_args:
            challenge_id = view_args["challenge_id"]
        elif path == "/api/v1/challenges/attempt":
            data = request.get_json(silent=True) or request.form
            challenge_id = data.get("challenge_id")
        elif path in ("/api/v1/plugins/ctfd-rounds/instance", "/api/v1/plugins/ctfd-whale/container"):
            challenge_id = request.args.get("challenge_id")
        elif path.startswith("/plugins/ctfd-rounds/download/"):
            challenge_id = (request.view_args or {}).get("challenge_id")
        elif path.startswith("/files/"):
            location = (request.view_args or {}).get("path", "")
            file = ChallengeFiles.query.filter_by(location=location).first()
            if file:
                challenge_id = file.challenge_id
        elif path.startswith("/api/v1/hints/"):
            hint = Hints.query.get((request.view_args or {}).get("hint_id"))
            if hint:
                challenge_id = hint.challenge_id
        elif path == "/api/v1/unlocks" and request.method == "POST":
            data = request.get_json(silent=True) or {}
            if data.get("type") != "hints":
                return deny("Only hints can be unlocked during an event.")
            hint = Hints.query.get(data.get("target"))
            if hint:
                challenge_id = hint.challenge_id
        elif path.startswith(("/api/v1/hints", "/api/v1/solutions")):
            # Bulk hints/solutions can reveal unreleased challenge metadata.
            return deny()
        if challenge_id is not None:
            try:
                challenge_id = int(challenge_id)
            except (ValueError, TypeError):
                return deny(code=404)
            reason = events.block_reason(challenge_id, writing=request.method not in ("GET", "HEAD"))
            if reason:
                return deny(reason)
            if path.endswith("/solves"):
                rows = Solves.query.join(Teams, Solves.team_id == Teams.id).filter(
                    Solves.challenge_id == challenge_id, Solves.team_id.in_(events.event_team_ids(event)),
                    Teams.hidden.is_(False), Teams.banned.is_(False),
                ).order_by(Solves.date).all()
                return jsonify(success=True, data=[{
                    "account_id": row.team_id, "name": row.team.name, "date": isoformat(row.date),
                    "account_url": f"/teams/{row.team_id}",
                } for row in rows])
            if path.endswith("/ratings"):
                return deny("Challenge ratings are not available in event mode.")

    @app.after_request
    def event_response(response):
        if not events.enabled():
            return response
        response.headers["Cache-Control"] = "private, no-store"
        response.vary.add("Cookie")
        user = get_current_user()
        if user and getattr(g, "workshop_registration_event", None) and response.status_code in (301, 302, 303):
            if EventUsers.query.get(user.id) is None:
                db.session.add(EventUsers(user_id=user.id, event_id=g.workshop_registration_event))
                db.session.commit()
        if is_admin() or user is None:
            return response
        event = events.user_event(user)
        if event is None:
            return response
        if user.team_id and request.method == "POST" and request.endpoint == "teams.new" and response.status_code in (301, 302, 303):
            if EventTeams.query.get(user.team_id) is None:
                db.session.add(EventTeams(team_id=user.team_id, event_id=event.id))
                db.session.commit()
        if request.method != "GET":
            events.sync_teams()
        if response.is_json and response.status_code == 200:
            payload = response.get_json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if request.path.rstrip("/") == "/api/v1/challenges" and isinstance(data, list):
                allowed = events.visible_challenge_ids(event)
                payload["data"] = data = [row for row in data if row.get("id") in allowed]
            if request.path.startswith("/api/v1/challenges") and isinstance(data, (list, dict)):
                for row in data if isinstance(data, list) else [data]:
                    if not isinstance(row, dict) or not isinstance(row.get("solves"), (int, type(None))):
                        continue
                    if "solves" in row:
                        row["solves"] = Solves.query.join(Teams, Solves.team_id == Teams.id).filter(
                            Solves.challenge_id == row.get("id"), Solves.team_id.in_(events.event_team_ids(event)),
                            Teams.hidden.is_(False), Teams.banned.is_(False),
                        ).count() if events.scores_shown(event) else None
            if request.path.startswith(("/api/v1/users/", "/api/v1/teams/")):
                if not events.scores_shown(event):
                    def hide_scores(value):
                        if isinstance(value, dict):
                            for key in list(value):
                                if key in ("score", "place", "solves", "solve_count"):
                                    value[key] = None
                                else:
                                    hide_scores(value[key])
                        elif isinstance(value, list):
                            for item in value:
                                hide_scores(item)
                    hide_scores(data)
                elif isinstance(data, dict) and "place" in data:
                    model = Teams if "/teams/" in request.path else Users
                    target = user.team_id if model is Teams else user.id
                    if (request.view_args or {}).get("team_id"):
                        target = request.view_args["team_id"]
                    if (request.view_args or {}).get("user_id"):
                        target = request.view_args["user_id"]
                    account = model.query.get(target)
                    data["place"] = DisplayAccount(account, event).get_place() if account else None
            response.set_data(json.dumps(payload))
        return response

    def scope_profile(context):
        if not events.enabled() or is_admin():
            return
        event = events.user_event()
        if event is None or request.endpoint not in (
            "users.private", "users.public", "teams.private", "teams.public"
        ):
            return
        shown = events.scores_shown(event)
        for key in ("user", "team", "account"):
            if context.get(key) is not None:
                context[key] = DisplayAccount(context[key], event)
        if not shown:
            context.update(score=None, place=None, solves=[], awards=[])
        elif context.get("team"):
            context["place"] = context["team"].get_place()
        context["scores_visible"] = lambda: shown

    # Flask 2.1 does not require Blinker. Apply display scoping after the
    # normal template context is assembled, without adding a signal dependency.
    original_context = app.update_template_context

    def scoped_context(context):
        original_context(context)
        scope_profile(context)

    app.update_template_context = scoped_context
    app.register_blueprint(bp)
