"""Opt-in workshop events. Separate tables keep existing round data intact."""

import datetime

from CTFd.models import db


class WorkshopEvents(db.Model):
    __tablename__ = "workshop_events"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)
    bracket_id = db.Column(db.Integer, db.ForeignKey("brackets.id"), nullable=False)
    registration_open = db.Column(db.Boolean, nullable=False, default=True)
    scores_visible = db.Column(db.Boolean, nullable=False, default=False)
    duration = db.Column(db.Integer, nullable=False, default=10800)
    state = db.Column(db.String(16), nullable=False, default="pending")
    started_at = db.Column(db.DateTime)
    frozen_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    paused_seconds = db.Column(db.Integer, nullable=False, default=0)

    def elapsed(self):
        if self.started_at is None:
            return 0
        end = self.ended_at or self.frozen_at or datetime.datetime.utcnow()
        return max(0, int((end - self.started_at).total_seconds()) - self.paused_seconds)

    def remaining(self):
        return max(0, self.duration - self.elapsed())


class EventUsers(db.Model):
    __tablename__ = "workshop_event_users"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("workshop_events.id"), nullable=False, index=True)


class EventTeams(db.Model):
    __tablename__ = "workshop_event_teams"
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("workshop_events.id"), nullable=False, index=True)


class EventChallenges(db.Model):
    __tablename__ = "workshop_event_challenges"
    event_id = db.Column(db.Integer, db.ForeignKey("workshop_events.id"), primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True)
    batch = db.Column(db.String(80), nullable=False, default="الدفعة الأولى")
    released = db.Column(db.Boolean, nullable=False, default=False)
