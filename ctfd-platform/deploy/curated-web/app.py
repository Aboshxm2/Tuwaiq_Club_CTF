"""Isolated, deliberately vulnerable CTF apps. Never mount this in CTFd.

Select exactly one app with CHALLENGE. FLAG is supplied by ctfd-whale.
All data is fictional. No database, credentials or files are shared with CTFd.
"""
import base64
import io
import json
import os
import sqlite3
import zipfile
from html import escape

from flask import Flask, Response, jsonify, make_response, redirect, request
from jinja2 import Environment, nodes, select_autoescape
from jinja2.sandbox import SandboxedEnvironment

app = Flask(__name__)
MODE = os.environ.get("CHALLENGE", "last-edit")
FLAG = os.environ.get("FLAG", "TAIBAH{local_preview_only}")
ALLOWED = {"last-edit", "forgotten-route", "frontend-pass", "trial-login",
           "refund-desk", "caravan-ledger", "template-studio"}
if MODE not in ALLOWED:
    raise RuntimeError("Unknown challenge mode")

PAGE = """<!doctype html><html lang="en" dir="ltr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} | Oasis Services</title><link rel="stylesheet" href="/style.css">
</head><body><header><a href="/" class="brand">OASIS<span> / {{ label }}</span></a>
<span class="tag">STAFF & COMMUNITY SERVICES</span></header>
<main><p class="eyebrow">{{ label }}</p><h1>{{ title }}</h1>{{ body | safe }}</main>
<footer>Oasis Services · Training environment · Fictional records</footer>
<script src="/site.js"></script></body></html>"""
CSS = """*{box-sizing:border-box}body{margin:0;background:#eef2f6;color:#172d42;font:16px/1.6 system-ui,sans-serif}
header{padding:22px 6vw;background:#142b40;color:white;display:flex;justify-content:space-between;gap:20px;align-items:center}
.brand{font-weight:800;color:white;text-decoration:none;letter-spacing:.07em}.brand span{font-weight:400;color:#b5cadb}
.tag,.eyebrow{font-size:12px;letter-spacing:.13em}.eyebrow{color:#64788b;text-transform:uppercase}
main{max-width:940px;margin:58px auto;padding:36px;background:white;border:1px solid #dce4ec;border-radius:16px;box-shadow:0 16px 50px #142b400a}
h1{font-size:clamp(28px,5vw,42px);line-height:1.15;margin:12px 0 24px}h2{font-size:22px}
input,textarea,button{font:inherit;border-radius:7px}input,textarea{padding:11px;border:1px solid #bccad5;width:100%;margin:8px 0 18px}
textarea{min-height:110px}button,.button{padding:11px 22px;background:#176078;color:white;border:0;text-decoration:none;display:inline-block;cursor:pointer}
button:disabled{background:#bdc7d0;cursor:not-allowed}label{font-weight:600;display:block}.notice{padding:16px;background:#eaf3f7;border-left:4px solid #176078}
.error{padding:16px;background:#fff0ec;border-left:4px solid #b85a37}code,pre{background:#f0f3f6;padding:3px 7px;overflow-wrap:anywhere;white-space:pre-wrap}
table{border-collapse:collapse;width:100%;margin:22px 0}td,th{text-align:left;border-bottom:1px solid #dce4ec;padding:12px}
footer{max-width:940px;margin:30px auto;padding:0 24px;color:#718396;font-size:12px}a{color:#176078}@media(max-width:600px){main{margin:22px 14px;padding:24px}.tag{display:none}}"""
VIEW_ENV = Environment(autoescape=select_autoescape(default=True))
TEMPLATE_ENV = SandboxedEnvironment(autoescape=True)


def page(title, body, status=200):
    return Response(VIEW_ENV.from_string(PAGE).render(
        title=title, label=MODE.replace("-", " "), body=body), status=status, mimetype="text/html")


def split_flag():
    a, b = len(FLAG) // 3, 2 * len(FLAG) // 3
    return FLAG[:a], FLAG[a:b], FLAG[b:]


@app.get("/style.css")
def style():
    tail = "\n/* Build note 2/3: " + split_flag()[1] + " */" if MODE == "last-edit" else ""
    return Response(CSS + tail, mimetype="text/css")


@app.get("/site.js")
def script():
    source = "// Oasis public interface.\n"
    if MODE == "last-edit":
        source += "// Build note 3/3: " + split_flag()[2] + "\n"
    return Response(source, mimetype="application/javascript")


@app.get("/")
def home():
    if MODE == "last-edit":
        return page("A place for the next idea", """<p>Registration for the Oasis community showcase opens soon.</p>
        <div class="notice">Our new site is almost ready. Take a look around while we finish the final edits.</div>
        <!-- Build note 1/3: """ + escape(split_flag()[0]) + " -->")
    if MODE == "forgotten-route":
        return page("The new archive", "<p>Our records have moved. Only this year's public collection appears in the new navigation.</p><p>Older exports have been removed from the menu.</p>")
    if MODE == "frontend-pass":
        response = make_response(page("Preview workspace", """<p>The staff preview is not ready for public visitors.</p>
        <button disabled onclick="location.href='/preview'">Open staff preview</button>
        <p class="notice">Preview preferences are saved in your browser.</p>"""))
        if not request.cookies.get("preview_state"):
            response.set_cookie("preview_state", base64.b64encode(b'{"view":"guest"}').decode(), samesite="Lax")
        return response
    if MODE == "trial-login":
        return page("Staff sign in", """<p>Use the legacy staff portal to access the handover note.</p>
        <form method="post" action="/login"><label>Username<input name="username" required></label>
        <label>Password<input name="password" type="password" required></label><button>Sign in</button></form>""")
    if MODE == "refund-desk":
        return page("Refund desk", """<p>You are signed in to a demonstration account as <strong>Morgan Reed</strong>.</p>
        <p>Your request: <a href="/requests/104">RF-104 · Duplicate booking</a></p>
        <div class="notice">A staff-only review was attached as request RF-108. Only its owner should be able to update it.</div>""")
    if MODE == "caravan-ledger":
        return ledger()
    return page("Make a welcome card", """<p>Personalize a card for the showcase. Our template engine supports more than plain text.</p>
        <form method="post" action="/render"><label>Card template<textarea name="template" maxlength="1200">Welcome, {{ guest }}!</textarea></label>
        <button>Preview card</button></form><p class="notice">Preview context: guest, event, config.</p>""")


@app.get("/robots.txt")
def robots():
    text = "User-agent: *\nDisallow: /retired-archive/\n" if MODE == "forgotten-route" else "User-agent: *\nDisallow:\n"
    return Response(text, mimetype="text/plain")


@app.get("/retired-archive/")
def retired():
    if MODE != "forgotten-route":
        return page("Not found", "<p>No such page.</p>", 404)
    return page("Retired exports", '<p>Migration copy — retained for audit.</p><a href="/retired-archive/portal-backup.zip">portal-backup.zip</a>')


@app.get("/retired-archive/portal-backup.zip")
def backup():
    if MODE != "forgotten-route":
        return Response(status=404)
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("README.txt", "Retired portal backup. The handover code was kept in settings.ini.\n")
        bundle.writestr("settings.ini", "[handover]\ncode=" + FLAG + "\n")
    return Response(data.getvalue(), mimetype="application/zip", headers={"Content-Disposition": 'attachment; filename="portal-backup.zip"'})


@app.get("/preview")
def preview():
    if MODE != "frontend-pass":
        return Response(status=404)
    try:
        state = json.loads(base64.b64decode(request.cookies.get("preview_state", ""), validate=True))
    except (ValueError, TypeError):
        state = {}
    if not isinstance(state, dict) or state.get("view") != "staff":
        return page("Preview unavailable", '<p class="error">Your saved preview state does not select the staff view.</p>', 403)
    return page("Staff preview", "<p>Handover code: <code>" + escape(FLAG) + "</code></p>")


@app.post("/login")
def login():
    if MODE != "trial-login":
        return Response(status=404)
    con = sqlite3.connect(":memory:")
    try:
        con.execute("CREATE TABLE users (name TEXT, password TEXT)")
        con.execute("INSERT INTO users VALUES (?, ?)", ("supervisor", os.urandom(20).hex()))
        # Deliberate SQL injection, only in this fictional in-memory database.
        query = "SELECT name FROM users WHERE name='" + request.form.get("username", "") + "' AND password='" + request.form.get("password", "") + "'"
        row = con.execute(query).fetchone()
    except sqlite3.Error:
        return page("Sign-in error", '<p class="error">The legacy query could not be processed.</p>', 400)
    finally:
        con.close()
    if not row:
        return page("Sign-in failed", '<p class="error">Incorrect username or password.</p>', 403)
    return page("Handover", "<p>Staff handover code: <code>" + escape(FLAG) + "</code></p>")


@app.get("/requests/<int:request_id>")
def request_page(request_id):
    if MODE != "refund-desk" or request_id not in (104, 108):
        return Response(status=404)
    return page("Request RF-" + str(request_id), """<pre id="record">Loading request...</pre>
    <button id="approve">Approve refund</button><pre id="result"></pre>
    <script>
    const requestId = """ + str(request_id) + """;
    fetch('/api/requests/'+requestId).then(r=>r.json()).then(d=>{
      document.getElementById('record').textContent=JSON.stringify(d,null,2);
      document.getElementById('approve').disabled=d.owner!=='Morgan Reed';
    });
    document.getElementById('approve').onclick=()=>fetch('/api/requests/'+requestId,{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'approve'})
    }).then(r=>r.json()).then(d=>document.getElementById('result').textContent=JSON.stringify(d,null,2));
    </script>""")


@app.route("/api/requests/<int:request_id>", methods=["GET", "POST"])
def refund_api(request_id):
    if MODE != "refund-desk" or request_id not in (104, 108):
        return jsonify(error="Request not found"), 404
    if request.method == "GET":
        return jsonify(id=request_id, owner="Morgan Reed" if request_id == 104 else "Casey Lane", status="awaiting_review", amount=45 if request_id == 104 else 120)
    if (request.get_json(silent=True) or {}).get("action") != "approve":
        return jsonify(error="Unknown action"), 400
    # Intentionally missing ownership check. The UI restriction is insufficient.
    if request_id == 108:
        return jsonify(status="approved", audit_code=FLAG)
    return jsonify(status="approved", message="Your own request was approved. Review the staff-only attachment.")


def ledger():
    q = request.args.get("q")
    form = '<form><label>Caravan name<input name="q" value="' + escape(q or "") + '"></label><button>Search</button></form>'
    if q is None:
        return page("Caravan ledger", "<p>Search public manifests. Private audit records are not included in the normal view.</p>" + form)
    con = sqlite3.connect(":memory:")
    try:
        con.executescript("CREATE TABLE caravans(name TEXT,cargo TEXT); INSERT INTO caravans VALUES('Northern Route','Dates'),('Coastal Route','Coffee'); CREATE TABLE audit_records(label TEXT,secret TEXT);")
        con.execute("INSERT INTO audit_records VALUES (?,?)", ("handover", FLAG))
        rows = con.execute("SELECT name,cargo FROM caravans WHERE name LIKE '%" + q + "%'").fetchall()
        body = "<table><tr><th>Name</th><th>Cargo</th></tr>" + "".join("<tr><td>" + escape(str(a)) + "</td><td>" + escape(str(b)) + "</td></tr>" for a, b in rows) + "</table>"
    except sqlite3.Error as exc:
        body = '<p class="error">Database error: ' + escape(str(exc)) + '</p>'
    finally:
        con.close()
    return page("Caravan ledger", form + body)


@app.post("/render")
def render_card():
    if MODE != "template-studio":
        return Response(status=404)
    text = request.form.get("template", "")
    if len(text) > 1200:
        return page("Card too long", "<p>Use at most 1,200 characters.</p>", 400)
    # A sandbox bounds this educational injection to a dummy context; no need
    # for command execution, real app.config or container environment access.
    try:
        template = TEMPLATE_ENV.from_string(text)
        if any(node.__class__.__name__ in {"For", "Macro", "Call", "Mul", "Pow"} for node in TEMPLATE_ENV.parse(text).find_all(nodes.Node)):
            return page("Unsupported template", "<p>This preview supports expressions and fields, not loops or function calls.</p>", 400)
        output = template.render(guest="Visitor", event="Oasis Showcase", config={"AUDIT_CODE": FLAG, "THEME": "oasis"})
    except Exception:
        return page("Template error", '<p class="error">The preview template could not be rendered.</p>', 400)
    return page("Card preview", "<pre>" + escape(output) + "</pre><a href='/'>Edit card</a>")


@app.after_request
def response_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "80")), debug=False)
