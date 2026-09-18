"""Phase 4 university CMS foundation.

Adds current-session state and makes section course optional so the section
administration foundation can exist before the later Course phase.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_phase4_cms"
down_revision = "0002_authentication"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("academic_sessions", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("sections", "course_id", existing_type=sa.UUID(), nullable=True)


def downgrade():
    # Downgrade is only safe if no course-less sections exist.
    op.alter_column("sections", "course_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("academic_sessions", "is_current")
