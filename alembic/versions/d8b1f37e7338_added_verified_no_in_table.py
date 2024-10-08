"""added verified no in table

Revision ID: d8b1f37e7338
Revises: ea0935b6203a
Create Date: 2024-10-04 16:43:17.485304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8b1f37e7338'
down_revision: Union[str, None] = 'ea0935b6203a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('players', sa.Column('verified', sa.Boolean(), server_default=sa.text('false'), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('players', 'verified')
    # ### end Alembic commands ###
