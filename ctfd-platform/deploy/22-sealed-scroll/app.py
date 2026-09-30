#!/usr/bin/env python3
"""Challenge 22 - Sealed Scroll (deployable).

A session "scroll" encrypted with AES-CBC and no integrity check. The scroll is
`IV || ciphertext` handed to the visitor. Because CBC has no MAC, a visitor can
flip bits in the IV to change the first plaintext block without the key. The
first block is `role=guest;xxxxx`, so flipping five bytes of the IV turns it
into `role=admin;xxxxx`, and the vault opens.

Intended solve (organizer note):
  * the scroll layout is shown on `/` (plaintext `role=guest;xxxxx`),
  * P0 = D(C0) XOR IV, so flipping IV[i] flips plaintext byte i of block 0,
  * for i in 5..9 set new_iv[i] = iv[i] ^ ord("guest"[i-5]) ^ ord("admin"[i-5]),
  * send the modified scroll to `/vault`.
Only the IV is touched, so the PKCS7 pad block (block 1) stays valid. The flag
is provided per team by whale in the FLAG env var.
"""

import base64
import os
import re

from flask import Flask, Response, request
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

FLAG = os.environ.get("FLAG", "TAIBAH{local_test_flag_for_challenge_22}")
PORT = int(os.environ.get("PORT", "80"))

KEY = os.urandom(16)
PLAINTEXT = b"role=guest;xxxxx"  # exactly one 16-byte AES block


def b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_scroll() -> str:
    iv = os.urandom(16)
    ct = AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(PLAINTEXT, 16))
    return b64e(iv + ct)


def open_scroll(token: str):
    """Return the decrypted first-block fields, or None if the scroll is junk."""
    try:
        raw = b64d(token.strip())
        iv, ct = raw[:16], raw[16:]
        if len(iv) != 16 or len(ct) == 0 or len(ct) % 16 != 0:
            return None
        plaintext = unpad(AES.new(KEY, AES.MODE_CBC, iv).decrypt(ct), 16)
    except (ValueError, KeyError):
        return None
    return plaintext


def scroll_token() -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):]
    return request.args.get("token") or request.cookies.get("token") or ""


def role_of(plaintext: bytes):
    for field in plaintext.split(b";"):
        match = re.match(rb"role=([A-Za-z0-9]+)$", field)
        if match:
            return match.group(1).decode()
    return None


PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Oasis Sealed Scroll</title>
<style>
 body {{ font-family: system-ui, Arial, sans-serif; background:#f4e4c1; color:#4a3b2a; margin:0; }}
 header {{ background:#8b5e3c; color:#fff; padding:18px 24px; }}
 main {{ padding:24px; max-width:820px; }}
 code, pre {{ background:#efe2c4; border:1px solid #d8c39a; border-radius:6px; }}
 pre {{ padding:12px; overflow-wrap:anywhere; white-space:pre-wrap; }}
 a {{ color:#8b5e3c; }}
</style></head>
<body>
<header><h1>Oasis Sealed Scroll</h1><p>Encrypted session scrolls for the archive</p></header>
<main>
  <p>You hold a <strong>guest</strong> scroll. It is <code>AES-CBC</code>, encoded as
     <code>base64url(IV || ciphertext)</code>:</p>
  <pre id="scroll">{token}</pre>
  <p>Decrypted, the first 16-byte block of your scroll reads:</p>
  <pre>{plaintext}</pre>
  <ul>
    <li><a href="/vault">/vault</a> &mdash; the archive vault (opens only for an <code>admin</code> scroll)</li>
  </ul>
  <p style="color:#7a6a4f">Present your scroll as a <code>token</code> cookie, a
     <code>?token=</code> parameter, or an <code>Authorization: Bearer</code> header.</p>
</main>
</body>
</html>
"""


app = Flask(__name__)


@app.route("/")
def index():
    token = issue_scroll()
    resp = Response(
        PAGE.format(token=token, plaintext=PLAINTEXT.decode()), mimetype="text/html"
    )
    resp.set_cookie("token", token)
    return resp


@app.route("/vault")
def vault():
    plaintext = open_scroll(scroll_token())
    if plaintext is None:
        return Response("No readable scroll. Get one at / first.\n", status=401, mimetype="text/plain")
    role = role_of(plaintext)
    if role != "admin":
        return Response(
            f"Scroll accepted for role '{role}', but the vault opens only for administrators.\n",
            status=403,
            mimetype="text/plain",
        )
    return Response(f"Vault unlocked.\n{FLAG}\n", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
