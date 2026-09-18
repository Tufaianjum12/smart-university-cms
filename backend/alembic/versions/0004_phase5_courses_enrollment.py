"""Phase 5 course management and enrollment."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_phase5_courses_enrollment"
down_revision = "0003_phase4_cms"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    postgresql.ENUM("core","elective","lab","theory","project","other", name="course_type").create(bind, checkfirst=True)
    op.add_column("courses", sa.Column("course_type", postgresql.ENUM("core","elective","lab","theory","project","other", name="course_type", create_type=False), nullable=True))
    op.execute("UPDATE courses SET course_type = 'theory' WHERE course_type IS NULL")
    op.alter_column("courses", "course_type", nullable=False, server_default="theory")

    op.create_table("program_courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommended_semester_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id","id",name="uq_program_courses_org_id"),
        sa.UniqueConstraint("organization_id","program_id","course_id",name="uq_program_course"),
        sa.ForeignKeyConstraint(["organization_id","program_id"],["programs.organization_id","programs.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id","course_id"],["courses.organization_id","courses.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id","recommended_semester_id"],["semesters.organization_id","semesters.id"],ondelete="RESTRICT"),
    )
    op.create_index("ix_program_courses_org_program","program_courses",["organization_id","program_id"])

    op.create_table("course_offerings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True)),
        sa.Column("max_students", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id","id",name="uq_course_offerings_org_id"),
        sa.UniqueConstraint("organization_id","course_id","section_id","semester_id",name="uq_course_offering_context"),
        sa.CheckConstraint("max_students IS NULL OR max_students > 0",name="ck_offering_capacity"),
        sa.ForeignKeyConstraint(["organization_id","course_id"],["courses.organization_id","courses.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id","section_id"],["sections.organization_id","sections.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id","academic_session_id"],["academic_sessions.organization_id","academic_sessions.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id","semester_id"],["semesters.organization_id","semesters.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id","teacher_id"],["teachers.organization_id","teachers.id"],ondelete="RESTRICT"),
    )
    for name, cols in [("ix_offerings_org_course",["organization_id","course_id"]),("ix_offerings_org_section",["organization_id","section_id"]),("ix_offerings_org_teacher",["organization_id","teacher_id"])]: op.create_index(name,"course_offerings",cols)

    # Convert the old Phase-4 section-based enrollment shape to the Phase-5 offering shape.
    op.add_column("enrollments", sa.Column("course_offering_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("enrollments", sa.Column("dropped_at", sa.DateTime(timezone=True)))
    op.create_table("_phase5_offering_backfill",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    )
    op.execute("""INSERT INTO _phase5_offering_backfill (organization_id,course_id,section_id,semester_id,id) SELECT organization_id,course_id,id,semester_id,id FROM sections WHERE course_id IS NOT NULL""")
    op.execute("""INSERT INTO course_offerings (id,organization_id,course_id,section_id,academic_session_id,semester_id,is_active,created_at,updated_at) SELECT b.id,b.organization_id,b.course_id,b.section_id,sess.id,b.semester_id,TRUE,now(),now() FROM _phase5_offering_backfill b JOIN semesters sem ON sem.organization_id=b.organization_id AND sem.id=b.semester_id JOIN academic_sessions sess ON sess.organization_id=sem.organization_id AND sess.id=sem.academic_session_id ON CONFLICT DO NOTHING""")
    op.execute("""UPDATE enrollments e SET course_offering_id=b.id FROM _phase5_offering_backfill b WHERE e.organization_id=b.organization_id AND e.section_id=b.section_id""")
    op.drop_table("_phase5_offering_backfill")
    op.drop_constraint("uq_enrollment_student_section","enrollments",type_="unique")
    op.drop_constraint("enrollments_organization_id_section_id_fkey","enrollments",type_="foreignkey")
    op.drop_column("enrollments","section_id")
    op.alter_column("enrollments","course_offering_id",nullable=False)
    op.create_foreign_key("enrollments_organization_id_course_offering_id_fkey","enrollments","course_offerings",["organization_id","course_offering_id"],["organization_id","id"],ondelete="RESTRICT")
    op.create_unique_constraint("uq_enrollment_student_offering","enrollments","organization_id","student_id","course_offering_id")
    op.create_index("ix_enrollments_org_offering","enrollments",["organization_id","course_offering_id"])

def downgrade():
    raise RuntimeError("Phase 5 downgrade is intentionally blocked because enrollment migration is data-sensitive; restore a backup before reverting.")
