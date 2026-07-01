"""
seed.py — Database Seeder
Smart Campus Attendance System

Run once to populate the database with:
  - 1 admin account
  - 10 demo students
  - 30 days of realistic attendance records
  - GPS location records

Usage:
    python seed.py
"""

import os
import random
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from models import db, User, Attendance, Location


# ── Demo data ─────────────────────────────────────────────────
ADMIN = {
    'name':     os.environ.get('ADMIN_NAME',     'Dr. S. Sharma'),
    'email':    os.environ.get('ADMIN_EMAIL',    'admin@campus.edu'),
    'password': os.environ.get('ADMIN_PASSWORD', 'Admin@1234'),
}

STUDENTS = [
    {'name': 'Ankita Kapoor',     'student_id': 'IT2401', 'email': 'ankita.kapoor@campus.edu',    'batch': 'IT-A'},
    {'name': 'Shifa Fatima',    'student_id': 'IT2402', 'email': 'shifa.fatima@campus.edu',   'batch': 'IT-A'},
    {'name': 'Suresh Mehta',   'student_id': 'IT2403', 'email': 'suresh.m@campus.edu',      'batch': 'IT-A'},
    {'name': 'Abdul Ahil',    'student_id': 'IT2404', 'email': 'ahil.a@campus.edu',       'batch': 'IT-A'},
    {'name': 'Abdul Hassan', 'student_id': 'IT2405', 'email': 'hassan.a@campus.edu',       'batch': 'IT-B'},
    {'name': 'Maya Singh',     'student_id': 'IT2406', 'email': 'maya.s@campus.edu',        'batch': 'IT-B'},
    {'name': 'Riya Singh',      'student_id': 'IT2407', 'email': 'riya.s@campus.edu',       'batch': 'IT-B'},
    {'name': 'Max Thomas',   'student_id': 'IT2408', 'email': 'max.t@campus.edu',       'batch': 'IT-B'},
    {'name': 'Deepak Nair',    'student_id': 'IT2409', 'email': 'deepak.n@campus.edu',      'batch': 'IT-A'},
    {'name': 'Kavitha Reddy',    'student_id': 'IT2410', 'email': 'kavitha.r@campus.edu',     'batch': 'IT-B'},
]

# Campus centre GPS (matches .env defaults)
CAMPUS_LAT = float(os.environ.get('CAMPUS_LAT', 17.4492))
CAMPUS_LON = float(os.environ.get('CAMPUS_LON', 78.3915))

# Attendance probability per student (realistic variation)
ATTENDANCE_RATES = [0.90, 0.95, 0.78, 0.97, 0.60, 0.70, 0.83, 0.74, 0.91, 0.82]


def random_checkin_time(day: date) -> datetime:
    """Return a realistic check-in time between 08:00 and 09:30."""
    hour   = random.randint(8, 9)
    minute = random.randint(0, 59) if hour == 8 else random.randint(0, 29)
    return datetime(day.year, day.month, day.day, hour, minute, random.randint(0, 59))


def random_checkout_time(checkin: datetime) -> datetime:
    """Return check-out time 5–9 hours after check-in."""
    hours   = random.uniform(5.0, 9.0)
    minutes = int(hours * 60)
    return checkin + timedelta(minutes=minutes)


def random_coords_inside() -> tuple:
    """Return GPS coords slightly offset from campus centre (inside boundary)."""
    jitter = 0.003
    return (
        round(CAMPUS_LAT + random.uniform(-jitter, jitter), 8),
        round(CAMPUS_LON + random.uniform(-jitter, jitter), 8),
    )


def working_days(start: date, end: date):
    """Yield each Monday–Friday between start and end inclusive."""
    current = start
    while current <= end:
        if current.weekday() < 5:   # 0=Mon … 4=Fri
            yield current
        current += timedelta(days=1)


# ─────────────────────────────────────────────────────────────
def run():
    app = create_app()
    with app.app_context():
        print("=" * 50)
        print(" Smart Campus Attendance System — Seeder")
        print("=" * 50)

        # Drop and recreate all tables for a clean seed
        db.drop_all()
        db.create_all()
        print("\n✅  Tables created")

        # ── 1. Admin ──────────────────────────────────────────
        admin = User(
            name  = ADMIN['name'],
            email = ADMIN['email'],
            role  = 'admin',
        )
        admin.set_password(ADMIN['password'])
        db.session.add(admin)
        db.session.flush()
        print(f"✅  Admin created  →  {admin.email}  /  {ADMIN['password']}")

        # ── 2. Students ───────────────────────────────────────
        student_objects = []
        for s_data in STUDENTS:
            student = User(
                name       = s_data['name'],
                email      = s_data['email'],
                student_id = s_data['student_id'],
                batch      = s_data['batch'],
                role       = 'student',
            )
            student.set_password('Student@1234')
            db.session.add(student)
            student_objects.append(student)

        db.session.flush()
        print(f"✅  {len(student_objects)} students created  (default password: Student@1234)")

        # ── 3. Attendance + Location records (last 30 days) ───
        today     = date.today()
        start_day = today - timedelta(days=30)
        days      = list(working_days(start_day, today))

        att_count = 0
        loc_count = 0

        for i, student in enumerate(student_objects):
            rate = ATTENDANCE_RATES[i]

            for day in days:
                is_present = random.random() < rate

                # Always create an attendance row (Present or Absent)
                att = Attendance(
                    user_id = student.id,
                    date    = day,
                    status  = 'Present' if is_present else 'Absent',
                )

                if is_present:
                    checkin  = random_checkin_time(day)
                    # Don't add checkout for today (simulate active session)
                    checkout = None if day == today else random_checkout_time(checkin)
                    att.login_time  = checkin
                    att.logout_time = checkout

                    # GPS check-in record
                    lat, lon = random_coords_inside()
                    loc_in = Location(
                        user_id    = student.id,
                        latitude   = lat,
                        longitude  = lon,
                        accuracy_m = round(random.uniform(3, 15), 1),
                        is_valid   = True,
                        event_type = 'checkin',
                        timestamp  = checkin,
                    )
                    db.session.add(loc_in)
                    loc_count += 1

                    # GPS check-out record
                    if checkout:
                        lat2, lon2 = random_coords_inside()
                        loc_out = Location(
                            user_id    = student.id,
                            latitude   = lat2,
                            longitude  = lon2,
                            accuracy_m = round(random.uniform(3, 15), 1),
                            is_valid   = True,
                            event_type = 'checkout',
                            timestamp  = checkout,
                        )
                        db.session.add(loc_out)
                        loc_count += 1

                db.session.add(att)
                att_count += 1

        db.session.commit()

        print(f"✅  {att_count} attendance records created")
        print(f"✅  {loc_count} location records created")

        # ── 4. Summary ────────────────────────────────────────
        print("\n" + "=" * 50)
        print(" Seed complete! Login credentials:")
        print("=" * 50)
        print(f"  Admin   →  {ADMIN['email']}  /  {ADMIN['password']}")
        print(f"  Student →  ankita.kapoor@campus.edu  /  Student@1234")
        print(f"\n  All students use password: Student@1234")
        print("=" * 50)


if __name__ == '__main__':
    run()