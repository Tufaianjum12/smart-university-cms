"""merge phase 5 and academic session heads

Revision ID: 133574b36f2a
Revises: 0004_phase5_courses_enrollment, d447b9cf8698
Create Date: 2026-09-16 21:35:28.082362
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '133574b36f2a'
down_revision: Union[str, None] = ('0004_phase5_courses_enrollment', 'd447b9cf8698')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
