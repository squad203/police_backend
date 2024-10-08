"""added kills in getTeames

Revision ID: effa6f2a9812
Revises: c032e9ebdfcb
Create Date: 2024-07-13 00:43:49.723015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'effa6f2a9812'
down_revision: Union[str, None] = 'c032e9ebdfcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('teams', sa.Column('kills', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('teams', 'kills')
    # ### end Alembic commands ###
