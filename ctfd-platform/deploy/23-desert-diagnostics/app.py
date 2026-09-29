#!/usr/bin/env python3
"""Challenge 23 - Desert Diagnostics (deployable).

A network-diagnostics page that runs `ping -c 1 <host>` through a shell. The
host field is dropped straight into the command line, so it is command
injectable. A naive denylist blocks spaces and the obvious `;`/`&` chaining, so
the intended solve has to reach the flag file without them.

Intended solve (organizer note): the flag is written to /flag.txt at start-up.
Chain a command with a pipe and rebuild the space with ${IFS} (or a redirect):
    127.0.0.1|cat${IFS}/flag.txt
    127.0.0.1|cat</flag.txt
The combined stdout/stderr is shown, so the file's contents come back even
though ping itself may fail in a container. The flag is provided per team by
whale in the FLAG env var.
"""

import os
import subprocess
import html

from flask import Flask, Response, request

FLAG = os.environ.get("FLAG", "TAIBAH{local_test_flag_for_challenge_23}")
PORT = int(os.environ.get("PORT", "80"))

# The diagnostics tool "hides" the flag in a file only reachable by running a
# command on the host.
with open("/flag.txt", "w") as handle:
    handle.write(FLAG + "\n")

app = Flask(__name__)

# A deliberately shallow filter: it stops the most obvious separators and any
# whitespace, but a shell has more than one way to make a space and chain a
# command.
BLOCKED = set(" \t\r\n;&")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Oasis Network Diagnostics</title>
<style>
 body {{ font-family: system-ui, Arial, sans-serif; background:#f4e4c1; color:#4a3b2a; margin:0; }}
 header {{ background:#8b5e3c; color:#fff; padding:18px 24px; }}
 main {{ padding:24px; max-width:820px; }}
 input[type=text] {{ padding:8px; width:60%; border:1px solid #c2a36b; border-radius:6px; }}
 button {{ padding:8px 16px; background:#8b5e3c; color:#fff; border:none; border-radius:6px; cursor:pointer; }}
 pre {{ background:#101820; color:#e6edf3; padding:12px; border-radius:6px; overflow-wrap:anywhere;
       white-space:pre-wrap; margin-top:18px; }}
 .err {{ color:#842029; }}
 code {{ background:#efe2c4; padding:1px 4px; border-radius:4px; }}
</style></head>
<body>
<header><h1>Oasis Network Diagnostics</h1><p>Reachability check for our desert relays</p></header>
<main>
  <form method="get" action="/">
    <label>Host to ping:
      <input type="text" name="host" value="{host}" placeholder="e.g. 8.8.8.8" autofocus>
    </label>
    <button type="submit">Ping</button>
  </form>
  {body}
  <p style="margin-top:28px;color:#7a6a4f">Only relay operators should use this page.</p>
</main>
</body>
</html>
"""


def render(host, body):
    return Response(PAGE.format(host=html.escape(host, quote=True), body=body), mimetype="text/html")


@app.route("/")
def index():
    host = request.args.get("host")
    if host is None:
        return render("", "")
    bad = sorted(BLOCKED & set(host))
    if bad:
        shown = " ".join(repr(c) for c in bad)
        return render(host, f'<pre class="err">Illegal character(s) in host: {html.escape(shown)}</pre>')
    # VULNERABLE ON PURPOSE: user input is placed on a shell command line.
    cmd = "ping -c 1 -W 1 " + host
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        output = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        output = "diagnostic timed out"
    return render(host, f"<pre>$ {html.escape(cmd)}\n{html.escape(output)}</pre>")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
