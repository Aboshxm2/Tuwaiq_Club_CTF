"""Hints are off for this event: purge them and refuse new ones."""

import re

from flask import request
from sqlalchemy import event

from CTFd.models import Hints, Unlocks, db

MESSAGE = "Hints are disabled for this event."

HINT_ITEM = re.compile(r"^/api/v1/hints/[^/]+/?$")


def purge_hints():
    try:
        Unlocks.query.filter_by(type="hints").delete(synchronize_session=False)
        Hints.query.delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()


def _blocked(path, method):
    path = path.rstrip("/") or "/"
    if path == "/api/v1/unlocks":
        return method == "POST"
    if path == "/api/v1/hints":
        return method != "GET"
    return bool(HINT_ITEM.match(path))


def install(app):
    purge_hints()

    @app.before_request
    def nohints_before_request():
        if _blocked(request.path or "", request.method):
            return {"success": False, "errors": {"": [MESSAGE]}}, 403

    if not getattr(app, "_nohints_hook", False):
        @event.listens_for(Hints, "before_insert", propagate=True)
        def _refuse_hint(mapper, connection, target):
            raise ValueError(MESSAGE)

        app._nohints_hook = True
