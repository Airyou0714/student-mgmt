from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import (
    Attendance,
    Course,
    Enrollment,
    Grade,
    SchoolClass,
    Student,
    User,
)

main_bp = Blueprint("main", __name__)


def _parse_float(val: str | None, default: float | None = None) -> float | None:
    if val is None or str(val).strip() == "":
        return default
    try:
        return float(str(val).strip())
    except ValueError:
        return default


def _parse_date(val: str | None) -> date | None:
    if not val or not str(val).strip():
        return None
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _enrollment_exists(student_id: int, course_id: int) -> bool:
    return (
        Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        is not None
    )


# --- 认证 ---


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_url = request.args.get("next")
            if next_url:
                return redirect(next_url)
            return redirect(url_for("main.dashboard"))
        flash("用户名或密码错误。", "danger")

    return render_template("login.html")


@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录。", "info")
    return redirect(url_for("main.login"))


# --- 概览 ---


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    ctx = {
        "total_students": Student.query.count(),
        "total_classes": SchoolClass.query.count(),
        "total_courses": Course.query.count(),
        "total_grades": Grade.query.count(),
        "today_attendance": Attendance.query.filter(
            Attendance.attend_date == today
        ).count(),
    }
    return render_template("dashboard.html", **ctx)


# --- 班级 ---


@main_bp.route("/classes")
@login_required
def classes_list():
    rows = SchoolClass.query.order_by(SchoolClass.grade, SchoolClass.name).all()
    return render_template("classes_list.html", classes=rows)


@main_bp.route("/classes/new", methods=["GET", "POST"])
@login_required
def classes_new():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("班级名称为必填项。", "warning")
            return render_template("class_form.html", cls=None)
        c = SchoolClass(
            name=name,
            code=(request.form.get("code") or "").strip(),
            grade=(request.form.get("grade") or "").strip(),
            head_teacher=(request.form.get("head_teacher") or "").strip(),
            remark=(request.form.get("remark") or "").strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash("班级已创建。", "success")
        return redirect(url_for("main.classes_list"))

    return render_template("class_form.html", cls=None)


@main_bp.route("/classes/<int:cid>/edit", methods=["GET", "POST"])
@login_required
def classes_edit(cid: int):
    c = SchoolClass.query.get_or_404(cid)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("班级名称为必填项。", "warning")
            return render_template("class_form.html", cls=c)
        c.name = name
        c.code = (request.form.get("code") or "").strip()
        c.grade = (request.form.get("grade") or "").strip()
        c.head_teacher = (request.form.get("head_teacher") or "").strip()
        c.remark = (request.form.get("remark") or "").strip()
        db.session.commit()
        flash("已保存。", "success")
        return redirect(url_for("main.classes_list"))

    return render_template("class_form.html", cls=c)


@main_bp.route("/classes/<int:cid>/delete", methods=["POST"])
@login_required
def classes_delete(cid: int):
    c = SchoolClass.query.get_or_404(cid)
    if c.students:
        flash("该班级下仍有学生，请先为学生更换班级后再删除。", "warning")
        return redirect(url_for("main.classes_list"))
    db.session.delete(c)
    db.session.commit()
    flash("班级已删除。", "info")
    return redirect(url_for("main.classes_list"))


# --- 课程 ---


@main_bp.route("/courses")
@login_required
def courses_list():
    rows = Course.query.order_by(Course.name).all()
    return render_template("courses_list.html", courses=rows)


@main_bp.route("/courses/new", methods=["GET", "POST"])
@login_required
def courses_new():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("课程名称为必填项。", "warning")
            return render_template("course_form.html", course=None)
        cr = Course(
            name=name,
            code=(request.form.get("code") or "").strip(),
            credits=float(_parse_float(request.form.get("credits"), 0) or 0),
            teacher_name=(request.form.get("teacher_name") or "").strip(),
            remark=(request.form.get("remark") or "").strip(),
        )
        db.session.add(cr)
        db.session.commit()
        flash("课程已创建。", "success")
        return redirect(url_for("main.courses_list"))

    return render_template("course_form.html", course=None)


@main_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def courses_edit(course_id: int):
    cr = Course.query.get_or_404(course_id)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("课程名称为必填项。", "warning")
            return render_template("course_form.html", course=cr)
        cr.name = name
        cr.code = (request.form.get("code") or "").strip()
        cr.credits = float(_parse_float(request.form.get("credits"), 0) or 0)
        cr.teacher_name = (request.form.get("teacher_name") or "").strip()
        cr.remark = (request.form.get("remark") or "").strip()
        db.session.commit()
        flash("已保存。", "success")
        return redirect(url_for("main.courses_list"))

    return render_template("course_form.html", course=cr)


@main_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def courses_delete(course_id: int):
    cr = Course.query.get_or_404(course_id)
    db.session.delete(cr)
    db.session.commit()
    flash("课程已删除（关联选课、成绩、考勤已一并清理）。", "info")
    return redirect(url_for("main.courses_list"))


# --- 选课 ---


@main_bp.route("/courses/<int:course_id>/enrollments", methods=["GET", "POST"])
@login_required
def course_enrollments(course_id: int):
    cr = (
        Course.query.options(
            joinedload(Course.enrollments)
            .joinedload(Enrollment.student)
            .joinedload(Student.school_class)
        )
        .filter_by(id=course_id)
        .first_or_404()
    )
    if request.method == "POST":
        sid_raw = request.form.get("student_id")
        try:
            sid = int(sid_raw)
        except (TypeError, ValueError):
            flash("请选择学生。", "warning")
            return redirect(url_for("main.course_enrollments", course_id=course_id))
        if not _enrollment_exists(sid, course_id):
            db.session.add(Enrollment(student_id=sid, course_id=course_id))
            db.session.commit()
            flash("已添加选课。", "success")
        else:
            flash("该学生已在课程中。", "info")
        return redirect(url_for("main.course_enrollments", course_id=course_id))

    enrolled_ids = {e.student_id for e in cr.enrollments}
    students = (
        Student.query.options(joinedload(Student.school_class))
        .order_by(Student.student_no)
        .all()
    )
    available = [s for s in students if s.id not in enrolled_ids]
    return render_template(
        "course_enrollments.html",
        course=cr,
        enrollments=cr.enrollments,
        available_students=available,
    )


@main_bp.route("/enrollments/<int:eid>/delete", methods=["POST"])
@login_required
def enrollment_delete(eid: int):
    e = Enrollment.query.get_or_404(eid)
    cid, sid = e.course_id, e.student_id
    Grade.query.filter_by(student_id=sid, course_id=cid).delete()
    Attendance.query.filter_by(student_id=sid, course_id=cid).delete()
    db.session.delete(e)
    db.session.commit()
    flash("已退选并清除该课程下的成绩与考勤记录。", "info")
    return redirect(url_for("main.course_enrollments", course_id=cid))


# --- 学生 ---


@main_bp.route("/students")
@login_required
def student_list():
    q = (request.args.get("q") or "").strip()
    query = Student.query.options(joinedload(Student.school_class)).order_by(
        Student.created_at.desc()
    )
    if q:
        like = f"%{q}%"
        query = query.outerjoin(SchoolClass).filter(
            or_(
                Student.name.like(like),
                Student.student_no.like(like),
                SchoolClass.name.like(like),
            )
        )
    students = query.all()
    return render_template("students_list.html", students=students, q=q)


@main_bp.route("/students/new", methods=["GET", "POST"])
@login_required
def student_new():
    classes = SchoolClass.query.order_by(SchoolClass.name).all()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        student_no = (request.form.get("student_no") or "").strip()
        if not name or not student_no:
            flash("姓名和学号为必填项。", "warning")
            return render_template(
                "student_form.html", student=None, classes=classes
            )

        if Student.query.filter_by(student_no=student_no).first():
            flash("学号已存在，请更换。", "danger")
            return render_template(
                "student_form.html", student=None, classes=classes
            )

        class_id = request.form.get("class_id")
        cid = int(class_id) if class_id else None
        if cid and SchoolClass.query.get(cid) is None:
            cid = None

        s = Student(
            name=name,
            student_no=student_no,
            gender=(request.form.get("gender") or "").strip(),
            phone=(request.form.get("phone") or "").strip(),
            email=(request.form.get("email") or "").strip(),
            class_id=cid,
            remark=(request.form.get("remark") or "").strip(),
        )
        db.session.add(s)
        db.session.commit()
        flash("学生已添加。", "success")
        return redirect(url_for("main.student_list"))

    return render_template("student_form.html", student=None, classes=classes)


@main_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def student_edit(student_id: int):
    s = Student.query.get_or_404(student_id)
    classes = SchoolClass.query.order_by(SchoolClass.name).all()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        student_no = (request.form.get("student_no") or "").strip()
        if not name or not student_no:
            flash("姓名和学号为必填项。", "warning")
            return render_template("student_form.html", student=s, classes=classes)

        other = Student.query.filter(
            Student.student_no == student_no, Student.id != s.id
        ).first()
        if other:
            flash("学号已被其他学生使用。", "danger")
            return render_template("student_form.html", student=s, classes=classes)

        class_id = request.form.get("class_id")
        cid = int(class_id) if class_id else None
        if cid and SchoolClass.query.get(cid) is None:
            cid = None

        s.name = name
        s.student_no = student_no
        s.gender = (request.form.get("gender") or "").strip()
        s.phone = (request.form.get("phone") or "").strip()
        s.email = (request.form.get("email") or "").strip()
        s.class_id = cid
        s.remark = (request.form.get("remark") or "").strip()
        db.session.commit()
        flash("已保存修改。", "success")
        return redirect(url_for("main.student_list"))

    return render_template("student_form.html", student=s, classes=classes)


@main_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def student_delete(student_id: int):
    s = Student.query.get_or_404(student_id)
    db.session.delete(s)
    db.session.commit()
    flash("已删除该学生。", "info")
    return redirect(url_for("main.student_list"))


# --- 成绩 ---


@main_bp.route("/grades")
@login_required
def grades_list():
    course_id = request.args.get("course_id", type=int)
    class_id = request.args.get("class_id", type=int)
    q = (request.args.get("q") or "").strip()

    query = (
        Grade.query.options(
            joinedload(Grade.student).joinedload(Student.school_class),
            joinedload(Grade.course),
        )
        .join(Student, Grade.student_id == Student.id)
        .join(Course, Grade.course_id == Course.id)
        .order_by(Grade.created_at.desc())
    )

    if course_id:
        query = query.filter(Grade.course_id == course_id)
    if class_id:
        query = query.filter(Student.class_id == class_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Student.name.like(like),
                Student.student_no.like(like),
                Course.name.like(like),
                Grade.title.like(like),
            )
        )

    grades = query.limit(500).all()
    courses = Course.query.order_by(Course.name).all()
    classes = SchoolClass.query.order_by(SchoolClass.name).all()
    return render_template(
        "grades_list.html",
        grades=grades,
        courses=courses,
        classes=classes,
        filter_course_id=course_id,
        filter_class_id=class_id,
        q=q,
    )


@main_bp.route("/grades/new", methods=["GET", "POST"])
@login_required
def grades_new():
    students = Student.query.order_by(Student.student_no).all()
    courses = Course.query.order_by(Course.name).all()
    if request.method == "POST":
        try:
            sid = int(request.form.get("student_id"))
            cid = int(request.form.get("course_id"))
        except (TypeError, ValueError):
            flash("请选择学生和课程。", "warning")
            return render_template(
                "grade_form.html",
                grade=None,
                students=students,
                courses=courses,
            )

        if not _enrollment_exists(sid, cid):
            flash("该学生未选此课程，请先在课程中完成选课。", "warning")
            return render_template(
                "grade_form.html",
                grade=None,
                students=students,
                courses=courses,
            )

        title = (request.form.get("title") or "").strip()
        if not title:
            flash("成绩项名称不能为空（如：期中、期末）。", "warning")
            return render_template(
                "grade_form.html",
                grade=None,
                students=students,
                courses=courses,
            )

        score = _parse_float(request.form.get("score"))
        max_score = _parse_float(request.form.get("max_score"), 100.0)
        if score is None:
            flash("请输入有效分数。", "warning")
            return render_template(
                "grade_form.html",
                grade=None,
                students=students,
                courses=courses,
            )
        max_score = max_score if max_score and max_score > 0 else 100.0

        if Grade.query.filter_by(
            student_id=sid, course_id=cid, title=title
        ).first():
            flash("该成绩项已存在，请更换名称或编辑已有记录。", "danger")
            return render_template(
                "grade_form.html",
                grade=None,
                students=students,
                courses=courses,
            )

        g = Grade(
            student_id=sid,
            course_id=cid,
            title=title,
            score=score,
            max_score=max_score,
        )
        db.session.add(g)
        db.session.commit()
        flash("成绩已录入。", "success")
        return redirect(url_for("main.grades_list"))

    return render_template(
        "grade_form.html",
        grade=None,
        students=students,
        courses=courses,
    )


@main_bp.route("/grades/<int:gid>/edit", methods=["GET", "POST"])
@login_required
def grades_edit(gid: int):
    g = Grade.query.get_or_404(gid)
    students = Student.query.order_by(Student.student_no).all()
    courses = Course.query.order_by(Course.name).all()
    if request.method == "POST":
        try:
            sid = int(request.form.get("student_id"))
            cid = int(request.form.get("course_id"))
        except (TypeError, ValueError):
            flash("请选择学生和课程。", "warning")
            return render_template(
                "grade_form.html", grade=g, students=students, courses=courses
            )

        if not _enrollment_exists(sid, cid):
            flash("该学生未选此课程。", "warning")
            return render_template(
                "grade_form.html", grade=g, students=students, courses=courses
            )

        title = (request.form.get("title") or "").strip()
        if not title:
            flash("成绩项名称不能为空。", "warning")
            return render_template(
                "grade_form.html", grade=g, students=students, courses=courses
            )

        score = _parse_float(request.form.get("score"))
        max_score = _parse_float(request.form.get("max_score"), 100.0)
        if score is None:
            flash("请输入有效分数。", "warning")
            return render_template(
                "grade_form.html", grade=g, students=students, courses=courses
            )
        max_score = max_score if max_score and max_score > 0 else 100.0

        dup = Grade.query.filter(
            Grade.student_id == sid,
            Grade.course_id == cid,
            Grade.title == title,
            Grade.id != g.id,
        ).first()
        if dup:
            flash("同一课程下成绩项名称重复。", "danger")
            return render_template(
                "grade_form.html", grade=g, students=students, courses=courses
            )

        g.student_id = sid
        g.course_id = cid
        g.title = title
        g.score = score
        g.max_score = max_score
        db.session.commit()
        flash("已保存。", "success")
        return redirect(url_for("main.grades_list"))

    return render_template(
        "grade_form.html", grade=g, students=students, courses=courses
    )


@main_bp.route("/grades/<int:gid>/delete", methods=["POST"])
@login_required
def grades_delete(gid: int):
    g = Grade.query.get_or_404(gid)
    db.session.delete(g)
    db.session.commit()
    flash("成绩已删除。", "info")
    return redirect(url_for("main.grades_list"))


# --- 考勤 ---


@main_bp.route("/attendance")
@login_required
def attendance_list():
    course_id = request.args.get("course_id", type=int)
    d_from = _parse_date(request.args.get("from"))
    d_to = _parse_date(request.args.get("to"))

    query = Attendance.query.options(
        joinedload(Attendance.student).joinedload(Student.school_class),
        joinedload(Attendance.course),
    ).order_by(Attendance.attend_date.desc(), Attendance.id.desc())

    if course_id:
        query = query.filter(Attendance.course_id == course_id)
    if d_from:
        query = query.filter(Attendance.attend_date >= d_from)
    if d_to:
        query = query.filter(Attendance.attend_date <= d_to)

    rows = query.limit(800).all()
    courses = Course.query.order_by(Course.name).all()
    return render_template(
        "attendance_list.html",
        rows=rows,
        courses=courses,
        filter_course_id=course_id,
        date_from=d_from.isoformat() if d_from else "",
        date_to=d_to.isoformat() if d_to else "",
    )


@main_bp.route("/attendance/<int:aid>/edit", methods=["GET", "POST"])
@login_required
def attendance_edit(aid: int):
    row = Attendance.query.get_or_404(aid)
    students = Student.query.order_by(Student.student_no).all()
    courses = Course.query.order_by(Course.name).all()
    today_iso = date.today().isoformat()
    if request.method == "POST":
        try:
            sid = int(request.form.get("student_id"))
            cid = int(request.form.get("course_id"))
        except (TypeError, ValueError):
            flash("请选择学生和课程。", "warning")
            return render_template(
                "attendance_form.html",
                row=row,
                students=students,
                courses=courses,
                today_iso=today_iso,
            )

        if not _enrollment_exists(sid, cid):
            flash("该学生未选此课程。", "warning")
            return render_template(
                "attendance_form.html",
                row=row,
                students=students,
                courses=courses,
                today_iso=today_iso,
            )

        ad = _parse_date(request.form.get("attend_date"))
        if not ad:
            flash("请选择有效日期。", "warning")
            return render_template(
                "attendance_form.html",
                row=row,
                students=students,
                courses=courses,
                today_iso=today_iso,
            )

        dup = Attendance.query.filter(
            Attendance.student_id == sid,
            Attendance.course_id == cid,
            Attendance.attend_date == ad,
            Attendance.id != row.id,
        ).first()
        if dup:
            flash("该学生在此日期的考勤记录已存在。", "danger")
            return render_template(
                "attendance_form.html",
                row=row,
                students=students,
                courses=courses,
                today_iso=today_iso,
            )

        row.student_id = sid
        row.course_id = cid
        row.attend_date = ad
        row.status = (request.form.get("status") or "出勤").strip()
        row.note = (request.form.get("note") or "").strip()
        db.session.commit()
        flash("考勤已更新。", "success")
        return redirect(url_for("main.attendance_list"))

    return render_template(
        "attendance_form.html",
        row=row,
        students=students,
        courses=courses,
        today_iso=today_iso,
    )


@main_bp.route("/attendance/new", methods=["GET", "POST"])
@login_required
def attendance_new():
    students = Student.query.order_by(Student.student_no).all()
    courses = Course.query.order_by(Course.name).all()
    today_iso = date.today().isoformat()
    if request.method == "POST":
        try:
            sid = int(request.form.get("student_id"))
            cid = int(request.form.get("course_id"))
        except (TypeError, ValueError):
            flash("请选择学生和课程。", "warning")
            return render_template(
                "attendance_form.html",
                row=None,
                students=students,
                courses=courses,
                today_iso=today_iso,
            )

        if not _enrollment_exists(sid, cid):
            flash("该学生未选此课程。", "warning")
            return render_template(
                "attendance_form.html",
                row=None,
                students=students,
                courses=courses,
                today_iso=today_iso,
            )

        ad = _parse_date(request.form.get("attend_date"))
        if not ad:
            flash("请选择有效日期。", "warning")
            return render_template(
                "attendance_form.html",
                row=None,
                students=students,
                courses=courses,
                today_iso=today_iso,
            )

        status = (request.form.get("status") or "出勤").strip()
        note = (request.form.get("note") or "").strip()

        ex = Attendance.query.filter_by(
            student_id=sid, course_id=cid, attend_date=ad
        ).first()
        if ex:
            ex.status = status
            ex.note = note
            db.session.commit()
            flash("已更新当日考勤记录。", "success")
            return redirect(url_for("main.attendance_list"))

        db.session.add(
            Attendance(
                student_id=sid,
                course_id=cid,
                attend_date=ad,
                status=status,
                note=note,
            )
        )
        db.session.commit()
        flash("考勤已记录。", "success")
        return redirect(url_for("main.attendance_list"))

    return render_template(
        "attendance_form.html",
        row=None,
        students=students,
        courses=courses,
        today_iso=today_iso,
    )


@main_bp.route("/attendance/bulk", methods=["GET", "POST"])
@login_required
def attendance_bulk():
    courses = Course.query.order_by(Course.name).all()
    if request.method == "POST":
        try:
            cid = int(request.form.get("course_id"))
        except (TypeError, ValueError):
            flash("请选择课程。", "warning")
            return render_template(
                "attendance_bulk.html",
                course=None,
                enrollments=[],
                attend_date=date.today().isoformat(),
                courses=courses,
                status_map={},
            )

        cr = Course.query.get(cid)
        if not cr:
            flash("课程不存在。", "danger")
            return redirect(url_for("main.attendance_bulk"))

        ad = _parse_date(request.form.get("attend_date"))
        if not ad:
            flash("请选择有效日期。", "warning")
            return render_template(
                "attendance_bulk.html",
                course=cr,
                enrollments=cr.enrollments,
                attend_date=request.form.get("attend_date") or "",
                courses=courses,
                status_map={},
            )

        if not cr.enrollments:
            flash("该课程暂无选课学生。", "warning")
            return render_template(
                "attendance_bulk.html",
                course=cr,
                enrollments=[],
                attend_date=ad.isoformat(),
                courses=courses,
                status_map={},
            )

        for e in cr.enrollments:
            sid = e.student_id
            status = (request.form.get(f"status_{sid}") or "出勤").strip()
            note = (request.form.get(f"note_{sid}") or "").strip()
            row = Attendance.query.filter_by(
                student_id=sid, course_id=cid, attend_date=ad
            ).first()
            if row:
                row.status = status
                row.note = note
            else:
                db.session.add(
                    Attendance(
                        student_id=sid,
                        course_id=cid,
                        attend_date=ad,
                        status=status,
                        note=note,
                    )
                )
        db.session.commit()
        flash("批量考勤已保存。", "success")
        return redirect(
            url_for(
                "main.attendance_bulk",
                course_id=cid,
                attend_date=ad.isoformat(),
            )
        )

    course_id = request.args.get("course_id", type=int)
    attend_date_s = request.args.get("attend_date") or date.today().isoformat()
    ad = _parse_date(attend_date_s) or date.today()

    course = None
    enrollments = []
    status_map = {}
    if course_id:
        course = (
            Course.query.options(
                joinedload(Course.enrollments)
                .joinedload(Enrollment.student)
                .joinedload(Student.school_class)
            )
            .filter_by(id=course_id)
            .first()
        )
        if course:
            enrollments = list(course.enrollments)
            for e in enrollments:
                status_map[e.student_id] = Attendance.query.filter_by(
                    student_id=e.student_id,
                    course_id=course.id,
                    attend_date=ad,
                ).first()

    return render_template(
        "attendance_bulk.html",
        course=course,
        enrollments=enrollments,
        attend_date=ad.isoformat(),
        courses=courses,
        status_map=status_map,
    )


@main_bp.route("/attendance/<int:aid>/delete", methods=["POST"])
@login_required
def attendance_delete(aid: int):
    row = Attendance.query.get_or_404(aid)
    db.session.delete(row)
    db.session.commit()
    flash("考勤记录已删除。", "info")
    return redirect(url_for("main.attendance_list"))
