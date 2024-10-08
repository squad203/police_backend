"""Added martch table

Revision ID: f097f8fafd80
Revises: 6720f76bcc4e
Create Date: 2024-07-17 22:36:59.763516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f097f8fafd80'
down_revision: Union[str, None] = '6720f76bcc4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bgmi_matches', 'match_name',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bgmi_matches', 'match_name',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    # ### end Alembic commands ###
