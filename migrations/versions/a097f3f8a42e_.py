"""empty message

Revision ID: a097f3f8a42e
Revises: 045addf59332
Create Date: 2020-10-16 09:04:23.962889

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a097f3f8a42e'
down_revision = '045addf59332'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pack', sa.Column('scarred_this_round_id', sa.Integer(), nullable=True))
    op.add_column('scar', sa.Column('locked_by_id', sa.Integer(), nullable=True))
    op.add_column('scar', sa.Column('locked_pack_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('scar', 'locked_pack_id')
    op.drop_column('scar', 'locked_by_id')
    op.drop_column('pack', 'scarred_this_round_id')
    # ### end Alembic commands ###