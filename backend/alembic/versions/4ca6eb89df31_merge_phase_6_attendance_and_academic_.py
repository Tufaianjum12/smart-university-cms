"""merge phase 6 attendance and academic session heads

Revision ID: 4ca6eb89df31
Revises: 0005_phase6_attendance, 133574b36f2a
Create Date: 2026-09-18 15:34:23.614946
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '4ca6eb89df31'
down_revision: Union[str, None] = ('0005_phase6_attendance', '133574b36f2a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
