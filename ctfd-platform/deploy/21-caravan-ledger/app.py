#!/usr/bin/env python3
"""Challenge 21 - Caravan Ledger (deployable).

A public "caravan manifest" search page backed by SQLite. The search box is
concatenated straight into the SQL, so the query is injectable. The team's flag
lives in a separate `secrets` table that the manifest page never selects from.

Intended solve (organizer note): the search runs
    SELECT name, cargo FROM caravans WHERE name LIKE '%<input>%'
so it has two output columns. Enumerate with sqlite_master, then read the flag
with a UNION, e.g.
    ' UNION SELECT label, secret FROM secrets --
Errors are shown on the page (error-based), so column-count and table names are
easy to discover. The flag is provided per team by whale in the FLAG env var.
"""

import os
import sqlite3
import html

from flask import Flask, Response, request

FLAG = os.environ.get("FLAG", "TAIBAH{local_test_flag_for_challenge_21}")
PORT = int(os.environ.get("PORT", "80"))

app = Flask(__name__)


def build_db():
    """A fresh in-memory database per request keeps teams from writing to a
    shared file and makes the challenge stateless."""
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE caravans (id INTEGER PRIMARY KEY, name TEXT, cargo TEXT);
        INSERT INTO caravans (name, cargo) VALUES
            ('Northern Dunes Express', 'dates, incense'),
            ('Red Sea Runner', 'coffee, textiles'),
            ('Hejaz Night Caravan', 'spices, silver'),
            ('Empty Quarter Freight', 'salt, rope'),
            ('Nafud Star', 'gold thread, myrrh');
        CREATE TABLE secrets (id INTEGER PRIMARY KEY, label TEXT, secret TEXT);
        """
    )
    con.execute("INSERT INTO secrets (label, secret) VALUES (?, ?)", ("vault_manifest", FLAG))
    con.commit()
    return con


PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Oasis Caravan Ledger</title>
<style>
 body {{ font-family: system-ui, Arial, sans-serif; background:#f4e4c1; color:#4a3b2a; margin:0; }}
 header {{ background:#8b5e3c; color:#fff; padding:18px 24px; }}
 main {{ padding:24px; max-width:860px; }}
 input[type=text] {{ padding:8px; width:60%; border:1px solid #c2a36b; border-radius:6px; }}
 button {{ padding:8px 16px; background:#8b5e3c; color:#fff; border:none; border-radius:6px; cursor:pointer; }}
 table {{ border-collapse:collapse; margin-top:18px; width:100%; }}
 th, td {{ border:1px solid #d8c39a; padding:8px 10px; text-align:left; }}
 th {{ background:#efe2c4; }}
 .err {{ background:#f8d7da; border:1px solid #d9a3a8; color:#842029; padding:10px 12px;
        border-radius:6px; margin-top:18px; white-space:pre-wrap; }}
 code {{ background:#efe2c4; padding:1px 4px; border-radius:4px; }}
</style></head>
<body>
<header><h1>Oasis Caravan Ledger</h1><p>Search the public caravan manifest</p></header>
<main>
  <form method="get" action="/">
    <input type="text" name="q" value="{q}" placeholder="caravan name, e.g. Dunes" autofocus>
    <button type="submit">Search</button>
  </form>
  {body}
  <p style="margin-top:28px;color:#7a6a4f">Tip: try searching a caravan name such as <code>Dunes</code>.</p>
</main>
</body>
</html>
"""


def render(q, body):
    return Response(PAGE.format(q=html.escape(q, quote=True), body=body), mimetype="text/html")


@app.route("/")
def index():
    q = request.args.get("q")
    if q is None:
        return render("", "")
    # VULNERABLE ON PURPOSE: the search term is concatenated into the SQL.
    query = "SELECT name, cargo FROM caravans WHERE name LIKE '%" + q + "%'"
    con = build_db()
    try:
        rows = con.execute(query).fetchall()
    except Exception as exc:  # noqa: BLE001 - error-based injection is intended
        return render(q, f'<div class="err">SQL error: {html.escape(str(exc))}\n\nQuery: {html.escape(query)}</div>')
    finally:
        con.close()

    if not rows:
        return render(q, "<p>No caravans matched your search.</p>")
    cells = "".join(
        "<tr><td>{}</td><td>{}</td></tr>".format(html.escape(str(a)), html.escape(str(b)))
        for a, b in rows
    )
    table = f"<table><tr><th>name</th><th>cargo</th></tr>{cells}</table>"
    return render(q, table)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
