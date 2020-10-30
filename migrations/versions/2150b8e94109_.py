"""empty message

Revision ID: 2150b8e94109
Revises: b29598d633cc
Create Date: 2020-10-29 18:01:04.596337

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2150b8e94109'
down_revision = 'b29598d633cc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pack_card', sa.Column('sideboard', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pack_card', 'sideboard')
    # ### end Alembic commands ###