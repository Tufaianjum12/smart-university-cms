"""Phase 6 attendance management.

Migrates the legacy Phase 1 attendance record shape into session-based
attendance while preserving existing records.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_phase6_attendance"
down_revision = "0004_phase5_courses_enrollment"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attendance_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_offering_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("topic", sa.String(300), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "id", name="uq_attendance_sessions_org_id"),
        sa.UniqueConstraint(
            "organization_id", "course_offering_id", "session_date", "start_time",
            name="uq_attendance_session_context",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "course_offering_id"],
            ["course_offerings.organization_id", "course_offerings.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "created_by_user_id"],
            ["users.organization_id", "users.id"],
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_attendance_sessions_org_offering_date",
        "attendance_sessions",
        ["organization_id", "course_offering_id", "session_date"],
    )
    op.create_index(
        "ix_attendance_sessions_org_date",
        "attendance_sessions",
        ["organization_id", "session_date"],
    )

    # Add new columns as nullable while legacy rows are migrated.
    op.add_column(
        "attendance_records",
        sa.Column("attendance_session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "attendance_records",
        sa.Column("remarks", sa.Text(), nullable=True),
    )
    op.add_column(
        "attendance_records",
        sa.Column("marked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "attendance_records",
        sa.Column("marked_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Preserve old records by creating one session per offering/date pair.
    op.execute("""
        INSERT INTO attendance_sessions
            (id, organization_id, course_offering_id, session_date,
             status, created_by_user_id, created_at, updated_at)
        SELECT
            md5(ar.organization_id::text || e.course_offering_id::text || ar.attendance_date::text)::uuid,
            ar.organization_id,
            e.course_offering_id,
            ar.attendance_date,
            'completed',
            MIN(ar.recorded_by_user_id::text)::uuid,
            MIN(ar.created_at),
            MAX(ar.updated_at)
        FROM attendance_records ar
        JOIN enrollments e
          ON e.organization_id = ar.organization_id
         AND e.id = ar.enrollment_id
        GROUP BY
            ar.organization_id,
            e.course_offering_id,
            ar.attendance_date
    """)

    op.execute("""
        UPDATE attendance_records ar
        SET attendance_session_id = s.id,
            remarks = ar.note,
            marked_at = ar.created_at,
            marked_by_user_id = ar.recorded_by_user_id
        FROM enrollments e, attendance_sessions s
        WHERE e.organization_id = ar.organization_id
          AND e.id = ar.enrollment_id
          AND s.organization_id = ar.organization_id
          AND s.course_offering_id = e.course_offering_id
          AND s.session_date = ar.attendance_date
    """)

    # The old unique constraint is no longer valid because a course can have
    # multiple sessions and records are unique per session + enrollment.
    op.drop_constraint(
        "uq_attendance_enrollment_date",
        "attendance_records",
        type_="unique",
    )
    op.drop_index("ix_attendance_org_enrollment_date", table_name="attendance_records")
    op.drop_column("attendance_records", "attendance_date")
    op.drop_column("attendance_records", "recorded_by_user_id")
    op.drop_column("attendance_records", "note")

    op.alter_column("attendance_records", "attendance_session_id", nullable=False)
    op.alter_column(
        "attendance_records",
        "marked_at",
        nullable=False,
        server_default=sa.func.now(),
    )
    op.alter_column("attendance_records", "marked_by_user_id", nullable=False)

    op.create_foreign_key(
        "attendance_records_org_session_fkey",
        "attendance_records",
        "attendance_sessions",
        ["organization_id", "attendance_session_id"],
        ["organization_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "attendance_records_org_marked_by_fkey",
        "attendance_records",
        "users",
        ["organization_id", "marked_by_user_id"],
        ["organization_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_attendance_session_enrollment",
        "attendance_records",
        ["organization_id", "attendance_session_id", "enrollment_id"],
    )
    op.create_index(
        "ix_attendance_records_org_session",
        "attendance_records",
        ["organization_id", "attendance_session_id"],
    )
    op.create_index(
        "ix_attendance_records_org_enrollment",
        "attendance_records",
        ["organization_id", "enrollment_id"],
    )
    op.create_index(
        "ix_attendance_records_org_status",
        "attendance_records",
        ["organization_id", "status"],
    )


def downgrade():
    raise RuntimeError(
        "Phase 6 downgrade is intentionally blocked because attendance data "
        "was migrated from date-based records to session-based records."
    )
