"""Add a set code field on cubes

Revision ID: 89b1b4ef1e03
Revises: dd1a53fd7acc
Create Date: 2021-01-10 15:33:26.249302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89b1b4ef1e03'
down_revision = 'dd1a53fd7acc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cube', sa.Column('set_code', sa.String(length=16), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cube', 'set_code')
    # ### end Alembic commands ###
