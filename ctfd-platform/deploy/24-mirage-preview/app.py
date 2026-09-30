#!/usr/bin/env python3
"""Challenge 24 - Mirage Preview (deployable).

A "link preview" service: paste a URL and the server fetches it and shows the
response. It has no SSRF protection beyond a naive substring blocklist, so it
can be pointed at an internal admin service that is bound to loopback and never
exposed to players.

Two servers run in one container:
  * public preview app  -> 0.0.0.0:80  (what whale routes to the team)
  * internal admin      -> 127.0.0.1:8081  (holds the flag; unroutable)

Intended solve (organizer note): the blocklist rejects the literal strings
"localhost" and "127.0.0.1", so reach the admin service through another spelling
of loopback, e.g.
    http://0.0.0.0:8081/flag
    http://2130706433:8081/flag      (decimal 127.0.0.1)
The admin service returns the flag, which the preview echoes back. The flag is
provided per team by whale in the FLAG env var.
"""

import html
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from urllib.request import urlopen
from urllib.error import URLError

from flask import Flask, Response, request

FLAG = os.environ.get("FLAG", "TAIBAH{local_test_flag_for_challenge_24}")
PORT = int(os.environ.get("PORT", "80"))
ADMIN_PORT = 8081

# ---------------------------------------------------------------------------
# Internal admin service: bound to loopback only, so players cannot reach it
# directly through whale (only port 80 is routed). It hands out the flag.
# ---------------------------------------------------------------------------
class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (http.server API)
        if self.path.rstrip("/") == "/flag":
            body = f"Oasis internal control panel\nvault key: {FLAG}\n".encode()
        else:
            body = b"Oasis internal control panel\nTry /flag\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep the container logs quiet
        pass


def serve_admin():
    ThreadingHTTPServer(("127.0.0.1", ADMIN_PORT), AdminHandler).serve_forever()


# ---------------------------------------------------------------------------
# Public preview app.
# ---------------------------------------------------------------------------
app = Flask(__name__)

BLOCKLIST = ("localhost", "127.0.0.1")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Oasis Mirage Preview</title>
<style>
 body {{ font-family: system-ui, Arial, sans-serif; background:#f4e4c1; color:#4a3b2a; margin:0; }}
 header {{ background:#8b5e3c; color:#fff; padding:18px 24px; }}
 main {{ padding:24px; max-width:820px; }}
 input[type=text] {{ padding:8px; width:70%; border:1px solid #c2a36b; border-radius:6px; }}
 button {{ padding:8px 16px; background:#8b5e3c; color:#fff; border:none; border-radius:6px; cursor:pointer; }}
 pre {{ background:#101820; color:#e6edf3; padding:12px; border-radius:6px; overflow-wrap:anywhere;
       white-space:pre-wrap; margin-top:18px; }}
 .err {{ color:#842029; }}
</style></head>
<body>
<header><h1>Oasis Mirage Preview</h1><p>Preview any link before you share it</p></header>
<main>
  <form method="get" action="/">
    <input type="text" name="url" value="{url}" placeholder="https://example.com/" autofocus>
    <button type="submit">Preview</button>
  </form>
  {body}
  <p style="margin-top:28px;color:#7a6a4f">Only public web addresses are allowed.</p>
</main>
</body>
</html>
"""


def render(url, body):
    return Response(PAGE.format(url=html.escape(url, quote=True), body=body), mimetype="text/html")


@app.route("/")
def index():
    url = request.args.get("url")
    if url is None:
        return render("", "")
    low = url.lower()
    if not (low.startswith("http://") or low.startswith("https://")):
        return render(url, '<pre class="err">Only http:// and https:// URLs are allowed.</pre>')
    if any(bad in low for bad in BLOCKLIST):
        return render(url, '<pre class="err">Refusing to preview an internal address.</pre>')
    try:
        # VULNERABLE ON PURPOSE: no check that the host is external.
        with urlopen(url, timeout=4) as resp:  # noqa: S310 (intended SSRF sink)
            data = resp.read(4096).decode("utf-8", "replace")
    except (URLError, ValueError, OSError) as exc:
        return render(url, f'<pre class="err">Could not fetch: {html.escape(str(exc))}</pre>')
    host = urlsplit(url).hostname or "?"
    return render(url, f"<pre>Preview of {html.escape(host)}:\n\n{html.escape(data)}</pre>")


if __name__ == "__main__":
    threading.Thread(target=serve_admin, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
