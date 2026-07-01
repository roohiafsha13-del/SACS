"""
models.py — Database Models
Smart Campus Attendance System

Tables:
  users        — students and admins (role-based)
  attendance   — daily check-in / check-out records
  locations    — GPS coordinate audit trail
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db     = SQLAlchemy()
bcrypt = Bcrypt()


# ============================================================
# USER MODEL  (students + admins in one table, role field)
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer,     primary_key=True)
    student_id    = db.Column(db.String(20),  unique=True,  nullable=True)   # e.g. CS2401
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(150), unique=True,  nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(10),  nullable=False, default='student')  # 'student' | 'admin'
    batch         = db.Column(db.String(20),  nullable=True)   # e.g. CS-A
    is_active     = db.Column(db.Boolean,     nullable=False, default=True)
    created_at    = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    # Relationships
    attendances = db.relationship('Attendance', back_populates='user',
                                  lazy='dynamic', cascade='all, delete-orphan')
    locations   = db.relationship('Location',   back_populates='user',
                                  lazy='dynamic', cascade='all, delete-orphan')

    # ── Password helpers ──────────────────────────────────────
    def set_password(self, raw_password: str):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    # ── Computed properties ───────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    @property
    def initials(self) -> str:
        parts = self.name.strip().split()
        return ''.join(p[0].upper() for p in parts[:2])

    def attendance_percentage(self, total_days: int = None) -> float:
        """Return attendance % over all recorded days or a given total."""
        present = self.attendances.filter_by(status='Present').count()
        if total_days is None:
            total = self.attendances.count()
        else:
            total = total_days
        return round((present / total) * 100, 1) if total > 0 else 0.0

    def todays_record(self):
        """Return today's Attendance row or None."""
        return self.attendances.filter_by(date=date.today()).first()

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'


# ============================================================
# ATTENDANCE MODEL
# ============================================================
class Attendance(db.Model):
    __tablename__ = 'attendance'

    id          = db.Column(db.Integer,  primary_key=True)
    user_id     = db.Column(db.Integer,  db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date        = db.Column(db.Date,     nullable=False, default=date.today)
    login_time  = db.Column(db.DateTime, nullable=True)   # check-in timestamp
    logout_time = db.Column(db.DateTime, nullable=True)   # check-out timestamp
    status      = db.Column(db.String(10), nullable=False, default='Absent')  # 'Present' | 'Absent'
    note        = db.Column(db.String(200), nullable=True)  # optional admin note

    # Relationship back to user
    user = db.relationship('User', back_populates='attendances')

    # ── Constraints ───────────────────────────────────────────
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )

    # ── Computed ──────────────────────────────────────────────
    @property
    def duration_seconds(self) -> int | None:
        """Return on-campus duration in seconds, or None if not checked out."""
        if self.login_time and self.logout_time:
            return int((self.logout_time - self.login_time).total_seconds())
        return None

    @property
    def duration_str(self) -> str:
        secs = self.duration_seconds
        if secs is None:
            return 'Active' if self.login_time else '—'
        h = secs // 3600
        m = (secs % 3600) // 60
        return f'{h}h {m:02d}m'

    @property
    def login_str(self) -> str:
        return self.login_time.strftime('%I:%M %p') if self.login_time else '—'

    @property
    def logout_str(self) -> str:
        return self.logout_time.strftime('%I:%M %p') if self.logout_time else '—'

    def __repr__(self):
        return f'<Attendance user={self.user_id} date={self.date} status={self.status}>'


# ============================================================
# LOCATION MODEL  (GPS audit trail)
# ============================================================
class Location(db.Model):
    __tablename__ = 'locations'

    id          = db.Column(db.Integer,  primary_key=True)
    user_id     = db.Column(db.Integer,  db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    latitude    = db.Column(db.Numeric(10, 8), nullable=False)
    longitude   = db.Column(db.Numeric(11, 8), nullable=False)
    accuracy_m  = db.Column(db.Float,   nullable=True)    # GPS accuracy in metres
    is_valid    = db.Column(db.Boolean,  nullable=False, default=False)  # within campus?
    event_type  = db.Column(db.String(10), nullable=False, default='check')  # 'checkin' | 'checkout' | 'check'
    timestamp   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', back_populates='locations')

    @property
    def coords_str(self) -> str:
        return f'{float(self.latitude):.4f}°N, {float(self.longitude):.4f}°E'

    def __repr__(self):
        return f'<Location user={self.user_id} valid={self.is_valid} at={self.timestamp}>'