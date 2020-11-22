"""empty message

Revision ID: aea33c6d093c
Revises: b722bc009264
Create Date: 2020-11-21 16:39:12.246415

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'aea33c6d093c'
down_revision = 'b722bc009264'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('state_json_a', mysql.MEDIUMTEXT(), nullable=True))
    op.drop_column('game', 'state_json_uni')
    op.drop_column('game', 'state_json')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('state_json', mysql.TEXT(), nullable=True))
    op.add_column('game', sa.Column('state_json_uni', mysql.TEXT(), nullable=True))
    op.drop_column('game', 'state_json_a')
    # ### end Alembic commands ###
