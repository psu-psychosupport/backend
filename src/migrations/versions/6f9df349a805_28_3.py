"""28_3

Revision ID: 6f9df349a805
Revises: d4b9bfff451c
Create Date: 2024-04-28 16:20:08.071732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f9df349a805'
down_revision: Union[str, None] = 'd4b9bfff451c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('unique_post', 'posts', ['category_id', 'subcategory_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_post', 'posts', type_='unique')
    # ### end Alembic commands ###
