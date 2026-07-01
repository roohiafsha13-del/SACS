"""
forms.py — WTForms Form Definitions
Smart Campus Attendance System
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField,
    BooleanField, HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo,
    Optional, ValidationError
)
from models import User


# ============================================================
# LOGIN FORM
# ============================================================
class LoginForm(FlaskForm):
    email    = StringField('Email',    validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    remember = BooleanField('Remember me')
    submit   = SubmitField('Sign In')


# ============================================================
# ADD / EDIT STUDENT FORM  (Admin)
# ============================================================
class StudentForm(FlaskForm):
    name       = StringField('Full Name',   validators=[DataRequired(), Length(max=120)])
    email      = StringField('Email',       validators=[DataRequired(), Email(), Length(max=150)])
    student_id = StringField('Student ID',  validators=[DataRequired(), Length(max=20)])
    batch      = SelectField('Batch',       choices=[('CS-A','CS-A'),('CS-B','CS-B'),('CS-C','CS-C')],
                             validators=[DataRequired()])
    password   = PasswordField('Password',  validators=[Optional(), Length(min=6)])
    submit     = SubmitField('Save Student')

    def __init__(self, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, field):
        # Allow same email on edit
        if field.data != self.original_email:
            if User.query.filter_by(email=field.data).first():
                raise ValidationError('Email already registered.')

    def validate_student_id(self, field):
        existing = User.query.filter_by(student_id=field.data).first()
        if existing:
            raise ValidationError('Student ID already in use.')


# ============================================================
# CHANGE PASSWORD FORM  (Student self-service)
# ============================================================
class ChangePasswordForm(FlaskForm):
    current_password  = PasswordField('Current Password',  validators=[DataRequired()])
    new_password      = PasswordField('New Password',       validators=[DataRequired(), Length(min=6)])
    confirm_password  = PasswordField('Confirm Password',   validators=[
                            DataRequired(), EqualTo('new_password', message='Passwords must match')
                        ])
    submit = SubmitField('Update Password')


# ============================================================
# ATTENDANCE MARK FORM  (GPS coords posted from JS)
# ============================================================
class MarkAttendanceForm(FlaskForm):
    latitude   = HiddenField('Latitude',  validators=[DataRequired()])
    longitude  = HiddenField('Longitude', validators=[DataRequired()])
    accuracy   = HiddenField('Accuracy',  validators=[Optional()])
    action     = HiddenField('Action',    validators=[DataRequired()])  # 'checkin' | 'checkout'
    submit     = SubmitField('Mark')


# ============================================================
# REPORT FILTER FORM  (Admin)
# ============================================================
class ReportFilterForm(FlaskForm):
    date_from   = StringField('From Date', validators=[Optional()])
    date_to     = StringField('To Date',   validators=[Optional()])
    batch       = SelectField('Batch', choices=[
                    ('all','All Batches'), ('IT-A','IT-A'), ('IT-B','IT-B')
                  ], validators=[Optional()])
    report_type = SelectField('Report Type', choices=[
                    ('summary',  'Attendance Summary'),
                    ('entryexit','Entry-Exit Report'),
                    ('absentee', 'Absentee Report'),
                  ])
    submit = SubmitField('Generate')