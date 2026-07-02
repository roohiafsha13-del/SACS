"""
app.py — Main Flask Application
Smart Campus Attendance System

Routes:
  /                        → redirect to login or dashboard
  /login                   → login page (student + admin)
  /logout                  → logout

  Student:
  /dashboard               → student home
  /mark-attendance         → GPS mark page
  /api/mark                → POST  — receive GPS, validate, write DB
  /history                 → personal attendance history

  Admin:
  /admin                   → admin dashboard
  /admin/students          → list + add students
  /admin/students/<id>/edit   → edit student
  /admin/students/<id>/delete → delete student
  /admin/attendance        → attendance monitor
  /admin/reports           → generate reports
  /admin/entry-exit        → entry-exit logs
  /admin/api/export-csv    → CSV export
"""

import csv
import io
from datetime import datetime, date

from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, jsonify, Response, abort,
    send_from_directory
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect

from config import get_config
from models import db, bcrypt, User, Attendance, Location
from forms import (
    LoginForm, StudentForm, MarkAttendanceForm,
    ReportFilterForm, ChangePasswordForm
)
from geo_validation import validate_campus_location, parse_coords


# ============================================================
# APPLICATION FACTORY
# ============================================================
def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints / routes
    register_routes(app)

    # Create tables on first run
    with app.app_context():
        db.create_all()

    return app


# ── Flask-Login setup ─────────────────────────────────────────
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view       = 'login_page'
login_manager.login_message    = 'Please sign in to continue.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


# ============================================================
# HELPERS
# ============================================================
def admin_required(f):
    """Decorator — redirect non-admins to student dashboard."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def get_today_stats():
    """Return (present_count, absent_count, total_students) for today."""
    total   = User.query.filter_by(role='student', is_active=True).count()
    present = Attendance.query.filter_by(date=date.today(), status='Present').count()
    absent  = total - present
    return present, absent, total


# ============================================================
# REGISTER ALL ROUTES
# ============================================================
def register_routes(app: Flask):

    @app.context_processor
    def inject_globals():
        """Inject commonly needed variables into every template."""
        return {
            'now':        datetime.utcnow(),
            'today_date': date.today(),
        }

    # ── PWA Routes ───────────────────────────────────────────
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory('static', 'manifest.json',
                                   mimetype='application/manifest+json')

    @app.route('/service-worker.js')
    def service_worker():
        response = send_from_directory('static', 'service-worker.js',
                                       mimetype='application/javascript')
        response.headers['Service-Worker-Allowed'] = '/'
        response.headers['Cache-Control'] = 'no-cache'
        return response

    # ── Root ──────────────────────────────────────────────────
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        return redirect(url_for('login_page'))


    # ── Login ─────────────────────────────────────────────────
    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = LoginForm()

        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.strip().lower()).first()

            if user and user.check_password(form.password.data) and user.is_active:
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.name.split()[0]}!', 'success')
                return redirect(next_page or url_for('index'))

            flash('Invalid email or password.', 'danger')

        return render_template('login.html', form=form)


    # ── Logout ────────────────────────────────────────────────
    @app.route('/logout', methods=['POST'])
    @login_required
    def logout():
        # Auto check-out if still checked in
        record = current_user.todays_record()
        if record and record.login_time and not record.logout_time:
            record.logout_time = datetime.utcnow()
            db.session.commit()
        logout_user()
        flash('You have been signed out.', 'info')
        return redirect(url_for('login_page'))


    # ===========================================================
    # STUDENT ROUTES
    # ===========================================================

    @app.route('/dashboard')
    @login_required
    def student_dashboard():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))

        today_record  = current_user.todays_record()
        total_days    = Attendance.query.filter_by(user_id=current_user.id).count()
        present_days  = Attendance.query.filter_by(user_id=current_user.id, status='Present').count()
        absent_days   = total_days - present_days
        pct           = current_user.attendance_percentage()

        # Last 7 attendance records for trend
        recent = (Attendance.query
                  .filter_by(user_id=current_user.id)
                  .order_by(Attendance.date.desc())
                  .limit(7).all())

        return render_template('student/dashboard.html',
            today    = today_record,
            total    = total_days,
            present  = present_days,
            absent   = absent_days,
            pct      = pct,
            recent   = recent,
        )


    @app.route('/mark-attendance', methods=['GET'])
    @login_required
    def mark_attendance_page():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        form         = MarkAttendanceForm()
        today_record = current_user.todays_record()
        return render_template('student/mark_attendance.html',
            form=form, today=today_record)


    @app.route('/api/mark', methods=['POST'])
    @login_required
    def api_mark():
        """
        JSON endpoint called from the frontend after GPS capture.
        Body: { latitude, longitude, accuracy, action }
        Returns: { success, message, status }
        """
        if current_user.is_admin:
            return jsonify({'success': False, 'message': 'Admins cannot mark attendance.'}), 403

        data = request.get_json(silent=True) or {}

        # 1. Parse & validate coordinates
        coords = parse_coords(data.get('latitude'), data.get('longitude'))
        if not coords:
            return jsonify({'success': False, 'message': 'Invalid GPS coordinates.'}), 400

        lat, lon = coords
        accuracy = data.get('accuracy')
        action   = data.get('action', 'checkin')   # 'checkin' | 'checkout'

        # 2. Server-side GPS accuracy check (check-in only)
        # If the browser sends accuracy worse than 50m, reject the check-in.
        # Check-out is allowed regardless of accuracy since the student is already recorded.
        MAX_ACCURACY_METRES = 50
        if action == 'checkin' and accuracy is not None:
            try:
                acc_val = float(accuracy)
                if acc_val > MAX_ACCURACY_METRES:
                    return jsonify({
                        'success': False,
                        'message': (
                            f'GPS accuracy too low (\u00b1{acc_val:.0f}m). '
                            f'Required: \u00b1{MAX_ACCURACY_METRES}m or better. '
                            f'Move outdoors and retry.'
                        ),
                        'accuracy': acc_val,
                    }), 200
            except (TypeError, ValueError):
                pass   # If accuracy unparseable, proceed — geo-validation is still done

        # 3. Geo-validation
        result = validate_campus_location(lat, lon)

        # 3. Log GPS regardless of validation result
        loc_record = Location(
            user_id    = current_user.id,
            latitude   = lat,
            longitude  = lon,
            accuracy_m = float(accuracy) if accuracy else None,
            is_valid   = result.is_valid,
            event_type = action,
        )
        db.session.add(loc_record)

        if not result.is_valid:
            db.session.commit()
            return jsonify({
                'success': False,
                'message': result.message,
                'distance': result.distance_metres,
            }), 200

        # 4. Upsert today's attendance record
        today_rec = current_user.todays_record()
        now       = datetime.utcnow()

        if action == 'checkin':
            if today_rec and today_rec.login_time:
                db.session.commit()
                return jsonify({'success': False, 'message': 'Already checked in today.'}), 200

            if not today_rec:
                today_rec = Attendance(user_id=current_user.id, date=date.today())
                db.session.add(today_rec)

            today_rec.login_time = now
            today_rec.status     = 'Present'

        elif action == 'checkout':
            if not today_rec or not today_rec.login_time:
                db.session.commit()
                return jsonify({'success': False, 'message': 'No active check-in found.'}), 200

            if today_rec.logout_time:
                db.session.commit()
                return jsonify({'success': False, 'message': 'Already checked out today.'}), 200

            today_rec.logout_time = now

        db.session.commit()

        return jsonify({
            'success':  True,
            'message':  result.message,
            'action':   action,
            'time':     now.strftime('%I:%M %p'),
            'distance': result.distance_metres,
        })


    @app.route('/history')
    @login_required
    def student_history():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))

        page    = request.args.get('page', 1, type=int)
        records = (Attendance.query
                   .filter_by(user_id=current_user.id)
                   .order_by(Attendance.date.desc())
                   .paginate(page=page, per_page=20, error_out=False))

        return render_template('student/history.html', records=records)


    @app.route('/entry-exit')
    @login_required
    def student_entry_exit():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))

        records = (Attendance.query
                   .filter_by(user_id=current_user.id)
                   .order_by(Attendance.date.desc())
                   .limit(30).all())

        return render_template('student/entry_exit.html', records=records)


    # ===========================================================
    # ADMIN ROUTES
    # ===========================================================

    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        present, absent, total = get_today_stats()

        # On-campus right now = checked in but not checked out today
        on_campus = (Attendance.query
                     .filter_by(date=date.today(), status='Present')
                     .filter(Attendance.logout_time.is_(None))
                     .count())

        # Recent entries (last 10 check-ins today)
        recent_entries = (Attendance.query
                          .filter_by(date=date.today())
                          .filter(Attendance.login_time.isnot(None))
                          .order_by(Attendance.login_time.desc())
                          .limit(10).all())

        # Absentees today
        absent_users = (User.query
                        .filter_by(role='student', is_active=True)
                        .outerjoin(Attendance, (Attendance.user_id == User.id) &
                                   (Attendance.date == date.today()))
                        .filter(Attendance.id.is_(None))
                        .all())

        return render_template('admin/dashboard.html',
            present       = present,
            absent        = absent,
            total         = total,
            on_campus     = on_campus,
            recent_entries= recent_entries,
            absent_users  = absent_users,
        )


    @app.route('/admin/students', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_students():
        form   = StudentForm()
        search = request.args.get('q', '')
        batch  = request.args.get('batch', '')
        page   = request.args.get('page', 1, type=int)

        query = User.query.filter_by(role='student')
        if search:
            query = query.filter(
                User.name.ilike(f'%{search}%') |
                User.email.ilike(f'%{search}%') |
                User.student_id.ilike(f'%{search}%')
            )
        if batch:
            query = query.filter_by(batch=batch)

        students = query.order_by(User.name).paginate(page=page, per_page=25, error_out=False)

        if form.validate_on_submit():
            student = User(
                name       = form.name.data.strip(),
                email      = form.email.data.strip().lower(),
                student_id = form.student_id.data.strip().upper(),
                batch      = form.batch.data,
                role       = 'student',
            )
            student.set_password(form.password.data)
            db.session.add(student)
            db.session.commit()
            flash(f'Student {student.name} added successfully.', 'success')
            return redirect(url_for('admin_students'))

        return render_template('admin/students.html',
            students=students, form=form, search=search, batch=batch)


    @app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_student_edit(student_id):
        student = User.query.get_or_404(student_id)
        form    = StudentForm(original_email=student.email, obj=student)

        if form.validate_on_submit():
            student.name       = form.name.data.strip()
            student.email      = form.email.data.strip().lower()
            student.student_id = form.student_id.data.strip().upper()
            student.batch      = form.batch.data
            if form.password.data:
                student.set_password(form.password.data)
            db.session.commit()
            flash('Student updated successfully.', 'success')
            return redirect(url_for('admin_students'))

        return render_template('admin/student_edit.html', form=form, student=student)


    @app.route('/admin/students/<int:student_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_student_delete(student_id):
        student = User.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student.name} removed.', 'info')
        return redirect(url_for('admin_students'))


    @app.route('/admin/attendance')
    @login_required
    @admin_required
    def admin_attendance():
        selected_date = request.args.get('date', date.today().isoformat())
        try:
            sel_date = date.fromisoformat(selected_date)
        except ValueError:
            sel_date = date.today()

        # All students with their attendance for selected date
        students = (User.query
                    .filter_by(role='student', is_active=True)
                    .outerjoin(Attendance, (Attendance.user_id == User.id) &
                               (Attendance.date == sel_date))
                    .add_columns(Attendance.login_time, Attendance.logout_time,
                                 Attendance.status, Attendance.id.label('att_id'))
                    .order_by(User.name)
                    .all())

        present = sum(1 for r in students if r.status == 'Present')
        total   = len(students)

        return render_template('admin/attendance.html',
            students=students, sel_date=sel_date,
            present=present, total=total)


    @app.route('/admin/reports', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_reports():
        form = ReportFilterForm()
        rows = []

        if form.validate_on_submit() or request.method == 'GET':
            # Date range
            try:
                date_from = date.fromisoformat(form.date_from.data or date.today().replace(day=1).isoformat())
                date_to   = date.fromisoformat(form.date_to.data   or date.today().isoformat())
            except ValueError:
                date_from = date.today().replace(day=1)
                date_to   = date.today()

            # Working days in range (Mon–Fri only)
            working_days = sum(
                1 for i in range((date_to - date_from).days + 1)
                if (date_from.toordinal() + i) % 7 not in (5, 6)   # skip Sat, Sun
            )

            students = User.query.filter_by(role='student', is_active=True)
            if form.batch.data and form.batch.data != 'all':
                students = students.filter_by(batch=form.batch.data)

            for s in students.order_by(User.name).all():
                present_count = (Attendance.query
                                 .filter(Attendance.user_id == s.id,
                                         Attendance.status == 'Present',
                                         Attendance.date.between(date_from, date_to))
                                 .count())
                absent_count  = working_days - present_count
                pct           = round((present_count / working_days) * 100, 1) if working_days else 0

                rows.append({
                    'student':      s,
                    'working_days': working_days,
                    'present':      present_count,
                    'absent':       absent_count,
                    'pct':          pct,
                    'status':       'Good' if pct >= 75 else ('At Risk' if pct >= 60 else 'Critical'),
                })

        return render_template('admin/reports.html',
            form=form, rows=rows)


    @app.route('/admin/entry-exit')
    @login_required
    @admin_required
    def admin_entry_exit():
        selected_date = request.args.get('date', date.today().isoformat())
        try:
            sel_date = date.fromisoformat(selected_date)
        except ValueError:
            sel_date = date.today()

        records = (Attendance.query
                   .filter_by(date=sel_date)
                   .join(User)
                   .filter(User.role == 'student')
                   .order_by(Attendance.login_time)
                   .all())

        on_campus = sum(1 for r in records if r.login_time and not r.logout_time)

        return render_template('admin/entry_exit.html',
            records=records, sel_date=sel_date, on_campus=on_campus)


    @app.route('/admin/api/export-csv')
    @login_required
    @admin_required
    def export_csv():
        """Stream attendance data as a downloadable CSV."""
        date_from_str = request.args.get('from', date.today().replace(day=1).isoformat())
        date_to_str   = request.args.get('to',   date.today().isoformat())

        try:
            date_from = date.fromisoformat(date_from_str)
            date_to   = date.fromisoformat(date_to_str)
        except ValueError:
            date_from = date.today().replace(day=1)
            date_to   = date.today()

        students = User.query.filter_by(role='student', is_active=True).order_by(User.name).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Student ID', 'Email', 'Batch',
                         'Date', 'Check-In', 'Check-Out', 'Duration', 'Status'])

        for s in students:
            records = (Attendance.query
                       .filter(Attendance.user_id == s.id,
                               Attendance.date.between(date_from, date_to))
                       .order_by(Attendance.date)
                       .all())
            for r in records:
                writer.writerow([
                    s.name, s.student_id, s.email, s.batch,
                    r.date.isoformat(),
                    r.login_str, r.logout_str, r.duration_str, r.status
                ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=attendance_{date_from_str}_{date_to_str}.csv'}
        )


    # ── One-time DB seed route ───────────────────────────────
    # IMPORTANT: Delete this entire route after visiting it once!
    @app.route('/setup-scas-db-1a2b3c')
    def setup_db():
        try:
            db.create_all()
            if User.query.filter_by(role='admin').first():
                return '<h2>Already seeded! Delete this route from app.py now.</h2>', 200
            # Admin account
            admin = User(name='Dr. S. Sharma', email='admin@campus.edu', role='admin')
            admin.set_password('Admin@1234')
            db.session.add(admin)
            # Your actual students
            students_data = [
                ('Ankita Kapoor',  'IT2401', 'ankita.kapoor@campus.edu', 'IT-A'),
                ('Shifa Fatima',   'IT2402', 'shifa.fatima@campus.edu',  'IT-A'),
                ('Suresh Mehta',   'IT2403', 'suresh.m@campus.edu',      'IT-A'),
                ('Abdul Ahil',     'IT2404', 'ahil.a@campus.edu',        'IT-A'),
                ('Abdul Hassan',   'IT2405', 'hassan.a@campus.edu',      'IT-B'),
                ('Maya Singh',     'IT2406', 'maya.s@campus.edu',        'IT-B'),
                ('Riya Singh',     'IT2407', 'riya.s@campus.edu',        'IT-B'),
                ('Max Thomas',     'IT2408', 'max.t@campus.edu',         'IT-B'),
                ('Deepak Nair',    'IT2409', 'deepak.n@campus.edu',      'IT-A'),
                ('Kavitha Reddy',  'IT2410', 'kavitha.r@campus.edu',     'IT-B'),
            ]
            for name, sid, email, batch in students_data:
                s = User(name=name, student_id=sid, email=email,
                         batch=batch, role='student')
                s.set_password('Student@1234')
                db.session.add(s)
            db.session.commit()
            return '''<html><body style="font-family:sans-serif;padding:2rem;background:#0b0f1a;color:#e8ecf4">
                <h2 style="color:#22c55e">&#10003; Database seeded successfully!</h2>
                <p style="margin:.5rem 0">Admin &nbsp;&nbsp;: admin@campus.edu / Admin@1234</p>
                <p style="margin:.5rem 0">Students: ankita.kapoor@campus.edu / Student@1234</p>
                <p style="margin:.5rem 0">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                   shifa.fatima@campus.edu / Student@1234</p>
                <p style="margin:.5rem 0">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                   (all 10 students use Student@1234)</p>
                <p style="color:#f59e0b;margin-top:1.5rem"><strong>
                &#9888; NOW: Delete the /setup-scas-db-1a2b3c route from app.py,
                push to GitHub again, then login.</strong></p>
                <a href="/login" style="color:#3d7eff;font-size:1.1rem">&#8594; Go to Login</a>
                </body></html>''', 200
        except Exception as e:
            return f'<h2 style="color:red">Error: {str(e)}</h2>', 500

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500


# ============================================================
# ENTRY POINT
# ============================================================
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)