#!/usr/bin/env python3
"""Challenge 20 - Token of Trust (deployable version).

A small staff portal that hands every visitor a *guest* JWT (HS256). The vault
returns the flag only to a token whose role is "admin". The signing secret is a
weak password taken from a backup that leaked and is served at /backup/wordlist.txt.

Intended solve (organizer note): read the guest token, recover the weak HS256
secret with the leaked wordlist, mint a token with role="admin", present it to
/vault. The flag is provided per team by whale in the FLAG env var.

No third-party crypto: HS256 is a plain HMAC-SHA256, done with the stdlib.
"""

import base64
import hashlib
import hmac
import json
import os
import random

from flask import Flask, Response, request

FLAG = os.environ.get("FLAG", "TAIBAH{local_test_flag_for_challenge_20}")
PORT = int(os.environ.get("PORT", "80"))

with open(os.path.join(os.path.dirname(__file__), "wordlist.txt")) as handle:
    WORDLIST = [line.strip() for line in handle if line.strip()]

# The portal's signing secret is one of the leaked passwords. Picking it at
# random per container means a secret recovered from one team's instance does
# not help against another's, and the flag itself is still unique per team.
SECRET = random.choice(WORDLIST)

app = Flask(__name__)


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign(signing_input: str, secret: str) -> str:
    mac = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return b64url(mac)


def issue(role: str) -> str:
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = b64url(
        json.dumps({"sub": "s441907", "name": "Guest Student", "role": role}, separators=(",", ":")).encode()
    )
    return f"{header}.{payload}.{sign(f'{header}.{payload}', SECRET)}"


def verify(token: str):
    """Return the payload dict for a correctly signed token, else None."""
    try:
        header, payload, signature = token.strip().split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(signature, sign(f"{header}.{payload}", SECRET)):
        return None
    try:
        return json.loads(b64url_decode(payload))
    except (ValueError, json.JSONDecodeError):
        return None


def bearer_token() -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):]
    return request.args.get("token") or request.cookies.get("token") or ""


PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Oasis Portal</title>
<style>
 body {{ font-family: system-ui, Arial, sans-serif; background:#f4e4c1; color:#4a3b2a; margin:0; }}
 header {{ background:#8b5e3c; color:#fff; padding:18px 24px; }}
 main {{ padding:24px; max-width:820px; }}
 code, pre {{ background:#efe2c4; border:1px solid #d8c39a; border-radius:6px; }}
 pre {{ padding:12px; overflow-wrap:anywhere; white-space:pre-wrap; }}
 a {{ color:#8b5e3c; }}
</style></head>
<body>
<header><h1>Oasis Portal</h1><p>Staff single sign-on</p></header>
<main>
  <p>Welcome, <strong>Guest Student</strong>. You are signed in with a guest session token:</p>
  <pre id="token">{token}</pre>
  <p>The token is a JSON Web Token (JWT, <code>HS256</code>): <code>header.payload.signature</code>.</p>
  <ul>
    <li><a href="/vault">/vault</a> &mdash; staff vault (requires an administrator token)</li>
    <li><a href="/backup/wordlist.txt">/backup/wordlist.txt</a> &mdash; a password backup that should not be here</li>
  </ul>
</main>
</body>
</html>
"""


@app.route("/")
def index():
    resp = Response(PAGE.format(token=issue("guest")), mimetype="text/html")
    resp.set_cookie("token", issue("guest"))
    return resp


@app.route("/backup/wordlist.txt")
def leaked_wordlist():
    return Response("\n".join(WORDLIST) + "\n", mimetype="text/plain")


@app.route("/vault")
def vault():
    claims = verify(bearer_token())
    if claims is None:
        return Response("No valid token. Sign in at / first.\n", status=401, mimetype="text/plain")
    if claims.get("role") != "admin":
        return Response(
            f"Token accepted for role '{claims.get('role')}', but the vault is for administrators only.\n",
            status=403,
            mimetype="text/plain",
        )
    return Response(f"Vault unlocked.\n{FLAG}\n", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
