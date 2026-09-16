"""add academic session current flag

Revision ID: d447b9cf8698
Revises: 0002_authentication
Create Date: 2026-09-16 10:02:31.553936
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d447b9cf8698"

down_revision: Union[str, None] = "0002_authentication"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "academic_sessions",
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "academic_sessions",
        "is_current",
    )