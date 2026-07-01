# Smart Campus Attendance System (SCAS)

A web-based attendance management system with GPS geo-validation and entry-exit monitoring, built with **Python Flask** and **SQLite/MySQL**.

---

## Project Structure

```
scas/
├── app.py                  # Main Flask app — all routes
├── config.py               # Configuration (dev / prod / test)
├── models.py               # SQLAlchemy models (User, Attendance, Location)
├── forms.py                # WTForms form definitions
├── geo_validation.py       # Haversine GPS boundary engine
├── seed.py                 # Database seeder (demo data)
├── wsgi.py                 # Production WSGI entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore
├── README.md
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
└── templates/
    ├── base.html
    ├── login.html
    ├── errors/
    │   ├── 403.html
    │   ├── 404.html
    │   └── 500.html
    ├── student/
    │   ├── dashboard.html
    │   ├── mark_attendance.html
    │   ├── history.html
    │   └── entry_exit.html
    └── admin/
        ├── dashboard.html
        ├── students.html
        ├── student_edit.html
        ├── attendance.html
        ├── reports.html
        └── entry_exit.html
```

---

## Quick Start

### 1. Clone / download the project

```bash
git clone https://github.com/yourname/scas.git
cd scas
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:
- `SECRET_KEY` — a long random string
- `CAMPUS_LAT` / `CAMPUS_LON` — your campus GPS centre
- `CAMPUS_RADIUS_METRES` — allowed radius (default 500m)

### 5. Seed the database

```bash
python seed.py
```

This creates all tables and populates 10 demo students + 30 days of attendance data.

### 6. Run the development server

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Login Credentials (after seeding)

| Role    | Email                      | Password      |
|---------|----------------------------|---------------|
| Admin   | admin@campus.edu           | Admin@1234    |
| Student | alex.kumar@campus.edu      | Student@1234  |
| Student | priya.reddy@campus.edu     | Student@1234  |

All 10 demo students share the password `Student@1234`.

---

## Environment Variables

| Variable                | Default              | Description                        |
|-------------------------|----------------------|------------------------------------|
| `SECRET_KEY`            | *(required)*         | Flask session secret key           |
| `DATABASE_URL`          | `sqlite:///scas.db`  | Database connection string         |
| `CAMPUS_LAT`            | `17.4492`            | Campus centre latitude             |
| `CAMPUS_LON`            | `78.3915`            | Campus centre longitude            |
| `CAMPUS_RADIUS_METRES`  | `500`                | GPS boundary radius in metres      |
| `FLASK_ENV`             | `development`        | `development` or `production`      |
| `ADMIN_EMAIL`           | `admin@campus.edu`   | Admin account email (seed only)    |
| `ADMIN_PASSWORD`        | `Admin@1234`         | Admin account password (seed only) |

---

## API Endpoints

| Method | Route                         | Auth     | Description                  |
|--------|-------------------------------|----------|------------------------------|
| GET    | `/`                           | Any      | Redirect to dashboard/login  |
| GET    | `/login`                      | Public   | Login page                   |
| POST   | `/login`                      | Public   | Authenticate user            |
| POST   | `/logout`                     | Required | Sign out + auto check-out    |
| GET    | `/dashboard`                  | Student  | Student home dashboard       |
| GET    | `/mark-attendance`            | Student  | GPS mark attendance page     |
| POST   | `/api/mark`                   | Student  | GPS validate + write DB      |
| GET    | `/history`                    | Student  | Personal attendance history  |
| GET    | `/entry-exit`                 | Student  | Entry/exit log               |
| GET    | `/admin`                      | Admin    | Admin dashboard              |
| GET    | `/admin/students`             | Admin    | Student management           |
| POST   | `/admin/students`             | Admin    | Add new student              |
| GET    | `/admin/students/<id>/edit`   | Admin    | Edit student form            |
| POST   | `/admin/students/<id>/edit`   | Admin    | Save student edit            |
| POST   | `/admin/students/<id>/delete` | Admin    | Delete student               |
| GET    | `/admin/attendance`           | Admin    | Attendance monitor           |
| GET    | `/admin/reports`              | Admin    | Generate reports             |
| GET    | `/admin/entry-exit`           | Admin    | Entry-exit logs              |
| GET    | `/admin/api/export-csv`       | Admin    | Download CSV report          |

---

## MySQL Setup (Production)

1. Create a database:
```sql
CREATE DATABASE scas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'scas_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON scas_db.* TO 'scas_user'@'localhost';
FLUSH PRIVILEGES;
```

2. Install MySQL driver:
```bash
pip install PyMySQL
```

3. Update `.env`:
```
DATABASE_URL=mysql+pymysql://scas_user:your_password@localhost:3306/scas_db
```

4. Re-run seeder:
```bash
python seed.py
```

---

## Production Deployment (Gunicorn)

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:application
```

---

## Security Notes

- All passwords are hashed with **bcrypt** (never stored as plain text)
- CSRF tokens on every form via **Flask-WTF**
- GPS validation is **server-side only** — cannot be bypassed from browser
- Role-based access control on all admin routes
- Session cookies are `HttpOnly` and `SameSite=Lax`
- Set `SESSION_COOKIE_SECURE=True` in production (requires HTTPS)

---

## Tech Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python 3.x, Flask 3.x             |
| Database | SQLite (dev) / MySQL (prod)       |
| ORM      | SQLAlchemy + Flask-SQLAlchemy     |
| Auth     | Flask-Login + Flask-Bcrypt        |
| Forms    | Flask-WTF + WTForms               |
| GPS      | HTML5 Geolocation API + Haversine |
| Frontend | HTML5, CSS3, Vanilla JavaScript   |
