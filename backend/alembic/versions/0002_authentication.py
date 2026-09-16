"""add authentication fields and user roles"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_authentication"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    role_enum = postgresql.ENUM(
        "super_admin", "university_admin", "department_admin", "teacher", "student", "parent_guardian",
        name="user_role",
    )
    role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("role", role_enum, nullable=True))

    # Existing Phase-2 seed users have no passwords/roles. Give them a safe migration
    # default only so the schema can be upgraded; Phase-3 seed_dev replaces these with
    # real development credentials.
    op.execute("UPDATE users SET password_hash = 'MIGRATE_WITH_PHASE3_SEED', role = 'student' WHERE password_hash IS NULL")
    op.alter_column("users", "password_hash", nullable=False)
    op.alter_column("users", "role", nullable=False)


def downgrade():
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)
