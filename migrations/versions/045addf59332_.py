"""empty message

Revision ID: 045addf59332
Revises: 16710174381b
Create Date: 2020-10-14 19:20:14.733380

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '045addf59332'
down_revision = '16710174381b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('achievement', sa.Column('finalized_timestamp', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('achievement', 'finalized_timestamp')
    # ### end Alembic commands ###
