"""Development-only seed data. Never run this against production."""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import *
from app.models.user import UserRole
from app.security.password import hash_password


DEV_PASSWORD = "DevPass123!"


def get_or_create_user(
    db,
    *,
    organization_id,
    email,
    full_name,
    role,
):
    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        user = User(
            organization_id=organization_id,
            email=email,
            full_name=full_name,
            password_hash=hash_password(DEV_PASSWORD),
            role=role,
            status=UserStatus.ACTIVE,
        )

        db.add(user)
        db.flush()

    else:
        user.organization_id = organization_id
        user.password_hash = hash_password(DEV_PASSWORD)
        user.role = role
        user.status = UserStatus.ACTIVE

    return user


def seed():
    db = SessionLocal()

    try:
        # ---------------------------------------------------------
        # ORGANIZATIONS
        # ---------------------------------------------------------

        org_a = db.scalar(
            select(Organization).where(
                Organization.slug == "dev-university-a"
            )
        )

        org_b = db.scalar(
            select(Organization).where(
                Organization.slug == "dev-college-b"
            )
        )

        if org_a is None:
            org_a = Organization(
                name="Development University A",
                slug="dev-university-a",
                organization_type=OrganizationType.UNIVERSITY,
                status=OrganizationStatus.ACTIVE,
            )

            db.add(org_a)
            db.flush()

            db.add(
                OrganizationSettings(
                    organization_id=org_a.id
                )
            )

            db.flush()

        if org_b is None:
            org_b = Organization(
                name="Development College B",
                slug="dev-college-b",
                organization_type=OrganizationType.COLLEGE,
                status=OrganizationStatus.ACTIVE,
            )

            db.add(org_b)
            db.flush()

            db.add(
                OrganizationSettings(
                    organization_id=org_b.id
                )
            )

            db.flush()

        # ---------------------------------------------------------
        # CAMPUSES
        # ---------------------------------------------------------

        campus_a = db.scalar(
            select(Campus).where(
                Campus.organization_id == org_a.id
            )
        )

        campus_b = db.scalar(
            select(Campus).where(
                Campus.organization_id == org_b.id
            )
        )

        if campus_a is None:
            campus_a = Campus(
                organization_id=org_a.id,
                name="Main Campus A",
                code="A-MAIN",
            )

            db.add(campus_a)
            db.flush()

        if campus_b is None:
            campus_b = Campus(
                organization_id=org_b.id,
                name="Main Campus B",
                code="B-MAIN",
            )

            db.add(campus_b)
            db.flush()

        # ---------------------------------------------------------
        # DEPARTMENTS
        # ---------------------------------------------------------

        dept_a = db.scalar(
            select(Department).where(
                Department.organization_id == org_a.id
            )
        )

        dept_b = db.scalar(
            select(Department).where(
                Department.organization_id == org_b.id
            )
        )

        if dept_a is None:
            dept_a = Department(
                organization_id=org_a.id,
                campus_id=campus_a.id,
                name="Computer Science A",
                code="CSA",
            )

            db.add(dept_a)
            db.flush()

        if dept_b is None:
            dept_b = Department(
                organization_id=org_b.id,
                campus_id=campus_b.id,
                name="Computer Science B",
                code="CSB",
            )

            db.add(dept_b)
            db.flush()

        # ---------------------------------------------------------
        # PROGRAMS
        # ---------------------------------------------------------

        prog_a = db.scalar(
            select(Program).where(
                Program.organization_id == org_a.id
            )
        )

        prog_b = db.scalar(
            select(Program).where(
                Program.organization_id == org_b.id
            )
        )

        if prog_a is None:
            prog_a = Program(
                organization_id=org_a.id,
                department_id=dept_a.id,
                name="BS Software Engineering",
                code="BSSE-A",
                duration_years=4,
            )

            db.add(prog_a)
            db.flush()

        if prog_b is None:
            prog_b = Program(
                organization_id=org_b.id,
                department_id=dept_b.id,
                name="BS Computer Science",
                code="BSCS-B",
                duration_years=4,
            )

            db.add(prog_b)
            db.flush()

        # ---------------------------------------------------------
        # ACADEMIC SESSIONS
        # ---------------------------------------------------------

        sess_a = db.scalar(
            select(AcademicSession).where(
                AcademicSession.organization_id == org_a.id
            )
        )

        sess_b = db.scalar(
            select(AcademicSession).where(
                AcademicSession.organization_id == org_b.id
            )
        )

        if sess_a is None:
            sess_a = AcademicSession(
                organization_id=org_a.id,
                code="2026-27",
                name="2026-2027",
            )

            db.add(sess_a)
            db.flush()

        if sess_b is None:
            sess_b = AcademicSession(
                organization_id=org_b.id,
                code="2026-27",
                name="2026-2027",
            )

            db.add(sess_b)
            db.flush()

        # ---------------------------------------------------------
        # SEMESTERS
        # ---------------------------------------------------------

        sem_a = db.scalar(
            select(Semester).where(
                Semester.organization_id == org_a.id
            )
        )

        sem_b = db.scalar(
            select(Semester).where(
                Semester.organization_id == org_b.id
            )
        )

        if sem_a is None:
            sem_a = Semester(
                organization_id=org_a.id,
                academic_session_id=sess_a.id,
                code="FALL-2026",
                name="Fall 2026",
            )

            db.add(sem_a)
            db.flush()

        if sem_b is None:
            sem_b = Semester(
                organization_id=org_b.id,
                academic_session_id=sess_b.id,
                code="FALL-2026",
                name="Fall 2026",
            )

            db.add(sem_b)
            db.flush()

        # ---------------------------------------------------------
        # PHASE 5 ACADEMIC STRUCTURE
        # ---------------------------------------------------------
        sess_a.is_current = True
        sess_b.is_current = True

        section_a = db.scalar(select(Section).where(Section.organization_id == org_a.id, Section.section_code == "BSSE-A"))
        if section_a is None:
            section_a = Section(organization_id=org_a.id, semester_id=sem_a.id, program_id=prog_a.id, section_code="BSSE-A", capacity=40)
            db.add(section_a); db.flush()
        section_b = db.scalar(select(Section).where(Section.organization_id == org_b.id, Section.section_code == "BSCS-B"))
        if section_b is None:
            section_b = Section(organization_id=org_b.id, semester_id=sem_b.id, program_id=prog_b.id, section_code="BSCS-B", capacity=40)
            db.add(section_b); db.flush()

        def course_for(org_id, code, department_id, title, credits, ctype):
            x = db.scalar(select(Course).where(Course.organization_id == org_id, Course.course_code == code))
            if x is None:
                x = Course(organization_id=org_id, department_id=department_id, course_code=code, title=title, credit_hours=credits, course_type=ctype)
                db.add(x); db.flush()
            return x

        cs101 = course_for(org_a.id, "SE-101", dept_a.id, "Programming Fundamentals", 3, CourseType.CORE)
        ds201 = course_for(org_a.id, "SE-201", dept_a.id, "Data Structures", 3, CourseType.CORE)
        dbs301 = course_for(org_a.id, "SE-301", dept_a.id, "Database Systems", 3, CourseType.CORE)
        b101 = course_for(org_b.id, "CS-101", dept_b.id, "Introduction to Computing", 3, CourseType.CORE)
        b201 = course_for(org_b.id, "CS-201", dept_b.id, "Data Structures", 3, CourseType.CORE)

        def prereq(course, prerequisite):
            if db.scalar(select(CoursePrerequisite).where(CoursePrerequisite.organization_id == course.organization_id, CoursePrerequisite.course_id == course.id, CoursePrerequisite.prerequisite_course_id == prerequisite.id)) is None:
                db.add(CoursePrerequisite(organization_id=course.organization_id, course_id=course.id, prerequisite_course_id=prerequisite.id))
        prereq(ds201, cs101); prereq(dbs301, cs101)

        def curriculum(program, course, semester):
            if db.scalar(select(ProgramCourse).where(ProgramCourse.organization_id == program.organization_id, ProgramCourse.program_id == program.id, ProgramCourse.course_id == course.id)) is None:
                db.add(ProgramCourse(organization_id=program.organization_id, program_id=program.id, course_id=course.id, recommended_semester_id=semester.id, is_required=True))
        curriculum(prog_a, cs101, sem_a); curriculum(prog_a, ds201, sem_a); curriculum(prog_a, dbs301, sem_a)
        curriculum(prog_b, b101, sem_b); curriculum(prog_b, b201, sem_b)

        # ---------------------------------------------------------
        # USERS
        # ---------------------------------------------------------

        # Platform-level identity.
        # organization_id is intentionally NULL.
        get_or_create_user(
            db,
            organization_id=None,
            email="superadmin@example.com",
            full_name="Platform Super Admin",
            role=UserRole.SUPER_ADMIN,
        )

        get_or_create_user(
            db,
            organization_id=org_a.id,
            email="admin.a@example.com",
            full_name="University A Admin",
            role=UserRole.UNIVERSITY_ADMIN,
        )

        get_or_create_user(
            db,
            organization_id=org_b.id,
            email="admin.b@example.com",
            full_name="College B Admin",
            role=UserRole.UNIVERSITY_ADMIN,
        )

        teacher_a = get_or_create_user(
            db,
            organization_id=org_a.id,
            email="teacher.a@example.com",
            full_name="Teacher A",
            role=UserRole.TEACHER,
        )

        teacher_b = get_or_create_user(
            db,
            organization_id=org_b.id,
            email="teacher.b@example.com",
            full_name="Teacher B",
            role=UserRole.TEACHER,
        )

        student_user_a = get_or_create_user(
            db,
            organization_id=org_a.id,
            email="student.a@example.com",
            full_name="Student A",
            role=UserRole.STUDENT,
        )

        student_user_b = get_or_create_user(
            db,
            organization_id=org_b.id,
            email="student.b@example.com",
            full_name="Student B",
            role=UserRole.STUDENT,
        )

        # ---------------------------------------------------------
        # STUDENTS
        # ---------------------------------------------------------

        student_a = db.scalar(
            select(Student).where(
                Student.organization_id == org_a.id
            )
        )

        student_b = db.scalar(
            select(Student).where(
                Student.organization_id == org_b.id
            )
        )

        if student_a is None:
            student_a = Student(
                organization_id=org_a.id,
                user_id=student_user_a.id,
                student_number="A-001",
                program_id=prog_a.id,
                academic_session_id=sess_a.id,
            )

            db.add(student_a)
            db.flush()

        if student_b is None:
            student_b = Student(
                organization_id=org_b.id,
                user_id=student_user_b.id,
                student_number="B-001",
                program_id=prog_b.id,
                academic_session_id=sess_b.id,
            )

            db.add(student_b)
            db.flush()

        # ---------------------------------------------------------
        # TEACHERS
        # ---------------------------------------------------------

        teacher_record_a = db.scalar(
            select(Teacher).where(
                Teacher.organization_id == org_a.id
            )
        )

        teacher_record_b = db.scalar(
            select(Teacher).where(
                Teacher.organization_id == org_b.id
            )
        )

        if teacher_record_a is None:
            db.add(
                Teacher(
                    organization_id=org_a.id,
                    user_id=teacher_a.id,
                    employee_number="A-T-001",
                    department_id=dept_a.id,
                )
            )

        if teacher_record_b is None:
            db.add(
                Teacher(
                    organization_id=org_b.id,
                    user_id=teacher_b.id,
                    employee_number="B-T-001",
                    department_id=dept_b.id,
                )
            )

        db.flush()
        teacher_record_a = db.scalar(select(Teacher).where(Teacher.organization_id == org_a.id, Teacher.user_id == teacher_a.id))
        teacher_record_b = db.scalar(select(Teacher).where(Teacher.organization_id == org_b.id, Teacher.user_id == teacher_b.id))
        def offering(org_id, course, section, sess, sem, teacher):
            x=db.scalar(select(CourseOffering).where(CourseOffering.organization_id==org_id, CourseOffering.course_id==course.id, CourseOffering.section_id==section.id, CourseOffering.semester_id==sem.id))
            if x is None:
                x=CourseOffering(organization_id=org_id,course_id=course.id,section_id=section.id,academic_session_id=sess.id,semester_id=sem.id,teacher_id=teacher.id if teacher else None,max_students=section.capacity)
                db.add(x); db.flush()
            return x
        off_a=offering(org_a.id,ds201,section_a,sess_a,sem_a,teacher_record_a)
        off_b=offering(org_b.id,b201,section_b,sess_b,sem_b,teacher_record_b)
        if db.scalar(select(Enrollment).where(Enrollment.organization_id==org_a.id,Enrollment.student_id==student_a.id,Enrollment.course_offering_id==off_a.id)) is None:
            db.add(Enrollment(organization_id=org_a.id,student_id=student_a.id,course_offering_id=off_a.id))
        if db.scalar(select(Enrollment).where(Enrollment.organization_id==org_b.id,Enrollment.student_id==student_b.id,Enrollment.course_offering_id==off_b.id)) is None:
            db.add(Enrollment(organization_id=org_b.id,student_id=student_b.id,course_offering_id=off_b.id))

        # ---------------------------------------------------------
        # COMMIT
        # ---------------------------------------------------------

        db.commit()

        print("Phase 3 development seed complete.")
        print(
            f"Development password for all seeded accounts: {DEV_PASSWORD}"
        )
        print("Organizations: dev-university-a, dev-college-b")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()