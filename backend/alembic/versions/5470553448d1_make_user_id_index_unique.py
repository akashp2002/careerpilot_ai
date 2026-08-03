"""make user_id index unique

Revision ID: 5470553448d1
Revises: eb5f416e86c1
Create Date: 2026-07-31 23:46:05.754062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5470553448d1'
down_revision: Union[str, Sequence[str], None] = 'eb5f416e86c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_candidate_profiles_user_id', table_name='candidate_profiles')
    op.create_index(
        op.f('ix_candidate_profiles_user_id'),
        'candidate_profiles',
        ['user_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_candidate_profiles_user_id'), table_name='candidate_profiles')
    op.create_index(
        op.f('ix_candidate_profiles_user_id'),
        'candidate_profiles',
        ['user_id'],
        unique=False,
    )