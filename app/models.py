from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Date, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class SchoolClass(db.Model):
    """班级"""

    __tablename__ = "school_classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(32), default="")
    grade = db.Column(db.String(32), default="")
    head_teacher = db.Column(db.String(64), default="")
    remark = db.Column(db.String(256), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    students = db.relationship("Student", back_populates="school_class")


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    student_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    gender = db.Column(db.String(8), default="")
    phone = db.Column(db.String(20), default="")
    email = db.Column(db.String(120), default="")
    class_id = db.Column(db.Integer, db.ForeignKey("school_classes.id"), nullable=True)
    remark = db.Column(db.String(256), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    school_class = db.relationship("SchoolClass", back_populates="students")
    enrollments = db.relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    grades = db.relationship(
        "Grade", back_populates="student", cascade="all, delete-orphan"
    )
    attendances = db.relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )


class Course(db.Model):
    """课程"""

    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(32), default="")
    credits = db.Column(db.Float, default=0.0)
    teacher_name = db.Column(db.String(64), default="")
    remark = db.Column(db.String(256), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    grades = db.relationship(
        "Grade", back_populates="course", cascade="all, delete-orphan"
    )
    attendances = db.relationship(
        "Attendance", back_populates="course", cascade="all, delete-orphan"
    )


class Enrollment(db.Model):
    """选课：学生与课程"""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")


class Grade(db.Model):
    """成绩"""

    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "title", name="uq_grade_title"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, default=100.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", back_populates="grades")
    course = db.relationship("Course", back_populates="grades")


class Attendance(db.Model):
    """考勤"""

    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "attend_date", name="uq_attendance_day"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    attend_date = db.Column(Date, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="出勤")
    note = db.Column(db.String(128), default="")

    student = db.relationship("Student", back_populates="attendances")
    course = db.relationship("Course", back_populates="attendances")
