"""empty message

Revision ID: c3f55e2c75a9
Revises: 37a0b78bc901
Create Date: 2020-10-04 14:44:17.584992

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f55e2c75a9'
down_revision = '37a0b78bc901'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scar', sa.Column('draft_id', sa.Integer(), nullable=True, comment='The draft in which this scar was applied, if any.'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('scar', 'draft_id')
    # ### end Alembic commands ###
