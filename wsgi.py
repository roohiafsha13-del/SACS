"""
wsgi.py — Production WSGI Entry Point
Smart Campus Attendance System

Usage with Gunicorn:
    gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:application

Usage with uWSGI:
    uwsgi --http 0.0.0.0:5000 --module wsgi:application --processes 4
"""

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()