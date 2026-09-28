#!/usr/bin/env python3
"""Exercise rounds, unique flags, the early-solve bonus, and the hint ban inside CTFd.

This resets round 1 and deletes the two test teams it creates.
Do not run it after the real event has started.
"""

import importlib
import sys

sys.path.insert(0, "/opt/CTFd")

from CTFd import create_app
from CTFd.models import Awards, Challenges, Hints, Solves, Teams, Users, db
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils.security.auth import login_user

TESTERS = ("roundtester-a", "roundtester-b")


def cleanup(models):
    users = Users.query.filter(Users.name.in_(TESTERS)).all()
    user_ids = [user.id for user in users]
    team_ids = [user.team_id for user in users if user.team_id]
    if user_ids:
        solve_ids = [
            row.id
            for row in Solves.query.filter(Solves.user_id.in_(user_ids)).all()
        ]
        if solve_ids:
            models.RoundBonuses.query.filter(models.RoundBonuses.solve_id.in_(solve_ids)).delete(
                synchronize_session=False
            )
            Solves.query.filter(Solves.id.in_(solve_ids)).delete(synchronize_session=False)
        Awards.query.filter(Awards.user_id.in_(user_ids)).delete(synchronize_session=False)
        models.RoundFlagAlerts.query.filter(models.RoundFlagAlerts.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )
    if team_ids:
        models.PersonalFlags.query.filter(models.PersonalFlags.account_id.in_(team_ids)).delete(
            synchronize_session=False
        )
        Teams.query.filter(Teams.id.in_(team_ids)).update(
            {Teams.captain_id: None}, synchronize_session=False
        )
    if user_ids:
        Users.query.filter(Users.id.in_(user_ids)).update(
            {Users.team_id: None}, synchronize_session=False
        )
        db.session.flush()
        if team_ids:
            Teams.query.filter(Teams.id.in_(team_ids)).delete(synchronize_session=False)
        Users.query.filter(Users.id.in_(user_ids)).delete(synchronize_session=False)
    db.session.commit()


def restore(logic, rnd):
    rnd.state = "pending"
    rnd.started_at = None
    rnd.frozen_at = None
    rnd.ended_at = None
    rnd.paused_seconds = 0
    db.session.commit()
    logic.apply_visibility()


def check_no_hints(challenge):
    assert Hints.query.count() == 0, "hints exist"
    db.session.add(Hints(challenge_id=challenge.id, content="should be refused"))
    try:
        db.session.flush()
    except ValueError as exc:
        assert "disabled" in str(exc), exc
    else:
        raise AssertionError("a hint was inserted")
    finally:
        db.session.rollback()
    assert Hints.query.count() == 0, "hints exist"


def make_player(name):
    user = Users(name=name, email=f"{name}@example.com", password="test-password")
    db.session.add(user)
    db.session.flush()
    team = Teams(
        name=name,
        email=f"{name}-team@example.com",
        password="test-password",
        captain_id=user.id,
    )
    db.session.add(team)
    db.session.flush()
    user.team_id = team.id
    db.session.commit()
    return user, team


def main():
    app = create_app()
    with app.app_context():
        rounds = importlib.import_module("CTFd.plugins.ctfd-rounds")
        logic = importlib.import_module("CTFd.plugins.ctfd-rounds.logic")
        models = importlib.import_module("CTFd.plugins.ctfd-rounds.models")
        rounds._wrap_challenge_classes()

        meta = models.ChallengeMeta.query.filter_by(slug="02-strange-letters").one()
        challenge = Challenges.query.filter_by(id=meta.challenge_id).one()
        rnd = logic.round_for_challenge(challenge.id)
        check_no_hints(challenge)
        cleanup(models)
        restore(logic, rnd)
        try:
            ok, message = logic.start_round(rnd)
            assert ok, message
            db.session.refresh(challenge)
            assert challenge.state == "visible", challenge.state
            hidden = Challenges.query.filter_by(name="Close Primes").one()
            assert hidden.state == "hidden", hidden.state

            first, first_team = make_player("roundtester-a")
            second, _second_team = make_player("roundtester-b")
            ok, message, row_a = logic.launch_instance(challenge, user=first)
            assert ok, message
            ok, message, row_b = logic.launch_instance(challenge, user=second)
            assert ok, message
            assert row_a.flag != row_b.flag
            assert row_a.flag.startswith("TAIBAH{") and row_a.flag.endswith("}")

            from flask import request

            with app.test_request_context(
                json={"submission": row_a.flag, "challenge_id": challenge.id},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            ):
                login_user(first)
                correct, text = CHALLENGE_CLASSES["standard"].attempt(challenge, request)
                assert correct, text
                CHALLENGE_CLASSES["standard"].solve(first, first_team, challenge, request)

            score = first.get_score(admin=True)
            assert score > challenge.value, score
            assert score <= challenge.value + challenge.value // 2 + 1, score

            with app.test_request_context(
                json={"submission": row_a.flag, "challenge_id": challenge.id},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            ):
                login_user(second)
                correct, text = CHALLENGE_CLASSES["standard"].attempt(challenge, request)
                assert not correct, text
                assert "another team" in text, text
            assert models.RoundFlagAlerts.query.filter_by(user_id=second.id).count() == 1
            assert (
                Solves.query.filter_by(user_id=second.id, challenge_id=challenge.id).count()
                == 0
            )

            ok, message = logic.freeze_round(rnd)
            assert ok, message
            with app.test_request_context(
                json={"submission": row_b.flag, "challenge_id": challenge.id},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            ):
                login_user(second)
                correct, text = CHALLENGE_CLASSES["standard"].attempt(challenge, request)
                assert not correct and "frozen" in text, text

            ok, message = logic.resume_round(rnd)
            assert ok, message
            ok, message = logic.end_round(rnd)
            assert ok, message
            db.session.refresh(challenge)
            assert challenge.state == "hidden"
            assert first.get_score(admin=True) == score
            print(f"PASS score={score} base={challenge.value} flags differ and do not transfer, no hints")
        finally:
            cleanup(models)
            restore(logic, rnd)


if __name__ == "__main__":
    main()
