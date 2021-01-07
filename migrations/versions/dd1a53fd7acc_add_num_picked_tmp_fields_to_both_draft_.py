"""Add num_picked_tmp fields to both Draft and Pack models

Revision ID: dd1a53fd7acc
Revises: 06fe4ec0936e
Create Date: 2021-01-07 14:20:20.377391

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd1a53fd7acc'
down_revision = '06fe4ec0936e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('draft', sa.Column('num_picked_tmp', sa.Integer(), nullable=True))
    op.add_column('pack', sa.Column('num_picked_tmp', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pack', 'num_picked_tmp')
    op.drop_column('draft', 'num_picked_tmp')
    # ### end Alembic commands ###
