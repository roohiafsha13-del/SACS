from app import app
from models import db, User

with app.app_context():

    admin = User(
        name='Administrator',
        email='admin@campus.edu',
        role='admin'
    )

    admin.set_password('Admin@1234')

    db.session.add(admin)
    db.session.commit()

    print("Admin created")