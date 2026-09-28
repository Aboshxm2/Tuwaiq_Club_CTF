import datetime

from CTFd.models import db

ACTIVE_STATES = ("running", "frozen")


class Rounds(db.Model):
    __tablename__ = "rounds"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    duration = db.Column(db.Integer, nullable=False)  # seconds
    # pending -> running <-> frozen -> ended
    state = db.Column(db.String(16), nullable=False, default="pending")
    started_at = db.Column(db.DateTime)
    frozen_at = db.Column(db.DateTime)
    paused_seconds = db.Column(db.Integer, nullable=False, default=0)
    ended_at = db.Column(db.DateTime)

    challenges = db.relationship(
        "RoundChallenges", backref="round", cascade="all, delete-orphan", lazy="select"
    )

    @property
    def challenge_ids(self):
        return [rc.challenge_id for rc in self.challenges]

    @property
    def is_active(self):
        return self.state in ACTIVE_STATES

    def elapsed(self, now=None):
        """Seconds the round has been running, excluding time spent frozen."""
        if self.started_at is None:
            return 0.0
        now = now or datetime.datetime.utcnow()
        if self.state == "ended" and self.ended_at:
            end = self.ended_at
        elif self.state == "frozen" and self.frozen_at:
            end = self.frozen_at
        else:
            end = now
        return max(0.0, (end - self.started_at).total_seconds() - self.paused_seconds)

    def remaining(self, now=None):
        return max(0.0, self.duration - self.elapsed(now))


class RoundChallenges(db.Model):
    __tablename__ = "round_challenges"
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(
        db.Integer, db.ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    challenge_id = db.Column(
        db.Integer,
        db.ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    challenge = db.relationship("Challenges", lazy="joined")


class RoundBonuses(db.Model):
    """Links an award created by the speed/first-blood rules to the solve that earned it."""

    __tablename__ = "round_bonuses"
    id = db.Column(db.Integer, primary_key=True)
    # Deliberately not a foreign key: the row must survive long enough for the solve-deletion
    # hook to find and delete the award.
    solve_id = db.Column(db.Integer, nullable=False, index=True)
    award_id = db.Column(
        db.Integer, db.ForeignKey("awards.id", ondelete="CASCADE"), nullable=False
    )
    kind = db.Column(db.String(16), nullable=False)


class ChallengeMeta(db.Model):
    """Maps a CTFd challenge to the handout generator that builds it."""

    __tablename__ = "round_challenge_meta"
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    slug = db.Column(db.String(80), nullable=False, unique=True)


class PersonalFlags(db.Model):
    """The only flag that scores for this account on this challenge."""

    __tablename__ = "personal_flags"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=False, index=True)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    flag = db.Column(db.String(160), nullable=False)
    token = db.Column(db.String(16), nullable=False)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("account_id", "challenge_id", name="uq_personal_flag_owner"),
        db.UniqueConstraint("challenge_id", "flag", name="uq_personal_flag_value"),
    )


class RoundFlagAlerts(db.Model):
    """A player submitted a flag that belongs to another team or user."""

    __tablename__ = "round_flag_alerts"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    account_id = db.Column(db.Integer)
    owner_account_id = db.Column(db.Integer)
    provided = db.Column(db.Text)

    challenge = db.relationship("Challenges", lazy="joined")
    user = db.relationship("Users", lazy="joined")
