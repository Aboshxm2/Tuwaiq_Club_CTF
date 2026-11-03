"""Integration tests against CTFd 3.8.7, using a disposable SQLite database.

Run with the platform plugins/theme installed on CTFd's Python path:
python -m unittest discover -s ctfd-platform/tests -v
No production database, Docker daemon, or live challenge service is used.
"""

import datetime
import importlib
import unittest
from unittest.mock import patch

from CTFd import create_app
from CTFd.cache import cache, clear_challenges, clear_standings
from CTFd.config import TestingConfig
from CTFd.models import Admins, Awards, ChallengeFiles, Challenges, Flags, Hints, Solves, Teams, Users, db
from CTFd.utils import set_config


class EventTests(unittest.TestCase):
    def setUp(self):
        class Config(TestingConfig):
            SAFE_MODE = False
            SQLALCHEMY_DATABASE_URI = "sqlite://"
            SERVER_NAME = "localhost.localdomain"

        plugins = ["challenges", "ctfd-registration", "ctfd-rounds", "dynamic_challenges", "flags"]
        with patch("CTFd.plugins.get_plugin_names", return_value=plugins):
            self.app = create_app(Config)
        self.context = self.app.app_context()
        self.context.push()
        db.session().expire_on_commit = False
        self.addCleanup(self.context.pop)
        self.addCleanup(cache.clear)
        for key, value in {
            "setup": True, "ctf_name": "Event tests", "user_mode": "teams", "team_size": 3,
            "ctf_theme": "tuwaiq", "challenge_visibility": "private", "account_visibility": "public",
            "score_visibility": "public", "registration_visibility": "public", "verify_emails": None,
        }.items():
            set_config(key, value)
        self.events = importlib.import_module("CTFd.plugins.ctfd-registration.events")
        self.models = importlib.import_module("CTFd.plugins.ctfd-registration.events_models")
        self.logic = importlib.import_module("CTFd.plugins.ctfd-rounds.logic")
        self.registration = importlib.import_module("CTFd.plugins.ctfd-registration")
        self.whale_calls = []

        def fake_whale():
            self.whale_calls.append(True)
            return {"success": True}

        # Exercise the same guarded route without starting real Docker services.
        self.app.add_url_rule("/api/v1/plugins/ctfd-whale/container", "test_whale", fake_whale,
                              methods=["GET", "POST", "PATCH"])
        admin = Admins(name="organizer", email="organizer@example.com", password="password")
        db.session.add(admin)
        db.session.commit()
        self.admin = self.login("organizer")
        self.client = self.app.test_client()

    def login(self, name):
        client = self.app.test_client()
        client.get("/login")
        response = self.post(client, "/login", {"name": name, "password": "password"})
        self.assertEqual(response.status_code, 302)
        with client.session_transaction() as sess:
            self.assertTrue(sess.get("id"))
        return client

    def post(self, client, path, data=None, json=None):
        with client.session_transaction() as sess:
            nonce = sess.get("nonce")
        if json is not None:
            return client.post(path, json=json, headers={"CSRF-Token": nonce or ""})
        return client.post(path, data={**(data or {}), "nonce": nonce})

    def enable(self):
        response = self.post(self.admin, "/plugins/ctfd-registration/admin/events", {"enable": "1", "confirm": "1"})
        self.assertEqual(response.status_code, 302)

    @property
    def boys(self):
        return self.models.WorkshopEvents.query.filter_by(slug="boys").one()

    @property
    def girls(self):
        return self.models.WorkshopEvents.query.filter_by(slug="girls").one()

    def player(self, name, event, team=True):
        user = Users(name=name, email=f"{name}@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        self.events.assign_user(user, event)
        user_id = user.id
        client = self.login(name)
        if team:
            response = self.post(client, "/teams/new", {"name": f"team-{name}", "password": "password", "bracket_id": self.girls.bracket_id})
            self.assertEqual(response.status_code, 302)
            user = Users.query.get(user_id)
            self.assertIsNotNone(self.events.team_event(user.team_id))
        return user, client

    def challenge(self, name, event, batch="first", released=True, category="Web"):
        challenge = Challenges(name=name, description=f"Description {name}", category=category,
                               value=100, type="standard", state="hidden", function="static")
        db.session.add(challenge)
        db.session.flush()
        db.session.add(Flags(challenge_id=challenge.id, type="static", content=f"TAIBAH{{{name}}}"))
        db.session.add(self.models.EventChallenges(event_id=event.id, challenge_id=challenge.id,
                                                   batch=batch, released=released))
        db.session.commit()
        return challenge

    def solve(self, user, challenge):
        db.session.add(Solves(user_id=user.id, team_id=user.team_id, challenge_id=challenge.id,
                              provided="flag", ip="127.0.0.1"))
        db.session.commit()
        clear_standings()
        clear_challenges()

    def admin_action(self, event, verb, **data):
        return self.post(self.admin, f"/plugins/ctfd-registration/admin/events/{event.id}/{verb}", data)

    def test_legacy_mode_is_unchanged_and_enable_is_explicit(self):
        self.assertFalse(self.events.enabled())
        self.assertEqual(self.client.get("/workshops").status_code, 404)
        response = self.post(self.admin, "/plugins/ctfd-registration/admin/events", {"enable": "1"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.events.enabled())
        self.enable()
        self.assertEqual(self.boys.duration, 10800)
        self.assertEqual(self.girls.state, "pending")
        self.assertNotEqual(self.boys.bracket_id, self.girls.bracket_id)
        page = self.admin.get("/plugins/ctfd-registration/admin/events")
        self.assertEqual(page.status_code, 200)
        self.assertIn("/workshops/boys", page.text)
        self.assertIn("/workshops/girls", page.text)

    def test_legacy_rounds_still_control_visibility_when_events_are_disabled(self):
        models = importlib.import_module("CTFd.plugins.ctfd-rounds.models")
        first = Challenges(name="legacy-first", description="legacy", category="Web", value=100, type="standard", state="hidden")
        second = Challenges(name="legacy-other", description="legacy", category="Web", value=100, type="standard", state="visible")
        db.session.add_all([first, second])
        db.session.flush()
        rnd = models.Rounds(name="Legacy", position=1, duration=60, state="pending")
        db.session.add(rnd)
        db.session.flush()
        db.session.add(models.RoundChallenges(round_id=rnd.id, challenge_id=first.id))
        db.session.commit()
        ok, _ = self.logic.start_round(rnd)
        self.assertTrue(ok)
        self.assertEqual(first.state, "visible")
        self.assertEqual(second.state, "hidden")
        self.logic.freeze_round(rnd)
        self.assertIn("frozen", self.logic.submission_block_reason(first))
        self.logic.end_round(rnd)
        self.assertEqual(first.state, "hidden")

    def test_registration_link_binds_event_and_cannot_switch(self):
        self.enable()
        self.assertEqual(self.client.get("/register").location, "/workshops")
        self.assertEqual(self.client.get("/workshops/boys").location, "/register")
        response = self.post(self.client, "/register", {
            "name": "new-player", "email": "new-player@example.com", "password": "password",
        })
        self.assertEqual(response.status_code, 302)
        user = Users.query.filter_by(name="new-player").one()
        self.assertEqual(self.events.user_event(user).id, self.boys.id)
        self.assertEqual(self.client.get("/workshops/girls").status_code, 403)
        self.assertEqual(self.post(self.client, "/workshops/select", {"event_id": self.girls.id}).status_code, 403)

    def test_closed_registration_cannot_create_account(self):
        self.enable()
        self.client.get("/workshops/boys")
        self.boys.registration_open = False
        db.session.commit()
        response = self.post(self.client, "/register", {"name": "late", "email": "late@example.com", "password": "password"})
        self.assertEqual(response.status_code, 403)
        self.assertIsNone(Users.query.filter_by(name="late").first())

    def test_team_bracket_is_event_and_cross_event_joins_are_blocked(self):
        self.enable()
        boy, boy_client = self.player("boy", self.boys)
        girl, girl_client = self.player("girl", self.girls, team=False)
        team = Teams.query.get(boy.team_id)
        self.assertEqual(team.bracket_id, self.boys.bracket_id)
        self.registration.sync_team_brackets()
        self.assertEqual(team.bracket_id, self.boys.bracket_id)
        response = self.post(girl_client, "/teams/join", {"name": team.name, "password": "password"})
        self.assertEqual(response.status_code, 403)
        with self.app.test_request_context():
            code = team.get_invite_code()
        self.assertEqual(girl_client.get(f"/teams/invite?code={code}").status_code, 403)
        self.assertEqual(self.post(girl_client, f"/teams/invite?code={code}").status_code, 403)
        girl = Users.query.get(girl.id)
        self.assertIsNone(girl.team_id)
        member, member_client = self.player("member", self.boys, team=False)
        self.assertEqual(self.post(member_client, "/teams/join", {"name": team.name, "password": "password"}).status_code, 302)
        member = Users.query.get(member.id)
        self.assertEqual(member.team_id, team.id)

    def test_challenge_lists_direct_urls_and_solves_are_scoped(self):
        self.enable()
        boy, client = self.player("boy", self.boys)
        girl, girl_client = self.player("girl", self.girls)
        shared = self.challenge("shared", self.boys)
        self.models.EventChallenges.query.session.add(self.models.EventChallenges(event_id=self.girls.id, challenge_id=shared.id, released=True, batch="first"))
        girl_only = self.challenge("girl-only", self.girls)
        unreleased = self.challenge("later", self.boys, released=False)
        self.events.action(self.boys, "start")
        self.events.action(self.girls, "start")
        self.solve(girl, shared)
        self.boys.scores_visible = True
        db.session.commit()
        response = client.get("/api/v1/challenges")
        self.assertEqual([row["id"] for row in response.json["data"]], [shared.id])
        self.assertEqual(response.json["data"][0]["solves"], 0)
        self.assertEqual(client.get(f"/api/v1/challenges/{girl_only.id}").status_code, 403)
        self.assertEqual(client.get(f"/api/v1/challenges/{unreleased.id}").status_code, 403)
        self.assertEqual(client.get(f"/api/v1/challenges/{shared.id}/solves").json["data"], [])
        hint = Hints(challenge_id=girl_only.id, content="other-event-secret", cost=0, type="standard")
        db.session.add(hint)
        db.session.commit()
        self.assertEqual(client.get(f"/api/v1/hints/{hint.id}").status_code, 403)
        self.assertEqual(client.get("/api/v1/hints").status_code, 403)
        self.assertEqual(self.post(client, "/api/v1/unlocks", json={"type": "hints", "target": hint.id}).status_code, 403)

    def test_members_and_scoreboards_ignore_other_bracket_query(self):
        self.enable()
        boy, client = self.player("boy", self.boys)
        girl, girl_client = self.player("girl", self.girls)
        c = self.challenge("shared", self.boys)
        self.challenge("girls", self.girls)
        self.events.action(self.boys, "start")
        self.events.action(self.girls, "start")
        self.solve(boy, c)
        self.boys.scores_visible = self.girls.scores_visible = True
        db.session.commit()
        for path in ("/users", "/teams", "/scoreboard", "/user", "/team"):
            response = client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertNotIn("team-girl", response.text)
        for path in (f"/users/{girl.id}", f"/teams/{girl.team_id}", f"/api/v1/users/{girl.id}", f"/api/v1/teams/{girl.team_id}"):
            self.assertEqual(client.get(path).status_code, 404, path)
        for path in ("/api/v1/users", "/api/v1/teams"):
            response = client.get(path)
            self.assertEqual(response.json["meta"]["pagination"]["total"], 1)
        response = client.get(f"/api/v1/scoreboard?bracket_id={self.girls.bracket_id}")
        self.assertEqual([x["name"] for x in response.json["data"]], ["team-boy"])
        self.assertEqual(girl_client.get("/api/v1/scoreboard").json["data"], [])
        graph = client.get(f"/api/v1/scoreboard/top/10?bracket_id={self.girls.bracket_id}")
        self.assertEqual(list(graph.json["data"].values())[0]["name"], "team-boy")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertIn("Cookie", response.headers["Vary"])

    def test_hiding_scores_covers_private_api_profiles_and_counts(self):
        self.enable()
        boy, client = self.player("boy", self.boys)
        c = self.challenge("first", self.boys)
        self.events.action(self.boys, "start")
        self.solve(boy, c)
        self.assertEqual(client.get("/api/v1/scoreboard").status_code, 403)
        self.assertEqual(client.get("/api/v1/teams/me").json["data"]["score"], None)
        self.assertEqual(client.get("/api/v1/teams/me/solves").status_code, 403)
        self.assertEqual(client.get(f"/api/v1/challenges/{c.id}").json["data"]["solves"], None)
        for path in ("/user", "/team"):
            response = client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("100 <small>", response.text)
        self.assertEqual(Teams.query.get(boy.team_id).get_score(admin=True), 100)

    def test_batches_category_hide_and_remaining_time(self):
        self.enable()
        boy, client = self.player("boy", self.boys)
        first = self.challenge("first", self.boys, released=False)
        second = self.challenge("second", self.boys, batch="second", released=False)
        self.events.action(self.boys, "start")
        self.admin_action(self.boys, "release", batch="first")
        self.assertEqual(self.events.visible_challenge_ids(self.boys), {first.id})
        self.admin_action(self.boys, "release", batch="second")
        self.assertEqual(self.events.visible_challenge_ids(self.boys), {first.id, second.id})
        self.admin_action(self.boys, "remaining", remaining="20")
        self.assertLessEqual(self.boys.remaining(), 1200)
        self.assertGreater(self.boys.remaining(), 1190)
        self.admin_action(self.boys, "hide", category="Web")
        self.assertEqual(self.events.visible_challenge_ids(self.boys), set())
        self.assertEqual(self.post(client, "/api/v1/challenges/attempt", json={"challenge_id": first.id, "submission": "TAIBAH{first}"}).status_code, 403)

    def test_pause_end_and_expiry_reject_even_direct_attempts(self):
        self.enable()
        boy, client = self.player("boy", self.boys)
        c = self.challenge("first", self.boys)
        self.events.action(self.boys, "start")
        self.events.action(self.boys, "pause")
        response = self.post(client, "/api/v1/challenges/attempt", json={"challenge_id": c.id, "submission": "TAIBAH{first}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(client.get(f"/api/v1/challenges/{c.id}").status_code, 200)
        self.assertEqual(self.post(client, f"/api/v1/plugins/ctfd-rounds/instance?challenge_id={c.id}").status_code, 403)
        self.events.action(self.boys, "resume")
        response = self.post(client, "/api/v1/challenges/attempt", json={"challenge_id": c.id, "submission": "TAIBAH{first}"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json["data"]["status"], "correct")
        self.assertFalse(importlib.import_module("CTFd.plugins.ctfd-rounds.models").RoundBonuses.query.first())
        self.boys.started_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=self.boys.duration + 1)
        db.session.commit()
        response = client.get("/api/v1/plugins/ctfd-rounds/status")
        self.assertEqual(response.json["round"]["state"], "ended")
        self.assertEqual(self.post(client, "/api/v1/challenges/attempt", json={"challenge_id": c.id, "submission": "TAIBAH{first}"}).status_code, 403)
        self.assertEqual(client.get(f"/plugins/ctfd-rounds/download/{c.id}").status_code, 403)
        self.assertEqual(Teams.query.get(boy.team_id).get_score(admin=True), 100)
        with self.assertRaises(ValueError):
            self.events.action(self.boys, "start")

    def test_unassigned_and_anonymous_accounts_fail_closed(self):
        self.enable()
        for path in ("/api/v1/challenges", "/api/v1/scoreboard", "/api/v1/users", "/api/v1/teams"):
            self.assertEqual(self.client.get(path).status_code, 403)
        legacy = Users(name="legacy", email="legacy@example.com", password="password")
        db.session.add(legacy)
        db.session.commit()
        client = self.login("legacy")
        self.assertEqual(client.get("/challenges").location, "/workshops")
        self.assertEqual(client.get("/api/v1/teams").status_code, 403)
        self.assertEqual(client.get("/plugins/ctfd-registration/admin/events").status_code, 302)

    def test_old_scores_cannot_be_moved_between_events(self):
        self.enable()
        user, client = self.player("boy", self.boys)
        c = self.challenge("first", self.boys)
        self.solve(user, c)
        with self.assertRaises(ValueError):
            self.events.assign_user(user, self.girls)
        old = Users(name="old", email="old@example.com", password="password")
        db.session.add(old)
        db.session.commit()
        db.session.add(Awards(user_id=old.id, name="previous", value=10))
        db.session.commit()
        with self.assertRaises(ValueError):
            self.events.assign_user(old, self.boys)

    def test_whale_launch_and_direct_files_follow_event_access(self):
        self.enable()
        user, client = self.player("boy", self.boys)
        c = self.challenge("first", self.boys)
        other = self.challenge("girls", self.girls)
        file = ChallengeFiles(challenge_id=other.id, location="other/event.zip")
        db.session.add(file)
        db.session.commit()
        self.events.action(self.boys, "start")
        self.events.action(self.girls, "start")
        self.assertEqual(client.get("/files/other/event.zip").status_code, 403)
        self.assertEqual(self.post(client, f"/api/v1/plugins/ctfd-whale/container?challenge_id={other.id}").status_code, 403)
        self.assertEqual(self.whale_calls, [])
        self.assertEqual(self.post(client, f"/api/v1/plugins/ctfd-whale/container?challenge_id={c.id}").status_code, 200)
        self.assertEqual(len(self.whale_calls), 1)
        self.events.action(self.boys, "pause")
        self.assertEqual(self.post(client, f"/api/v1/plugins/ctfd-whale/container?challenge_id={c.id}").status_code, 403)
        self.events.action(self.boys, "end")
        self.assertEqual(client.get(f"/api/v1/plugins/ctfd-whale/container?challenge_id={c.id}").status_code, 403)
        self.assertEqual(len(self.whale_calls), 1)

    def test_admin_save_persists_assignment_and_no_scores_leak_into_html(self):
        self.enable()
        user, client = self.player("boy", self.boys)
        c = self.challenge("first", self.boys)
        self.admin_action(self.boys, "save", name="Wednesday", minutes="180",
                          challenges=[str(c.id)], **{f"batch_{c.id}": "first"})
        self.assertEqual(self.boys.name, "Wednesday")
        self.events.action(self.boys, "start")
        self.solve(user, c)
        self.admin_action(self.boys, "remaining", remaining="20")
        duration = self.boys.duration
        self.admin_action(self.boys, "save", name="Wednesday", minutes=str(duration // 60),
                          scores_visible="1", challenges=[str(c.id)], **{f"batch_{c.id}": "first"})
        self.assertEqual(self.boys.duration, duration)
        self.assertTrue(self.boys.scores_visible)
        self.assertEqual(client.get("/api/v1/scoreboard").json["data"][0]["score"], 100)
        self.assertEqual(self.admin.get("/plugins/ctfd-registration/admin/events").status_code, 200)

    def test_global_visibility_is_not_bypassed_and_csrf_is_required(self):
        self.enable()
        user, client = self.player("boy", self.boys)
        self.boys.scores_visible = True
        db.session.commit()
        set_config("score_visibility", "hidden")
        self.assertEqual(client.get("/api/v1/scoreboard").status_code, 403)
        response = self.admin.post(f"/plugins/ctfd-registration/admin/events/{self.boys.id}/start", data={})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.boys.state, "pending")

    def test_alternative_numeric_ids_cannot_bypass_event_guards(self):
        self.enable()
        boy, client = self.player("boy", self.boys)
        girl, _ = self.player("girl", self.girls)
        own = self.challenge("own", self.boys)
        other = self.challenge("other", self.girls)
        self.events.action(self.boys, "start")
        self.events.action(self.girls, "start")
        self.boys.scores_visible = True
        db.session.commit()
        for representation in (f"+{other.id}", f"0{other.id}", f"{other.id}.0"):
            self.assertIn(client.get(f"/api/v1/challenges/{representation}").status_code, (403, 404))
        self.assertEqual(client.get(f"/api/v1/users/+{girl.id}/solves").status_code, 404)
        self.assertEqual(client.get(f"/api/v1/teams/+{girl.team_id}/solves").status_code, 404)


if __name__ == "__main__":
    unittest.main()
